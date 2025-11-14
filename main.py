from dotenv import load_dotenv
import json
import os
from datetime import datetime

load_dotenv()
import google.genai as genai
from google.genai import types

client = genai.Client()
from scripts.evaluation import calculate_pii_metrics, print_metrics_report
from scripts.read_file import read_input_document
from scripts.validator import validate_output
from scripts.schema import PIIExtractionOutput
from scripts.prompts import get_prompt
from scripts.preprocess import clean_document_for_llm

# 1. read input document
input_file_path = "evaluation_data/documents.xlsx"
raw_text_df = read_input_document(file_path=input_file_path)

# Define which prompts to test (modify this list as needed)
prompt_ids = [0, 1, 2, 3, 4]  # Example prompt IDs - adjust based on your available prompts

# Create directory for results if it doesn't exist
results_dir = "evaluation_results"
os.makedirs(results_dir, exist_ok=True)

all_results = {}

for prompt_id in prompt_ids:
    print(f"\n{'='*60}")
    print(f"🔄 Processing with Prompt ID: {prompt_id}")
    print(f"{'='*60}")

    predictions = {}
    prompt_content = get_prompt(prompt_id)

    for i in range(raw_text_df.shape[0]):
        clean_text = clean_document_for_llm(
            raw_document_text=raw_text_df["content"].iloc[i]
        )
        print(
            f"✅ Prompt {prompt_id} - Document {i+1}/{raw_text_df.shape[0]} - text length: {len(clean_text)}"
        )

        contents = f"""Input Text: {clean_text}"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=prompt_content,
                    response_json_schema=PIIExtractionOutput.model_json_schema(),
                ),
            )

            print(f"✅ Prompt {prompt_id} - Raw API Response for document {i+1}")

            validated_data = validate_output(response.text)
            document_name = raw_text_df["name"].iloc[i]
            predictions[document_name] = validated_data

        except Exception as e:
            print(f"❌ Error processing document {i+1} with prompt {prompt_id}: {e}")
            document_name = raw_text_df["name"].iloc[i]
            predictions[document_name] = {"error": str(e)}

    # Save predictions for this prompt
    prompt_output_file = f"{results_dir}/predictions_prompt_{prompt_id}.json"
    try:
        with open(prompt_output_file, "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=4, ensure_ascii=False)
        print(
            f"✅ Successfully saved predictions for prompt {prompt_id} to: {prompt_output_file}"
        )
    except Exception as e:
        print(f"❌ Error saving predictions for prompt {prompt_id}: {e}")

    # Calculate metrics for this prompt
    ground_truth_file = "evaluation_data/parsed_data.json"
    try:
        with open(ground_truth_file, "r") as file:
            ground_truth = json.load(file)

        metrics = calculate_pii_metrics(
            predictions=predictions, ground_truth=ground_truth
        )

        # Save metrics for this prompt
        metrics_file = f"{results_dir}/metrics_prompt_{prompt_id}.json"
        metrics_data = {
            "prompt_id": prompt_id,
            "prompt_content": prompt_content,
            "metrics": metrics,
            "total_documents": len(predictions),
            "evaluation_timestamp": datetime.now().isoformat(),
        }

        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=4, ensure_ascii=False)
        print(
            f"✅ Successfully saved metrics for prompt {prompt_id} to: {metrics_file}"
        )

        # Print report for this prompt
        print(f"\n📊 METRICS REPORT - Prompt {prompt_id}")
        print(f"{'-'*40}")
        print_metrics_report(metrics)

        # Store in all results
        all_results[prompt_id] = {
            "predictions": predictions,
            "metrics": metrics,
            "prompt_content": prompt_content,
        }

    except Exception as e:
        print(f"❌ Error calculating metrics for prompt {prompt_id}: {e}")

# Save comprehensive comparison
comparison_file = f"{results_dir}/all_prompts_comparison.json"
try:
    comparison_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_prompts_tested": len(prompt_ids),
            "model_used": "gemini-2.5-flash",
            "total_documents": raw_text_df.shape[0],
        },
        "prompts_comparison": {},
    }

    for prompt_id in all_results:
        comparison_data["prompts_comparison"][prompt_id] = {
            "prompt_preview": (
                all_results[prompt_id]["prompt_content"][:100] + "..."
                if len(all_results[prompt_id]["prompt_content"]) > 100
                else all_results[prompt_id]["prompt_content"]
            ),
            "metrics": all_results[prompt_id]["metrics"],
            "total_documents_processed": len(all_results[prompt_id]["predictions"]),
        }

    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Successfully saved comprehensive comparison to: {comparison_file}")

except Exception as e:
    print(f"❌ Error saving comparison file: {e}")

# Print final summary
print(f"\n{'='*60}")
print(f"🎯 EVALUATION COMPLETED")
print(f"{'='*60}")
print(f"Total prompts tested: {len(prompt_ids)}")
print(f"Results saved in: {results_dir}/")
print(f"Files generated:")
for prompt_id in prompt_ids:
    print(f"  - predictions_prompt_{prompt_id}.json")
    print(f"  - metrics_prompt_{prompt_id}.json")
print(f"  - all_prompts_comparison.json")
print(f"{'='*60}")
