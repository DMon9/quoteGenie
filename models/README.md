Model containers are mocked as HTTP microservices exposing a simple POST /api/... endpoint.
In production you will run the actual model servers (Ollama, vLLM, or vendor-provided images).

Each model should support a small JSON API and accept either base64 bytes or structured input.

Example endpoints expected by orchestrator:
- POST http://moondream2:11403/api/vision { file_bytes: <base64> }
- POST http://qwen2:11402/api/estimate { description: "...", job_type: "..." }
- POST http://llama3:11400/api/format { partial_results: {...} }

Additional model_server endpoints (compose profile "models"):
- POST http://gemma2:11404/api/generate { prompt: "..." }
- POST http://llama31:11405/api/generate { prompt: "..." }
- POST http://tinyllama:11406/api/generate { prompt: "..." }  # tiny for SD cards
- POST http://qwen25_0_5b:11407/api/generate { prompt: "..." }  # tiny for SD cards
 - POST http://smolvlm:11408/api/vision { image: "`<base64>`", prompt: "Describe the scene" }
