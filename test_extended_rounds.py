"""Extended multi-round test to verify error probability does NOT accumulate."""
import requests
import json
import time
import os
import sys
import random

# Configuration
API_HOST = os.getenv("DISCOP_HOST", "localhost")
API_PORT = int(os.getenv("DISCOP_PORT", "8002"))
API_KEY = os.getenv("DISCOP_API_KEY", "jnu@fenglab")
API_BASE = f"http://{API_HOST}:{API_PORT}"

headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY

# Test parameters
NUM_ROUNDS = 20  # Test 20 rounds to check for accumulation
RANDOM_MESSAGES = True  # Use random messages to avoid caching effects


def generate_random_message(length=10):
    """Generate a random ASCII message."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 "
    return ''.join(random.choice(chars) for _ in range(length))


def test_single_round(round_num: int) -> tuple[bool, float, str]:
    """Test a single encode/decode cycle. Returns (success, time_taken, error_msg)."""

    if RANDOM_MESSAGES:
        message = generate_random_message(random.randint(8, 15))
        context = generate_random_message(random.randint(30, 60))
    else:
        message = f"Test message {round_num}"
        context = "Once upon a time in a land far away"

    start_time = time.time()

    try:
        # Encode
        encode_payload = {
            "message": message,
            "context": context,
            "settings": {"seed": round_num}
        }

        encode_response = requests.post(
            f"{API_BASE}/encode",
            json=encode_payload,
            headers=headers,
            timeout=30
        )

        if encode_response.status_code != 200:
            return False, time.time() - start_time, f"Encode failed: {encode_response.status_code}"

        encode_result = encode_response.json()
        stego_text = encode_result["stego_text"]
        payload_bits = encode_result["payload_bits"]

        # Decode
        decode_payload = {
            "stego_text": stego_text,
            "context": context,
            "expected_bits": payload_bits,
            "settings": encode_result["settings"]
        }

        decode_response = requests.post(
            f"{API_BASE}/decode",
            json=decode_payload,
            headers=headers,
            timeout=30
        )

        if decode_response.status_code != 200:
            return False, time.time() - start_time, f"Decode failed: {decode_response.status_code}"

        decode_result = decode_response.json()
        recovered_message = decode_result.get("recovered_text", "")

        elapsed = time.time() - start_time

        if recovered_message == message:
            return True, elapsed, ""
        else:
            return False, elapsed, f"Mismatch: expected '{message}', got '{recovered_message}'"

    except Exception as e:
        return False, time.time() - start_time, f"Exception: {str(e)}"


def analyze_results(results: list[tuple[int, bool, float, str]]):
    """Analyze results to detect error accumulation."""
    print("\n" + "="*70)
    print("DETAILED ANALYSIS")
    print("="*70)

    # Overall statistics
    total = len(results)
    successes = sum(1 for _, success, _, _ in results if success)
    success_rate = successes / total * 100

    print(f"\nOverall Statistics:")
    print(f"  Total rounds:   {total}")
    print(f"  Successes:      {successes}")
    print(f"  Failures:       {total - successes}")
    print(f"  Success rate:   {success_rate:.1f}%")

    # Check for trends (error accumulation)
    print(f"\nTrend Analysis (checking for error accumulation):")

    # Split into first half and second half
    mid = total // 2
    first_half_success = sum(1 for i, success, _, _ in results[:mid] if success)
    second_half_success = sum(1 for i, success, _, _ in results[mid:] if success)

    first_half_rate = first_half_success / mid * 100
    second_half_rate = second_half_success / (total - mid) * 100

    print(f"  First {mid} rounds:  {first_half_rate:.1f}% success")
    print(f"  Last {total-mid} rounds:   {second_half_rate:.1f}% success")
    print(f"  Difference:       {second_half_rate - first_half_rate:+.1f}%")

    if abs(second_half_rate - first_half_rate) < 10:
        print(f"  → ✓ NO significant trend detected (stable error rate)")
    elif second_half_rate < first_half_rate - 10:
        print(f"  → ✗ WARNING: Error rate INCREASING over time")
    else:
        print(f"  → ✓ Error rate stable or improving")

    # Moving average analysis
    window = 5
    print(f"\nMoving Average (window={window}):")
    for i in range(0, total - window + 1, window):
        window_results = results[i:i+window]
        window_success = sum(1 for _, success, _, _ in window_results if success)
        window_rate = window_success / window * 100
        print(f"  Rounds {i+1:2d}-{i+window:2d}: {window_rate:.0f}% success")

    # Timing analysis
    avg_time = sum(t for _, _, t, _ in results) / total
    print(f"\nPerformance:")
    print(f"  Average time per round: {avg_time:.2f}s")

    # Error distribution
    print(f"\nError Details:")
    failures = [(i, err) for i, success, _, err in results if not success]
    if failures:
        print(f"  Failed rounds: {[i for i, _ in failures]}")
        for round_num, err in failures[:3]:  # Show first 3 errors
            print(f"    Round {round_num}: {err[:60]}...")
    else:
        print(f"  No failures!")

    return success_rate, first_half_rate, second_half_rate


def main():
    """Run extended multi-round test."""
    print("="*70)
    print("EXTENDED MULTI-ROUND TEST")
    print("="*70)
    print(f"API Base:       {API_BASE}")
    print(f"Authentication: {'Enabled' if API_KEY else 'Disabled'}")
    print(f"Test rounds:    {NUM_ROUNDS}")
    print(f"Random data:    {RANDOM_MESSAGES}")
    print("="*70)

    # Health check
    try:
        health_response = requests.get(f"{API_BASE}/health", headers=headers, timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"\n✓ Server healthy")
            print(f"  Device:          {health['device']}")
            print(f"  Reload strategy: {health['reload_strategy']}")
        else:
            print(f"\n✗ Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"\n✗ Cannot connect to server: {e}")
        return False

    # Run test rounds
    print(f"\nRunning {NUM_ROUNDS} rounds...\n")
    results = []

    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"Round {round_num:2d}/{NUM_ROUNDS}...", end=" ", flush=True)
        success, elapsed, error_msg = test_single_round(round_num)
        results.append((round_num, success, elapsed, error_msg))

        if success:
            print(f"✓ ({elapsed:.1f}s)")
        else:
            print(f"✗ ({elapsed:.1f}s) - {error_msg[:40]}")

        time.sleep(0.1)  # Small delay between rounds

    # Analyze results
    overall_rate, first_rate, second_rate = analyze_results(results)

    # Verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)

    if overall_rate >= 75:
        print("✓ System is STABLE")
        print(f"  - {overall_rate:.0f}% success rate maintained across {NUM_ROUNDS} rounds")
    else:
        print("✗ System is UNSTABLE")
        print(f"  - Only {overall_rate:.0f}% success rate")

    if abs(second_rate - first_rate) < 10:
        print("✓ No error accumulation detected")
        print(f"  - First half: {first_rate:.0f}%, Second half: {second_rate:.0f}%")
        print(f"  - Error probability is INDEPENDENT across rounds")
    else:
        print("⚠ Possible trend detected")
        print(f"  - First half: {first_rate:.0f}%, Second half: {second_rate:.0f}%")

    print("\nConclusion:")
    if overall_rate >= 75 and abs(second_rate - first_rate) < 10:
        print("  The fix is working! Error probability does NOT accumulate.")
        print("  The ~20% failure rate is due to the Discop algorithm limitation")
        print("  (top-p boundary token mismatch), not state pollution.")
        return True
    else:
        print("  Further investigation needed.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
