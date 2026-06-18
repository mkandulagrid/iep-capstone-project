from pydantic import BaseModel, EmailStr


class UserRegisterRequest(BaseModel):
    """Request body for registering a new user."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    """Public user data returned in responses."""
    id: int
    email: EmailStr
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Request body for logging in."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token returned after successful login."""
    access_token: str
    token_type: str = "bearer"
