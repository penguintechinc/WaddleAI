# Ollama Backend Setup

Use Ollama for fast, local LLM inference with WaddleAI.

## Why Ollama?

- **Free**: No API costs
- **Fast**: Local inference, low latency
- **Private**: Data never leaves your machine
- **Powerful**: Run models like Llama, CodeLlama, Mistral

## Installation

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS

```bash
brew install ollama
```

### Windows

Download from [ollama.com](https://ollama.com/download)

### Docker

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Pull Models

### Routing Model (Required)

The stage-2 routing classifier, and the other quick/light internal roles
(summarization, docs-fetch):

```bash
ollama pull gemma4:e4b
```

`gemma4:e4b` is the **supported minimum**. `gemma4:e2b` was the default until
2026-09-07 and was withdrawn: it does not classify tool type and complexity
reliably enough to route on. Nothing below `e4b` — and in particular no sub-2B
model such as `llama3.2:1b` — is supported for routing or memory work.

Valid Gemma 4 tags are `e2b`/`e4b`/`12b`/`26b`/`31b`. The `e` prefix marks the
MatFormer effective-size variants only, so the 12B tag is `12b`, never `e12b`,
and `gemma4:2b` does not exist.

### General Purpose Models

`gemma4:e4b` is the default for every role. For **more complex operations —
coding especially — `gemma4:12b-it-qat` is the recommendation**, wherever the host can
carry it (~8GB VRAM):

```bash
# Recommended default for general local generation
ollama pull gemma4:12b-it-qat

# Larger, if the GPU allows
ollama pull gemma4:26b
ollama pull gemma4:31b
```

### Code Models

```bash
# Code generation
ollama pull codellama

# Code completion
ollama pull codellama:7b-code

# Best for code
ollama pull codellama:34b
```

### Specialized Models

```bash
# Fast chat
ollama pull mistral

# Analysis
ollama pull mixtral

# Embeddings
ollama pull nomic-embed-text
```

## Configure WaddleAI

### Add Ollama Provider

Management Portal:
1. Navigate to "LLM Providers"
2. Click "Add Provider"
3. Fill in:
   - **Name**: Local Ollama
   - **Type**: ollama
   - **Base URL**: http://localhost:11434
   - **API Key**: (leave empty)
   - **Enable**: ✓
4. Click "Test Connection"
5. Click "Save"

### Set as Routing LLM

The routing classifier's model is **not** an environment variable. It is the
`routing-classifier` row in `model_assignments`, edited in the Management
Portal under **Routing → Routing LLM Model** (admin only). The selector offers
`gemma4:e4b` (default), `gemma4:12b`, `gemma4:26b` and `gemma4:31b`.

Point the Ollama provider itself at your endpoint (Management Portal → LLM
Providers → Base URL, e.g. `http://localhost:11434`); the classifier is served
by whichever connector advertises the assigned model, Ollama by convention.

### Configure Routing

Set routing instructions to use Ollama:

Management Portal → Routing Configuration:

```
Route simple questions to llama3.2:3b.
Route programming to codellama.
Route complex analysis to mixtral.
Route everything else to llama3.2:3b.
```

## Docker Compose Integration

Add to `docker-compose.env.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  proxy:
    environment:
      - ROUTING_LLM_ENDPOINT=http://ollama:11434

volumes:
  ollama_data:
```

Pull models in container:

```bash
docker-compose exec ollama ollama pull gemma4:e4b
docker-compose exec ollama ollama pull codellama
```

## GPU Acceleration

### NVIDIA GPU

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Run Ollama with GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 ollama/ollama
```

### AMD GPU

```bash
# Run with ROCm
docker run -d --device=/dev/kfd --device=/dev/dri -v ollama:/root/.ollama -p 11434:11434 ollama/ollama
```

### Apple Silicon

GPU automatically enabled on M1/M2/M3 Macs.

## Model Management

### List Models

```bash
ollama list
```

### Remove Model

```bash
ollama rm codellama
```

### Model Info

```bash
ollama show llama3.2:3b
```

### Custom Models

Create `Modelfile`:

```dockerfile
FROM llama3.2:3b

SYSTEM "You are a Python expert. Always provide clear, well-commented code."

PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
```

Build and use:

```bash
ollama create python-expert -f Modelfile
ollama run python-expert "Write a Python function"
```

## Performance Tuning

### System Resources

**CPU Only**:
```bash
# Smallest supported routing model
ollama pull gemma4:e4b   # ~4GB RAM
ollama pull llama3.2:3b  # ~2GB RAM (general use only -- not for routing)
```

**GPU**:
```bash
# Use larger models
ollama pull llama3.2:70b  # ~40GB VRAM
ollama pull codellama:34b # ~20GB VRAM
```

### Concurrent Requests

Set in Ollama:

```bash
OLLAMA_NUM_PARALLEL=4 ollama serve
```

### Context Length

```bash
# Longer context
ollama run llama3.2:3b --num-ctx 8192
```

## Testing

### Direct Test

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Via WaddleAI

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <your-waddleai-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Monitoring

### Ollama Logs

```bash
# macOS
tail -f ~/.ollama/logs/server.log

# Linux
journalctl -u ollama -f

# Docker
docker logs -f ollama
```

### Resource Usage

```bash
# Monitor GPU
nvidia-smi -l 1

# Monitor CPU/RAM
htop
```

### WaddleAI Analytics

Management Portal → Analytics:
- Filter by provider: ollama
- View requests, tokens, response times
- Compare with cloud providers

## Troubleshooting

### "Connection refused"

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# macOS
brew services restart ollama

# Linux
sudo systemctl restart ollama

# Docker
docker restart ollama
```

### "Model not found"

```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.2:3b
```

### Slow Performance

1. Use GPU if available
2. Use smaller models for simple tasks
3. Increase OLLAMA_NUM_PARALLEL
4. Check system resources

### Out of Memory

```bash
# Use quantized models
ollama pull llama3.2:3b-q4  # 4-bit quantization

# Routing cannot go below the e4b minimum -- quantize rather than downsize
ollama pull gemma4:e4b
```

## Cost Comparison

### Ollama (Local)

- **Cost**: $0 (free)
- **Latency**: 50-200ms
- **Quality**: Good for most tasks
- **Hardware**: Requires GPU for best performance

### OpenAI GPT-3.5

- **Cost**: $0.0015 per 1K tokens
- **Latency**: 500-2000ms
- **Quality**: Excellent
- **Hardware**: None required

### Hybrid Strategy

Use WaddleAI routing:
- Simple queries → Ollama (free, fast)
- Complex queries → GPT-4 (best quality)
- Code → CodeLlama (Ollama, optimized)

**Estimated savings**: 70-90% compared to all-cloud

## Recommended Models

### By Use Case

| Use Case | Model | Size | Quality |
|----------|-------|------|---------|
| Routing / quick / light | gemma4:e4b | ~4GB | Fast — supported minimum |
| Complex ops / coding | gemma4:12b-it-qat | ~8GB | Recommended, not the default — opt in |
| Embeddings | nomic-embed-text | ~0.3GB | Required for memory/RAG |
| Code | codellama | 4GB | Excellent |
| Analysis | mixtral | 26GB | Excellent |
| Embeddings | nomic-embed-text | 274MB | Good |

### By Hardware

> **Sizing from VRAM, not download size.** The complete e4b-only set
> (`gemma4:e4b` + `shieldgemma:2b` + `nomic-embed-text`) is **5.72 GB
> resident**, measured with all three loaded at once. 8 GB is the floor and
> 12 GB+ the recommendation — see
> [GPU requirements](../getting-started/installation.md#gpu-requirements-local-model-serving).
> Note `gemma4:e4b` is 9.61 GB on disk but only 3.26 GB resident; the download
> size is misleading.

**4GB RAM, No GPU**:
- gemma4:e4b (routing; tight)
- llama3.2:3b (general use only, slow)

**8GB RAM, No GPU**:
- llama3.2:3b
- codellama:7b
- mistral

**16GB RAM + GPU**:
- llama3.2:8b
- codellama:13b
- mixtral

**32GB+ RAM + GPU**:
- llama3.2:70b
- codellama:34b
- All models

## Next Steps

- [Configure Routing](../getting-started/configuration.md)
- [Anthropic Setup](anthropic-config.md)
- [OpenAI Setup](openai-config.md)
