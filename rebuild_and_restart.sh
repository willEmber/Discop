#!/bin/bash
# rebuild_and_restart.sh - Rebuild Cython modules and restart API server

echo "========================================"
echo "Rebuilding Cython Extensions"
echo "========================================"

# Build the Cython extensions
python setup.py build_ext --inplace

if [ $? -ne 0 ]; then
    echo "✗ Build failed!"
    exit 1
fi

echo ""
echo "✓ Build successful!"
echo ""
echo "========================================"
echo "Cython module rebuilt with:"
echo "  - reset_global_state() function"
echo "========================================"
echo ""
echo "Now restart your API server:"
echo "  python api_server.py"
echo ""
echo "Or with uvicorn:"
echo "  uvicorn api_server:app --host 0.0.0.0 --port 8002"
echo ""
