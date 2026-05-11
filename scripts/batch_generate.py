#!/usr/bin/env python3
"""
batch_generate.py — Crestline Shreshth AI Batch Generation Script

Connects to a running ComfyUI instance via its REST API and queues a batch
of image generation jobs from the prompt library. All runs are saved to
outputs/batch_YYYYMMDD_HHMMSS/ with descriptive filenames.

USAGE
-----
  # ComfyUI must be running first (use launch.bat or open manually)

  # Generate all exterior prompts:
  python scripts/batch_generate.py --mode exterior

  # Generate all interior prompts:
  python scripts/batch_generate.py --mode interior

  # Generate both:
  python scripts/batch_generate.py --mode all

  # Limit to first N prompts:
  python scripts/batch_generate.py --mode exterior --count 5

  # Use a fixed seed (reproducible results):
  python scripts/batch_generate.py --mode exterior --seed 42

  # Target a specific prompt by ID:
  python scripts/batch_generate.py --mode exterior --id EXT_001

  # Custom ComfyUI host (if not using default):
  python scripts/batch_generate.py --mode all --host 127.0.0.1 --port 8188

NOTES
-----
- Manual ComfyUI clicking still works perfectly alongside this script.
- The script polls the ComfyUI /history endpoint to track job completion.
- Output images are saved to: outputs/batch_YYYYMMDD_HHMMSS/<id>_<label>.png
- If ComfyUI is not running, the script will print a clear error and exit.
"""

import argparse
import copy
import json
import os
import sys
import time
import urllib.request
import urllib.error
import uuid
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
WORKFLOWS_DIR = REPO_ROOT / "workflows"
OUTPUTS_DIR = REPO_ROOT / "outputs"

EXTERIOR_PROMPTS = PROMPTS_DIR / "exterior_prompts.json"
INTERIOR_PROMPTS = PROMPTS_DIR / "interior_prompts.json"
EXTERIOR_WORKFLOW = WORKFLOWS_DIR / "Crestline_Exterior_v2.json"
INTERIOR_WORKFLOW = WORKFLOWS_DIR / "Crestline_Interior_v2.json"


# ── ComfyUI API helpers ────────────────────────────────────────────────────────

def check_comfyui(host: str, port: int) -> bool:
    """Return True if ComfyUI is reachable."""
    try:
        url = f"http://{host}:{port}/system_stats"
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def queue_prompt(workflow: dict, host: str, port: int, client_id: str) -> str:
    """POST a workflow to ComfyUI and return the prompt_id."""
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"http://{host}:{port}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["prompt_id"]


def poll_until_done(prompt_id: str, host: str, port: int, timeout: int = 300) -> dict:
    """Poll /history until the prompt_id appears (job complete). Returns history entry."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = f"http://{host}:{port}/history/{prompt_id}"
        try:
            with urllib.request.urlopen(url) as r:
                data = json.loads(r.read())
                if prompt_id in data:
                    return data[prompt_id]
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Job {prompt_id} did not complete within {timeout}s")


def download_image(filename: str, subfolder: str, host: str, port: int, dest: Path):
    """Download a generated image from ComfyUI's /view endpoint."""
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    url = f"http://{host}:{port}/view?{params}"
    urllib.request.urlretrieve(url, dest)


# ── Workflow injection ─────────────────────────────────────────────────────────

def inject_prompt(workflow: dict, positive: str, negative: str,
                  cfg: float, steps: int, seed: int | None) -> dict:
    """
    Inject a prompt entry into the workflow graph.

    Searches for nodes by class_type rather than hardcoded IDs so this works
    even if the workflow node IDs change.
    """
    wf = copy.deepcopy(workflow)

    # Find the KSampler node
    ksampler_id = None
    for node_id, node in wf.items():
        if node.get("class_type") == "KSampler":
            ksampler_id = node_id
            break

    if ksampler_id is None:
        raise ValueError("Could not find a KSampler node in the workflow.")

    ksampler = wf[ksampler_id]

    # Override cfg and steps
    ksampler["inputs"]["cfg"] = cfg
    ksampler["inputs"]["steps"] = steps
    if seed is not None:
        ksampler["inputs"]["seed"] = seed
    else:
        ksampler["inputs"]["seed"] = int(time.time() * 1000) % (2**31)

    # Find connected CLIP text encoder nodes via the KSampler's positive/negative links
    pos_node_id = str(ksampler["inputs"]["positive"][0])
    neg_node_id = str(ksampler["inputs"]["negative"][0])

    wf[pos_node_id]["inputs"]["text"] = positive
    wf[neg_node_id]["inputs"]["text"] = negative

    return wf


