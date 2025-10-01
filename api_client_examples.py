"""
Discop Steganography API - Python 客户端示例

这个文件包含了调用 Discop API 的各种 Python 示例代码。
"""

import requests
import json
from typing import Optional, Dict, Any


# =============================================================================
# 配置
# =============================================================================

API_BASE_URL = "http://localhost:8002"
API_KEY = "jnu@fenglab"  # 替换为你的 API Key

# HTTP Headers
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


# =============================================================================
# 基础功能函数
# =============================================================================

def check_health() -> Dict[str, Any]:
    """
    检查 API 服务器健康状态

    Returns:
        服务器状态信息
    """
    response = requests.get(f"{API_BASE_URL}/health", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def encode_message(
    message: str,
    context: Optional[str] = None,
    top_p: float = 0.88,
    length: Optional[int] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    编码消息到隐写文本中

    Args:
        message: 要隐藏的秘密消息
        context: 文本生成的起始上下文（可选）
        top_p: Nucleus 采样阈值，推荐 0.88 (默认 0.88)
        length: 生成文本的最大长度（可选，自动计算）
        seed: 随机种子（可选）

    Returns:
        包含隐写文本和元数据的字典
    """
    payload = {
        "message": message,
        "settings": {
            "top_p": top_p
        }
    }

    if context is not None:
        payload["context"] = context

    if length is not None:
        payload["settings"]["length"] = length

    if seed is not None:
        payload["settings"]["seed"] = seed

    response = requests.post(
        f"{API_BASE_URL}/encode",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def decode_message(
    stego_text: str,
    context: str,
    settings: Dict[str, Any],
    expected_bits: Optional[int] = None
) -> Dict[str, Any]:
    """
    从隐写文本中解码消息

    Args:
        stego_text: 包含隐藏消息的文本
        context: 编码时使用的上下文（必须完全相同！）
        settings: 编码时使用的设置参数（必须完全相同！）
        expected_bits: 预期的比特数（可选）

    Returns:
        包含恢复消息的字典
    """
    payload = {
        "stego_text": stego_text,
        "context": context,
        "settings": settings
    }

    if expected_bits is not None:
        payload["expected_bits"] = expected_bits

    response = requests.post(
        f"{API_BASE_URL}/decode",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def reload_model() -> Dict[str, str]:
    """
    手动重载模型

    Returns:
        重载状态信息
    """
    response = requests.post(f"{API_BASE_URL}/reload", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def reset_state() -> Dict[str, str]:
    """
    手动重置模型状态

    Returns:
        重置状态信息
    """
    response = requests.post(f"{API_BASE_URL}/reset", headers=HEADERS)
    response.raise_for_status()
    return response.json()


# =============================================================================
# 示例 1: 基础的编码-解码流程
# =============================================================================

def example_1_basic_encode_decode():
    """示例 1: 基础的编码和解码"""
    print("=" * 70)
    print("示例 1: 基础的编码-解码流程")
    print("=" * 70)

    # 要隐藏的消息
    secret_message = "This is a secret message"
    print(f"\n原始消息: '{secret_message}'")

    # 编码
    print("\n正在编码...")
    encode_result = encode_message(secret_message)

    stego_text = encode_result["stego_text"]
    settings = encode_result["settings"]

    print(f"✓ 编码成功")
    print(f"  隐写文本: {stego_text[:80]}...")
    print(f"  嵌入率: {encode_result['embedding_rate']:.2f} bits/token")

    # 解码
    print("\n正在解码...")
    decode_result = decode_message(
        stego_text=stego_text,
        context="We were both young when I first saw you, I close my eyes and the flashback starts.",
        settings=settings,
        expected_bits=encode_result["payload_bits"]
    )

    recovered_message = decode_result["recovered_text"]
    print(f"✓ 解码成功")
    print(f"  恢复的消息: '{recovered_message}'")

    # 验证
    if recovered_message == secret_message:
        print("\n✓ 验证成功: 消息完全恢复！")
    else:
        print("\n✗ 验证失败: 消息不匹配")


# =============================================================================
# 示例 2: 使用自定义上下文
# =============================================================================

def example_2_custom_context():
    """示例 2: 使用自定义上下文"""
    print("\n" + "=" * 70)
    print("示例 2: 使用自定义上下文")
    print("=" * 70)

    secret_message = "Meet me at the usual place"
    custom_context = "In the heart of the ancient forest, where sunlight barely reaches"

    print(f"\n原始消息: '{secret_message}'")
    print(f"自定义上下文: '{custom_context}'")

    # 编码
    print("\n正在编码...")
    encode_result = encode_message(
        message=secret_message,
        context=custom_context,
        top_p=0.88,
        seed=42  # 使用固定种子确保可复现
    )

    print(f"✓ 编码成功")
    print(f"  隐写文本: {encode_result['stego_text'][:100]}...")

    # 解码
    print("\n正在解码...")
    decode_result = decode_message(
        stego_text=encode_result["stego_text"],
        context=custom_context,  # 必须使用相同的上下文！
        settings=encode_result["settings"],
        expected_bits=encode_result["payload_bits"]
    )

    print(f"✓ 解码成功")
    print(f"  恢复的消息: '{decode_result['recovered_text']}'")


# =============================================================================
# 示例 3: 批量处理多个消息
# =============================================================================

def example_3_batch_processing():
    """示例 3: 批量处理多个消息"""
    print("\n" + "=" * 70)
    print("示例 3: 批量处理多个消息")
    print("=" * 70)

    messages = [
        "First secret",
        "Second secret",
        "Third secret"
    ]

    # 存储编码结果
    encoded_data = []

    print("\n批量编码...")
    for i, msg in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] 编码: '{msg}'")
        result = encode_message(msg, seed=i)
        encoded_data.append({
            "original": msg,
            "stego_text": result["stego_text"],
            "context": "We were both young when I first saw you, I close my eyes and the flashback starts.",
            "settings": result["settings"],
            "payload_bits": result["payload_bits"]
        })

    print(f"\n✓ 已编码 {len(encoded_data)} 条消息")

    # 批量解码
    print("\n批量解码...")
    success_count = 0
    for i, data in enumerate(encoded_data, 1):
        print(f"  [{i}/{len(encoded_data)}] 解码...")
        result = decode_message(
            stego_text=data["stego_text"],
            context=data["context"],
            settings=data["settings"],
            expected_bits=data["payload_bits"]
        )

        if result["recovered_text"] == data["original"]:
            success_count += 1
            print(f"    ✓ 成功: '{result['recovered_text']}'")
        else:
            print(f"    ✗ 失败")

    print(f"\n成功率: {success_count}/{len(encoded_data)} ({success_count/len(encoded_data)*100:.1f}%)")


# =============================================================================
# 示例 4: 错误处理
# =============================================================================

def example_4_error_handling():
    """示例 4: 正确的错误处理"""
    print("\n" + "=" * 70)
    print("示例 4: 错误处理示例")
    print("=" * 70)

    def encode_with_retry(message: str, max_retries: int = 3):
        """编码并在失败时自动重试"""
        for attempt in range(max_retries):
            try:
                # 每次重试降低 top_p
                top_p = 0.92 - (attempt * 0.02)
                print(f"\n尝试 {attempt + 1}/{max_retries} (top_p={top_p})...")

                result = encode_message(message, top_p=top_p)
                print("✓ 编码成功")
                return result

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    print(f"✗ 编码失败: {e.response.json().get('detail', 'Unknown error')}")
                    if attempt < max_retries - 1:
                        print("  正在重试...")
                        continue
                elif e.response.status_code == 401:
                    print("✗ 认证失败: API Key 无效")
                    return None
                else:
                    print(f"✗ 错误 {e.response.status_code}: {e.response.text}")
                    return None
            except requests.exceptions.ConnectionError:
                print("✗ 连接失败: 无法连接到服务器")
                return None

        print(f"✗ 编码失败: 已达到最大重试次数")
        return None

    # 测试
    message = "A relatively short message"
    result = encode_with_retry(message)

    if result:
        print(f"\n最终结果:")
        print(f"  嵌入率: {result['embedding_rate']:.2f} bits/token")
        print(f"  困惑度: {result['perplexity']:.2f}")


# =============================================================================
# 示例 5: 完整的应用示例（前端对接）
# =============================================================================

class DiscopClient:
    """Discop API 客户端封装类"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

    def health_check(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def hide_message(
        self,
        message: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        隐藏消息（编码）

        Returns:
            包含 stego_text, settings, context 等信息的字典，失败返回 None
        """
        try:
            payload = {
                "message": message,
                "settings": {
                    "top_p": kwargs.get("top_p", 0.88)
                }
            }

            if context:
                payload["context"] = context

            response = requests.post(
                f"{self.base_url}/encode",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 返回前端需要保存的数据
            return {
                "stego_text": result["stego_text"],
                "settings": result["settings"],
                "context": context or "We were both young when I first saw you, I close my eyes and the flashback starts.",
                "payload_bits": result["payload_bits"],
                "metadata": {
                    "embedding_rate": result["embedding_rate"],
                    "token_count": result["token_count"],
                    "perplexity": result["perplexity"]
                }
            }
        except Exception as e:
            print(f"编码失败: {e}")
            return None

    def reveal_message(
        self,
        stego_text: str,
        context: str,
        settings: Dict[str, Any],
        expected_bits: int
    ) -> Optional[str]:
        """
        提取消息（解码）

        Returns:
            恢复的原始消息，失败返回 None
        """
        try:
            payload = {
                "stego_text": stego_text,
                "context": context,
                "settings": settings,
                "expected_bits": expected_bits
            }

            response = requests.post(
                f"{self.base_url}/decode",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result.get("recovered_text")

        except Exception as e:
            print(f"解码失败: {e}")
            return None


def example_5_client_class():
    """示例 5: 使用客户端类（前端对接推荐方式）"""
    print("\n" + "=" * 70)
    print("示例 5: 使用 DiscopClient 类")
    print("=" * 70)

    # 初始化客户端
    client = DiscopClient(
        base_url="http://localhost:8002",
        api_key="jnu@fenglab"
    )

    # 健康检查
    print("\n检查服务器状态...")
    if not client.health_check():
        print("✗ 服务器不可用")
        return
    print("✓ 服务器正常")

    # 编码
    secret = "This is my secret message"
    print(f"\n隐藏消息: '{secret}'")

    encode_data = client.hide_message(secret)
    if not encode_data:
        print("✗ 编码失败")
        return

    print("✓ 编码成功")
    print(f"  隐写文本: {encode_data['stego_text'][:60]}...")
    print(f"  嵌入率: {encode_data['metadata']['embedding_rate']:.2f} bits/token")

    # 前端应该将 encode_data 保存到数据库或发送给接收方
    # encode_data 包含: stego_text, settings, context, payload_bits

    # 解码
    print(f"\n提取消息...")
    recovered = client.reveal_message(
        stego_text=encode_data["stego_text"],
        context=encode_data["context"],
        settings=encode_data["settings"],
        expected_bits=encode_data["payload_bits"]
    )

    if recovered:
        print(f"✓ 解码成功")
        print(f"  恢复的消息: '{recovered}'")

        if recovered == secret:
            print("\n✓ 验证成功!")
        else:
            print("\n✗ 验证失败: 消息不匹配")
    else:
        print("✗ 解码失败")


# =============================================================================
# 示例 6: 前端 JSON 数据格式
# =============================================================================

def example_6_frontend_data_format():
    """示例 6: 前端应该保存的 JSON 数据格式"""
    print("\n" + "=" * 70)
    print("示例 6: 前端数据格式示例")
    print("=" * 70)

    # 编码
    message = "Secret data"
    encode_result = encode_message(message, seed=123)

    # 前端应该保存这样的 JSON 数据
    frontend_data = {
        "id": "unique-message-id-123",
        "timestamp": "2025-09-30T10:30:00Z",
        "original_message": message,  # 可选，调试用
        "stego_text": encode_result["stego_text"],
        "encoding_params": {
            "context": "We were both young when I first saw you, I close my eyes and the flashback starts.",
            "settings": encode_result["settings"],
            "payload_bits": encode_result["payload_bits"]
        },
        "metadata": {
            "embedding_rate": encode_result["embedding_rate"],
            "token_count": encode_result["token_count"],
            "perplexity": encode_result["perplexity"]
        }
    }

    print("\n前端应该保存的 JSON 格式:")
    print(json.dumps(frontend_data, indent=2, ensure_ascii=False))

    # 解码时使用
    print("\n解码时的请求格式:")
    decode_request = {
        "stego_text": frontend_data["stego_text"],
        "context": frontend_data["encoding_params"]["context"],
        "settings": frontend_data["encoding_params"]["settings"],
        "expected_bits": frontend_data["encoding_params"]["payload_bits"]
    }
    print(json.dumps(decode_request, indent=2, ensure_ascii=False))


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有示例"""
    print("Discop API Python 客户端示例")
    print("=" * 70)

    # 检查服务器状态
    try:
        health = check_health()
        print(f"\n✓ 服务器状态: {health['status']}")
        print(f"  设备: {health['device']}")
        print(f"  重载策略: {health['reload_strategy']}")
    except Exception as e:
        print(f"\n✗ 无法连接到服务器: {e}")
        print("请确保服务器正在运行: python api_server.py")
        return

    # 运行示例
    try:
        example_1_basic_encode_decode()
        example_2_custom_context()
        example_3_batch_processing()
        example_4_error_handling()
        example_5_client_class()
        example_6_frontend_data_format()

        print("\n" + "=" * 70)
        print("所有示例执行完成!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n中断执行")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
