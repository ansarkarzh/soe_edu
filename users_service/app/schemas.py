from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date, datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    username: str
    password: str

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'Username must be alphanumeric'
        return v

    @validator('password')
    def password_min_length(cls, v):
        assert len(v) >= 8, 'Password must be at least 8 characters'
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

    @validator('phone_number')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('Phone number must contain only digits')
        return v

class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginForm(BaseModel):
    username: str
    password: str
