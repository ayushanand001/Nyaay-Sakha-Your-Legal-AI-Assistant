from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email:EmailStr
    password:str
    name:str
    phone:str

class VerifyRegistrationRequest(BaseModel):
    registration_id:str
    otp:str

class LoginRequest(BaseModel):
    email:EmailStr
    password:str

class ResendOTPRequest(BaseModel):
    registration_id: str
