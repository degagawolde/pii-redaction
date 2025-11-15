from pydantic import BaseModel, Field
from typing import List


class PIIExtractionOutput(BaseModel):
  
    Name: List[str] = Field(
        default_factory=list,
        description="Full names, partial names, or titles (e.g., Orval O'Riocht, Mr. Shingali).",
    )
    Company_Name: List[str] = Field(
        default_factory=list,
        description="Organization names (e.g., The Right Brothers, Bank of Ireland).",
    )
    Address: List[str] = Field(
        default_factory=list,
        description="Full or partial street addresses, city, postal codes, and country (e.g., 15 Grafton Street, Dublin 2, Ireland).",
    )
    Date_of_Birth: List[str] = Field(
        default_factory=list,
        description="Dates specifically identifying a birth date (e.g., 23 August 1987).",
    )
    Email_Address: List[str] = Field(
        default_factory=list, description="Standard email formats."
    )
    Phone_Number: List[str] = Field(
        default_factory=list, description="Complete phone or fax numbers."
    )
    PPS_Number: List[str] = Field(
        default_factory=list,
        description="Irish Personal Public Service numbers (e.g., 8472639T).",
    )
    License_Number: List[str] = Field(
        default_factory=list,
        description="Driver's licenses, professional licenses, VAT/Tax numbers (e.g., AML-IE-8472639, IE8472639T).",
    )
    Passport_Number: List[str] = Field(
        default_factory=list, description="Passport document numbers (e.g., P8472639)."
    )
    Bank_Information: List[str] = Field(
        default_factory=list,
        description="Account numbers, IBANs, and Sort Codes (e.g., IE64 BOFI..., 90-73-28).",
    )
    ID_Number: List[str] = Field(
        default_factory=list,
        description="National/other ID numbers (e.g., 19870823-1234-567).",
    )
    Reference_Number: List[str] = Field(
        default_factory=list,
        description="Any unique legal, tax, employer, or case reference number (e.g., RC-RB-2025-847263, C-247/25).",
    )