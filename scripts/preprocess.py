import re

def clean_document_for_llm(raw_document_text: str) -> str:
    """
    Cleans a structured document string by removing metadata tags,
    formatting, and normalizing whitespace, preparing it for LLM input.
    """
    
    # 1. Remove Document Start/End Tags and Extra Whitespace
    # Pattern: <START OF DOCUMENT:...> | <END OF DOCUMENT>
    cleaned_text = re.sub(r'<START OF DOCUMENT:.*?>\n?|\n?<END OF DOCUMENT>', '', raw_document_text, flags=re.DOTALL)
    
    # 2. Remove Paragraph IDs (e.g., [Par-fe9b83399b]:)
    # Pattern: [Par- followed by any alphanumeric/hyphen characters and ending with a colon and space
    cleaned_text = re.sub(r'\[Par-[a-f0-9]+\]:\s*', '', cleaned_text)
    
    # 3. Remove Markdown Bold and Escaped Hyphens
    # Remove ** bolding
    cleaned_text = cleaned_text.replace('**', '')
    # Fix escaped hyphens (\\-) often used in phone numbers in this dataset
    cleaned_text = cleaned_text.replace('\\-', '-')
    
    # 4. Remove excessive newlines and normalize spaces
    # Replace multiple newlines with a single space to create a continuous text flow
    cleaned_text = re.sub(r'\n\s*\n', ' ', cleaned_text) 
    # Replace remaining single newlines with a space
    cleaned_text = cleaned_text.replace('\n', ' ')
    # Normalize multiple spaces to a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text