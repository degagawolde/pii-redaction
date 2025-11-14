import pandas as pd
import re
from collections import defaultdict
import json

def read_input_document(file_path):
    try:
        # Read the file into a DataFrame
        df = pd.read_excel(file_path, names=["name", "content"])
        print("✅ Successfully connected to and read the CSV file.")
        print("\n--- First 5 Rows ---")
        print(df.head())
        print("\n--- Data Structure ---")
        print(df.info())
        return df
    except FileNotFoundError:
        print(f"❌ Error: The file at '{file_path}' was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("❌ Error: The file is empty.")
        return None


def parse_label_document(raw_data: str) -> dict:
    """
    Parses structured text with 'Test X' blocks and '###KEY #VALUE' pairs
    into a nested dictionary suitable for JSON serialization.
    """

    # 1. Define the Regex Pattern
    # Captures the key (Group 1) and the value (Group 2)
    # Handles structures like '###Name #Value' and '###Na   me #Value'
    entity_pattern = re.compile(r"^\s*#+([A-Za-z_]+)\s*#\s*(.+)", flags=re.MULTILINE)

    # 2. Split the data by "Test [X]" headers to isolate each block.
    test_blocks = re.split(r"(Test [A-Z])\s*\n?", raw_data.strip())

    # Remove the first element if it's empty (which happens if the data starts with a Test ID)
    if test_blocks and test_blocks[0].strip() == "":
        test_blocks.pop(0)

    parsed_data = {}
    current_test_id = None

    # 3. Iterate and Extract
    for i, block in enumerate(test_blocks):
        if i % 2 == 0:
            # This block is the Test ID (e.g., "Test A", "Test C")
            current_test_id = block.strip()
            parsed_data[current_test_id] = defaultdict(list)
        else:
            # This block is the content for the current_test_id
            if current_test_id is None:
                continue

            # Iterate over all matches within the content block
            for match in entity_pattern.finditer(block):
                field_key = match.group(1).strip()
                value = match.group(2).strip()

                # Append the value to the list for the corresponding key
                parsed_data[current_test_id][field_key].append(value)

    # 4. Convert defaultdicts back to regular dicts
    final_data = {test_id: dict(data) for test_id, data in parsed_data.items()}

    return final_data

def parse_document_to_json(raw_data: str) -> dict:
    """
    Parses structured text with 'Test X' blocks and '###KEY #VALUE' pairs
    into a nested dictionary suitable for JSON serialization.
    """

    # Regex to capture the field key and value from lines like '###Name #Orval O'Riocht'
    # Group 1: The key (e.g., Name, Company_Name). Handles irregular spacing like 'Na   me' in Test F.
    # Group 2: The value (the rest of the line).
    entity_pattern = re.compile(r"^\s*#+([A-Za-z_]+)\s*#\s*(.+)", flags=re.MULTILINE)

    # Split the data by "Test [X]" to isolate each block.
    # The split includes the delimiter (Test ID) in the results.
    test_blocks = re.split(r"(Test [A-Z])\s*\n?", raw_data.strip())

    # Remove the first element if it's empty (which happens if the data starts with "Test A")
    if test_blocks and test_blocks[0].strip() == "":
        test_blocks.pop(0)

    parsed_data = {}
    current_test_id = None

    # Iterate through blocks (which alternate between Test ID and block content)
    for i, block in enumerate(test_blocks):
        if i % 2 == 0:
            # This block is the Test ID (e.g., "Test A", "Test C")
            current_test_id = block.strip()
            parsed_data[current_test_id] = defaultdict(list)
        else:
            # This block is the content for the current_test_id
            if current_test_id is None:
                continue

            # Iterate over all matches within the content block
            for match in entity_pattern.finditer(block):
                field_key = match.group(1).strip()
                value = match.group(2).strip()

                # Append the value to the list for the corresponding key
                parsed_data[current_test_id][field_key].append(value)

    # Convert defaultdicts back to regular dicts for final JSON structure
    final_data = {test_id: dict(data) for test_id, data in parsed_data.items()}

    return final_data
