import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from scripts.preprocess import clean_document_for_llm
from scripts.read_file import read_input_document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_prompt_data(prompt_path: str) -> Dict:
    """
    Load and validate prompt JSON file.

    Args:
        prompt_path: Path to the prompt JSON file.

    Returns:
        Dictionary containing prompt data.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    prompt_path_obj = Path(prompt_path)
    if not prompt_path_obj.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_data = json.load(f)
        logger.info(f"Successfully loaded prompt data from {prompt_path}")
        return prompt_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in prompt file: {e}")


def validate_inputs(
    document_name: str,
    documents_df: pd.DataFrame,
    prompt_data: Dict,
) -> None:
    """
    Validate that all required inputs are present and correct.

    Args:
        document_name: Name of the document to process.
        documents_df: DataFrame containing documents.
        prompt_data: Dictionary containing prompt/redaction data.

    Raises:
        ValueError: If validation fails.
    """
    if documents_df is None or documents_df.empty:
        raise ValueError("Input document dataset is empty or could not be loaded.")

    doc_row = documents_df[documents_df["name"] == document_name]
    if doc_row.empty:
        available_docs = ", ".join(documents_df["name"].unique().tolist())
        raise ValueError(
            f"Document '{document_name}' not found. "
            f"Available documents: {available_docs}"
        )

    if document_name not in prompt_data:
        available_docs = ", ".join(prompt_data.keys())
        raise ValueError(
            f"No redaction data found for document '{document_name}' in prompt JSON. "
            f"Available documents: {available_docs}"
        )


def prepare_redaction_patterns(
    prompt_config: Dict[str, List[str]],
) -> List[Tuple[str, str, int]]:
    """
    Prepare redaction patterns sorted by length (longest first) to handle
    overlapping matches correctly.

    Args:
        prompt_config: Dictionary mapping PII categories to lists of values.

    Returns:
        List of tuples (pattern, mask, length) sorted by length descending.
    """
    patterns = []

    for category, values in prompt_config.items():
        if not isinstance(values, list):
            logger.warning(
                f"Skipping category '{category}': expected list, got {type(values)}"
            )
            continue

        mask = f"<{category}_REDACTED>"

        for value in values:
            if not value or not isinstance(value, str):
                continue

            # Escape special regex characters
            escaped_value = re.escape(value)
            patterns.append((escaped_value, mask, len(value)))

    # Sort by length descending to handle overlapping matches
    # (e.g., "John Smith" should be redacted before "John")
    patterns.sort(key=lambda x: x[2], reverse=True)

    logger.info(f"Prepared {len(patterns)} redaction patterns")
    return patterns


def perform_redaction(
    text: str, patterns: List[Tuple[str, str, int]], case_sensitive: bool = False
) -> Tuple[str, Dict[str, int]]:
    """
    Perform redaction on text using prepared patterns.

    Args:
        text: Text to redact.
        patterns: List of (pattern, mask, length) tuples.
        case_sensitive: Whether to perform case-sensitive matching.

    Returns:
        Tuple of (redacted_text, statistics_dict).
    """
    redacted_text = text
    stats = defaultdict(int)

    flags = 0 if case_sensitive else re.IGNORECASE

    for pattern, mask, _ in patterns:
        matches = list(re.finditer(pattern, redacted_text, flags=flags))
        if matches:
            # Replace from end to start to preserve indices
            for match in reversed(matches):
                redacted_text = (
                    redacted_text[: match.start()] + mask + redacted_text[match.end() :]
                )
                stats[mask] += 1

    logger.info(f"Redaction complete. Statistics: {dict(stats)}")
    return redacted_text, dict(stats)


def redaction(
    prompt_path: str,
    document_name: str,
    input_file_path: str,
    output_dir: str = "results",
    case_sensitive: bool = False,
    save_stats: bool = True,
) -> Tuple[str, Dict[str, int]]:
    """
    Select the prompt for a given document, clean it,
    generate a redacted version, and save it to results/.

    Args:
        prompt_path: Path to prompt JSON file containing PII values to redact.
        document_name: Name of the document to process (e.g., "Test_A", "Test_C").
        input_file_path: Path to input document dataset (Excel file).
        output_dir: Directory to save the redacted file (default: "results").
        case_sensitive: Whether to perform case-sensitive redaction (default: False).
        save_stats: Whether to save redaction statistics to a JSON file (default: True).

    Returns:
        Tuple of (redacted_text, statistics_dict).

    Raises:
        FileNotFoundError: If input files are not found.
        ValueError: If document or prompt data is invalid.
    """
    # Ensure output directory exists
    output_path_obj = Path(output_dir)
    output_path_obj.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path_obj.absolute()}")

    # 1. Read input documents
    logger.info(f"Reading input document from {input_file_path}")
    documents_df = read_input_document(file_path=input_file_path)

    # 2. Load prompt JSON
    prompt_data = load_prompt_data(prompt_path)

    # 3. Validate inputs
    validate_inputs(document_name, documents_df, prompt_data)

    # 4. Extract document text
    doc_row = documents_df[documents_df["name"] == document_name]
    document_text = doc_row["content"].iloc[0]

    if not document_text or not isinstance(document_text, str):
        raise ValueError(f"Document '{document_name}' has invalid or empty content.")

    logger.info(f"Processing document: {document_name} ({len(document_text)} characters)")

    # 5. Clean text
    clean_text = clean_document_for_llm(document_text)
    logger.info(f"Cleaned text length: {len(clean_text)} characters")

    # 6. Get prompt configuration
    prompt_config = prompt_data[document_name]

    # 7. Prepare redaction patterns
    patterns = prepare_redaction_patterns(prompt_config)

    if not patterns:
        logger.warning("No redaction patterns found. Returning original text.")
        redacted_text = clean_text
        stats = {}
    else:
        # 8. Perform redaction
        redacted_text, stats = perform_redaction(clean_text, patterns, case_sensitive)

    # 9. Save redacted document
    output_file = output_path_obj / f"{document_name}_redacted.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(redacted_text)

    logger.info(f"✓ Redacted file saved at: {output_file.absolute()}")

    # 10. Save statistics if requested
    if save_stats and stats:
        stats_file = output_path_obj / f"{document_name}_redaction_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "document_name": document_name,
                    "statistics": stats,
                    "total_redactions": sum(stats.values()),
                },
                f,
                indent=2,
            )
        logger.info(f"✓ Statistics saved at: {stats_file.absolute()}")

    return redacted_text, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run PII redaction on a selected document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python redaction.py --prompt data/parsed_data.json --document Test_A --input data/documents.xlsx
  python redaction.py --prompt data/parsed_data.json --document Test_C --input data/documents.xlsx --output results --case-sensitive
        """,
    )

    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to prompt JSON file containing PII values to redact.",
    )

    parser.add_argument(
        "--document",
        required=True,
        help="Document name, e.g., Test_A, Test_C, Test_D, Test_F.",
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input document dataset (Excel file).",
    )

    parser.add_argument(
        "--output",
        default="results",
        help="Directory to save the redacted file (default: results).",
    )

    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Perform case-sensitive redaction (default: case-insensitive).",
    )

    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Skip saving redaction statistics to JSON file.",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level (default: INFO).",
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        redacted_text, stats = redaction(
            prompt_path=args.prompt,
            document_name=args.document,
            input_file_path=args.input,
            output_dir=args.output,
            case_sensitive=args.case_sensitive,
            save_stats=not args.no_stats,
        )

        # Print summary
        total_redactions = sum(stats.values()) if stats else 0
        logger.info(
            f"\n{'='*60}\n"
            f"Redaction Summary:\n"
            f"  Document: {args.document}\n"
            f"  Total redactions: {total_redactions}\n"
            f"  Categories: {len(stats)}\n"
            f"{'='*60}"
        )

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        exit(1)
