import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def validate_password_complexity(v: str) -> str:
    """Enforces min 8 characters, at least one letter, and at least one number."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one number")
    return v


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(...)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class ForgotPasswordSchema(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class ResetPasswordSchema(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(...)

    @field_validator("token")
    @classmethod
    def clean_token(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Token cannot be empty")
        return cleaned

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UpdateProfileSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Name must be at least 2 characters")
            return cleaned
        return None

    @model_validator(mode="after")
    def validate_password_change(self):
        if self.new_password:
            if not self.current_password:
                raise ValueError("Current password is required to set a new password")
            validate_password_complexity(self.new_password)
        return self


def serialize_user(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serializes a MongoDB user document into a safe API response dictionary.
    Guarantees password_hash, reset_token_hash, and reset_token_expiry are NEVER exposed.
    """
    if not user_doc:
        return {}

    user_id = str(user_doc.get("_id"))
    created_at = user_doc.get("created_at")
    updated_at = user_doc.get("updated_at")

    if isinstance(created_at, datetime):
        created_at_iso = created_at.isoformat()
    else:
        created_at_iso = str(created_at) if created_at else None

    if isinstance(updated_at, datetime):
        updated_at_iso = updated_at.isoformat()
    else:
        updated_at_iso = str(updated_at) if updated_at else None

    return {
        "id": user_id,
        "name": user_doc.get("name", ""),
        "email": user_doc.get("email", ""),
        "created_at": created_at_iso,
        "updated_at": updated_at_iso,
    }

