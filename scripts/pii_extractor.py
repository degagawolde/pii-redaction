# pii_extractor.py
import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_CONFIG

class PIIExtractor:
    def __init__(self):
        # Client automatically uses the key from the environment/config
        self.client = genai.Client()

    def extract_pii(self, document_text: str) -> list[dict]:
        """Calls the Gemini API to extract PII entities in JSON format."""

        # Craft the user contents based on the prompt engineering
        contents = f"The text to analyze is: {document_text}"

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=GEMINI_CONFIG,
        )

        # The response.text is guaranteed to be a JSON string
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            print("Warning: LLM returned invalid JSON.")
            return []

    def redact_document(self, document_text: str, entities: list[dict]) -> str:
        """Applies masking to the text based on the extracted entities."""
        # Simple back-to-front replacement logic to avoid index shift issues
        redacted_text = list(document_text)

        # Sort by end index descending to avoid issues when replacing spans
        sorted_entities = sorted(entities, key=lambda x: x["end"], reverse=True)

        for entity in sorted_entities:
            start, end = entity["start"], entity["end"]
            entity_type = entity["type"]

            # Mask format: [TYPE]
            mask = f"[{entity_type}]"

            # Replace the characters in the list
            redacted_text[start:end] = list(mask)

        return "".join(redacted_text)
