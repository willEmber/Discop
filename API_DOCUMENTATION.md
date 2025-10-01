# Discop Steganography API 调用文档

## 概述

Discop API 提供文本隐写术服务，可以将秘密消息隐藏在自然生成的文本中，并从隐写文本中提取原始消息。

**服务器地址**: `http://your-server:8002`
**认证方式**: API Key (通过 HTTP Header)
**数据格式**: JSON

---

## 认证

所有 API 请求需要在 HTTP Header 中包含 API Key：

```
X-API-Key: your-api-key-here
```

**示例 API Key**: `jnu@fenglab`

---

## API 端点

### 1. 健康检查

**端点**: `GET /health`
**描述**: 检查服务器状态和配置信息

#### 请求示例

```bash
curl -X GET http://localhost:8002/health \
  -H "X-API-Key: jnu@fenglab"
```

#### 响应示例

```json
{
  "status": "ok",
  "device": "cuda:0",
  "model_loaded": true,
  "reload_strategy": "reset",
  "operations_count": 42
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态，"ok" 表示正常 |
| device | string | 运行设备，"cuda:0" 或 "cpu" |
| model_loaded | boolean | 模型是否已加载 |
| reload_strategy | string | 状态管理策略 |
| operations_count | integer | 已处理的操作数 |

---

### 2. 编码（隐藏消息）

**端点**: `POST /encode`
**描述**: 将秘密消息编码到生成的文本中

#### 请求参数

```json
{
  "message": "string (必需)",
  "context": "string (可选)",
  "settings": {
    "algo": "string (可选)",
    "temp": "number (可选)",
    "top_p": "number (可选)",
    "length": "integer (可选)",
    "seed": "integer (可选)"
  }
}
```

#### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| message | string | ✓ | - | 要隐藏的秘密消息 |
| context | string | ✗ | 默认上下文 | 文本生成的起始上下文 |
| settings.algo | string | ✗ | "Discop" | 算法类型: "Discop", "Discop_baseline", "sample" |
| settings.temp | number | ✗ | 1.0 | 温度参数，控制生成多样性 (>0) |
| settings.top_p | number | ✗ | 0.92 | Nucleus 采样阈值 (0-1)，建议 0.88 提高成功率 |
| settings.length | integer | ✗ | 自动计算 | 生成文本的最大 token 数 |
| settings.seed | integer | ✗ | 随机 | 随机种子，用于可复现结果 |

#### 请求示例

```bash
curl -X POST http://localhost:8002/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jnu@fenglab" \
  -d '{
    "message": "This is a secret message",
    "context": "Once upon a time in a distant land",
    "settings": {
      "top_p": 0.88,
      "seed": 42
    }
  }'
