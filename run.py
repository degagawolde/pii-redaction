# main.py
import json
import os
from scripts.pii_extractor import PIIExtractor
from scripts.evaluation import PIIEvaluator

# --- Configuration (Update these paths) ---
DOCUMENTS_DIR = "data/documents"
GOLD_LABELS_FILE = "data/gold_labels.json"
OUTPUT_DIR = "output"

def run_assignment():
    """Main execution function."""
    
    extractor = PIIExtractor()
    evaluator = PIIEvaluator(GOLD_LABELS_FILE)
    
    # Initialize totals for aggregation across all documents
    TP_total, FP_total, FN_total = 0, 0, 0
    
    for doc_file in os.listdir(DOCUMENTS_DIR):
        if not doc_file.endswith(".txt"):
            continue

        doc_path = os.path.join(DOCUMENTS_DIR, doc_file)
        doc_id = doc_file.replace(".txt", "")

        with open(doc_path, 'r', encoding='utf-8') as f:
            document_text = f.read()

        # 1. Extraction
        predicted_entities = extractor.extract_pii(document_text)

        # 2. Redaction
        redacted_text = extractor.redact_document(document_text, predicted_entities)

        # 3. Evaluation
        TP, FP, FN = evaluator.compare_and_score(doc_id, predicted_entities)
        
        TP_total += TP
        FP_total += FP
        FN_total += FN
        
        # Save redacted output
        output_path = os.path.join(OUTPUT_DIR, f"{doc_id}_redacted.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
            
        print(f"Processed {doc_id}. TP/FP/FN: {TP}/{FP}/{FN}")

    # 4. Final Metrics
    final_metrics = evaluator.calculate_metrics(TP_total, FP_total, FN_total)
    
    print("\n--- FINAL EVALUATION METRICS ---")
    for key, value in final_metrics.items():
        print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")
        
    # Save metrics to a file
    with open(os.path.join(OUTPUT_DIR, "metrics.json"), 'w') as f:
        json.dump(final_metrics, f, indent=4)

if __name__ == "__main__":
    run_assignment()