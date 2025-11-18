"""PII Extraction Evaluation Script

This script evaluates multiple prompts for PII extraction using Gemini API
and calculates performance metrics for comparison.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

from scripts.evaluation import calculate_pii_metrics, print_metrics_report
from scripts.read_file import read_input_document
from scripts.validator import validate_output
from scripts.schema import PIIExtractionOutput
from scripts.prompts import get_prompt
from scripts.preprocess import clean_document_for_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PIIEvaluationRunner:
    """Main class to run PII extraction evaluation across multiple prompts."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """Initialize the evaluation runner.

        Args:
            model_name: Name of the Gemini model to use
        """
        load_dotenv()
        self.client = genai.Client()
        self.model_name = model_name
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

    def detect_pii(
        self,
        document_text: str,
        document_name: str,
        prompt_content: str,
        prompt_id: int,
    ) -> Dict[str, Any]:
        """Process a single document with the given prompt.

        Args:
            document_text: Raw document text to process
            document_name: Identifier for the document
            prompt_content: System prompt content
            prompt_id: ID of the prompt being tested

        Returns:
            Dictionary containing processed results or error information
        """
        try:
            clean_text = clean_document_for_llm(document_text)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Input Text: {clean_text}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=prompt_content,
                    response_json_schema=PIIExtractionOutput.model_json_schema(),
                ),
            )

            validated_data = validate_output(response.text)
            return validated_data

        except Exception as e:
            logger.error(
                f"❌ Error processing document '{document_name}' with prompt {prompt_id}: {e}"
            )
            return {"error": str(e), "status": "error"}

    def run_prompt_evaluation(
        self, prompt_id: int, documents_df, ground_truth: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Run evaluation for a single prompt across all documents.

        Args:
            prompt_id: ID of the prompt to evaluate
            documents_df: DataFrame containing documents
            ground_truth: Ground truth data for evaluation

        Returns:
            Dictionary containing evaluation results or None if failed
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing with Prompt ID: {prompt_id}")
        logger.info(f"{'='*60}")

        predictions = {}
        prompt_content = get_prompt(prompt_id)

        # Process all documents
        for i in range(documents_df.shape[0]):
            document_name = documents_df["name"].iloc[i]
            document_text = documents_df["content"].iloc[i]

            logger.info(
                f"✅ Prompt {prompt_id} - Document {i+1}/{documents_df.shape[0]} - {document_name}"
            )

            result = self.detect_pii(
                document_text=document_text,
                document_name=document_name,
                prompt_content=prompt_content,
                prompt_id=prompt_id,
            )

            predictions[document_name] = result

        # Save predictions
        if not self._save_predictions(predictions, prompt_id):
            return None

        # Calculate and save metrics
        return self._calculate_and_save_metrics(
            predictions, ground_truth, prompt_id, prompt_content
        )


    def _save_predictions(self, predictions: Dict[str, Any], prompt_id: int) -> bool:
        """
        Save predictions to JSON file with clean formatting.
        Automatically converts JSON strings into real dictionaries.
        """

        # Fix: convert stringified JSON to proper dicts
        cleaned = {}

        for key, value in predictions.items():
            if isinstance(value, str):
                # Value *is* raw JSON in string form
                try:
                    cleaned[key] = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(
                        f"⚠️ Failed to decode JSON for key: {key}. Keeping original string."
                    )
                    cleaned[key] = value
            else:
                cleaned[key] = value

        output_file = self.results_dir / f"predictions_prompt_{prompt_id}.json"

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=4, ensure_ascii=False)
            logger.info(f"✅ Successfully saved predictions for prompt {prompt_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving predictions for prompt {prompt_id}: {e}")
            return False

    def _calculate_and_save_metrics(
        self,
        predictions: Dict[str, Any],
        ground_truth: Dict[str, Any],
        prompt_id: int,
        prompt_content: str,
    ) -> Optional[Dict[str, Any]]:
        """Calculate metrics and save results.

        Args:
            predictions: Model predictions
            ground_truth: Ground truth data
            prompt_id: ID of the prompt
            prompt_content: Content of the prompt

        Returns:
            Dictionary containing metrics and results
        """
        try:
            # Clean and filter predictions: parse JSON strings and filter out errors
            successful_predictions = {}
            
            for doc_name, result in predictions.items():
                # Skip error cases
                if result is None or (isinstance(result, dict) and result.get("status") == "error"):
                    logger.warning(f"⚠️ Skipping document '{doc_name}' due to error status")
                    continue
                
                # Parse JSON strings to dictionaries
                if isinstance(result, str):
                    try:
                        parsed_result = json.loads(result)
                        successful_predictions[doc_name] = parsed_result
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Failed to parse JSON for document '{doc_name}'. Skipping.")
                        continue
                elif isinstance(result, dict):
                    successful_predictions[doc_name] = result
                else:
                    logger.warning(f"⚠️ Unexpected result type for document '{doc_name}': {type(result)}. Skipping.")
                    continue

            if not successful_predictions:
                logger.error(f"❌ No valid predictions found for prompt {prompt_id}")
                return None

            metrics = calculate_pii_metrics(
                predictions=successful_predictions, ground_truth=ground_truth
            )

            # Prepare metrics data
            metrics_data = {
                "prompt_id": prompt_id,
                "prompt_content": prompt_content,
                "metrics": metrics,
                "total_documents": len(predictions),
                "successful_documents": len(successful_predictions),
                "failed_documents": len(predictions) - len(successful_predictions),
                "evaluation_timestamp": datetime.now().isoformat(),
            }

            # Save metrics
            metrics_file = self.results_dir / f"metrics_prompt_{prompt_id}.json"
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=4, ensure_ascii=False)

            logger.info(f"✅ Successfully saved metrics for prompt {prompt_id}")

            # Print report
            logger.info(f"\n📊 METRICS REPORT - Prompt {prompt_id}")
            logger.info(f"{'-'*40}")
            print_metrics_report(metrics)

            return {
                "predictions": predictions,
                "metrics": metrics,
                "prompt_content": prompt_content,
                "metrics_data": metrics_data,
            }

        except Exception as e:
            logger.error(f"❌ Error calculating metrics for prompt {prompt_id}: {e}")
            return None

    def save_comprehensive_comparison(
        self,
        all_results: Dict[int, Dict[str, Any]],
        prompt_ids: List[int],
        documents_df,
    ) -> bool:
        """Save comprehensive comparison of all prompts.

        Args:
            all_results: Dictionary containing results for all prompts
            prompt_ids: List of prompt IDs that were tested
            documents_df: DataFrame containing processed documents

        Returns:
            True if successful, False otherwise
        """
        comparison_file = self.results_dir / "all_prompts_comparison.json"

        try:
            comparison_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_prompts_tested": len(prompt_ids),
                    "model_used": self.model_name,
                    "total_documents": documents_df.shape[0],
                },
                "prompts_comparison": {},
            }

            for prompt_id, results in all_results.items():
                comparison_data["prompts_comparison"][prompt_id] = {
                    "prompt_preview": (
                        results["prompt_content"][:100] + "..."
                        if len(results["prompt_content"]) > 100
                        else results["prompt_content"]
                    ),
                    "metrics": results["metrics"],
                    "total_documents_processed": len(results["predictions"]),
                }

            with open(comparison_file, "w", encoding="utf-8") as f:
                json.dump(comparison_data, f, indent=4, ensure_ascii=False)

            logger.info(f"✅ Successfully saved comprehensive comparison")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving comparison file: {e}")
            return False

    def print_final_summary(
        self, prompt_ids: List[int], all_results: Dict[int, Dict[str, Any]]
    ):
        """Print final summary of the evaluation.

        Args:
            prompt_ids: List of prompt IDs that were tested
            all_results: Dictionary containing results for all prompts
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 EVALUATION COMPLETED")
        logger.info(f"{'='*60}")
        logger.info(f"Total prompts tested: {len(prompt_ids)}")
        logger.info(f"Successful evaluations: {len(all_results)}")
        logger.info(f"Results saved in: {self.results_dir}/")
        logger.info(f"Files generated:")
        for prompt_id in prompt_ids:
            logger.info(f"  - predictions_prompt_{prompt_id}.json")
            logger.info(f"  - metrics_prompt_{prompt_id}.json")
        logger.info(f"  - all_prompts_comparison.json")
        logger.info(f"{'='*60}")


