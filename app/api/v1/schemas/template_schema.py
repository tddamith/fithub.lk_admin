from pydantic import BaseModel
from typing import Optional,Dict,List


class ImageBase(BaseModel):
    url:str
    file_name:str
   

class TemplateBase(BaseModel):
    template_name: str
    # latest_version: Optional[str]
    category_id: str
    sub_category_id:str
    base64_data: str
    filename: str
    cover_image:ImageBase
    type: Optional[str]
    
    
class TemplateUpdateBase(BaseModel):
    template_name: str
    # latest_version: Optional[str]
    category_id: str
    sub_category_id:str
    base64_data: Optional[str]
    filename: Optional[str]
    cover_image:Optional[ImageBase]
    type: Optional[str]
    
