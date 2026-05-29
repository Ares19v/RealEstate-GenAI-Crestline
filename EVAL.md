# EVAL — RealEstate-GenAI-Crestline

> **Evaluation Date:** 2026-05-29  
> **Evaluator:** Automated Portfolio Review  
> **Maturity Level:** MVP

---

## 1. Project Purpose & Problem Statement

Real estate marketing agencies pay ₹5,000–₹25,000 per 3D render and wait days for delivery — or use generic AI generators that produce a different building every generation. Crestline Shreshth solves this by fine-tuning Stable Diffusion 1.5 with LoRA on 32 photographs of the actual Crestline Shreshth residential property, permanently encoding the building's architectural identity into two trigger words (`CrestlineExt` for exteriors, `CrestlineInt` for interiors). The result is a pipeline that generates photorealistic, brand-consistent marketing assets — exterior shots in any lighting, interior amenity renders, and animated 2-second MP4 clips via AnimateDiff — at zero marginal cost per output.

This is the sister project to Healthcare-GenAI-Helios; the two share the same LoRA fine-tuning methodology but are adapted to different commercial verticals and include distinct lessons learned between V1 and V2.

---

## 2. Technical Architecture

**Training Phase:**
1. 32 property photographs deposited into `dataset/20_CrestlineExt/` (11 images) and `dataset/20_CrestlineInt/` (21 images)
2. Caption engineering: exterior images auto-tagged via WD14 SwinV2 + manual refinement; interior images hand-captioned (no WD14, as interior semantic tags require human judgment for real estate vocabulary)
3. Kohya_ss LoRA training at 768×768 resolution (vs 512px in V1 — a key improvement for facade detail preservation)
4. Output: `Crestline_Shreshth_v2.safetensors` (~7 MB, bf16)

**Generation Phase — Image:**
- ComfyUI with KSampler (dpmpp_2m / karras / 30 steps / CFG 6.5) → 768×1024 PNG
- `batch_generate.py` calls ComfyUI REST API, injects from 30 curated prompt presets (15 exterior, 15 interior) by node class type
- Timestamped output folders with per-preset naming

**Generation Phase — Video:**
- AnimateDiff-Evolved + VideoHelperSuite custom nodes
- Txt2Vid: direct text-to-video from prompt library (12 video presets)
- Img2Vid: `RepeatImageBatch × 16 → add noise → KSampler + AnimateDiff motion module → VAEDecode → MP4` — a clean exploitation of AnimateDiff temporal attention for "breathing life" into generated stills
- Output: 768×432, 16 frames, 8 fps, H.264 MP4

---

## 3. Model / Algorithm Details

**Base Model:** Stable Diffusion v1.5

**Fine-tuning Method:** LoRA (rank=32, alpha=16) via Kohya_ss sd-scripts

**Key Hyperparameters:**
| Parameter | Value | Reasoning |
|---|---|---|
| Resolution | 768×768 | Facade detail below patch threshold at 512px (V1 lesson) |
| LoRA rank | 32 | Up from 8 in V1; insufficient capacity was a root cause of V1 failure |
| LoRA alpha | 16 | alpha/dim = 0.5; V1 had alpha=1 on dim=8 causing extreme updates |
| Precision | bf16 | RTX 5060 native; prevents gradient overflow vs fp16 |
| Optimizer | AdamW8bit | ~40% VRAM reduction |
| LR scheduler | cosine | Prevents late-epoch destructive updates |
| Epochs | 6 | 640 images/epoch × 6 = 1,920 total steps |

**Training Loss Curve:** 0.130 → 0.111 (healthy convergence, no overfit spike in final epoch)

**V1 → V2 Improvements:** The V1/V2 comparison table in the README is exceptional — 8 specific errors in V1 (wrong resolution, insufficient rank, alpha instability, wrong precision, swapped trigger words, PreviewImage vs SaveImage output, missing interior captions, low-quality sampler) all identified and corrected in V2. This demonstrates genuine debugging methodology rather than trial-and-error.

---

## 4. Strengths

