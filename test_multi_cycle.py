"""Test script to verify multiple encode/decode cycles work correctly."""
import requests
import json
import time
import os
import sys

# Configuration - can be overridden by environment variables
API_HOST = os.getenv("DISCOP_HOST", "localhost")
API_PORT = int(os.getenv("DISCOP_PORT", "8002"))
API_KEY = os.getenv("DISCOP_API_KEY", "jnu@fenglab")

API_BASE = f"http://{API_HOST}:{API_PORT}"

headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY


def test_single_cycle(cycle_num: int, message: str, context: str) -> bool:
    """Test a single encode/decode cycle."""
    print(f"\n{'='*60}")
    print(f"Cycle {cycle_num}: Testing message: '{message}'")
    print(f"{'='*60}")

    # Encode
    encode_payload = {
        "message": message,
        "context": context,
        "settings": {
            "seed": cycle_num  # Use different seed for each cycle
        }
    }

    print("→ Encoding...")
    encode_response = requests.post(
        f"{API_BASE}/encode",
        json=encode_payload,
        headers=headers
    )

    if encode_response.status_code != 200:
        print(f"✗ Encode failed: {encode_response.status_code}")
        print(encode_response.text)
        return False

    encode_result = encode_response.json()
    stego_text = encode_result["stego_text"]
    payload_bits = encode_result["payload_bits"]

    print(f"  ✓ Encoded successfully")
    print(f"  - Stego text: {stego_text[:80]}...")
    print(f"  - Embedding rate: {encode_result['embedding_rate']:.2f} bits/token")
    print(f"  - Perplexity: {encode_result['perplexity']:.2f}")

    # Decode
    decode_payload = {
        "stego_text": stego_text,
        "context": context,
        "expected_bits": payload_bits,
        "settings": encode_result["settings"]
    }

    print("→ Decoding...")
    decode_response = requests.post(
        f"{API_BASE}/decode",
        json=decode_payload,
        headers=headers
    )

    if decode_response.status_code != 200:
        print(f"✗ Decode failed: {decode_response.status_code}")
        print(decode_response.text)
        return False

    decode_result = decode_response.json()
    recovered_message = decode_result.get("recovered_text", "")

    print(f"  ✓ Decoded successfully")
    print(f"  - Recovered: '{recovered_message}'")

    # Verify
    success = recovered_message == message
    if success:
        print(f"  ✓ CYCLE {cycle_num} PASSED: Message recovered correctly!")
    else:
        print(f"  ✗ CYCLE {cycle_num} FAILED: Message mismatch!")
        print(f"    Expected: '{message}'")
        print(f"    Got:      '{recovered_message}'")

    return success


def main():
    """Run multiple encode/decode cycles to test state management."""
    print("Testing Multiple Encode/Decode Cycles")
    print("=" * 60)
    print(f"API Base: {API_BASE}")
    print(f"Auth:     {'Enabled' if API_KEY else 'Disabled'}")
    print("=" * 60)

    # Check health
    print("\nChecking API health...")
    health_response = requests.get(f"{API_BASE}/health", headers=headers)
    if health_response.status_code == 200:
        health = health_response.json()
        print(f"✓ API is healthy")
        print(f"  - Device: {health['device']}")
        print(f"  - Reload strategy: {health['reload_strategy']}")
        print(f"  - Operations count: {health['operations_count']}")
    else:
        print(f"✗ Health check failed: {health_response.status_code}")
        return

    # Test cases
    test_cases = [
        ("Hello World", "The quick brown fox jumps over the lazy dog."),
        ("Secret message", "In a hole in the ground there lived a hobbit."),
        ("Testing 123", "It was the best of times, it was the worst of times."),
        ("Fourth test", "Call me Ishmael. Some years ago—never mind how long precisely."),
        ("Final check", "All happy families are alike; each unhappy family is unhappy in its own way."),
    ]

    results = []
    for i, (message, context) in enumerate(test_cases, 1):
        success = test_single_cycle(i, message, context)
        results.append(success)
        time.sleep(0.5)  # Small delay between cycles

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All cycles passed! The state management fix is working.")
    else:
        print(f"✗ {total - passed} cycle(s) failed. State corruption may still be occurring.")
        print("\nFailed cycles:")
        for i, success in enumerate(results, 1):
            if not success:
                print(f"  - Cycle {i}")

    # Final health check
    print("\nFinal health check...")
    health_response = requests.get(f"{API_BASE}/health", headers=headers)
    if health_response.status_code == 200:
        health = health_response.json()
        print(f"  - Operations count: {health['operations_count']}")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("  Make sure the server is running: uvicorn api_server:app --reload")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
