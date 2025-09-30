"""Demo script that showcases Discop text steganography with a natural-language payload."""
import copy
import math
import torch

from config import text_default_settings
from model import get_model, get_tokenizer


def text_to_bits(text: str) -> str:
    """Convert ASCII text to a bit string."""
    return ''.join(f"{ord(ch):08b}" for ch in text)


def bits_to_text(bits: str) -> str:
    """Convert a bit string back to text, ignoring trailing incomplete bytes."""
    chars = []
    for idx in range(0, len(bits), 8):
        byte = bits[idx:idx + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)


def suggest_length(bit_len: int, target_rate: float = 3.6, safety_tokens: int = 8) -> int:
    base = math.ceil(bit_len / max(target_rate, 1e-6))
    return max(32, base + safety_tokens)


def main() -> None:
    message_plain = "Meet me at midnight behind the old library."
    context = (
        "The evening breeze drifted through the open window, carrying the scent of old books "
        "and whispered stories waiting to be told."
    )

    settings = copy.deepcopy(text_default_settings)
    settings.device = torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
    settings.top_p = 0.9
    settings.seed = 1234

    from stega_cy import encode_text, decode_text  # type: ignore

    message_bits = text_to_bits(message_plain)
    target_length = suggest_length(len(message_bits))
    settings.length = target_length

    model = get_model(settings)
    tokenizer = get_tokenizer(settings)

    single_example_output = encode_text(model, tokenizer, message_bits, context, settings)

    if single_example_output.n_bits < len(message_bits):
        settings.length = max(settings.length + 16, len(message_bits) // 2)
        single_example_output = encode_text(model, tokenizer, message_bits, context, settings)

    decoded_bits = decode_text(
        model,
        tokenizer,
        single_example_output.generated_ids,
        context,
        settings
    )

    decoded_bits_trimmed = decoded_bits[:len(message_bits)]
    recovered_message = bits_to_text(decoded_bits_trimmed)

    print("=== Steganographic Text ===")
    print(single_example_output.stego_object)
    print()
    print(f"Embedded bits       : {single_example_output.n_bits} (~{single_example_output.n_bits / 8:.2f} bytes)")
    print(f"Embedding rate      : {single_example_output.embedding_rate:.2f} bits/token")
    print(f"Utilization rate    : {single_example_output.utilization_rate:.3f}")
    print(f"Perplexity          : {single_example_output.perplexity:.2f}\n")

    print("Recovered matches original payload:", decoded_bits_trimmed == message_bits)
    print("Recovered message   :", recovered_message)
    if single_example_output.n_bits > len(message_bits):
        remaining = single_example_output.n_bits - len(message_bits)
        print(f"Remaining capacity  : {remaining} bits (auto-padded with zeros)")


if __name__ == "__main__":
    main()

