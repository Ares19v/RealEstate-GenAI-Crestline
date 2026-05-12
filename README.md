<div align="center">

# Crestline Shreshth — AI Real Estate Marketing Pipeline

**Custom LoRA Fine-Tuning · ComfyUI Automation · AnimateDiff Video Generation**

[![CI — Validate Pipeline](https://github.com/Ares19v/RealEstate-GenAI-Crestline/actions/workflows/ci.yml/badge.svg)](https://github.com/Ares19v/RealEstate-GenAI-Crestline/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Stable Diffusion 1.5](https://img.shields.io/badge/Base_Model-SD_1.5-7C3AED)](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5)
[![AnimateDiff](https://img.shields.io/badge/Video-AnimateDiff_v3-E11D48)](https://github.com/guoyww/AnimateDiff)
[![Kohya_ss](https://img.shields.io/badge/Training-Kohya__ss-F59E0B)](https://github.com/kohya-ss/sd-scripts)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)

*A production-grade generative AI pipeline that fine-tunes Stable Diffusion on a real estate property's architecture, then automates photorealistic image and video marketing asset generation — on demand, at zero marginal cost per output.*

</div>

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [What This Pipeline Does](#2-what-this-pipeline-does)
3. [Architecture](#3-architecture)
4. [Technical Deep-Dive](#4-technical-deep-dive)
5. [Dataset Engineering](#5-dataset-engineering)
6. [Training Configuration](#6-training-configuration)
7. [Quick Start](#7-quick-start)
8. [Image Generation](#8-image-generation)
9. [Video Generation](#9-video-generation)
10. [Prompt Library](#10-prompt-library)
11. [Automation Scripts](#11-automation-scripts)
12. [Project Structure](#12-project-structure)
13. [V1 → V2: What Was Wrong & How It Was Fixed](#13-v1--v2-what-was-wrong--how-it-was-fixed)
14. [Retraining](#14-retraining)
15. [Roadmap](#15-roadmap)
16. [Acknowledgements](#16-acknowledgements)

---

## 1. The Problem

When advertising agencies market luxury real estate, they face two expensive constraints:

- **3D rendering studios** charge ₹5,000–₹25,000 per image and take days to deliver
- **Generic AI generators** produce random buildings every time — unusable for brand-consistent marketing

This project eliminates both problems. By fine-tuning Stable Diffusion with LoRA on the actual Crestline Shreshth property, the model **memorizes the building's exact architectural identity**. Two trigger words (`CrestlineExt`, `CrestlineInt`) reliably reproduce it in any lighting, angle, or cinematic composition — at zero cost per image.

---

## 2. What This Pipeline Does

```
Training Phase (one-time, ~90 min on RTX 5060)
  32 architectural photos  →  LoRA fine-tuning  →  Crestline_Shreshth_v2.safetensors

Generation Phase (on demand, seconds per image / ~10 min per video)
  CrestlineExt + prompt   →  ComfyUI             →  768×1024 exterior PNG
  CrestlineInt + prompt   →  ComfyUI             →  768×1024 interior PNG
  Any still image         →  AnimateDiff Img2Vid →  768×432 MP4 video clip
```

**Key capabilities:**
- ✅ Photorealistic exterior shots — any time of day, any weather, any angle
- ✅ Interior amenity renders — pool, gym, library, lobby, spa, meditation room
- ✅ Animated video clips from stills — 2-second MP4s for social media / presentations
- ✅ Batch generation via Python API — unattended overnight runs
- ✅ 30 curated prompt presets + 12 video presets, immediately usable
- ✅ Fully automated deployment — one `launch.bat` sets everything up

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRAINING PHASE                               │
│                                                                     │
│  Raw Photos (32)                                                    │
│       │                                                             │
│       ▼                                                             │
│  Caption Engineering ──── WD14 auto-tag + manual refinement         │
│  ├── dataset/20_CrestlineExt/   (11 images, trigger: CrestlineExt)  │
│  └── dataset/20_CrestlineInt/   (21 images, trigger: CrestlineInt)  │
│       │                                                             │
│       ▼                                                             │
│  Kohya_ss LoRA Training                                             │
│  ├── Base: SD 1.5 (2.1 GB)                                          │
│  ├── Optimizer: AdamW8bit | Precision: bf16 | Res: 768px            │
│  ├── Network: dim=32, alpha=16 | Steps: 1,920 | Epochs: 6           │
│  └── Loss: 0.13 → 0.11 (healthy convergence, no overfit)            │
│       │                                                             │
│       ▼                                                             │
│  Crestline_Shreshth_v2.safetensors  (~7 MB)                         │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                     GENERATION PHASE                                │
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────────────────────┐ │
│  │   IMAGE PIPELINE    │    │          VIDEO PIPELINE             │ │
│  │                     │    │                                     │ │
│  │  ComfyUI Studio     │    │  AnimateDiff (Text-to-Video)        │ │
│  │  ├── SD 1.5 base    │    │  ├── SD 1.5 + LoRA + motion module  │ │
│  │  ├── LoRA plugin    │    │  ├── 16 frames @ 8fps               │ │
│  │  ├── KSampler       │    │  └── 768×432 MP4 output             │ │
│  │  │   30 steps       │    │                                     │ │
│  │  │   CFG 6.5        │    │  AnimateDiff (Image-to-Video)       │ │
│  │  │   dpmpp_2m       │    │  ├── Load any generated still       │ │
│  │  │   karras         │    │  ├── RepeatImageBatch × 16          │ │
│  │  └── 768×1024 PNG   │    │  ├── VAE encode → KSampler          │ │
│  │                     │    │  │   denoise=0.65 (gentle motion)   │ │
│  │  30 prompt presets  │    │  └── MP4 via VideoHelperSuite       │ │
│  └─────────────────────┘    └─────────────────────────────────────┘ │
│                                      │                              │
│                             outputs/ folder                         │
│                             PNG renders + MP4 clips                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Deep-Dive

### What is LoRA?

LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning technique. Rather than retraining Stable Diffusion's entire 860M-parameter UNet (which would cost ~4 days of GPU time), LoRA injects two small trainable matrices (`A` and `B`) alongside the existing frozen weight matrices (`W₀`):

```
Output = W₀x + ΔWx,   where ΔW = B·A   (B ∈ ℝᵐˣʳ, A ∈ ℝʳˣⁿ, rank r ≪ n)
```

With `network_dim = 32` (rank = 32), the LoRA updates roughly **0.37% of the UNet's parameters**, producing a ~7 MB file that permanently alters the model's output without touching the base weights.

### Why These Specific Hyperparameters

| Parameter | Value | Reasoning |
|---|---|---|
| `network_dim` (rank) | 32 | Low rank = compact. 32 gives enough capacity for 32 distinct architectural elements without overfitting a 32-image dataset. |
| `network_alpha` | 16 | Alpha controls effective learning rate as `alpha/dim`. Setting `alpha = dim/2` is the industry standard for stable training — avoids the alpha=1 instability of v1. |
| `resolution` | 768×768 | SD 1.5's attention layers process images as 96×96 latent patches. At 512px, fine facade details (glass texture, railing geometry) fall below the patch resolution. 768px preserves them. |
| `mixed_precision` | bf16 | RTX 5060 (Ada Lovelace) has dedicated bf16 tensor cores. bf16 has a wider dynamic range than fp16 (8-bit exponent vs 5-bit), preventing gradient overflow during high-loss early training. |
| `optimizer` | AdamW8bit | Stores optimizer states in 8-bit integers — cuts VRAM usage by ~40% vs standard AdamW with no meaningful quality loss. Enables batch_size=2 on 8GB VRAM. |
| `lr_scheduler` | cosine | Cosine decay prevents the optimizer from making large updates at the end of training that could overwrite fine detail learned in earlier epochs. |
| `epoch` | 6 | Math: (11 ext × 20 rep) + (21 int × 20 rep) = 640 images/epoch. batch_size=2 → 320 steps/epoch × 6 = 1,920 total steps. Sufficient for convergence without overfitting. |

### Training Loss Curve

```
Step    0:  loss ≈ 0.130  ← AI generating pure noise, maximum error
Step  320:  loss ≈ 0.127  ← Epoch 1: basic shapes emerging
Step  640:  loss ≈ 0.118  ← Epoch 2: facade geometry recognized
Step  960:  loss ≈ 0.114  ← Epoch 3: material textures learning
Step 1280:  loss ≈ 0.112  ← Epoch 4: trigger words firmly associated
Step 1600:  loss ≈ 0.121  ← Epoch 5: slight variance (normal)
Step 1920:  loss ≈ 0.111  ← Epoch 6 final: converged, stable
```

> Loss plateau at ~0.11 is expected for architectural data. Lower would indicate overfitting (the model memorizes photos instead of learning to regenerate them from noise).

### AnimateDiff — How Img2Vid Works

The img2vid pipeline exploits AnimateDiff's temporal attention layers:

```
Input still image
       │
       ▼
VAE Encode → latent z₀  (single frame, shape [1, 4, 54, 96])
       │
       ▼
RepeatImageBatch × 16 → latents [16, 4, 54, 96]  (16 identical frames)
       │
       ▼
Add noise at timestep T·denoise  (denoise=0.65 → moderate noise)
       │
       ▼
KSampler + AnimateDiff motion module
  → Temporal attention creates inter-frame variance
  → Each frame denoises slightly differently
  → Result: 16 frames of coherent motion
       │
       ▼
VAEDecode → 16 RGB frames → VHS_VideoCombine → MP4 @ 8fps
```

The `denoise` value controls how much the image can "drift":
- **0.4** — subtle shimmer, building almost unchanged
- **0.65** — default: natural ambient motion (light wind, subtle light shift)
- **0.8** — strong motion, may deviate from original framing

---

## 5. Dataset Engineering

| Subset | Folder | Images | Repeats | Trigger Word | Caption Method |
|---|---|---|---|---|---|
| Exterior | `20_CrestlineExt/` | 11 | 20× | `CrestlineExt` | WD14 + manual |
| Interior | `20_CrestlineInt/` | 21 | 20× | `CrestlineInt` | Hand-written |
| **Total** | | **32** | | | **640 training images/epoch** |

### The Folder Math
The `20_` prefix tells Kohya_ss to repeat each image 20 times per epoch, giving the model sufficient exposure to each photo without requiring hundreds of raw images. This is standard practice for small-dataset LoRA training.

### Caption Strategy
Each image has a paired `.txt` caption file. Captions serve two critical functions:

1. **Isolation**: Tag only architectural elements, not ambient elements like sky color or weather (which we want the model to vary freely)
2. **Trigger association**: Every caption begins with the trigger word, firmly linking `CrestlineExt`/`CrestlineInt` to the property's visual identity

**Example caption** (`Swimming pool 1-1.txt`):
```
CrestlineInt, indoors, no humans, swimming pool, turquoise water, poolside,
modern pool area, ambient lighting, luxury amenity, tiles, residential complex
```

---

## 6. Training Configuration

Full config: [`training/config_lora_v2.toml`](training/config_lora_v2.toml)

**Hardware:** HP Omen 16 · NVIDIA RTX 5060 8GB VRAM · Windows 11

```toml
# Network
network_module  = "networks.lora"
network_dim     = 32      # LoRA rank
network_alpha   = 16      # Effective LR scale = alpha/dim = 0.5

# Resolution & Bucketing
resolution            = "768,768"
enable_bucket         = true
bucket_no_upscale     = true   # Preserves native aspect ratios

# Optimizer
optimizer_type        = "AdamW8bit"
learning_rate         = 0.0001
lr_scheduler          = "cosine"

# Training duration
epoch                 = 6
max_train_steps       = 1920
train_batch_size      = 2

# Precision
mixed_precision       = "bf16"   # Native to RTX 5060 Ada architecture
save_precision        = "bf16"
```

---

## 7. Quick Start

### Prerequisites
- [ComfyUI Desktop App](https://github.com/comfyanonymous/ComfyUI/releases)
- `Crestline_Shreshth_v2.safetensors` in `models/` (see [Retraining](#14-retraining) if not present)
- Python 3.10+ (for batch scripts only)

### 1. Launch the Studio

```bat
launch.bat
```

This automatically:
- Copies the LoRA into ComfyUI's `models/loras/`
- Deploys all 4 workflows into ComfyUI's workflow browser
- Opens the ComfyUI interface

### 2. Install Script Dependencies

```bash
pip install -r scripts/requirements.txt
```

---

## 8. Image Generation

### Manual (ComfyUI)

In ComfyUI, open the **Browse** panel and load a workflow:

| Workflow | Use Case | Output |
|---|---|---|
| `Crestline_Exterior_v2` | Building exteriors | 768×1024 PNG |
| `Crestline_Interior_v2` | Amenity interiors | 768×1024 PNG |

Edit the positive prompt text and hit **Queue Prompt**. Generated images save to ComfyUI's output folder and the project's `outputs/` directory.

### Batch (Python Script)

```bash
# All 15 exterior presets
python scripts/batch_generate.py --mode exterior

# All 15 interior presets
python scripts/batch_generate.py --mode interior

# Both sets, limit to 5, fixed seed for reproducibility
python scripts/batch_generate.py --mode all --count 5 --seed 42

# Single preset by ID
python scripts/batch_generate.py --mode exterior --id EXT_007
```

Outputs: `outputs/batch_YYYYMMDD_HHMMSS/<ID>_<Label>.png`

### Sample Prompt Structure

```json
{
  "id": "EXT_001",
  "label": "Golden Hour Hero Shot",
  "positive": "CrestlineExt, high-end modern residential skyscraper, glass balconies, golden hour lighting, cinematic, 8k",
  "negative": "blurry, low quality, people, watermark",
  "cfg": 6.5,
  "steps": 30
}
```

---

## 9. Video Generation

> **One-time setup required.** See [`docs/VIDEO_SETUP.md`](docs/VIDEO_SETUP.md) for the full AnimateDiff installation guide.

### Prerequisites
- **AnimateDiff-Evolved** custom node (install via ComfyUI Manager)
- **VideoHelperSuite** custom node (install via ComfyUI Manager)
- **Motion module:** `v3_sd15_mm.ckpt` → `ComfyUI/models/animatediff_models/`

### Method A: Animate a Still You Already Generated (Recommended)

```bash
# Animate a single image
python scripts/batch_video.py img2vid --input "outputs/batch_xxx/EXT_001_Golden_Hour.png"

# Animate an entire batch folder
python scripts/batch_video.py img2vid --input-dir "outputs/batch_20260511_120000"

# Control motion intensity
python scripts/batch_video.py img2vid --input "render.png" --denoise 0.5
```

### Method B: Generate Video Directly from Text

```bash
# Exterior video prompts
python scripts/batch_video.py txt2vid --scene exterior

# Interior video prompts
python scripts/batch_video.py txt2vid --scene interior

# First 3 only, fixed seed
python scripts/batch_video.py txt2vid --scene all --count 3 --seed 42
```

### Manual (ComfyUI)

| Workflow | Description | Settings |
|---|---|---|
| `Crestline_AnimateDiff_Img2Vid_v1` | Animate any existing still | Load image → adjust denoise → Queue |
| `Crestline_AnimateDiff_Txt2Vid_v1` | Generate video from prompt | Edit prompt → Queue |

**Output specs:** 768×432 · 16 frames · 8 fps · ~2 seconds · H.264 MP4

---

## 10. Prompt Library

All prompts live in `prompts/` and are consumed by both the manual workflows and batch scripts.

| File | Count | Type | Coverage |
|---|---|---|---|
| `exterior_prompts.json` | 15 | Image | Golden hour, night, aerial, fog, B&W, billboard, drone, rain, symmetrical, etc. |
| `interior_prompts.json` | 15 | Image | Pool, gym, library, lobby, spa, meditation, rooftop, indoor garden, play area, etc. |
| `video_prompts.json` | 12 | Video | Exterior: 7 cinematic scenes · Interior: 5 amenity animations |

Each entry has `id`, `label`, `positive`, `negative`, `cfg`, and `steps`. Add your own freely — scripts pick them up automatically.

---

## 11. Automation Scripts

### `scripts/batch_generate.py` — Image Batch Generation

Talks to ComfyUI's REST API, injects prompts into the workflow graph by node class type (not hardcoded IDs), polls `/history` for completion, and downloads outputs.

```
ComfyUI API: POST /prompt → poll /history/{id} → GET /view?filename=...
```

### `scripts/batch_video.py` — Video Batch Generation

Two sub-commands with different pipelines:

```
txt2vid:  prompts → workflow injection → ComfyUI API → MP4
img2vid:  image → copy to ComfyUI input/ → workflow injection → ComfyUI API → MP4
```

| Feature | Detail |
|---|---|
| Timestamped output folders | `outputs/batch_YYYYMMDD_HHMMSS/` |
| Graceful error handling | Per-job try/catch, continues on failure |
| ComfyUI health check | Exits cleanly if ComfyUI not running |
| Reproducible seeds | `--seed` flag for deterministic outputs |
| Motion intensity control | `--denoise 0.4–0.8` for img2vid |

---

## 12. Project Structure

```
RealEstate-GenAI-Crestline/
│
├── .github/
│   └── workflows/ci.yml          → CI: Python lint, JSON/TOML validation,
│                                       dataset integrity, required files check
├── .gitignore                    → Excludes models, outputs, PREP.txt
├── LICENSE                       → MIT
├── README.md                     → This file
├── launch.bat                    → One-click deploy + launch ComfyUI
│
├── dataset/
│   ├── 20_CrestlineExt/          → 11 exterior images + .txt captions
│   └── 20_CrestlineInt/          → 21 interior images + .txt captions
│
├── docs/
│   └── VIDEO_SETUP.md            → AnimateDiff install guide
│
├── models/                       → LoRA weights — gitignored, never committed
│   └── Crestline_Shreshth_v2.safetensors
│
├── outputs/                      → Generated assets — gitignored
│   ├── batch_YYYYMMDD/           → Image batch runs
│   └── video_batch_YYYYMMDD/     → Video batch runs
│
├── prompts/
│   ├── exterior_prompts.json     → 15 image presets (exterior)
│   ├── interior_prompts.json     → 15 image presets (interior)
│   └── video_prompts.json        → 12 video presets (7 ext + 5 int)
│
├── scripts/
│   ├── batch_generate.py         → Image batch CLI (ComfyUI REST API)
│   ├── batch_video.py            → Video batch CLI (txt2vid + img2vid)
│   └── requirements.txt          → requests, websocket-client
│
├── training/
│   ├── config_lora_v2.toml       → Full Kohya_ss training configuration
│   └── sample_prompt.txt         → Monitor prompts evaluated every 320 steps
│
└── workflows/
    ├── Crestline_Exterior_v2.json          → Image: exterior shots
    ├── Crestline_Interior_v2.json          → Image: interior spaces
    ├── Crestline_AnimateDiff_Txt2Vid_v1.json → Video: text-to-video
    └── Crestline_AnimateDiff_Img2Vid_v1.json → Video: animate a still image
```

---

## 13. V1 → V2: What Was Wrong & How It Was Fixed

The v1 model (`Crestline_Shreshth_v1.safetensors`) was trained with 8 critical errors. V2 addresses every one:

| # | Problem | V1 | V2 (Fixed) | Impact |
|---|---|---|---|---|
| 1 | **Resolution** | 512×512 | 768×768 | Facade material detail below patch threshold at 512px |
| 2 | **LoRA rank** | `dim=8` | `dim=32` | 8 had insufficient capacity for 32 architectural concepts |
| 3 | **Alpha instability** | `alpha=1` on `dim=8` | `alpha=16` on `dim=32` | alpha/dim=0.125 caused extreme weight updates |
| 4 | **Precision** | `fp16` | `bf16` | RTX 5060 bf16 tensor cores unused; fp16 prone to overflow |
| 5 | **Interior trigger** | `CrestlineExt` (wrong) | `CrestlineInt` | Interior workflow produced exterior shots |
| 6 | **Output node** | `PreviewImage` | `SaveImage` | Renders saved to `/temp/`, deleted on restart |
| 7 | **Interior captions** | None | 21 hand-tuned files | Model learned shapes but not semantic concepts |
| 8 | **Sampler** | euler + simple + 20 steps | dpmpp_2m + karras + 30 steps | Marketing quality requires slower, higher-quality sampling |

---

## 14. Retraining

To add new property photos and retrain:

**1. Add images and captions**
```
dataset/20_CrestlineExt/NewShot.jpg
dataset/20_CrestlineExt/NewShot.txt   ← "CrestlineExt, [describe elements]"
```

**2. Launch training** (PowerShell, Kohya venv active)
```powershell
cd C:\kohya_ss
C:\kohya_ss\venv\Scripts\python.exe -m accelerate.commands.launch `
  --num_cpu_threads_per_process 2 sd-scripts\train_network.py `
  --config_file "C:\path\to\RealEstate-GenAI-Crestline\training\config_lora_v2.toml"
```

**3. Pick the best epoch**

Six checkpoints are saved automatically (`v2-000001` through `v2-000005`). Compare sample images in `models/sample/` — the best result is typically **epoch 4 or 5**.

---

## 15. Roadmap

- [ ] **Upscaling node** — chain Real-ESRGAN 4× into image workflows for print-ready 4K output
- [ ] **Regularization dataset** — add class images to prevent model drift on full retrain
- [ ] **Extended dataset** — 80+ images for night, rain, drone, and seasonal lighting coverage
- [ ] **Motion LoRAs** — add pan/zoom/tilt camera control to AnimateDiff workflows
- [ ] **SVD img2vid** — Stable Video Diffusion for premium 4–6s hero clips
- [ ] **ControlNet depth** — guide generation from hand-drawn building layouts

---

## 16. Acknowledgements

- **[Stability AI](https://stability.ai/)** — Stable Diffusion v1.5 base model
- **[kohya-ss](https://github.com/kohya-ss/sd-scripts)** — LoRA training framework
- **[comfyanonymous](https://github.com/comfyanonymous/ComfyUI)** — ComfyUI node-based generation interface
- **[Kosinkadink](https://github.com/Kosinkadink)** — AnimateDiff-Evolved + VideoHelperSuite
- **[guoyww](https://github.com/guoyww/AnimateDiff)** — AnimateDiff motion modules

---

<div align="center">

Built with purpose for the **Crestline Shreshth** real estate development · MIT License · 2026

</div>
