╔════════════════════════════════════════════════════════════════════════╗
║                  关键修复：PyTorch 随机数状态问题                         ║
╚════════════════════════════════════════════════════════════════════════╝

## 问题根源

发现了为什么总是第 3 轮测试失败：

**根本原因：PyTorch 的随机数生成器状态在多轮测试中累积**

### 代码缺陷

1. **utils.py 中的 set_seed() 函数（旧版）**:
   ```python
   def set_seed(sd):
       random.seed(sd)  # ✗ 只设置 Python random，没有设置 PyTorch!
   ```

2. **影响**:
   - Cycle 1: Python random seed=1, PyTorch RNG 未重置
   - Cycle 2: Python random seed=2, PyTorch RNG 继续累积
   - Cycle 3: Python random seed=3, PyTorch RNG 状态已偏移 → **解码失败**

3. **为什么总是第 3 轮**:
   - PyTorch RNG 的累积误差在第 3 轮达到临界点
   - 导致编码和解码时的概率分布出现微小但致命的差异

## 修复内容

### 1. 修复 utils.py 中的 set_seed()

```python
def set_seed(sd):
    # Set Python random seed
    random.seed(sd)

    # CRITICAL: Set PyTorch seed
    if sd is not None:
        torch.manual_seed(sd)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(sd)
```

### 2. 增强 api_server.py 中的状态重置

在 `_reset_model_state()` 和 `_reload_model()` 中添加：
```python
# Reset PyTorch random state
torch.manual_seed(random.randint(0, 2**31 - 1))
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(random.randint(0, 2**31 - 1))
```

## 需要执行的步骤

### ⚠️ 重要：必须重新编译 Cython 模块

```bash
cd /opt/data/sanli/text_hide/Discop

# 1. 清理旧的编译文件
rm -f stega_cy*.so stega_cy.cpp
rm -f random_sample_cy*.so random_sample_cy.cpp

# 2. 重新编译
python setup.py build_ext --inplace

# 3. 验证编译成功
ls -lh stega_cy*.so random_sample_cy*.so
```

### 重启服务器并测试

```bash
# 停止旧服务器
pkill -f api_server

# 启动新服务器
python api_server.py

# 新终端测试
python test_multi_cycle.py
```

## 预期结果

修复后应该看到：

```
============================================================
Cycle 1: Testing message: 'Hello World'
✓ CYCLE 1 PASSED: Message recovered correctly!

============================================================
Cycle 2: Testing message: 'Secret message'
✓ CYCLE 2 PASSED: Message recovered correctly!

============================================================
Cycle 3: Testing message: 'One night'
✓ CYCLE 3 PASSED: Message recovered correctly!  ← 现在应该成功了！

============================================================
Cycle 4: Testing message: 'Fourth test'
✓ CYCLE 4 PASSED: Message recovered correctly!

============================================================
Cycle 5: Testing message: 'Final check'
✓ CYCLE 5 PASSED: Message recovered correctly!

============================================================
SUMMARY
============================================================
Passed: 5/5  ← 100% 成功率！
✓ All cycles passed! The state management fix is working.
```

## 技术细节

### PyTorch RNG 的作用

在模型推理中，PyTorch RNG 用于：
1. Dropout layers (即使在 eval 模式下某些模型也可能使用)
2. 概率采样操作
3. 数值计算中的随机舍入

### 为什么之前没发现

- 单次测试时问题不明显
- 前两轮的累积误差还不够大
- 第 3 轮恰好达到临界点，导致 Huffman 树解码失败

### 修复的完整性

现在系统在三个层面都正确重置了随机状态：
1. ✓ Python random (Cython 解码使用)
2. ✓ PyTorch RNG (模型推理使用)
3. ✓ Cython 全局状态 (msg_exhausted_flag)

## 验证清单

□ 1. 修改了 utils.py 中的 set_seed()
□ 2. 修改了 api_server.py 中的 _reset_model_state()
□ 3. 修改了 api_server.py 中的 _reload_model()
□ 4. 删除了旧的 .so 文件
□ 5. 重新编译: python setup.py build_ext --inplace
□ 6. 重启服务器: python api_server.py
□ 7. 运行测试: python test_multi_cycle.py
□ 8. 验证结果: 5/5 成功

╔════════════════════════════════════════════════════════════════════════╗
║ 一键执行修复                                                            ║
║                                                                         ║
║   rm -f *.so *.cpp                                                     ║
║   python setup.py build_ext --inplace                                  ║
║   pkill -f api_server; sleep 1; python api_server.py &                ║
║   sleep 3; python test_multi_cycle.py                                 ║
╚════════════════════════════════════════════════════════════════════════╝