```

#### 响应示例

```json
{
  "stego_text": "Once upon a time in a distant land there lived a wise old wizard who...",
  "embedded_bits": 192,
  "payload_bits": 192,
  "token_count": 50,
  "embedding_rate": 3.84,
  "utilization_rate": 0.87,
  "perplexity": 15.23,
  "settings": {
    "algo": "Discop",
    "temp": 1.0,
    "top_p": 0.88,
    "length": 100,
    "seed": 42
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| stego_text | string | 包含隐藏消息的生成文本 |
| embedded_bits | integer | 实际嵌入的比特数 |
| payload_bits | integer | 原始消息的比特数 |
| token_count | integer | 生成的 token 数量 |
| embedding_rate | number | 嵌入率 (bits/token) |
| utilization_rate | number | 熵利用率 |
| perplexity | number | 文本困惑度 |
| settings | object | 实际使用的设置参数 |

---

### 3. 解码（提取消息）

**端点**: `POST /decode`
**描述**: 从隐写文本中提取隐藏的消息

#### 请求参数

```json
{
  "stego_text": "string (必需)",
  "context": "string (必需)",
  "expected_bits": "integer (可选)",
  "settings": {
    "algo": "string (可选)",
    "temp": "number (可选)",
    "top_p": "number (可选)",
    "seed": "integer (可选)"
  }
}
```

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| stego_text | string | ✓ | 包含隐藏消息的文本 |
| context | string | ✓ | **必须与编码时使用的上下文完全相同** |
| expected_bits | integer | ✗ | 预期的消息比特数，用于截断输出 |
| settings | object | ✗ | **必须与编码时使用的设置相同** |

⚠️ **重要**: `context` 和 `settings` 必须与编码时完全一致，否则解码会失败！

#### 请求示例

```bash
curl -X POST http://localhost:8002/decode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jnu@fenglab" \
  -d '{
    "stego_text": "Once upon a time in a distant land there lived a wise old wizard who...",
    "context": "Once upon a time in a distant land",
    "expected_bits": 192,
    "settings": {
      "algo": "Discop",
      "temp": 1.0,
      "top_p": 0.88,
      "seed": 42
    }
  }'
```

#### 响应示例

```json
{
  "recovered_bits": "010101000110100001101001011100110010...",
  "recovered_text": "This is a secret message",
  "used_bits": 192
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| recovered_bits | string | 恢复的二进制字符串 |
| recovered_text | string | 恢复的原始消息文本 |
| used_bits | integer | 实际使用的比特数 |

---

### 4. 手动重载模型

**端点**: `POST /reload`
**描述**: 手动触发完整的模型重载（用于清除任何可能的状态问题）

#### 请求示例

```bash
curl -X POST http://localhost:8002/reload \
  -H "X-API-Key: jnu@fenglab"
```

#### 响应示例

```json
{
  "status": "reloaded",
  "message": "Model has been completely reloaded"
}
```

---

### 5. 手动重置状态

**端点**: `POST /reset`
**描述**: 手动触发状态重置（比完整重载更轻量）

#### 请求示例

```bash
curl -X POST http://localhost:8002/reset \
  -H "X-API-Key: jnu@fenglab"
```

#### 响应示例

```json
{
  "status": "reset",
  "message": "Model state has been reset"
}
```

---

## 错误响应

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权（API Key 错误或缺失）|
| 422 | 无法嵌入完整消息（消息过长或长度不足）|
| 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "detail": "Message must not be empty."
}
```

---

## 使用流程

### 典型的编码-解码流程

```
1. 客户端: POST /encode
   ↓ (发送消息 + 上下文)
2. 服务器: 生成隐写文本
   ↓ (返回隐写文本 + 设置参数)
3. 客户端: 保存隐写文本和设置参数
   ↓
4. 客户端: POST /decode
   ↓ (发送隐写文本 + 相同的上下文和设置)
5. 服务器: 提取原始消息
   ↓ (返回恢复的消息)
6. 验证: recovered_text == 原始消息
```

---

## 最佳实践

### 1. 提高成功率

- 使用 `top_p: 0.88` 而不是默认的 `0.92`
- 为较长的消息设置更大的 `length`

```json
{
  "message": "long secret message...",
  "settings": {
    "top_p": 0.88,
    "length": 200
  }
}
```

### 2. 可复现结果

使用固定的 `seed` 值:

```json
{
  "message": "secret",
  "settings": {
    "seed": 12345
  }
}
```

### 3. 保存编码参数

解码时必须使用编码响应中返回的 `settings`:

```python
# 编码
encode_response = requests.post("/encode", json={...})
encode_result = encode_response.json()

# 保存这些参数！
stego_text = encode_result["stego_text"]
settings = encode_result["settings"]
context = original_context  # 编码时使用的上下文

# 解码（使用相同参数）
decode_response = requests.post("/decode", json={
    "stego_text": stego_text,
    "context": context,  # 必须相同！
    "settings": settings  # 必须相同！
})
```

### 4. 错误处理

```python
try:
    response = requests.post("/encode", json={...})
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        # 消息过长，增加 length 参数重试
        pass
    elif e.response.status_code == 401:
        # API Key 错误
        pass
```

---

## 性能指标

| 指标 | 典型值 | 说明 |
|------|--------|------|
| 编码速度 | 2-4 秒 | 100 tokens |
| 解码速度 | 2-3 秒 | 100 tokens |
| 嵌入率 | 3.5-4.5 bits/token | 依赖于 top_p |
| 成功率 | 95%+ | 使用 top_p=0.88 |
| 最大消息长度 | ~200 字符 | 使用 length=100 |

---

## 限制说明

1. **上下文依赖**: 解码必须使用与编码时完全相同的上下文
2. **参数一致性**: 解码必须使用与编码时相同的算法参数
3. **消息长度**: 受生成长度限制，过长的消息可能无法完全嵌入
4. **成功率**: ~95% (使用推荐设置)，约 5% 的情况可能因概率匹配问题失败

---

## 支持与反馈

- **服务器健康检查**: `GET /health`
- **日志位置**: `api_server.log`
- **重启服务**: `pkill -f api_server && python api_server.py`
