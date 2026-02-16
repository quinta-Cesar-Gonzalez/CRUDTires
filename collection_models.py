from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime
from decimal import Decimal


# Enums
ServiceEnum = Literal[
    'app', 'sensors', 'field_service', 'installations', 
    'spare_parts', 'general_service', 'tires', 'hardware', 'training'
]

StatusEnum = Literal['pending', 'partially_paid', 'paid', 'overdue', 'cancelled']

BranchEnum = Literal['Q1', 'Q2', 'QT']


# Base Models
class CollectionBase(BaseModel):
    """Base collection model with common fields."""
    invoice_number: str = Field(..., min_length=1, max_length=100)
    company_id: int = Field(..., gt=0)
    customer_name: str = Field(..., min_length=1, max_length=255)
    user_id: int = Field(..., gt=0)
    service: ServiceEnum
    invoice_date: date
    due_date: date
    amount: Decimal = Field(..., ge=0)
    amount_paid: Optional[Decimal] = Field(0.00, ge=0)
    status: StatusEnum = 'pending'
    last_partial_payment_date: Optional[date] = None
    branch: BranchEnum


class CollectionCreate(CollectionBase):
    """Model for creating a new collection record."""
    pass


class CollectionUpdate(BaseModel):
    """Model for updating an existing collection record."""
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    company_id: Optional[int] = Field(None, gt=0)
    customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    user_id: Optional[int] = Field(None, gt=0)
    service: Optional[ServiceEnum] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    status: Optional[StatusEnum] = None
    last_partial_payment_date: Optional[date] = None
    branch: Optional[BranchEnum] = None


class CollectionResponse(CollectionBase):
    """Model for collection response with additional fields."""
    id: int
    outstanding_balance: Decimal
    is_deleted: bool
    created_at: datetime
    last_update: datetime

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    total_pages: int


class CollectionListResponse(BaseModel):
    """Response model for collection list with pagination."""
    success: bool = True
    data: list[CollectionResponse]
    pagination: PaginationInfo


class CollectionDetailResponse(BaseModel):
    """Response model for single collection."""
    success: bool = True
    data: CollectionResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    success: bool
    message: str


class CompanyResponse(BaseModel):
    """Response for company data."""
    id: int
    company_name: str
    
    class Config:
        from_attributes = True


class CompaniesListResponse(BaseModel):
    """Response for companies list."""
    success: bool = True
    data: list[CompanyResponse]


class EnumsResponse(BaseModel):
    """Response for enum values."""
    success: bool = True
    data: dict


class BulkUploadError(BaseModel):
    """Error details for bulk upload."""
    row: int
    error: str


class BulkUploadResponse(BaseModel):
    """Response for bulk upload operation."""
    success: bool
    total_rows: int
    inserted: int
    failed: int
    errors: list[BulkUploadError]
