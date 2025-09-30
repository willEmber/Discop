#!/bin/bash
# verify_migration.sh - 验证项目目录迁移后的完整性

echo "========================================================================"
echo "Discop 项目迁移验证"
echo "========================================================================"
echo ""

# 检查当前目录
echo "1. 检查当前目录..."
pwd
echo ""

# 检查关键文件
echo "2. 检查关键文件是否存在..."
files=(
    "api_server.py"
    "config.py"
    "model.py"
    "utils.py"
    "stega_cy.pyx"
    "setup.py"
    "test_multi_cycle.py"
)

missing_files=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
        missing_files=$((missing_files + 1))
    fi
done
echo ""

if [ $missing_files -gt 0 ]; then
    echo "✗ 错误: 有 $missing_files 个文件缺失"
    echo "请确保在正确的项目目录中运行此脚本"
    exit 1
fi

# 检查 Cython 编译状态
echo "3. 检查 Cython 模块编译状态..."
if [ -f "stega_cy.cpython-*.so" ] || [ -f "stega_cy.so" ]; then
    echo "  ✓ stega_cy 模块已编译"
    ls -lh stega_cy*.so 2>/dev/null | tail -1
else
    echo "  ⚠ stega_cy 模块未编译"
    echo "  需要运行: python setup.py build_ext --inplace"
fi
echo ""

# 检查配置
echo "4. 检查配置..."
if grep -q "API_KEY = " api_server.py; then
    api_key=$(grep "^API_KEY = " api_server.py | head -1)
    echo "  $api_key"
fi
if grep -q "SERVER_PORT = " api_server.py; then
    port=$(grep "^SERVER_PORT = " api_server.py | head -1)
    echo "  $port"
fi
echo ""

# 检查环境变量
echo "5. 检查环境变量..."
if [ -n "$DISCOP_API_KEY" ]; then
    echo "  ✓ DISCOP_API_KEY=${DISCOP_API_KEY}"
else
    echo "  - DISCOP_API_KEY 未设置"
fi

if [ -n "$DISCOP_PORT" ]; then
    echo "  ✓ DISCOP_PORT=${DISCOP_PORT}"
else
    echo "  - DISCOP_PORT 未设置 (默认: 8000)"
fi
echo ""

# 检查是否有服务器在运行
echo "6. 检查服务器状态..."
if pgrep -f "api_server" > /dev/null; then
    echo "  ⚠ API 服务器正在运行"
    echo "  PID: $(pgrep -f api_server)"
    echo "  如需重启，请先运行: pkill -f api_server"
else
    echo "  - API 服务器未运行"
fi
echo ""

# 检查 Python 环境
echo "7. 检查 Python 环境..."
python_version=$(python --version 2>&1)
echo "  Python: $python_version"

if python -c "import torch" 2>/dev/null; then
    echo "  ✓ PyTorch 已安装"
else
    echo "  ✗ PyTorch 未安装"
fi

if python -c "import transformers" 2>/dev/null; then
    echo "  ✓ Transformers 已安装"
else
    echo "  ✗ Transformers 未安装"
fi

if python -c "import fastapi" 2>/dev/null; then
    echo "  ✓ FastAPI 已安装"
else
    echo "  ✗ FastAPI 未安装"
fi
echo ""

# 总结
echo "========================================================================"
echo "验证完成"
echo "========================================================================"

if [ $missing_files -eq 0 ]; then
    echo "✓ 所有关键文件都存在"

    if [ -f "stega_cy.cpython-*.so" ] || [ -f "stega_cy.so" ]; then
        echo "✓ Cython 模块已编译"
        echo ""
        echo "下一步:"
        echo "  1. 启动服务器: python api_server.py"
        echo "  2. 测试: python test_multi_cycle.py"
    else
        echo "⚠ 需要编译 Cython 模块"
        echo ""
        echo "下一步:"
        echo "  1. 编译: python setup.py build_ext --inplace"
        echo "  2. 启动: python api_server.py"
        echo "  3. 测试: python test_multi_cycle.py"
    fi
else
    echo "✗ 项目文件不完整，请检查目录"
    exit 1
fi