- **V1 → V2 documented post-mortem** — explicitly listing 8 V1 errors with root causes and fixes is rare in portfolio projects and demonstrates real engineering discipline.
- **Img2Vid pipeline is technically elegant** — the `RepeatImageBatch → noise → KSampler + AnimateDiff` chain correctly exploits temporal attention for coherent ambient motion with controllable intensity via `denoise` parameter.
- **Prompt library at scale** — 30 image presets + 12 video presets with parameterized cfg/steps/sampler/seed is production-ready for a non-technical marketing user.
- **768×768 resolution** — correct upgrade from 512px; preserves architectural detail that falls below the 96×96 latent patch threshold at lower resolution.
- **`batch_generate.py` node class injection** — injecting by class type rather than hardcoded node IDs is a robust design that survives ComfyUI workflow schema changes.
- **`launch.bat` auto-deploys LoRA and workflows** — one-click deployment that copies weights and workflow JSONs to the correct ComfyUI directories is excellent DX.
- **GitHub Actions CI** — Python lint, JSON/TOML validation, dataset integrity, required files check.
- **`journey.md` documents the AnimateDiff pipeline math** in detail — RepeatImageBatch, denoise parameter effects, and fps/frame math are all explained.

---

## 5. Limitations & Known Gaps

- **SD 1.5 base model is aging.** Same limitation as Healthcare-GenAI-Helios — the industry has moved to SDXL, Flux, and SDXL-Lightning. SD 1.5 at 768px is the ceiling; modern luxury real estate marketing expects 4K+ photorealism.
- **Only 32 unique training images.** 11 exterior shots is particularly thin — covering only a subset of building angles, lighting conditions, and weather. Night shots, fog, and aerial perspectives are under-represented, requiring prompting to compensate.
- **No quantitative output quality metrics.** No FID, no CLIP-image similarity, no SSIM against real property photos. All evaluation is qualitative (viewing generated images).
- **AnimateDiff videos are 2 seconds at 8fps.** This is sufficient for a social media loop but not for a property walkthrough video or presentation clip; SVD (Stable Video Diffusion) would produce higher-quality longer clips.
- **No regularization dataset.** Standard practice for preventing concept drift on full retrains includes adding generic architecture images; not implemented.
- **ComfyUI prerequisite is heavy.** Users need a separate ComfyUI Desktop installation before the pipeline is usable; the README documents this clearly but it remains a significant setup barrier.
- **`PREP.txt` is gitignored** — its content (presumably client briefing or personal notes) is not accessible, which is correct but means some context is lost.

---

## 6. Code Quality Assessment

**Structure:** Mirrors Healthcare-GenAI-Helios architecture with clear `dataset/`, `docs/`, `models/`, `outputs/`, `prompts/`, `scripts/`, `training/`, `workflows/` separation. Consistent and clean.

**Documentation:** README is the second-most detailed in the portfolio after Healthcare-GenAI-Helios. The V1/V2 comparison table, AnimateDiff pipeline math, and training loss curve are all valuable technical depth. `docs/VIDEO_SETUP.md` covers AnimateDiff prerequisites.

**Test Coverage:** CI validates schema and file structure. No functional inference tests.

**Security:** `.gitignore` properly excludes models, outputs, `PREP.txt`. No API keys in the generation pipeline (ComfyUI runs locally).

---

## 7. Maturity Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Functionality | 7/10 | Both image and video pipelines working; limited by SD 1.5 ceiling |
| Code Quality | 7/10 | Clean structure; robust API injection pattern |
| Documentation | 9/10 | Exceptional — V1→V2 post-mortem and loss curve are standout |
| Scalability | 5/10 | Local only; ComfyUI dependency; no automated quality filtering |
| Security | 8/10 | Properly gitignores sensitive files; synthetic/real-property data distinction |
| **Overall** | **7.2/10** | Strong methodological depth; SD 1.5 ceiling limits practical output quality |

---

## 8. Suggested Next Steps

1. **Migrate to SDXL 1.0 or Flux.1** base model and retrain. SDXL LoRA at 1024×1024 would produce dramatically better architectural detail and photorealism — the difference in output quality for luxury real estate would be visible immediately.
2. **Expand the exterior dataset to 30+ images** covering night, golden hour, overcast, aerial (drone), and rain conditions — the current 11 exterior images under-constrain the model for diverse lighting scenarios.
3. **Add a real property photo vs generated output comparison section to the README.** Side-by-side comparisons with actual Crestline Shreshth photographs would demonstrate trigger word effectiveness far more convincingly than generated images alone.

---

## 9. Verdict

RealEstate-GenAI-Crestline is a more mature iteration of the Helios pipeline, improved by honest documentation of V1 failures and eight specific technical fixes. The V1→V2 post-mortem table is the best piece of technical writing in the portfolio — it demonstrates debugging methodology, not just final results. The img2vid AnimateDiff pipeline is technically elegant and the prompt library is production-usable. The project is limited by the same SD 1.5 ceiling as Helios, and the thin exterior dataset (11 images) constrains lighting and angle diversity. A migration to a modern backbone and dataset expansion would be transformative for the practical output quality.
