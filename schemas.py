from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import date
from typing import List, Optional, Any

class PersonBase(BaseModel):
    name: str
    email: EmailStr

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class SegmentBase(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date

class PersonResponse(PersonBase):
    id: int
    segments: List[SegmentBase] = []
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator('segments', mode='before')
    @classmethod
    def extract_segment(cls, v: Any) -> Any:
        if isinstance(v, list):
            return [item.segment for item in v if hasattr(item, 'segment')]
        return v

class SegmentCreate(BaseModel):
    name: str
    start_date: date
    end_date: date

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v

class SegmentResponse(SegmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SegmentAssignmentCreate(BaseModel):
    segment_id: int

class PaginatedPeople(BaseModel):
    total: int
    page: int
    limit: int
    data: List[PersonResponse]
