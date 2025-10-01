# API 文档索引

本文档索引列出了所有 API 相关的文档和示例文件。

## 📚 文档列表

### 1. API_DOCUMENTATION.md
**完整的 API 参考文档**

- ✓ 所有端点的详细说明
- ✓ 请求/响应参数说明
- ✓ 错误码说明
- ✓ 性能指标
- ✓ 最佳实践

**适用于**: 开发者需要完整 API 参考时查阅

---

### 2. api_client_examples.py
**Python 客户端示例代码**

包含 6 个完整示例:
- ✓ 示例 1: 基础编码-解码流程
- ✓ 示例 2: 使用自定义上下文
- ✓ 示例 3: 批量处理多个消息
- ✓ 示例 4: 错误处理
- ✓ 示例 5: DiscopClient 封装类（推荐）
- ✓ 示例 6: 前端数据格式

**运行**: `python api_client_examples.py`

**适用于**: Python 开发者学习如何调用 API

---

### 3. FRONTEND_INTEGRATION_GUIDE.md
**前端集成快速指南**

- ✓ 快速开始（最小代码）
- ✓ 完整工作流程
- ✓ 数据库表结构建议
- ✓ JavaScript/TypeScript 示例
- ✓ React 组件示例
- ✓ 错误处理示例

**适用于**: 前端开发者对接 API

---

### 4. API_QUICK_REFERENCE.txt
**API 快速参考卡片**

- ✓ 一页纸参考
- ✓ 所有端点概览
- ✓ 最小代码示例
- ✓ 错误码速查
- ✓ 性能参考

**适用于**: 快速查阅 API 用法

---

## 🎯 根据场景选择文档

### 场景 1: 我是 Python 开发者，想快速试用

1. 查看 `API_QUICK_REFERENCE.txt` (3 分钟)
2. 运行 `python api_client_examples.py` (5 分钟)
3. 复制示例 5 的 `DiscopClient` 类到你的项目

### 场景 2: 我是前端开发者，需要对接 API

1. 阅读 `FRONTEND_INTEGRATION_GUIDE.md` (15 分钟)
2. 复制 JavaScript 或 React 示例到你的项目
3. 参考数据库表结构设计存储

### 场景 3: 我需要完整的 API 文档

1. 阅读 `API_DOCUMENTATION.md` (30 分钟)
2. 了解所有端点和参数
3. 根据需要参考示例代码

### 场景 4: 我遇到了问题，需要调试

1. 检查 `API_DOCUMENTATION.md` 的错误响应部分
2. 查看 `api_client_examples.py` 的示例 4（错误处理）
3. 运行 `curl -H "X-API-Key: your-key" http://localhost:8002/health` 检查服务器

---

## 📋 快速开始检查清单

### 服务器端

- [ ] 服务器已启动: `python api_server.py`
- [ ] 服务器可访问: `curl http://localhost:8002/health`
- [ ] API Key 已配置: 查看 `api_server.py` 第 81 行

### 客户端

- [ ] 已安装 requests: `pip install requests`
- [ ] API URL 正确: 默认 `http://localhost:8002`
- [ ] API Key 正确: 与服务器配置一致
- [ ] 测试连接: `python api_client_examples.py`

---

## 🔧 常用代码片段

### Python - 最小示例

```python
import requests

API_URL = "http://localhost:8002"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "jnu@fenglab"
}

# 编码
encode_resp = requests.post(f"{API_URL}/encode", headers=headers, json={
    "message": "Secret message",
    "settings": {"top_p": 0.88}
})
result = encode_resp.json()

# 解码
decode_resp = requests.post(f"{API_URL}/decode", headers=headers, json={
    "stego_text": result["stego_text"],
    "context": "We were both young when I first saw you, I close my eyes and the flashback starts.",
    "settings": result["settings"],
    "expected_bits": result["payload_bits"]
})
print(decode_resp.json()["recovered_text"])
```

