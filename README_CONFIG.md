# Discop API Server - Configuration Summary

## Quick Configuration

Edit these values in `api_server.py` (lines 80-90):

```python
# API Security
API_KEY = None  # Change to "your-secret-key" to enable auth

# Server Configuration
SERVER_HOST = "0.0.0.0"  # "127.0.0.1" for localhost only
SERVER_PORT = 8000       # Port number

# Model reload strategy
RELOAD_STRATEGY = "reset"  # Options: "reset", "reload", "periodic", "none"
```

## Running the Server

### Simplest way:
```bash
python api_server.py
```

### With custom configuration:
```bash
# Edit api_server.py first, then:
python api_server.py
```

### Using environment variables:
```bash
DISCOP_API_KEY="my-key" DISCOP_PORT=9000 python api_server.py
```

### Using uvicorn directly:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

## Testing the Fix

```bash
# Terminal 1: Start server
python api_server.py

# Terminal 2: Run tests
python test_multi_cycle.py
```

Expected result: `✓ All cycles passed! (5/5)`

## API Endpoints

### POST /encode
Embed a secret message in generated text.

```bash
curl -X POST http://localhost:8000/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "message": "Secret message",
    "context": "Once upon a time"
  }'
```

### POST /decode
Extract the hidden message from stego text.

```bash
curl -X POST http://localhost:8000/decode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "stego_text": "...",
    "context": "Once upon a time",
    "expected_bits": 104
  }'
```

### GET /health
Check server status and configuration.

```bash
curl http://localhost:8000/health -H "X-API-Key: your-key"
```

### POST /reload
Manually trigger full model reload.

```bash
curl -X POST http://localhost:8000/reload -H "X-API-Key: your-key"
```

### POST /reset
Manually trigger state reset (lighter than reload).

```bash
curl -X POST http://localhost:8000/reset -H "X-API-Key: your-key"
```

## Configuration Options

### API_KEY
- `None`: Authentication disabled (default)
- `"your-key"`: Authentication enabled, requires X-API-Key header

### SERVER_HOST
- `"127.0.0.1"`: Localhost only (secure)
- `"0.0.0.0"`: All interfaces (accessible from network)

### SERVER_PORT
- Default: `8000`
- Any valid port number (1024-65535 recommended)

### RELOAD_STRATEGY
- `"reset"` (default): Clear state between requests - **Recommended**
- `"reload"`: Full model reload between requests - Maximum safety, slower
- `"periodic"`: Reload every N operations - Balanced approach
- `"none"`: No state management - Original broken behavior

### RELOAD_EVERY_N_OPS
- Default: `10`
- Only used when `RELOAD_STRATEGY = "periodic"`
- Number of operations before triggering full reload

## Environment Variables

All settings can be overridden with environment variables:

- `DISCOP_API_KEY`: API key for authentication
- `DISCOP_HOST`: Server host
- `DISCOP_PORT`: Server port
- `DISCOP_RELOAD_STRATEGY`: Reload strategy
- `DISCOP_RELOAD_EVERY_N`: Periodic reload interval

Environment variables take precedence over values in the file.

## Files Created

- `api_server.py` - Main API server (modified)
- `test_multi_cycle.py` - Multi-cycle test script
- `API_STATE_FIX.md` - Detailed technical documentation
- `QUICKSTART.txt` - Quick reference guide
- `CONFIG_EXAMPLES.txt` - Configuration examples
- `README_CONFIG.md` - This file

## Troubleshooting

**Q: Server won't start**
- Check if port is already in use: `lsof -i :8000`
- Try a different port: Edit `SERVER_PORT` in api_server.py

**Q: Authentication fails**
- Make sure `API_KEY` is set in api_server.py
- Include `X-API-Key` header in all requests
- Value must match exactly

**Q: Still seeing state corruption**
- Switch to `RELOAD_STRATEGY = "reload"`
- Check test results: `python test_multi_cycle.py`
- Manually reset: `curl -X POST http://localhost:8000/reload`

**Q: Server too slow**
- Check if using `RELOAD_STRATEGY = "reload"` (switch to "reset")
- Monitor GPU memory: `nvidia-smi`
- Check operations count: `curl http://localhost:8000/health`

## Support

For detailed information, see:
- `API_STATE_FIX.md` - Full technical documentation
- `CLAUDE.md` - Codebase architecture overview
- `CONFIG_EXAMPLES.txt` - Configuration scenarios
