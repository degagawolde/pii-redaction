from dotenv import load_dotenv
load_dotenv()
import google.genai as genai
from google.genai import types

client = genai.Client()
from scripts.read_file import read_input_document
from scripts.validator import validate_output
from scripts.schema import PIIExtractionOutput
from scripts.prompts import get_prompt
from scripts.preprocess import clean_document_for_llm
client = genai.Client()

# 1. read input document
input_file_path = "evaluation_data/documents.xlsx"
raw_text_df = read_input_document(file_path=input_file_path)
clean_text = clean_document_for_llm(raw_document_text=raw_text_df["content"].iloc[0])
print(f"✅ text length:{len(clean_text)}")
contents = f"""Intput Text: {clean_text}"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=get_prompt(1),
        response_json_schema=PIIExtractionOutput.model_json_schema(),
    ),
)
print("\n✅ Raw API Response JSON")
print(response.text)

validate_output(response.text)
