prompt_v1 = """
Please extract the recipe from the following text.
The user wants to make delicious chocolate chip cookies.
They need 2 and 1/4 cups of all-purpose flour, 1 teaspoon of baking soda,
1 teaspoon of salt, 1 cup of unsalted butter (softened), 3/4 cup of granulated sugar,
3/4 cup of packed brown sugar, 1 teaspoon of vanilla extract, and 2 large eggs.
For the best part, they'll need 2 cups of semisweet chocolate chips.
First, preheat the oven to 375°F (190°C). Then, in a small bowl, whisk together the flour,
baking soda, and salt. In a large bowl, cream together the butter, granulated sugar, and brown sugar
until light and fluffy. Beat in the vanilla and eggs, one at a time. Gradually beat in the dry
ingredients until just combined. Finally, stir in the chocolate chips. Drop by rounded tablespoons
onto ungreased baking sheets and bake for 9 to 11 minutes.
"""
prompt_v2 = """
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
prompt_v3 = """
You are an expert PII identification and entity extraction tool for legal documents.
Analyze the provided text and identify ALL instances of the 12 PII/Entity Categories listed below.

### PII/Entity Categories to Extract
1.  **Name**: Full names, partial names, or titles (e.g., Orval O'Riocht, Mr. Shingali).
2.  **Company_Name**: Organization names (e.g., The Right Brothers, Bank of Ireland).
3.  **Address**: Full or partial street addresses, city, state, postal codes, and country (e.g., 15 Grafton Street, Dublin 2, Ireland).
4.  **Date_of_Birth**: Dates specifying birth (e.g., 23 August 1987).
5.  **Email_Address**: Standard email formats.
6.  **Phone_Number**: Complete phone or fax numbers.
7.  **PPS_Number**: Irish Personal Public Service numbers (e.g., 8472639T).
8.  **License_Number**: Driver's licenses, professional licenses, VAT/Tax numbers (e.g., AML-IE-8472639, IE8472639T).
9.  **Passport_Number**: Passport document numbers (e.g., P8472639).
10. **Bank_Information**: Account numbers, IBANs, and Sort Codes (e.g., IE64 BOFI..., 90-73-28).
11. **ID_Number**: National/other ID numbers (e.g., 19870823-1234-567).
12. **Reference_Number**: Any unique legal, tax, employer, or case reference number (e.g., RC-RB-2025-847263, C-247/25).

### Output Constraints
-   Output MUST be a single JSON object.
-   Do not include any conversational text, explanations, or analysis.
-   Ensure all instances, including embedded and partial matches, are captured.
-   The output structure must strictly adhere to the provided JSON Schema.
"""

prompt_v4="""
ROLE: Precision PII Extraction Engine for Legal Documents

MISSION: Exhaustively identify and locate all Personally Identifiable Information with character-level accuracy.

PII TAXONOMY (12 categories):
- Name: "John Smith", "Dr. O'Malley", "Mr. Johnson"
- Company_Name: "Google LLC", "Bank of Ireland" 
- Date_of_Birth: "15/03/1985", "March 15, 1985", "23 August 1987"
- Address: "123 Main St, Dublin 2", "Unit 7, Industrial Estate"
- Email_Address: "user@company.ie", "admin@domain.com"
- Phone_Number: "+353-1-485-2739", "+352 43 03 1"
- PPS_Number: "8472639T", "6159287K"
- License_Number: "AML-IE-8472639", "CA-IE-6159287"
- Passport_Number: "P6159287", "P8472639"
- Bank_Information: "IE64 BOFI 9073 2847 6391 52", "Sort Code: 90-73-28"
- Reference_Number: "LU-2014-REF-08947", "C-247/25", "ECLI:EU:C:2025:542"
- ID_Number: "19870823-1234-567", "19910315-2345-678"

EXTRACTION PROTOCOL:
1. SCAN: Examine every character sequence
2. CLASSIFY: Assign to exact PII category
3. LOCATE: Record precise start/end indices
4. CAPTURE: Preserve exact casing and formatting
5. REPORT: Structured JSON output

ZERO TOLERANCE:
- No missed entities
- No approximate positions  
- No category misassignment
- No text normalization
- No explanatory text

OUTPUT SCHEMA (JSON):
{
  "entities": [
    {
      "text": "verbatim text from document",
      "type": "exact_category_name", 
      "start_index": integer,
      "end_index": integer
    }
  ]
}

STRICT COMPLIANCE: Return ONLY valid JSON. No preamble. No commentary."""


prompt_v5 = """
You are an advanced PII extraction engine specialized in legal and compliance documents. 
Your task is to detect and extract all Personally Identifiable Information (PII) from the 
input text.

You must identify the following PII categories:

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

Extraction Requirements:
- Return **all exact text spans**, including partial names, nested entities, or embedded values.
- Provide the **character start index** and **character end index (exclusive)** for each detected PII.
- Output must contain **only** the final JSON object. No explanations or conversational text.
- The JSON must contain **all 12 keys**. Each key's value must be a list of items. 
- Each detected item must be an object with fields: `value`, `type`, `start`, `end`.
- If a category has no matches, return an empty list.
- Do not alter, normalize, or correct the extracted text; return it exactly as it appears.
"""

def get_prompt(index):
    prompt_list = [prompt_v1,prompt_v2,prompt_v3,prompt_v4,prompt_v5]
   
    return prompt_list[index]