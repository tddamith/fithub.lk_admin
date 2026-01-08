from pydantic import BaseModel
from typing import Optional,Dict,List

class FacilityBase(BaseModel):
    facility_name: str    

class UpdateFacility(BaseModel):
    facility_name: Optional[str]    
