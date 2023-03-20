from pydantic import BaseModel

class Base(BaseModel):
    class Config:
        orm_mode = True