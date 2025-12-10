from pydantic import BaseModel
from typing import Optional,Dict,List



class Sub_category_items(BaseModel):
    id:Optional[str]
    name:Optional[str]

class SubCategoryBase(BaseModel):
    category_id: str
    sub_category_name: str    
    sub_category_items: Optional[List[Sub_category_items]] = []

class UpdateSubcategory(BaseModel):
    sub_category_name: Optional[str]    
    sub_category_items: Optional[List[Sub_category_items]] = []

class UpdateSubCategoryItem(BaseModel):
    sub_category_items: Optional[List[Sub_category_items]] = []