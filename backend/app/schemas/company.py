from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class CompanyCreate(BaseModel):
    company_code: str
    company_name: str
    industry_type: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    employee_strength: Optional[int] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_mobile: Optional[str] = None

    @field_validator("company_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters")
        return v


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    industry_type: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    employee_strength: Optional[int] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_mobile: Optional[str] = None


class CompanyResponse(BaseModel):
    company_id: int
    company_code: str
    company_name: str
    industry_type: Optional[str]
    website: Optional[str]
    registration_number: Optional[str]
    gst_number: Optional[str]
    address: Optional[str]
    contact_person: Optional[str]
    status: str
    employee_strength: Optional[int]
    contact_email: Optional[str]
    contact_mobile: Optional[str]

    class Config:
        from_attributes = True  # allows creating from SQLAlchemy model


class CompanyLanguagePreference(BaseModel):
    language_id: int
    language_name: str
    enabled: bool
    is_default: bool = False


class CompanyLanguageUpdate(BaseModel):
    language_ids: list[int]
    default_language_id: Optional[int] = None
