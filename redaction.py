import argparse
import json
import os
import re
from scripts.preprocess import clean_document_for_llm
from scripts.read_file import read_input_document


def redaction(
    prompt_path, document_name, input_file_path, output_dir="results"
):
    """
    Select the prompt for a given document, clean it,
    generate a redacted version, and save it to results/.
    """

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Read input documents
    documents_df = read_input_document(file_path=input_file_path)

    # 2. Find the correct document
    doc_row = documents_df[documents_df["name"] == document_name]
    if doc_row.empty:
        raise ValueError(f"Document '{document_name}' not found.")

    document_text = doc_row["content"].iloc[0]

    # 3. Clean text
    clean_text = clean_document_for_llm(document_text)

    # 4. Load prompt JSON
    with open(prompt_path, "r") as f:
        prompt_data = json.load(f)

    if document_name not in prompt_data:
        raise ValueError(
            f"No prompt found for document '{document_name}' in prompt JSON."
        )

    prompt_config = prompt_data[document_name]

    # 5. Perform redaction
    redacted_text = clean_text

    for category, values in prompt_config.items():
        if not isinstance(values, list):
            continue

        mask = f"<{category}_REDACTED>"

        for value in values:
            if not value:
                continue

            escaped_value = re.escape(value)

            redacted_text = re.sub(
                escaped_value,
                mask,
                redacted_text,
                flags=re.IGNORECASE,
            )

    # 6. Save redacted document
    output_path = os.path.join(output_dir, f"{document_name}_redacted.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(redacted_text)

    print(f"✔ Redacted file saved at: {output_path}")

    return redacted_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run PII redaction on a selected document."
    )

    parser.add_argument("--prompt", required=True, help="Path to prompt JSON file.")

    parser.add_argument(
        "--document",
        required=True,
        help="Document name, e.g., Test_A, Test_C, Test_D, Test_F.",
    )

    parser.add_argument(
        "--input", required=True, help="Path to input document dataset."
    )

    parser.add_argument(
        "--output",
        default="results",
        help="Directory to save the redacted file (default: results).",
    )

    args = parser.parse_args()

    redaction(
        prompt_path=args.prompt,
        document_name=args.document,
        input_file_path=args.input,
        output_dir=args.output,
    )