def load_ground_truth(ground_truth_path: str) -> Dict[str, Any]:
    """Load ground truth data from JSON file.

    Args:
        ground_truth_path: Path to ground truth JSON file

    Returns:
        Dictionary containing ground truth data

    Raises:
        FileNotFoundError: If ground truth file doesn't exist
        JSONDecodeError: If ground truth file is not valid JSON
    """
    ground_truth_path = Path(ground_truth_path)
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")

    with open(ground_truth_path, "r") as file:
        return json.load(file)


def main():
    """Main execution function."""
    # Configuration
    INPUT_FILE_PATH = "data/documents.xlsx"
    GROUND_TRUTH_FILE = "data/parsed_data.json"
    PROMPT_IDS = [6]  # Adjust based on available prompts

    try:
        # Initialize evaluation runner
        evaluator = PIIEvaluationRunner()

        # Load data
        logger.info("📂 Loading input documents...")
        raw_text_df = read_input_document(file_path=INPUT_FILE_PATH)

        logger.info("📂 Loading ground truth data...")
        ground_truth = load_ground_truth(GROUND_TRUTH_FILE)

        # Run evaluation for each prompt
        all_results = {}

        for prompt_id in PROMPT_IDS:
            results = evaluator.run_prompt_evaluation(
                prompt_id=prompt_id, documents_df=raw_text_df, ground_truth=ground_truth
            )

            if results:
                all_results[prompt_id] = results

        # Save comprehensive comparison
        if all_results:
            evaluator.save_comprehensive_comparison(
                all_results=all_results, prompt_ids=PROMPT_IDS, documents_df=raw_text_df
            )

        # Print final summary
        evaluator.print_final_summary(prompt_ids=PROMPT_IDS, all_results=all_results)

    except Exception as e:
        logger.critical(f"💥 Critical error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
