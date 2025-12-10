from pydantic import BaseModel


class CategoryBase(BaseModel):
    icon_name: str
    category_name: str
