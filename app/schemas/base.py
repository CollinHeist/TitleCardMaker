from pydantic import BaseModel

# Default value to use for arguments in Update objects that accept None
UNSPECIFIED = '__default__'

class Base(BaseModel):
    class Config:
        orm_mode = True