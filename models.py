from pydantic import BaseModel, Field
from typing import Optional


class TireBase(BaseModel):
    """Base tire model with common fields."""
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    size: str = Field(..., min_length=1, max_length=50)
    layer_index: Optional[str] = Field(None, max_length=50)
    layers: Optional[int] = Field(0, ge=0)
    max_pressure: Optional[int] = Field(0, ge=0)
    min_pressure: Optional[int] = Field(0, ge=0)
    max_depth: Optional[int] = Field(0, ge=0)
    min_depth: Optional[int] = Field(0, ge=0)
    wear_type: Optional[str] = Field(None, max_length=50)
    profitability: Optional[int] = Field(0, ge=0)
    performance: Optional[int] = Field(0, ge=0)
    temperature: Optional[str] = Field(None, max_length=50)
    speed: Optional[str] = Field(None, max_length=50)
    speed_number: Optional[int] = Field(0, ge=0)
    braking: Optional[str] = Field(None, max_length=50)
    load_type: Optional[str] = Field(None, max_length=50)
    _load: Optional[int] = Field(0, ge=0, alias='load')
    road_type: Optional[str] = Field(None, max_length=50)
    terrain_type: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=50)


class TireCreate(TireBase):
    """Model for creating a new tire."""
    pass


class TireUpdate(TireBase):
    """Model for updating an existing tire."""
    pass


class TireResponse(TireBase):
    """Model for tire response with additional fields."""
    id: int
    created_at: int
    updated_at: int

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    total_pages: int


class TireListResponse(BaseModel):
    """Response model for tire list with pagination."""
    success: bool = True
    data: list[TireResponse]
    pagination: PaginationInfo


class TireDetailResponse(BaseModel):
    """Response model for single tire."""
    success: bool = True
    data: TireResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: Optional[str] = None


class FiltersResponse(BaseModel):
    """Response for available filters."""
    success: bool = True
    data: dict
