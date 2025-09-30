#!/bin/bash
# fix_pytorch_rng.sh - 修复 PyTorch RNG 状态问题并重启服务器

echo "========================================================================"
echo "修复 PyTorch RNG 状态问题"
echo "========================================================================"
echo ""

# 检查当前目录
if [ ! -f "setup.py" ]; then
    echo "✗ 错误: 当前目录没有 setup.py 文件"
    echo "请在项目根目录运行此脚本"
    exit 1
fi

# 步骤 1: 清理旧的编译文件
echo "步骤 1: 清理旧的编译文件..."
rm -f stega_cy*.so stega_cy.cpp
rm -f random_sample_cy*.so random_sample_cy.cpp
echo "  ✓ 清理完成"
echo ""

# 步骤 2: 重新编译 Cython 模块
echo "步骤 2: 重新编译 Cython 模块..."
python setup.py build_ext --inplace

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ 编译失败!"
    echo "请检查编译错误信息"
    exit 1
fi

echo ""
echo "  ✓ 编译成功"
echo ""

# 步骤 3: 验证编译结果
echo "步骤 3: 验证编译结果..."
if [ -f stega_cy.*.so ] || [ -f stega_cy.so ]; then
    echo "  ✓ stega_cy 模块已编译"
    ls -lh stega_cy*.so 2>/dev/null | tail -1
else
    echo "  ✗ stega_cy 模块编译失败"
    exit 1
fi

if [ -f random_sample_cy.*.so ] || [ -f random_sample_cy.so ]; then
    echo "  ✓ random_sample_cy 模块已编译"
    ls -lh random_sample_cy*.so 2>/dev/null | tail -1
else
    echo "  ✗ random_sample_cy 模块编译失败"
    exit 1
fi
echo ""

# 步骤 4: 停止旧的服务器
echo "步骤 4: 停止旧的服务器..."
if pgrep -f "api_server" > /dev/null; then
    echo "  正在停止旧的服务器..."
    pkill -f "api_server"
    sleep 2

    if pgrep -f "api_server" > /dev/null; then
        echo "  ⚠ 服务器仍在运行，强制终止..."
        pkill -9 -f "api_server"
        sleep 1
    fi
    echo "  ✓ 旧服务器已停止"
else
    echo "  - 没有运行中的服务器"
fi
echo ""

# 步骤 5: 启动新服务器
echo "步骤 5: 启动新服务器..."
echo "  运行: python api_server.py &"
python api_server.py > api_server.log 2>&1 &
SERVER_PID=$!

# 等待服务器启动
echo "  等待服务器启动..."
sleep 3

if ps -p $SERVER_PID > /dev/null; then
    echo "  ✓ 服务器已启动 (PID: $SERVER_PID)"

    # 检查服务器健康状态
    if command -v curl > /dev/null 2>&1; then
        echo "  检查服务器健康状态..."
        sleep 1
        HEALTH_CHECK=$(curl -s -H "X-API-Key: jnu@fenglab" http://localhost:8002/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "  ✓ 服务器健康检查通过"
        else
            echo "  ⚠ 无法连接到服务器，可能需要等待"
        fi
    fi
else
    echo "  ✗ 服务器启动失败"
    echo "  查看日志: tail api_server.log"
    exit 1
fi
echo ""

# 步骤 6: 运行测试
echo "步骤 6: 运行测试..."
echo "  运行: python test_multi_cycle.py"
echo ""
sleep 2

python test_multi_cycle.py

TEST_RESULT=$?

echo ""
echo "========================================================================"
echo "修复完成"
echo "========================================================================"

if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ 测试通过！PyTorch RNG 问题已修复"
    echo ""
    echo "服务器信息:"
    echo "  PID: $SERVER_PID"
    echo "  日志: api_server.log"
    echo "  停止: pkill -f api_server"
else
    echo "⚠ 测试未完全通过，请查看测试结果"
    echo ""
    echo "如果仍然失败，尝试:"
    echo "  1. 降低 top_p: 编辑 config.py, 将 top_p 从 0.92 改为 0.88"
    echo "  2. 重新编译: bash fix_pytorch_rng.sh"
    echo "  3. 扩展测试: python test_extended_rounds.py"
fi
echo ""
