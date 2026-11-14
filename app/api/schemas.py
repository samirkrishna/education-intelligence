
from pydantic import BaseModel, ConfigDict, HttpUrl


class UniversityCreate(BaseModel):
    name: str
    country: str
    website_url: HttpUrl | None = None


class UniversityResponse(BaseModel):
    id: int
    name: str
    country: str
    website_url: str | None
    active: bool

    model_config = ConfigDict(from_attributes=True)



class MonitoringSourceCreate(BaseModel):
    university_id: int
    source_name: str
    source_type: str
    url: HttpUrl
    scan_interval_minutes: int = 360


class MonitoringSourceResponse(BaseModel):
    id: int
    university_id: int
    source_name: str
    source_type: str
    url: str
    active: bool
    scan_interval_minutes: int

    model_config = ConfigDict(from_attributes=True)