### JavaScript - 最小示例

```javascript
const API_URL = "http://localhost:8002";
const headers = {
    "Content-Type": "application/json",
    "X-API-Key": "jnu@fenglab"
};

// 编码
const encodeResp = await fetch(`${API_URL}/encode`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
        message: "Secret message",
        settings: { top_p: 0.88 }
    })
});
const result = await encodeResp.json();

// 解码
const decodeResp = await fetch(`${API_URL}/decode`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
        stego_text: result.stego_text,
        context: "We were both young when I first saw you, I close my eyes and the flashback starts.",
        settings: result.settings,
        expected_bits: result.payload_bits
    })
});
const decoded = await decodeResp.json();
console.log(decoded.recovered_text);
```

### cURL - 测试命令

```bash
# 健康检查
curl -H "X-API-Key: jnu@fenglab" http://localhost:8002/health

# 编码
curl -X POST http://localhost:8002/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jnu@fenglab" \
  -d '{"message": "test", "settings": {"top_p": 0.88}}'

# 解码（需要先从编码响应获取参数）
curl -X POST http://localhost:8002/decode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jnu@fenglab" \
  -d '{
    "stego_text": "...",
    "context": "We were both young when I first saw you, I close my eyes and the flashback starts.",
    "settings": {...},
    "expected_bits": 192
  }'
```

---

## 🐛 故障排查

### 问题: 无法连接到服务器

```bash
# 检查服务器是否运行
ps aux | grep api_server

# 检查端口是否监听
netstat -tuln | grep 8002

# 重启服务器
pkill -f api_server
python api_server.py
```

### 问题: 401 认证失败

检查:
1. `api_server.py` 中的 `API_KEY` 配置（第 81 行）
2. 请求 Header 中的 `X-API-Key` 是否正确
3. API Key 是否包含特殊字符需要转义

### 问题: 解码失败

检查:
1. 是否使用了与编码时**完全相同**的 `context`
2. 是否使用了与编码时**完全相同**的 `settings`
3. `stego_text` 是否被修改过

### 问题: 成功率低

尝试:
1. 使用 `top_p: 0.88` 而不是默认的 `0.92`
2. 缩短消息长度
3. 增加 `length` 参数

---

## 📊 性能优化建议

### 提高成功率

```python
# 使用更保守的 top_p
settings = {
    "top_p": 0.88,  # 而不是 0.92
    "seed": 42      # 固定种子确保可复现
}
```

### 处理长消息

```python
# 自动计算合适的长度
message_length = len(message)
estimated_bits = message_length * 8

settings = {
    "top_p": 0.88,
    "length": max(100, estimated_bits // 3)  # 预估需要的 token 数
}
```

### 批量处理

```python
import concurrent.futures

def encode_message_batch(messages):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(encode_message, msg) for msg in messages]
        return [f.result() for f in concurrent.futures.as_completed(futures)]
```

---

## 📞 获取帮助

- **API 文档**: `API_DOCUMENTATION.md`
- **示例代码**: `api_client_examples.py`
- **快速参考**: `API_QUICK_REFERENCE.txt`
- **前端集成**: `FRONTEND_INTEGRATION_GUIDE.md`

- **服务器日志**: `api_server.log`
- **测试脚本**: `test_multi_cycle.py`
- **健康检查**: `GET /health`

---

## 📝 更新日志

### 2025-09-30
- ✓ 添加完整的 API 文档
- ✓ 添加 Python 客户端示例（6 个示例）
- ✓ 添加前端集成指南（JavaScript/React）
- ✓ 添加快速参考卡片
- ✓ 修复 PyTorch RNG 状态问题
- ✓ 成功率提升至 95%+（使用 top_p=0.88）

---

## 🚀 下一步

1. 阅读适合你角色的文档
2. 运行示例代码测试连接
3. 复制相关代码到你的项目
4. 根据需要调整参数
5. 部署到生产环境

**祝开发顺利！**
