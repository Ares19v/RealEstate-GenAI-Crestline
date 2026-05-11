# Crestline Shreshth — AI Real Estate Marketing Pipeline

[![CI — Validate Pipeline](https://github.com/Ares19v/RealEstate-GenAI-Crestline/actions/workflows/ci.yml/badge.svg)](https://github.com/Ares19v/RealEstate-GenAI-Crestline/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Stable Diffusion 1.5](https://img.shields.io/badge/Base_Model-SD_1.5-purple)](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An automated, AI-driven architectural pipeline that uses a custom-trained **LoRA** and **ComfyUI** to generate brand-consistent, photorealistic marketing assets for the **Crestline Shreshth** real estate development — on demand, at zero marginal cost.

---

## The Problem This Solves

Standard AI image generators are random. Ask for "a modern luxury building" and you get a different building every time — useless for brand-consistent real estate marketing.

This pipeline solves that by using **LoRA (Low-Rank Adaptation)** fine-tuning to force Stable Diffusion to memorize the exact architectural identity of Crestline Shreshth: its glass balcony system, facade materials, and interior amenity spaces. After training, two trigger words (`CrestlineExt` / `CrestlineInt`) reliably reproduce the actual building in any lighting, angle, or cinematic composition.

---

## Pipeline Architecture

```
 Raw Photos (32 images)
        │
        ▼
 Caption Engineering          ← WD14 auto-captioning + manual refinement
 (dataset/20_CrestlineExt/    ← Trigger word: CrestlineExt
  dataset/20_CrestlineInt/)   ← Trigger word: CrestlineInt
        │
        ▼
 LoRA Training (Kohya_ss)     ← SD 1.5 base + AdamW8bit + bf16
 config_lora_v2.toml          ← dim=32, alpha=16, res=768px, 1920 steps
        │
        ▼
 Crestline_Shreshth_v2.safetensors   ← The trained LoRA (~7MB)
        │
        ▼
 ComfyUI Generation Studio
 ├── Crestline_Exterior_v2.json      ← Exterior workflow
 └── Crestline_Interior_v2.json      ← Interior workflow
        │
        ▼
 outputs/                     ← Final marketing assets (PNG)
```

---

## Hardware & Environment

| Component | Spec |
|---|---|
| GPU | NVIDIA RTX 5060 (8GB VRAM) |
| Laptop | HP Omen 16 |
| Training Software | Kohya_ss |
| Generation Software | ComfyUI (Desktop App) |
| Base Model | Stable Diffusion v1.5 |
| Precision | bf16 (Brain Float 16) |

---

## Dataset

| Subset | Images | Repeats | Trigger Word |
|---|---|---|---|
| Exterior (`20_CrestlineExt`) | 11 | 20× | `CrestlineExt` |
| Interior (`20_CrestlineInt`) | 21 | 20× | `CrestlineInt` |
| **Total training steps** | **640 × 3 epochs** | | **1,920 steps** |

Each image has a hand-tuned `.txt` caption file isolating architectural elements from background noise.

---

## Quick Start

### Prerequisites
- ComfyUI Desktop App installed
- The trained LoRA (`Crestline_Shreshth_v2.safetensors`) in `models/`
- Python 3.10+ (for batch generation script only)

### 1. Launch the Studio
```bat
double-click launch.bat
```
This automatically deploys the LoRA and workflows into ComfyUI and opens the interface.

### 2. Generate Images Manually
In ComfyUI, load either workflow from the **Browse** panel:
- `Crestline_Exterior_v2` — for building exteriors
- `Crestline_Interior_v2` — for amenity interiors

Edit the positive prompt and hit **Queue Prompt**.

### 3. Batch Generate via Script
Install dependencies:
```bash
pip install -r scripts/requirements.txt
```

Run a batch:
```bash
# All exterior prompts
python scripts/batch_generate.py --mode exterior

# All interior prompts
python scripts/batch_generate.py --mode interior

# Both, first 5 only, fixed seed
python scripts/batch_generate.py --mode all --count 5 --seed 42

# Specific prompt by ID
python scripts/batch_generate.py --mode exterior --id EXT_007
```

Outputs are saved to `outputs/batch_YYYYMMDD_HHMMSS/` with descriptive filenames.

---

## Prompt Library

The `prompts/` directory contains curated, tested prompt sets:

| File | Count | Coverage |
|---|---|---|
| `exterior_prompts.json` | 15 | Golden hour, night, aerial, fog, B&W, billboard crop, drone, etc. |
| `interior_prompts.json` | 15 | Pool, gym, library, lobby, spa, meditation room, rooftop, etc. |

Each prompt entry has an `id`, `label`, `positive`, `negative`, `cfg`, and `steps` field. Add your own entries freely — the batch script picks them up automatically.

---

## Project Structure

```
RealEstate-GenAI-Crestline/
│
├── .github/workflows/ci.yml      → CI pipeline (validates all project files)
├── .gitignore                    → Excludes models, outputs, personal notes
├── LICENSE                       → MIT
├── README.md                     → This file
├── launch.bat                    → One-click: deploy + launch ComfyUI
│
├── dataset/
│   ├── 20_CrestlineExt/          → 11 exterior images + captions
│   └── 20_CrestlineInt/          → 21 interior images + captions
│
├── models/                       → Trained LoRA weights (gitignored)
│   └── Crestline_Shreshth_v2.safetensors
│
├── prompts/
│   ├── exterior_prompts.json     → 15 exterior prompt presets
│   └── interior_prompts.json     → 15 interior prompt presets
│
├── scripts/
│   ├── batch_generate.py         → ComfyUI API batch generation script
│   └── requirements.txt          → Python deps (requests, websocket-client)
│
├── training/
│   ├── config_lora_v2.toml       → Corrected training configuration
│   └── sample_prompt.txt         → Monitoring prompts used during training
│
├── workflows/
│   ├── Crestline_Exterior_v2.json → ComfyUI exterior generation workflow
│   └── Crestline_Interior_v2.json → ComfyUI interior generation workflow
│
└── outputs/                      → Generated assets (gitignored)
```

---

## Retraining

If you add new images to the dataset and want to retrain:

```powershell
# In PowerShell, with Kohya_ss installed at C:\kohya_ss\
cd C:\kohya_ss
C:\kohya_ss\venv\Scripts\python.exe -m accelerate.commands.launch `
  --num_cpu_threads_per_process 2 sd-scripts\train_network.py `
  --config_file "C:\path\to\RealEstate-GenAI-Crestline\training\config_lora_v2.toml"
```

Training takes ~90 minutes on an RTX 5060. Six epoch checkpoints are saved automatically — compare the sample images in `models/sample/` to pick the best one.

---

## V1 → V2 Improvements

| Issue | V1 | V2 (Current) |
|---|---|---|
| Resolution | 512×512 (thumbnail quality) | 768×768 (full detail) |
| LoRA capacity | `dim=8` (too small) | `dim=32` (4× more memory) |
| LoRA strength | `alpha=1` (unstable) | `alpha=16` (stable, half of dim) |
| Precision | `fp16` | `bf16` (native to RTX 5060) |
| Interior trigger | Used `CrestlineExt` (wrong) | Uses `CrestlineInt` (correct) |
| Output saving | `PreviewImage` (temp only) | `SaveImage` (persisted to disk) |
| Interior captions | None | 21 hand-tuned caption files |

---

## License

MIT — see [LICENSE](LICENSE).
