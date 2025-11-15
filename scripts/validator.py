from urllib import response
from scripts.schema import PIIExtractionOutput
import logging

# Configure logger
logger = logging.getLogger(__name__)

def validate_output(response_text):
    try:
        # Use model_validate_json to validate the JSON string and instantiate the Pydantic model
        pii_data_model = PIIExtractionOutput.model_validate_json(response_text)

        logger.info("\n✅ Pydantic Validation Successful!")
        logger.info("\n--- Structured PII Data (Python Object) ---")

        # Use model_dump_json for a clean, indented printout of the validated data
        validated_data = pii_data_model.model_dump_json(indent=2)
        logger.info(validated_data)

        return validated_data

    except Exception as e:
        logger.error(f"\n❌ Pydantic Validation Failed! Error: {e}")
        logger.debug("\nAttempting to print raw JSON for debugging...")
        # This helps debug if the LLM output violates the schema
        logger.debug(response_text)
        
        return None
