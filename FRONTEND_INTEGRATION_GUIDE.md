# 前端集成快速指南

## 快速开始

### 1. 基础配置

```python
import requests

API_URL = "http://your-server:8002"
API_KEY = "jnu@fenglab"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}
```

### 2. 隐藏消息（编码）

```python
def hide_message(message: str) -> dict:
    """将消息隐藏到文本中"""
    response = requests.post(
        f"{API_URL}/encode",
        headers=headers,
        json={
            "message": message,
            "settings": {
                "top_p": 0.88  # 推荐值，提高成功率
            }
        }
    )
    return response.json()

# 使用
result = hide_message("This is secret")
stego_text = result["stego_text"]  # 隐写文本
settings = result["settings"]       # 保存这个！
payload_bits = result["payload_bits"]  # 保存这个！
```

### 3. 提取消息（解码）

```python
def reveal_message(stego_text: str, settings: dict, payload_bits: int) -> str:
    """从隐写文本中提取消息"""
    response = requests.post(
        f"{API_URL}/decode",
        headers=headers,
        json={
            "stego_text": stego_text,
            "context": "We were both young when I first saw you, I close my eyes and the flashback starts.",  # 默认上下文
            "settings": settings,  # 使用编码时返回的 settings
            "expected_bits": payload_bits
        }
    )
    return response.json()["recovered_text"]

# 使用
recovered = reveal_message(stego_text, settings, payload_bits)
print(recovered)  # "This is secret"
```

---

## 完整工作流程

### 步骤 1: 用户输入秘密消息

```python
secret_message = "Meet me at 3pm"
```

### 步骤 2: 调用编码 API

```python
encode_response = requests.post(
    f"{API_URL}/encode",
    headers=headers,
    json={
        "message": secret_message,
        "settings": {"top_p": 0.88}
    }
)

encode_data = encode_response.json()
```

### 步骤 3: 保存到数据库

```python
# 需要保存的数据
database_record = {
    "user_id": current_user.id,
    "timestamp": datetime.now(),
    "stego_text": encode_data["stego_text"],
    "settings": json.dumps(encode_data["settings"]),
    "payload_bits": encode_data["payload_bits"],
    "context": "We were both young when I first saw you, I close my eyes and the flashback starts."
}

# 保存到数据库
db.save(database_record)
```

### 步骤 4: 显示隐写文本给用户

```python
# 前端显示
print(f"您的隐写文本:")
print(encode_data["stego_text"])
```

### 步骤 5: 解码时从数据库读取

```python
# 从数据库读取
record = db.get(message_id)

# 调用解码 API
decode_response = requests.post(
    f"{API_URL}/decode",
    headers=headers,
    json={
        "stego_text": record["stego_text"],
        "context": record["context"],
        "settings": json.loads(record["settings"]),
        "expected_bits": record["payload_bits"]
    }
)

recovered_message = decode_response.json()["recovered_text"]
```

---

## 数据库表结构建议

