# CRITICAL FIX: Cython Global State Issue

## Root Cause Identified

The state corruption is caused by a **global variable in the Cython module** (`stega_cy.pyx`):

```cython
cdef bint msg_exhausted_flag = False
```

This flag persists across API requests because:
1. Python model reload doesn't reload the compiled Cython `.so` module
2. The flag gets set during encode operations
3. It contaminates subsequent decode operations
4. This causes "Fail to decode!" errors and empty recovered messages

## The Fix

I've added a `reset_global_state()` function to `stega_cy.pyx` that resets this flag before each operation.

## IMPORTANT: You Must Rebuild

The fix requires **rebuilding the Cython extension**:

```bash
# In your project directory (e.g., /opt/data/sanli/text_hide/Discop)
python setup.py build_ext --inplace
```

Or use the provided script:

```bash
./rebuild_and_restart.sh
```

## After Rebuilding

1. **Stop the current server** (Ctrl+C)
2. **Restart it**:
   ```bash
   python api_server.py
   # Or: uvicorn api_server:app --host 0.0.0.0 --port 8002
   ```
3. **Test again**:
   ```bash
   python test_multi_cycle.py
   ```

Expected result: All 5 cycles should pass ✓

## What Was Changed

### `stega_cy.pyx` (lines 28-35):
```python
def reset_global_state():
    """Reset all global state variables in the Cython module."""
    global msg_exhausted_flag
    msg_exhausted_flag = False
```

### `api_server.py`:
- Imports `reset_global_state()` if available (after rebuild)
- Calls it in `_reset_model_state()` and `_reload_model()`
- Also resets Python's `random` state for good measure
- Works without rebuild (degraded mode), but **needs rebuild for full fix**

## Why This Happens

The issue occurs when:
1. **Encode operation**: Sets `msg_exhausted_flag = True` when message is exhausted
2. **Decode operation**: Tries to use the same Cython module
3. **Flag still True**: Decode logic gets confused and fails
4. **Result**: Empty recovered message

## Verification

After rebuilding, check the server output:
- Cycle 1: Should see "Hello World" ✓
- Cycle 2: Should see "Secret message" ✓ (not empty)
- Cycle 3: Should see "Testing 123" ✓ (not empty)
- All cycles: Should pass ✓

## Troubleshooting

### Q: Still getting empty messages after rebuild?
```bash
# Make sure the .so file was regenerated
ls -la stega_cy*.so
# Should show recent timestamp

# Completely clean and rebuild
rm -f stega_cy*.so stega_cy.cpp
python setup.py build_ext --inplace
```

### Q: Getting import errors?
The API server will work in "degraded mode" without the rebuild, but the global state won't be reset. You **must** rebuild for the fix to work.

### Q: How do I know if the rebuild worked?
Check the health endpoint after restarting:
```bash
curl -H "X-API-Key: jnu@fenglab" http://localhost:8002/health
```

If `HAS_RESET_FUNCTION` is available, the server will use it.

## Alternative: Nuclear Option

If rebuilding doesn't work, use a more aggressive workaround:

Edit `api_server.py` and change line 105:
```python
RELOAD_STRATEGY = "reload"  # Full reload every request
```

This is slower but **might** help by reloading Python's reference to the Cython module. However, **rebuilding is the proper fix**.

## Summary

1. ✓ Root cause: `msg_exhausted_flag` global in Cython
2. ✓ Solution: Added `reset_global_state()` function
3. ⚠️  **ACTION REQUIRED**: Rebuild Cython module
4. ✓ After rebuild: Restart server and retest

```bash
python setup.py build_ext --inplace
pkill -f "uvicorn api_server"
python api_server.py &
python test_multi_cycle.py
```