# ── Core batch logic ───────────────────────────────────────────────────────────

def load_prompts(path: Path, filter_id: str | None = None) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    prompts = data["prompts"]
    if filter_id:
        prompts = [p for p in prompts if p["id"] == filter_id]
    return prompts


def load_workflow(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_batch(
    prompts: list[dict],
    workflow_path: Path,
    output_dir: Path,
    host: str,
    port: int,
    seed: int | None,
    count: int | None,
):
    import urllib.parse  # noqa: PLC0415 — needed here for download helper

    workflow_base = load_workflow(workflow_path)
    client_id = str(uuid.uuid4())
    output_dir.mkdir(parents=True, exist_ok=True)

    if count:
        prompts = prompts[:count]

    total = len(prompts)
    print(f"\n  Queuing {total} job(s) → {output_dir.name}/\n")

    for i, entry in enumerate(prompts, 1):
        label_safe = entry["label"].replace(" ", "_").replace("/", "-").replace("—", "-")
        out_path = output_dir / f"{entry['id']}_{label_safe}.png"

        print(f"  [{i}/{total}] {entry['id']} — {entry['label']}")

        wf = inject_prompt(
            workflow_base,
            positive=entry["positive"],
            negative=entry["negative"],
            cfg=entry.get("cfg", 6.5),
            steps=entry.get("steps", 30),
            seed=seed,
        )

        try:
            prompt_id = queue_prompt(wf, host, port, client_id)
            print(f"           Queued  → prompt_id: {prompt_id[:8]}...")

            history = poll_until_done(prompt_id, host, port, timeout=300)

            # Extract output filename from history
            outputs = history.get("outputs", {})
            saved = False
            for node_out in outputs.values():
                images = node_out.get("images", [])
                for img in images:
                    download_image(img["filename"], img.get("subfolder", ""), host, port, out_path)
                    print(f"           Saved   → {out_path.name}")
                    saved = True
                    break
                if saved:
                    break

            if not saved:
                print(f"           WARNING: No output image found in history for {prompt_id}")

        except TimeoutError as e:
            print(f"           TIMEOUT: {e}")
        except Exception as e:
            print(f"           ERROR:   {e}")

        print()

    print(f"  Batch complete. {total} job(s) processed.")
    print(f"  Output folder: {output_dir}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    import urllib.parse  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description="Crestline Shreshth — ComfyUI Batch Generation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode", choices=["exterior", "interior", "all"], required=True,
        help="Which prompt set to run."
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help="Limit to the first N prompts. Default: run all."
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Fixed seed for reproducible results. Default: random."
    )
    parser.add_argument(
        "--id", dest="prompt_id", default=None,
        help="Run a single prompt by its ID (e.g. EXT_001)."
    )
    parser.add_argument("--host", default="127.0.0.1", help="ComfyUI host.")
    parser.add_argument("--port", type=int, default=8188, help="ComfyUI port.")

    args = parser.parse_args()

    # ── Check ComfyUI is running
    print(f"\n  Checking ComfyUI at {args.host}:{args.port} ...")
    if not check_comfyui(args.host, args.port):
        print("\n  ERROR: Cannot reach ComfyUI.")
        print("  Make sure ComfyUI is running (use launch.bat or open it manually).")
        print("  ComfyUI should be accessible at http://127.0.0.1:8188\n")
        sys.exit(1)
    print("  ComfyUI is reachable. ✓\n")

    # ── Timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_out = OUTPUTS_DIR / f"batch_{timestamp}"

    # ── Run selected mode(s)
    modes_to_run = []
    if args.mode in ("exterior", "all"):
        modes_to_run.append(("exterior", EXTERIOR_PROMPTS, EXTERIOR_WORKFLOW))
    if args.mode in ("interior", "all"):
        modes_to_run.append(("interior", INTERIOR_PROMPTS, INTERIOR_WORKFLOW))

    for mode_name, prompt_file, workflow_file in modes_to_run:
        if not prompt_file.exists():
            print(f"  ERROR: Prompt file not found: {prompt_file}")
            continue
        if not workflow_file.exists():
            print(f"  ERROR: Workflow file not found: {workflow_file}")
            print(f"  Make sure {workflow_file.name} exists in the workflows/ folder.")
            continue

        print(f"  ── {mode_name.upper()} BATCH ──────────────────────────────")
        prompts = load_prompts(prompt_file, filter_id=args.prompt_id)

        if not prompts:
            print(f"  No prompts found (id filter: {args.prompt_id})")
            continue

        out_dir = batch_out / mode_name
        run_batch(prompts, workflow_file, out_dir, args.host, args.port, args.seed, args.count)


if __name__ == "__main__":
    main()