```sql
CREATE TABLE stego_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 原始消息（可选，加密存储）
    original_message TEXT,

    -- 隐写文本
    stego_text TEXT NOT NULL,

    -- 编码参数（JSON 格式）
    encoding_settings JSON NOT NULL,
    context TEXT NOT NULL,
    payload_bits INT NOT NULL,

    -- 元数据
    embedding_rate FLOAT,
    token_count INT,
    perplexity FLOAT,

    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### 示例数据

```json
{
    "id": 1,
    "user_id": 123,
    "created_at": "2025-09-30 10:30:00",
    "original_message": "Meet me at 3pm",
    "stego_text": "Sitting near the corner, at first his left arm would move...",
    "encoding_settings": {
        "algo": "Discop",
        "temp": 1.0,
        "top_p": 0.88,
        "length": 100,
        "seed": 42
    },
    "context": "We were both young when I first saw you...",
    "payload_bits": 112,
    "embedding_rate": 3.61,
    "token_count": 31,
    "perplexity": 15.05
}
```

---

## 错误处理

```python
def encode_with_error_handling(message: str):
    """编码并处理错误"""
    try:
        response = requests.post(
            f"{API_URL}/encode",
            headers=headers,
            json={"message": message, "settings": {"top_p": 0.88}},
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return {"success": False, "error": "认证失败"}
        elif e.response.status_code == 422:
            return {"success": False, "error": "消息过长，请缩短消息"}
        else:
            return {"success": False, "error": f"服务器错误: {e.response.status_code}"}

    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "无法连接到服务器"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时"}

# 使用
result = encode_with_error_handling("Secret message")
if result["success"]:
    print("编码成功:", result["data"]["stego_text"])
else:
    print("编码失败:", result["error"])
```

---

## JavaScript/TypeScript 示例

### Fetch API

```javascript
// 编码
async function encodeMessage(message) {
    const response = await fetch('http://localhost:8002/encode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'jnu@fenglab'
        },
        body: JSON.stringify({
            message: message,
            settings: {
                top_p: 0.88
            }
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

// 解码
async function decodeMessage(stegoText, settings, payloadBits) {
    const response = await fetch('http://localhost:8002/decode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'jnu@fenglab'
        },
        body: JSON.stringify({
            stego_text: stegoText,
            context: "We were both young when I first saw you, I close my eyes and the flashback starts.",
            settings: settings,
            expected_bits: payloadBits
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.recovered_text;
}

// 使用
(async () => {
    try {
        // 编码
        const encodeResult = await encodeMessage("Secret message");
        console.log("Stego text:", encodeResult.stego_text);

        // 解码
        const recovered = await decodeMessage(
            encodeResult.stego_text,
            encodeResult.settings,
            encodeResult.payload_bits
        );
        console.log("Recovered:", recovered);
    } catch (error) {
        console.error("Error:", error);
    }
})();
```

### Axios

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8002',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'jnu@fenglab'
    }
});

// 编码
async function encodeMessage(message) {
    const response = await api.post('/encode', {
        message: message,
        settings: { top_p: 0.88 }
    });
    return response.data;
}

// 解码
async function decodeMessage(stegoText, settings, payloadBits) {
    const response = await api.post('/decode', {
        stego_text: stegoText,
        context: "We were both young when I first saw you, I close my eyes and the flashback starts.",
        settings: settings,
        expected_bits: payloadBits
    });
    return response.data.recovered_text;
}
```

---

## React 组件示例

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const SteganographyWidget = () => {
    const [message, setMessage] = useState('');
    const [stegoText, setStegoText] = useState('');
    const [encodingData, setEncodingData] = useState(null);
    const [recovered, setRecovered] = useState('');
    const [loading, setLoading] = useState(false);

    const api = axios.create({
        baseURL: 'http://localhost:8002',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'jnu@fenglab'
        }
    });

    const handleEncode = async () => {
        setLoading(true);
        try {
            const response = await api.post('/encode', {
                message: message,
                settings: { top_p: 0.88 }
            });

            setStegoText(response.data.stego_text);
            setEncodingData({
                settings: response.data.settings,
                payload_bits: response.data.payload_bits,
                context: "We were both young when I first saw you, I close my eyes and the flashback starts."
            });
        } catch (error) {
            alert('编码失败: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDecode = async () => {
        if (!encodingData) {
            alert('请先编码消息');
            return;
        }

        setLoading(true);
        try {
            const response = await api.post('/decode', {
                stego_text: stegoText,
                context: encodingData.context,
                settings: encodingData.settings,
                expected_bits: encodingData.payload_bits
            });

            setRecovered(response.data.recovered_text);
        } catch (error) {
            alert('解码失败: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-4">文本隐写术</h2>

            <div className="mb-4">
                <label className="block mb-2">秘密消息:</label>
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="w-full p-2 border rounded"
                    placeholder="输入要隐藏的消息"
                />
            </div>

            <button
                onClick={handleEncode}
                disabled={loading || !message}
                className="bg-blue-500 text-white px-4 py-2 rounded mb-4"
            >
                {loading ? '处理中...' : '编码'}
            </button>

            {stegoText && (
                <div className="mb-4">
                    <label className="block mb-2">隐写文本:</label>
                    <textarea
                        value={stegoText}
                        readOnly
                        className="w-full p-2 border rounded h-32"
                    />
                </div>
            )}

            {stegoText && (
                <button
                    onClick={handleDecode}
                    disabled={loading}
                    className="bg-green-500 text-white px-4 py-2 rounded mb-4"
                >
                    {loading ? '处理中...' : '解码'}
                </button>
            )}

            {recovered && (
                <div className="mb-4">
                    <label className="block mb-2">恢复的消息:</label>
                    <input
                        type="text"
                        value={recovered}
                        readOnly
                        className="w-full p-2 border rounded"
                    />
                    {recovered === message && (
                        <p className="text-green-600 mt-2">✓ 验证成功!</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default SteganographyWidget;
```

---

## 测试清单

部署前检查:

- [ ] API 服务器可访问
- [ ] API Key 正确配置
- [ ] 编码请求返回 200
- [ ] 解码请求返回 200
- [ ] 消息可正确恢复
- [ ] 错误处理正常工作
- [ ] 超时设置合理 (建议 30 秒)
- [ ] 数据库表结构正确
- [ ] 保存了所有必需参数

---

## 常见问题

**Q: 解码失败怎么办?**
A: 确保使用与编码时完全相同的 `context` 和 `settings`

**Q: 如何提高成功率?**
A: 使用 `top_p: 0.88` 而不是默认的 `0.92`

**Q: 消息长度限制?**
A: 约 200 字符（使用 length=100），可通过增加 `length` 参数扩展

**Q: 性能如何?**
A: 编码/解码各约 2-4 秒

**Q: 支持中文吗?**
A: 支持，但嵌入率可能略低

---

## 获取帮助

- API 文档: `API_DOCUMENTATION.md`
- Python 示例: `api_client_examples.py`
- 运行示例: `python api_client_examples.py`
