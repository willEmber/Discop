"""FastAPI service exposing Discop text steganography encode/decode endpoints."""
import copy
import gc
import math
import os
import random
import threading
from typing import Any, Optional

import torch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from config import Settings, text_default_settings
from model import get_model, get_tokenizer

try:
    from stega_cy import decode_text, encode_text  # type: ignore
    # Try to import reset function if it exists (after rebuild)
    try:
        from stega_cy import reset_global_state  # type: ignore
        HAS_RESET_FUNCTION = True
    except ImportError:
        HAS_RESET_FUNCTION = False
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Failed to import stega_cy extension. Build the project first.") from exc


app = FastAPI(title="Discop Steganography API", version="0.1.0")

# Configure CORS to allow frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - restrict in production!
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers including X-API-Key
)

_DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
_BASE_SETTINGS = copy.deepcopy(text_default_settings)
_BASE_SETTINGS.device = _DEVICE

_MODEL_LOCK = threading.Lock()
_MODEL = None
_TOKENIZER = None
_OPERATION_COUNTER = 0  # Track number of operations for potential reload


def _reset_model_state() -> None:
    """Reset model internal states and clear caches to prevent state contamination."""
    global _MODEL

    # Reset Python random state (used by Cython decode)
    random.seed(None)

    # CRITICAL: Reset PyTorch random state (used by model inference)
    torch.manual_seed(random.randint(0, 2**31 - 1))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(random.randint(0, 2**31 - 1))

    # Reset Cython global state if function is available
    if HAS_RESET_FUNCTION:
        reset_global_state()

    if _MODEL is not None:
        # Reset model to eval mode
        _MODEL.eval()
        # Clear gradients if any
        _MODEL.zero_grad(set_to_none=True)
        # Clear CUDA cache if using GPU
        if _DEVICE.type == 'cuda':
            torch.cuda.empty_cache()
    # Force garbage collection
    gc.collect()


def _ensure_model_loaded() -> None:
    """Lazy load model and tokenizer on first use."""
    global _MODEL, _TOKENIZER
    if _MODEL is None or _TOKENIZER is None:
        _MODEL = get_model(_BASE_SETTINGS)
        _TOKENIZER = get_tokenizer(_BASE_SETTINGS)


def _reload_model() -> None:
    """Completely reload the model from scratch to ensure clean state."""
    global _MODEL, _TOKENIZER

    # Reset Python random state
    random.seed(None)

    # CRITICAL: Reset PyTorch random state
    torch.manual_seed(random.randint(0, 2**31 - 1))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(random.randint(0, 2**31 - 1))

    # Reset Cython global state if function is available
    if HAS_RESET_FUNCTION:
        reset_global_state()

    # Delete existing model
    if _MODEL is not None:
        del _MODEL
    if _TOKENIZER is not None:
        del _TOKENIZER
    # Clear caches
    if _DEVICE.type == 'cuda':
        torch.cuda.empty_cache()
    gc.collect()
    # Reload fresh model
    _MODEL = get_model(_BASE_SETTINGS)
    _TOKENIZER = get_tokenizer(_BASE_SETTINGS)


# ============================================================================
# CONFIGURATION - Modify these values as needed
# ============================================================================

# API Security
API_KEY = "jnu@fenglab"  # Set to a string to enable authentication, e.g., "your-secret-key-here"
API_KEY_HEADER_NAME = "X-API-Key"

# Server Configuration
SERVER_HOST = "0.0.0.0"  # Use "127.0.0.1" for localhost only, "0.0.0.0" for all interfaces
SERVER_PORT = 8002       # Port to run the server on

# Model reload strategy: "reset" (default), "reload", "periodic", or "none"
RELOAD_STRATEGY = "reset"
RELOAD_EVERY_N_OPS = 10  # For periodic strategy: reload every N operations

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Override with environment variables if set
API_KEY = os.getenv("DISCOP_API_KEY", API_KEY)
RELOAD_STRATEGY = os.getenv("DISCOP_RELOAD_STRATEGY", RELOAD_STRATEGY)
RELOAD_EVERY_N_OPS = int(os.getenv("DISCOP_RELOAD_EVERY_N", str(RELOAD_EVERY_N_OPS)))
SERVER_HOST = os.getenv("DISCOP_HOST", SERVER_HOST)
SERVER_PORT = int(os.getenv("DISCOP_PORT", str(SERVER_PORT)))

