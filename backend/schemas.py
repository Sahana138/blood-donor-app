from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str
    role: str = "donor"   # donor or requester

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: str

    model_config = {"from_attributes": True}