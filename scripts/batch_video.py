#!/usr/bin/env python3
"""
batch_video.py — Crestline Shreshth AI Batch Video Generation Script

Connects to a running ComfyUI instance and generates MP4 video clips using
AnimateDiff. Supports two modes:

  1. txt2vid  — generate video directly from text prompts (uses the video
                prompt library + AnimateDiff Txt2Vid workflow)

  2. img2vid  — animate an existing still image that you already generated
                with the image pipeline (uses AnimateDiff Img2Vid workflow)

PREREQUISITES (one-time setup — see docs/VIDEO_SETUP.md)
---------
  - AnimateDiff-Evolved custom node installed in ComfyUI
  - ComfyUI-VideoHelperSuite custom node installed in ComfyUI
  - Motion module placed in ComfyUI/models/animatediff_models/v3_sd15_mm.ckpt
  - FFmpeg available (bundled with ComfyUI Desktop, or install separately)

USAGE
-----
  # ComfyUI must be running first (use launch.bat)

  # Text-to-video — all exterior prompts:
  python scripts/batch_video.py --mode txt2vid --scene exterior

  # Text-to-video — all interior prompts:
  python scripts/batch_video.py --mode txt2vid --scene interior

  # Text-to-video — both, first 3 only:
  python scripts/batch_video.py --mode txt2vid --scene all --count 3

  # Img-to-video — animate a specific still image:
  python scripts/batch_video.py --mode img2vid --input "outputs/batch_20260511/EXT_001_Golden_Hour.png"

  # Img-to-video — animate ALL images in a batch folder:
  python scripts/batch_video.py --mode img2vid --input-dir "outputs/batch_20260511_120000"

  # Control motion intensity (img2vid only):
  python scripts/batch_video.py --mode img2vid --input "my_image.png" --denoise 0.5

  # Fixed seed for reproducible results:
  python scripts/batch_video.py --mode txt2vid --scene exterior --seed 42

MOTION INTENSITY (img2vid --denoise)
------
  0.4 — very subtle: barely any movement, image almost unchanged
  0.65 — default: gentle natural motion while preserving building identity
  0.8 — strong motion: more creative, may drift from original image
  1.0 — full generation: ignores image, pure text-to-video
"""

import argparse
import copy
import json
import os
import sys
import time
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
WORKFLOWS_DIR = REPO_ROOT / "workflows"
OUTPUTS_DIR = REPO_ROOT / "outputs"

TXT2VID_WORKFLOW = WORKFLOWS_DIR / "Crestline_AnimateDiff_Txt2Vid_v1.json"
IMG2VID_WORKFLOW = WORKFLOWS_DIR / "Crestline_AnimateDiff_Img2Vid_v1.json"
VIDEO_PROMPTS = PROMPTS_DIR / "video_prompts.json"

COMFYUI_INPUT_DIR = Path(
    r"C:\Users\Devansh Tyagi\Documents\ComfyUI\input"
)


def check_comfyui(host, port):
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/system_stats", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def queue_prompt(workflow, host, port, client_id):
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"http://{host}:{port}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["prompt_id"]


def poll_until_done(prompt_id, host, port, timeout=600):
    """Video generation takes longer — 600s timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://{host}:{port}/history/{prompt_id}"
            ) as r:
                data = json.loads(r.read())
                if prompt_id in data:
                    return data[prompt_id]
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Job {prompt_id} timed out after {timeout}s")


def copy_image_to_comfyui_input(image_path):
    """Copy the source image into ComfyUI's input folder so it can be loaded."""
    src = Path(image_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = COMFYUI_INPUT_DIR / src.name
    import shutil
    shutil.copy2(src, dest)
    return src.name  # return just the filename for the LoadImage node


def inject_txt2vid_prompt(workflow, prompt_entry, seed):
    wf = copy.deepcopy(workflow)
    for node in wf.values():
        if node.get("class_type") == "CLIPTextEncode":
            current = node["inputs"].get("text", "")
            if "CrestlineExt" in current or "CrestlineInt" in current:
                node["inputs"]["text"] = prompt_entry["positive"]
            elif "blurry" in current:
                node["inputs"]["text"] = prompt_entry["negative"]
        elif node.get("class_type") == "KSampler":
            node["inputs"]["cfg"] = prompt_entry.get("cfg", 7.0)
            node["inputs"]["steps"] = prompt_entry.get("steps", 20)
            node["inputs"]["seed"] = seed if seed is not None else int(time.time() * 1000) % (2**31)
    return wf


def inject_img2vid_prompt(workflow, image_filename, prompt_text, neg_text, cfg, steps, denoise, seed):
    wf = copy.deepcopy(workflow)
    for node in wf.values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_filename
        elif node.get("class_type") == "CLIPTextEncode":
            current = node["inputs"].get("text", "")
            if "CrestlineExt" in current or "CrestlineInt" in current or "smooth" in current:
                node["inputs"]["text"] = prompt_text
            elif "blurry" in current or "flickering" in current:
                node["inputs"]["text"] = neg_text
        elif node.get("class_type") == "KSampler":
            node["inputs"]["denoise"] = denoise
            node["inputs"]["cfg"] = cfg
            node["inputs"]["steps"] = steps
            node["inputs"]["seed"] = seed if seed is not None else int(time.time() * 1000) % (2**31)
    return wf


def find_output_video(history):
    """Extract video filename from ComfyUI history."""
    for node_out in history.get("outputs", {}).values():
        for key in ("gifs", "videos"):
            for item in node_out.get(key, []):
                return item.get("filename"), item.get("subfolder", "")
    return None, None


def download_file(filename, subfolder, host, port, dest):
    import urllib.parse
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    urllib.request.urlretrieve(f"http://{host}:{port}/view?{params}", dest)


def run_txt2vid(args):
    data = json.loads(VIDEO_PROMPTS.read_text(encoding="utf-8"))
    scenes = []
    if args.scene in ("exterior", "all"):
        scenes += data.get("exterior", [])
    if args.scene in ("interior", "all"):
        scenes += data.get("interior", [])
    if args.count:
        scenes = scenes[: args.count]

    workflow_base = json.loads(TXT2VID_WORKFLOW.read_text(encoding="utf-8"))
    client_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUTS_DIR / f"video_batch_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Txt2Vid — {len(scenes)} clip(s) → {out_dir.name}/\n")
    for i, entry in enumerate(scenes, 1):
        label_safe = entry["label"].replace(" ", "_").replace("/", "-")
        out_path = out_dir / f"{entry['id']}_{label_safe}.mp4"
        print(f"  [{i}/{len(scenes)}] {entry['id']} — {entry['label']}")

        wf = inject_txt2vid_prompt(workflow_base, entry, args.seed)
        try:
            pid = queue_prompt(wf, args.host, args.port, client_id)
            print(f"           Queued  → {pid[:8]}...")
            history = poll_until_done(pid, args.host, args.port)
            fname, subfolder = find_output_video(history)
            if fname:
                download_file(fname, subfolder, args.host, args.port, out_path)
                print(f"           Saved   → {out_path.name}")
            else:
                print("           WARNING: No video found in output")
        except Exception as e:
            print(f"           ERROR:   {e}")
        print()

    print(f"  Batch complete. Output: {out_dir}\n")


