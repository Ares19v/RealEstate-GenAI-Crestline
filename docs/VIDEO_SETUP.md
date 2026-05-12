# Video Pipeline Setup Guide
## AnimateDiff + ComfyUI — One-Time Installation

This guide walks through everything you need to install before the video
workflows and batch_video.py script will work. You only do this once.

---

## Step 1 — Install Custom Nodes via ComfyUI Manager

Open ComfyUI (run `launch.bat`), then click **Manager** in the top-right menu.

### 2a. AnimateDiff-Evolved
1. Click **Install Custom Nodes**
2. Search: `AnimateDiff Evolved`
3. Find the one by **Kosinkadink** — click **Install**
4. Click **Restart** when done

### 2b. ComfyUI-VideoHelperSuite
1. Still in **Install Custom Nodes**
2. Search: `VideoHelperSuite`
3. Find the one by **Kosinkadink** — click **Install**
4. Click **Restart** when done

---

## Step 2 — Download the Motion Module

The motion module is the AnimateDiff brain (~1.7 GB). Download one of these:

| File | Quality | Recommended |
|---|---|---|
| `v3_sd15_mm.ckpt` | Best quality | ✅ Use this one |
| `mm_sd_v15_v2.ckpt` | Good, smaller | Fallback |

**Download from HuggingFace:**
```
https://huggingface.co/guoyww/animatediff/tree/main
```
Look for `v3_sd15_mm.ckpt` and download it directly.

**Place it here:**
```
C:\Users\Devansh Tyagi\Documents\ComfyUI\models\animatediff_models\v3_sd15_mm.ckpt
```

Create the `animatediff_models` folder if it doesn't exist.

---

## Step 3 — Verify FFmpeg (for MP4 export)

The ComfyUI Desktop App ships with FFmpeg bundled. To check:

```powershell
# Open PowerShell and run:
ffmpeg -version
```

If it's not found, download from: https://www.gyan.dev/ffmpeg/builds/
(Download the "release essentials" ZIP, extract, add to PATH)

---

## Step 4 — Test the Setup

1. Run `launch.bat` to open ComfyUI
2. In ComfyUI, go to **Browse Workflows**
3. Load `Crestline_AnimateDiff_Txt2Vid_v1`
4. In the `ADE_AnimateDiffLoaderWithContext` node, select `v3_sd15_mm.ckpt`
5. Hit **Queue Prompt**
6. Expected time: ~8–12 minutes for a 16-frame clip on RTX 5060

If it errors with **"AnimateDiff Evolved not found"** → Step 1 wasn't done yet.
If it errors with **"model not found"** → Motion module not in the right folder.

---

## How to Use the Two Video Workflows

### Workflow A: Txt2Vid (`Crestline_AnimateDiff_Txt2Vid_v1`)
- Generates video purely from text, using the LoRA trigger words
- Good for: quick content, social media loops, motion posters
- Edit the positive prompt node, hit Queue Prompt

### Workflow B: Img2Vid (`Crestline_AnimateDiff_Img2Vid_v1`)
- Animates an existing still image you already generated
- Good for: hero clips, premium presentations, best-of-batch animation
- **How to use:**
  1. Generate your best still image using the normal image workflows
  2. In the `LoadImage` node, click **Upload** and select your PNG
  3. Adjust `denoise` in the KSampler node:
     - `0.4` = very subtle motion (barely moves)
     - `0.65` = default gentle motion (recommended)
     - `0.8` = strong motion (may drift from original)
  4. Hit Queue Prompt

---

## Batch Script Usage

```bash
# Animate all exterior prompts from text:
python scripts/batch_video.py txt2vid --scene exterior

# Animate all interior prompts from text:
python scripts/batch_video.py txt2vid --scene interior

# Animate a specific still image:
python scripts/batch_video.py img2vid --input "outputs/batch_xxx/EXT_001_Golden_Hour.png"

# Animate all images in an entire batch folder:
python scripts/batch_video.py img2vid --input-dir "outputs/batch_20260511_120000"

# Gentle motion (0.5) on a single image:
python scripts/batch_video.py img2vid --input "my_render.png" --denoise 0.5
```

---

## Output

All videos are saved to:
```
outputs/
  video_batch_YYYYMMDD_HHMMSS/     ← txt2vid outputs
    VID_EXT_001_Golden_Hour.mp4
    VID_EXT_002_Blue_Hour.mp4
    ...
  video_img2vid_YYYYMMDD_HHMMSS/   ← img2vid outputs
    EXT_001_Golden_Hour_animated.mp4
    ...
```

---

## Hardware Notes (RTX 5060 8GB)

| Setting | Value |
|---|---|
| Resolution | 768 × 432 (16:9) |
| Frames | 16 |
| FPS | 8 |
| Output length | ~2 seconds |
| Time per clip | 8–12 minutes |
| VRAM peak | ~7–7.5 GB |

If you get out-of-memory errors, reduce to 512 × 288 in the `EmptyLatentImage` node.
