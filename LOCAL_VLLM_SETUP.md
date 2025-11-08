# Local vLLM Setup for `openai/gpt-oss-20b`

This guide helps you run the GPT-OSS 20B model locally via vLLM with an OpenAI-compatible API.

> WARNING: `openai/gpt-oss-20b` is a very large (≈20B parameter) model. Full precision requires >40GB GPU VRAM. Typical consumer GPUs (8–12GB) cannot host it without aggressive quantization. Consider using a smaller model or a hosted provider (OpenRouter) unless you have a data center–class GPU (e.g., A100 40GB, H100, multiple 3090/4090 with tensor parallel).

## 1. Recommended Alternatives (If You Lack Large GPU Memory)

| Option | Pros | Cons |
|--------|------|------|
| OpenRouter API (`openai/gpt-oss-20b`) | Zero setup | Network latency, paid usage |
| Smaller local model (e.g. 7B–8B) | Fits 12GB GPU | Lower quality |
| Quantized 20B (AWQ/GPTQ) | Lower memory | Slight quality loss; vLLM limited native quant support |
| Server GPU (Runpod, Lambda, Vast.ai) | Scales easily | Hourly cost |

If you still want to run 20B locally, read on.

## 2. Prerequisites

- Windows 11 or WSL2 Ubuntu (WSL strongly recommended for CUDA stability)
- Python 3.11 (matching your project)
- CUDA 12.1+ drivers installed (for nightly PyTorch wheel URL used below)
- At least 40GB VRAM (or plan to use tensor parallel across multiple GPUs)

## 3. Using `uv` for Fast Environment & Install

`uv` is a high-performance Python package installer and environment manager.

### Install `uv` (if not already installed)

```powershell
powershell -Command "iwr https://astral.sh/install.ps1 -useb | iex"
```

### Create an isolated environment

```powershell
uv venv .venv-vllm
.\.venv-vllm\Scripts\Activate.ps1
```

### Install vLLM with GPT-OSS 20B support

The command you provided (with line continuations adapted for PowerShell):

```powershell
uv pip install --pre vllm==0.10.1+gptoss \
  --extra-index-url https://wheels.vllm.ai/gpt-oss/ \
  --extra-index-url https://download.pytorch.org/whl/nightly/cu128 \
  --index-strategy unsafe-best-match
```

If PowerShell complains about the backslashes, put it on one line:

```powershell
uv pip install --pre vllm==0.10.1+gptoss --extra-index-url https://wheels.vllm.ai/gpt-oss/ --extra-index-url https://download.pytorch.org/whl/nightly/cu128 --index-strategy unsafe-best-match
```

> NOTE: `--index-strategy unsafe-best-match` is occasionally needed due to the custom wheels. If resolution errors occur, try removing it first.

## 4. Launch the Server

Basic serve (OpenAI-compatible):

```powershell
vllm serve openai/gpt-oss-20b --port 8081 --host 0.0.0.0
```

### Useful Flags

| Flag | Purpose |
|------|---------|
| `--tensor-parallel-size N` | Split model across N GPUs |
| `--gpu-memory-utilization 0.90` | Try to use 90% of GPU VRAM |
| `--max-model-len 8192` | Adjust context length (reduce to save memory) |
| `--dtype auto` | Let vLLM choose optimal dtype |

Example (multi-GPU A100s):

```powershell
vllm serve openai/gpt-oss-20b --tensor-parallel-size 2 --max-model-len 4096 --gpu-memory-utilization 0.9
```

## 5. Testing the Local API

OpenAI-compatible endpoint exposed at `http://localhost:8081/v1/chat/completions`.

```powershell
$body = @{ 
  model = "openai/gpt-oss-20b"; 
  messages = @(@{role="user"; content="Give me a concise drywall material list."}) 
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri http://localhost:8081/v1/chat/completions -Method POST -Body $body -ContentType "application/json"
```

## 6. Integrating with Your FastAPI Backend

Add an environment variable pointing to local vLLM endpoint:

```powershell
setx OPENROUTER_API_KEY "LOCAL_VLLM"  # dummy to trigger availability logic if needed
setx OPENROUTER_MODEL "openai/gpt-oss-20b"
```

Then modify your service (already added support) to prefer a direct endpoint call instead of OpenRouter if you want. A simple adjustment could check something like:

```python
if self.openrouter_api_key == "LOCAL_VLLM":
    # call local vLLM endpoint instead of OpenRouter remote
```

(We can implement this if desired.)

## 7. Memory Optimization Strategies

| Strategy | Impact |
|----------|--------|
| Lower `--max-model-len` | Reduces KV cache size significantly |
| Use tensor parallel | Split VRAM load across multiple GPUs |
| Use smaller model (8B) | Immediate relief |
| Quantization (AWQ/GPTQ) | Not first-class in vLLM yet for all variants |

If you cannot meet memory requirements, strongly consider using the hosted OpenRouter model instead.

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| CUDA driver mismatch | Update NVIDIA drivers to latest supporting CUDA 12.x |
| `OutOfMemoryError` | Reduce `--max-model-len`, use smaller model, increase tensor parallel |
| Slow load | First load downloads weights; ensure fast disk and stable connection |
| Wheel resolution fails | Remove `--index-strategy unsafe-best-match`, retry |
| vLLM not found | Ensure environment activated: `Get-Command vllm` |

## 9. Cleanup

```powershell
Deactivate
Remove-Item .venv-vllm -Recurse -Force
```

## 10. Alternative: Use OpenRouter Instead

If local hosting is impractical:

```powershell
flyctl secrets set OPENROUTER_API_KEY=sk-or-... -a quotegenie-api
```

Requests will route through OpenRouter with much lower local resource usage.

---
**Need help adjusting backend for local vLLM override?** Ask and we can add a conditional path to call `http://localhost:8081/v1/chat/completions` directly.