def run_img2vid(args):
    workflow_base = json.loads(IMG2VID_WORKFLOW.read_text(encoding="utf-8"))
    client_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUTS_DIR / f"video_img2vid_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect input images
    images = []
    if args.input:
        images = [Path(args.input)]
    elif args.input_dir:
        images = sorted(Path(args.input_dir).glob("*.png"))
        if not images:
            images = sorted(Path(args.input_dir).glob("*.jpg"))
    if not images:
        print("  ERROR: No input images found. Use --input or --input-dir.")
        sys.exit(1)

    # Generic guide prompts for img2vid (the image drives identity, not the text)
    pos_prompt = "smooth gentle motion, cinematic, photorealistic, architectural photography, ultra-detailed, 8k"
    neg_prompt = "blurry, distorted, cartoon, people, watermark, flickering, jitter, fast motion, noise"

    print(f"\n  Img2Vid — {len(images)} image(s) → {out_dir.name}/\n")
    for i, img_path in enumerate(images, 1):
        out_path = out_dir / (img_path.stem + "_animated.mp4")
        print(f"  [{i}/{len(images)}] {img_path.name}")

        try:
            img_filename = copy_image_to_comfyui_input(img_path)
            print(f"           Copied  → ComfyUI input: {img_filename}")

            wf = inject_img2vid_prompt(
                workflow_base,
                image_filename=img_filename,
                prompt_text=pos_prompt,
                neg_text=neg_prompt,
                cfg=6.0,
                steps=20,
                denoise=args.denoise,
                seed=args.seed,
            )

            pid = queue_prompt(wf, args.host, args.port, client_id)
            print(f"           Queued  → {pid[:8]}...")
            history = poll_until_done(pid, args.host, args.port)
            fname, subfolder = find_output_video(history)
            if fname:
                download_file(fname, subfolder, args.host, args.port, out_path)
                print(f"           Saved   → {out_path.name}")
            else:
                print("           WARNING: No video found in output")
        except Exception as e:
            print(f"           ERROR:   {e}")
        print()

    print(f"  Img2Vid complete. Output: {out_dir}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Crestline — AnimateDiff Batch Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # txt2vid sub-command
    t = sub.add_parser("txt2vid", help="Generate video from text prompts")
    t.add_argument("--scene", choices=["exterior", "interior", "all"], required=True)
    t.add_argument("--count", type=int, default=None)
    t.add_argument("--seed", type=int, default=None)
    t.add_argument("--host", default="127.0.0.1")
    t.add_argument("--port", type=int, default=8188)

    # img2vid sub-command
    v = sub.add_parser("img2vid", help="Animate an existing still image")
    v.add_argument("--input", default=None, help="Path to a single PNG/JPG image")
    v.add_argument("--input-dir", default=None, help="Path to a folder of images to animate")
    v.add_argument("--denoise", type=float, default=0.65, help="Motion intensity 0.4–0.8 (default: 0.65)")
    v.add_argument("--seed", type=int, default=None)
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8188)

    args = parser.parse_args()

    print(f"\n  Checking ComfyUI at {args.host}:{args.port} ...")
    if not check_comfyui(args.host, args.port):
        print("\n  ERROR: Cannot reach ComfyUI. Start it first (launch.bat).\n")
        sys.exit(1)
    print("  ComfyUI reachable. ✓")

    if args.mode == "txt2vid":
        run_txt2vid(args)
    else:
        run_img2vid(args)


if __name__ == "__main__":
    main()
