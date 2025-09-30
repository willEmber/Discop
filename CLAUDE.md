# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **Discop** (Distribution-Preserving Steganography) research codebase that implements steganographic embedding in three modalities: text generation, image completion, and text-to-speech. The system hides binary messages within generated content while maintaining natural statistical distributions.

## Building the Project

The project uses Cython extensions that must be compiled before use:

```bash
python setup.py build_ext --inplace
```

This compiles two critical Cython modules:
- `stega_cy.pyx` → Core Discop encoding/decoding using Huffman trees
- `random_sample_cy.pyx` → Baseline random sampling implementation

The compiled `.so` files must exist before running any steganography operations.

## Running Tests and Examples

### Single Example (Text)
```bash
python run_single_example.py
```

Edit the `__main__` section to switch between text/image/TTS modes and algorithms.

### API Server
```bash
uvicorn api_server:app --reload
```

The FastAPI server exposes `/encode` and `/decode` endpoints for text steganography. Optional API key authentication via `DISCOP_API_KEY` environment variable.

### Get Statistics
```bash
python get_statistics.py
```

Runs batch evaluation and collects embedding rate, perplexity, and KLD metrics.

## Architecture

### Core Algorithm (`stega_cy.pyx`)

The Discop algorithm uses Huffman coding over probability distributions:

1. **Encoding**: At each generation step, constructs a Huffman tree from the model's output probability distribution (after temperature/top-p filtering). Traverses the tree using bits from the secret message to select the next token. Records the path as steganographic payload.

2. **Decoding**: Given the generated tokens and original context, reconstructs the probability distributions at each step, rebuilds Huffman trees, and extracts the hidden bits by finding which tree path corresponds to each sampled token.

3. **Variants**:
   - `Discop`: Full algorithm with Huffman encoding
   - `Discop_baseline`: Simplified variant
   - `sample`: Random sampling baseline (no steganography)

### Configuration (`config.py`)

The `Settings` class centralizes all generation parameters:
- `task`: 'text', 'image', or 'text-to-speech'
- `algo`: 'Discop', 'Discop_baseline', or 'sample'
- `model_name`: HuggingFace model identifier
- `temp`, `top_p`: Sampling parameters
- `length`: Max generation length
- `device`: PyTorch device

Default settings objects: `text_default_settings`, `image_default_settings`, `audio_default_settings`

### Model Loading (`model.py`)

Factory functions that load pre-trained models:
- `get_model()`: Returns GPT-2, Transformer-XL, or ImageGPT model
- `get_tokenizer()`: Returns corresponding tokenizer for text models
- `get_feature_extractor()`: Returns feature extractor for image models

Default text model is `transfo-xl-wt103`.

### Utilities (`utils.py`)

- `get_probs_indices_past()`: Core function that extracts probability distributions from language models, applies filtering (removes problematic tokens), and handles KV-cache (`past`)
- `SingleExampleOutput`: Result object containing statistics (embedding rate, perplexity, KLD, entropy)
- Token filtering: Removes problematic GPT-2 tokens that cause decoding issues (newlines, certain punctuation)

### TTS Module (`stega_tts.py`)

Integrates Tacotron and UniversalVocoder for speech steganography:
- `get_tts_model()`: Loads pretrained Tacotron and Univoc models
- `encode_speech()`: Embeds message in vocoder generation
- `decode_speech()`: Extracts message from speech

The vocoder implements the steganographic algorithm at the waveform level.

### API Server (`api_server.py`)

Production-ready FastAPI service with **state management fix** for multi-cycle operation:

**Configuration** (lines 80-90, or use environment variables):
- `API_KEY`: Set to enable authentication (default: `None`)
- `SERVER_HOST`: Host to bind to (default: `"0.0.0.0"`)
- `SERVER_PORT`: Port to run on (default: `8000`)
- `RELOAD_STRATEGY`: State management - `"reset"` (default), `"reload"`, `"periodic"`, `"none"`

**Running**:
```bash
python api_server.py
# Or: DISCOP_API_KEY="key" DISCOP_PORT=9000 python api_server.py
```

**Key features**:
- Thread-safe model loading with `_MODEL_LOCK`
- **State reset/reload** between operations to prevent corruption
- Automatic length estimation based on payload size
- Retry logic if initial embedding fails
- Returns detailed metrics (embedding rate, utilization, perplexity)

**Endpoints**: `/encode`, `/decode`, `/health`, `/reload`, `/reset`

See `README_CONFIG.md` for configuration and `API_STATE_FIX.md` for state management details.

**Testing**: Run `python test_multi_cycle.py` to verify multiple encode/decode cycles work correctly.

## Key Dependencies

- **transformers**: HuggingFace models (GPT-2, Transformer-XL, ImageGPT)
- **torch**: Neural network inference
- **Cython**: Performance-critical encoding/decoding loops
- **FastAPI**: API server
- **tacotron** & **univoc**: TTS models (subdirectories)

## Important Implementation Details

### Huffman Tree Construction
The Huffman tree is rebuilt at every generation step from the current probability distribution. This ensures the encoding is adaptive to the model's changing beliefs about what token should come next.

### Past/Mems Management
`utils.limit_past()` truncates the KV-cache to prevent memory explosion during long generations. Transformer-XL uses `mems` instead of `past_key_values`.

### Message Format
Messages are binary strings ('0' and '1' characters). The API server handles text ↔ binary conversion via `_text_to_bits()` and `_bits_to_text()`.

### Context Importance
The decoder **must** receive the same context used during encoding, as it reconstructs probability distributions. Context mismatch causes decoding failure.

## Testing Strategy

Run single examples first to verify the build:
```bash
python run_single_example.py
```

Then test API endpoints:
```bash
curl -X POST http://localhost:8000/encode \
  -H "Content-Type: application/json" \
  -d '{"message": "secret", "context": "Once upon a time"}'
```

For TTS, check that `temp/test.flac` is generated and decoding recovers the original message.
