# PII Redaction for Legal Documents

[Documentation read more...](PII_Redaction.pdf)

## **Overview**

This project builds an automated PII redaction system for legal documents using LLMs, with a core focus on how prompt engineering directly impacts extraction accuracy. Traditional NER models often miss context-dependent PII, but LLMs can perform significantly better when guided by strict, well-structured prompts. The goal is to evaluate the effect of different prompt designs on precision, recall, and reliability, particularly using the Gemini free-tier model, where strong prompt constraints are crucial due to model limitations.

## **Project Structure**

### **1. `scripts/` Directory**

* **`evaluation.py`** – Evaluates the performance of each prompt version.
* **`preprocess.py`** – Utility functions for text cleaning and preprocessing.
* **`prompts.py`** – Contains all versions of the PII extraction and redaction prompts.
* **`read_file.py`** – Parses input documents and label files into the correct internal format.
* **`schema.py`** – Defines the schema used to validate and guide model outputs.
* **`validator.py`** – Validates the model output against the defined schema.

---

### **2. `main.py`**

Runs the entire pipeline end-to-end, including preprocessing, inference, and evaluation.

### 3.`redaction.py`

Select a prompt and an input document, then run this script to generate a redacted version of the document.

### **4. `results/`**

* Stores all evaluation outputs.
* Saves extracted PII results in JSON format.
* Store redacted documents for each prompt

### **5. `data/`**

Contains the input documents and their corresponding target (ground-truth) PII annotations.

## **How to Run**

```
#1 create python environment 
python3 -m venv penv 
source penv/bin/activate
#2 install all required packages
pip install -r requirements.txt
#3 run the pipeline
python main.py
#4 redact a given document with a selected prompt
python redaction.py --prompt prompts.json --document Test_C --input data.json --output results
```

```
# make sure you have GEMINI_API_KEY in your .env file
GEMINI_API_KEY=<AIzaSyCktOc........>
```

## Data Description

The project utilized four specific test legal documents:  **Test_A** ,  **Test_C** ,  **Test_D** , and  **Test_F** . These documents were sourced from an Excel file, loaded, and subjected to a preprocessing stage for initial data cleaning. Crucially, each document was accompanied by a  **target label** —a curated list of all true PII instances within that document. This ground truth was essential for accurately comparing and measuring the performance of the various prompt engineering strategies.

## **Prompt Engineering Approach**

The project follows an iterative prompt-engineering workflow, continuously enhancing structure, specificity, and constraints to improve model behavior.

* More constraints: Tight instructions greatly reduce false positives and random outputs.
* Structured formats enable objective evaluation: JSON schemas prevent formatting drift and improve metric computation.
* Examples reduce confusion: Helps models correctly detect rare legal PII (ID types, contract numbers).
* Role-based instructions increase compliance: “Extraction engine” framing minimizes conversational behavior.

## **Model**

The project uses the **Gemini free-tier model** as the inference engine. Despite being a cost-efficient model, it proves capable of performing entity recognition and redaction with reasonable accuracy when properly guided by well-designed prompts. Prompt engineering plays a key role in compensating for model limitations inherent in free-tier or lightweight LLM variants.

## **Evaluation Methodology**

Model outputs were compared against ground-truth PII labels using standard information-retrieval metrics:

* **Precision** – proportion of correctly detected PII among all detected items
* **Recall** – proportion of ground-truth PII successfully identified
* **F1 Score** – harmonic mean of precision and recall, representing overall detection quality

## conclusion

Prompt engineering, not the model alone, determines PII extraction accuracy. Structured constraints, definitions, and strict schemas turned an unreliable baseline into a high-precision redaction system, even using a free-tier LLM.

## Future Work

* Few-shot prompt variants
* Self-consistency prompting with a hidden chain-of-thought
* Prompt ensembles for robustness
