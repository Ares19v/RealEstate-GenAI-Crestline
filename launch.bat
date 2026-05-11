@echo off
setlocal

echo.
echo  ============================================================
echo   Crestline Shreshth AI Pipeline — Launch Script
echo  ============================================================
echo.

:: ── Paths ─────────────────────────────────────────────────────────────────────
set "COMFYUI_APP=C:\Users\Devansh Tyagi\AppData\Local\Programs\ComfyUI\ComfyUI.exe"
set "COMFYUI_DIR=C:\Users\Devansh Tyagi\Documents\ComfyUI"
set "COMFY_LORA_DIR=%COMFYUI_DIR%\models\loras"
set "COMFY_WORKFLOW_DIR=%COMFYUI_DIR%\user\default\workflows"

set "REPO_LORA=models\Crestline_Shreshth_v2.safetensors"
set "REPO_WORKFLOW_EXT=workflows\Crestline_Exterior_v2.json"
set "REPO_WORKFLOW_INT=workflows\Crestline_Interior_v2.json"

:: ── Check ComfyUI is installed ────────────────────────────────────────────────
if not exist "%COMFYUI_APP%" (
    echo  [ERROR] ComfyUI not found at:
    echo          %COMFYUI_APP%
    echo.
    echo  Please install the ComfyUI Desktop App first.
    echo  Download: https://github.com/comfyanonymous/ComfyUI/releases
    echo.
    pause
    exit /b 1
)

:: ── Deploy LoRA ───────────────────────────────────────────────────────────────
echo  [1/3] Deploying LoRA model...
if exist "%REPO_LORA%" (
    copy /y "%REPO_LORA%" "%COMFY_LORA_DIR%\Crestline_Shreshth_v2.safetensors" >nul
    echo        OK ^→ Crestline_Shreshth_v2.safetensors
) else (
    echo        WARNING: LoRA not found in models\
    echo        Run training first, or copy the .safetensors file into models\
)

:: ── Deploy Workflows ──────────────────────────────────────────────────────────
echo  [2/3] Deploying workflows...
if exist "%REPO_WORKFLOW_EXT%" (
    copy /y "%REPO_WORKFLOW_EXT%" "%COMFY_WORKFLOW_DIR%\Crestline_Exterior_v2.json" >nul
    echo        OK ^→ Crestline_Exterior_v2.json
) else (
    echo        WARNING: Exterior workflow not found in workflows\
)

if exist "%REPO_WORKFLOW_INT%" (
    copy /y "%REPO_WORKFLOW_INT%" "%COMFY_WORKFLOW_DIR%\Crestline_Interior_v2.json" >nul
    echo        OK ^→ Crestline_Interior_v2.json
) else (
    echo        WARNING: Interior workflow not found in workflows\
)

:: ── Launch ────────────────────────────────────────────────────────────────────
echo  [3/3] Launching ComfyUI...
echo.
echo  ============================================================
echo   Studio is opening. Access it at: http://127.0.0.1:8188
echo  ============================================================
echo.

start "" "%COMFYUI_APP%"
exit /b 0
