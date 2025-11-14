from dotenv import load_dotenv
load_dotenv()
import google.genai as genai
from google.genai import types
from read_file import read_input_document
client = genai.Client()

from scripts.schema import Recipe
from scripts.prompts import prompt
from scripts.preprocess import clean_document_for_llm
client = genai.Client()

# 1. read input document
input_file_path = "evaluation_data/documents.xlsx"
raw_text_df = read_input_document(file_path=input_file_path)
clean_text = clean_document_for_llm(raw_document_text=raw_text_df["content"].iloc[0])
print(f"✅ text length:{len(clean_text)}")
contents = f"""Intput Text: {clean_text}"""

# Optimized System Instruction: Sets the role, constraints, and output format.
optimized_system_instruction = """
You are an expert PII identification tool for legal documents. Your task is to analyze the 
provided text and extract all instances of Personally Identifiable Information (PII). 

PII Categories to identify:
1. Name (including partial names, nicknames)
2. Company_Name
3. Date_of_Birth
4. Address (street, city, postal codes)
5. Email_Address
6. Phone_Number

1. Name
2. Company_Name
3. Address
4. PPS_Number
5. License_Number
6. Phone_Number
7. Email_Address
8. Passport_Number
9. Bank_Information
10. Reference_Number
11. ID_Number
12. Date_of_Birth

Do not generate any conversational text, explanations, or analysis. For each entity, 
return the exact text, the assigned type, the character start index, and the character 
end index (exclusive). Do not miss partial matches or embedded entities.
Output must be a single JSON object. The keys must be the PII categories, 
and the value must be a list of all detected instances. 
If a category is not found, its list should be empty.
"""
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=optimized_system_instruction,
        # response_json_schema= Recipe.model_json_schema()
    ),
)
print(response.text)

# recipe = Recipe.model_validate_json(response.text)
# print(recipe)
