from google import genai

from scripts.schema import Recipe
from scripts.prompts import prompt

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": Recipe.model_json_schema(),
    },
)
recipe = Recipe.model_validate_json(response.text)
print(recipe)