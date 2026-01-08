from pydantic import BaseModel


class CategoryBase(BaseModel):
    category_name: str
