from urllib import response
from scripts.schema import PIIExtractionOutput

def validate_output(response_text):
    try:
        # Use model_validate_json to validate the JSON string and instantiate the Pydantic model
        pii_data_model = PIIExtractionOutput.model_validate_json(response_text)

        print("\n✅ Pydantic Validation Successful!")
        print("\n--- Structured PII Data (Python Object) ---")

        # Use model_dump_json for a clean, indented printout of the validated data
        validated_data = pii_data_model.model_dump_json(indent=2)
        print(validated_data)

        return validated_data

    except Exception as e:
        print(f"\n❌ Pydantic Validation Failed! Error: {e}")
        print("\nAttempting to print raw JSON for debugging...")
        # This helps debug if the LLM output violates the schema
        print(response.text)
        
        return None