_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


class SettingsOverride(BaseModel):
    algo: Optional[str] = Field(None, description="Algorithm variant to use (Discop, Discop_baseline, sample).")
    temp: Optional[float] = Field(None, gt=0, description="Softmax temperature.")
    top_p: Optional[float] = Field(None, gt=0, le=1, description="Nucleus sampling threshold.")
    length: Optional[int] = Field(None, gt=0, description="Maximum number of tokens to generate.")
    seed: Optional[int] = Field(None, ge=0, description="PRNG seed used during sampling.")


class EncodeRequest(BaseModel):
    message: str = Field(..., description="Plain text payload that should be hidden.")
    context: Optional[str] = Field(
        None,
        description="Optional priming context for the language model. Uses a neutral default when omitted."
    )
    settings: Optional[SettingsOverride] = Field(
        None,
        description="Overrides applied on top of the default text settings."
    )


class EncodeResponse(BaseModel):
    stego_text: str
    embedded_bits: int
    payload_bits: int
    token_count: int
    embedding_rate: float
    utilization_rate: float
    perplexity: float
    settings: SettingsOverride


class DecodeRequest(BaseModel):
    stego_text: str = Field(..., description="Generated text that potentially carries a hidden payload.")
    context: str = Field(..., description="Context that was used when encoding the payload.")
    expected_bits: Optional[int] = Field(
        None,
        gt=0,
        description="Optional bit length of the original payload for trimming the decoded output."
    )
    settings: Optional[SettingsOverride] = Field(
        None,
        description="Overrides that reproduce the encoder configuration."
    )


class DecodeResponse(BaseModel):
    recovered_bits: str
    recovered_text: Optional[str]
    used_bits: int


_DEFAULT_CONTEXT = (
    "We were both young when I first saw you, I close my eyes and the flashback starts."
)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Invalid or missing API key"):
        super().__init__(status_code=401, detail=detail)


def _text_to_bits(text: str) -> str:
    return "".join(f"{ord(ch):08b}" for ch in text)


def _bits_to_text(bits: str) -> str:
    chars = []
    for idx in range(0, len(bits), 8):
        byte = bits[idx:idx + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return "".join(chars)


def _suggest_length(bit_len: int, target_rate: float = 3.6, safety_tokens: int = 8) -> int:
    base = math.ceil(bit_len / max(target_rate, 1e-6))
    return max(32, base + safety_tokens)


def _coerce_seed(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bytes):
        if len(value) == 0:
            return 0
        return int.from_bytes(value, byteorder="big")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(value, 10)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="`settings.seed` must be an integer.") from exc
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="`settings.seed` must be an integer.") from exc


def _apply_overrides(settings: Settings, overrides: Optional[SettingsOverride]) -> Settings:
    if overrides is None:
        return settings
    data = overrides.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "seed":
            setattr(settings, key, _coerce_seed(value))
        else:
            setattr(settings, key, value)
    return settings


def _encode_impl(req: EncodeRequest) -> EncodeResponse:
    global _OPERATION_COUNTER

    message_bits = _text_to_bits(req.message)
    if not message_bits:
        raise HTTPException(status_code=400, detail="Message must not be empty.")

    settings = copy.deepcopy(_BASE_SETTINGS)
    settings.seed = _coerce_seed(settings.seed)
    _apply_overrides(settings, req.settings)

    if settings.length is None or settings.length <= 0:
        settings.length = _suggest_length(len(message_bits))

    context = req.context or _DEFAULT_CONTEXT

    with _MODEL_LOCK:
        # Ensure model is loaded
        _ensure_model_loaded()

        # Apply state management strategy
        if RELOAD_STRATEGY == "reload":
            _reload_model()
        elif RELOAD_STRATEGY == "reset":
            _reset_model_state()
        elif RELOAD_STRATEGY == "periodic" and _OPERATION_COUNTER % RELOAD_EVERY_N_OPS == 0:
            _reload_model()

        output = encode_text(_MODEL, _TOKENIZER, message_bits, context, settings)

        if output.n_bits < len(message_bits):
            settings.length = max(settings.length + 16, len(message_bits) // 2)
            # Reset again before retry
            if RELOAD_STRATEGY in ["reload", "reset"]:
                _reset_model_state()
            output = encode_text(_MODEL, _TOKENIZER, message_bits, context, settings)

        # Increment operation counter
        _OPERATION_COUNTER += 1

    if output.n_bits < len(message_bits):
        raise HTTPException(
            status_code=422,
            detail=(
                "Failed to embed the entire payload. Consider increasing `settings.length` or reducing the message size."
            ),
        )

    response_settings = SettingsOverride(**{
        "algo": settings.algo,
        "temp": settings.temp,
        "top_p": settings.top_p,
        "length": settings.length,
        "seed": _coerce_seed(settings.seed),
    })

    return EncodeResponse(
        stego_text=output.stego_object,
        embedded_bits=output.n_bits,
        payload_bits=len(message_bits),
        token_count=output.n_tokens,
        embedding_rate=output.embedding_rate,
        utilization_rate=output.utilization_rate,
        perplexity=output.perplexity,
        settings=response_settings,
    )


def _decode_impl(req: DecodeRequest) -> DecodeResponse:
    global _OPERATION_COUNTER

    settings = copy.deepcopy(_BASE_SETTINGS)
    settings.seed = _coerce_seed(settings.seed)
    _apply_overrides(settings, req.settings)

    with _MODEL_LOCK:
        # Ensure model is loaded
        _ensure_model_loaded()

        token_ids = _TOKENIZER.encode(req.stego_text, add_special_tokens=False)
        if not token_ids:
            raise HTTPException(status_code=400, detail="Unable to tokenize stego text. Verify the input content.")

        # Apply state management strategy
        if RELOAD_STRATEGY == "reload":
            _reload_model()
        elif RELOAD_STRATEGY == "reset":
            _reset_model_state()
        elif RELOAD_STRATEGY == "periodic" and _OPERATION_COUNTER % RELOAD_EVERY_N_OPS == 0:
            _reload_model()

        recovered_bits = decode_text(_MODEL, _TOKENIZER, token_ids, req.context, settings)

        # Increment operation counter
        _OPERATION_COUNTER += 1

    if req.expected_bits is not None:
        recovered_bits = recovered_bits[: req.expected_bits]

    recovered_text = None
    if recovered_bits:
        recovered_text = _bits_to_text(recovered_bits)

    return DecodeResponse(
        recovered_bits=recovered_bits,
        recovered_text=recovered_text if recovered_text else None,
        used_bits=len(recovered_bits),
    )


def _verify_api_key(provided_key: Optional[str] = Depends(_api_key_header)) -> None:
    """Verify API key if authentication is enabled."""
    if API_KEY is None:
        return  # Authentication disabled
    if not provided_key or provided_key != API_KEY:
        raise UnauthorizedError()


@app.post("/encode", response_model=EncodeResponse, dependencies=[Depends(_verify_api_key)])
async def encode(req: EncodeRequest) -> EncodeResponse:
    return await run_in_threadpool(_encode_impl, req)


@app.post("/decode", response_model=DecodeResponse, dependencies=[Depends(_verify_api_key)])
async def decode(req: DecodeRequest) -> DecodeResponse:
    return await run_in_threadpool(_decode_impl, req)


@app.get("/health", dependencies=[Depends(_verify_api_key)])
def health() -> dict:
    return {
        "status": "ok",
        "device": str(_DEVICE),
        "model_loaded": _MODEL is not None,
        "reload_strategy": RELOAD_STRATEGY,
        "operations_count": _OPERATION_COUNTER
    }


@app.post("/reload", dependencies=[Depends(_verify_api_key)])
def manual_reload() -> dict:
    """Manually trigger a full model reload to clear any state corruption."""
    with _MODEL_LOCK:
        _reload_model()
    return {"status": "reloaded", "message": "Model has been completely reloaded"}


@app.post("/reset", dependencies=[Depends(_verify_api_key)])
def manual_reset() -> dict:
    """Manually trigger a state reset (lighter than full reload)."""
    with _MODEL_LOCK:
        _reset_model_state()
    return {"status": "reset", "message": "Model state has been reset"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Discop Steganography API Server")
    print("=" * 70)
    print(f"Host:            {SERVER_HOST}")
    print(f"Port:            {SERVER_PORT}")
    print(f"Device:          {_DEVICE}")
    print(f"Reload Strategy: {RELOAD_STRATEGY}")
    print(f"Authentication:  {'Enabled' if API_KEY else 'Disabled'}")
    print("=" * 70)
    print()

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


