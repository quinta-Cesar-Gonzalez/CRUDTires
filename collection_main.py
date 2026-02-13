import os
import math
import io
from typing import Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from collection_models import (
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionListResponse, CollectionDetailResponse, MessageResponse,
    CompanyResponse, CompaniesListResponse, EnumsResponse,
    BulkUploadResponse, BulkUploadError, PaginationInfo
)
import database as db

load_dotenv()

app = FastAPI(
    title="Collection Management API",
    description="API for managing invoices collection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_period_dates(period: str) -> Tuple[date, date]:
    """Calculate date range from period string."""
    today = datetime.now().date()
    
    if period == "today":
        return today, today
    
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    
    elif period == "current_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    
    elif period == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end
    
    elif period == "current_month":
        start = today.replace(day=1)
        return start, today
    
    elif period == "last_month":
        first_current = today.replace(day=1)
        last_month_end = first_current - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start, last_month_end
    
    elif period == "last_3_months":
        end = today
        start = (today.replace(day=1) - timedelta(days=90)).replace(day=1)
        return start, end
    
    elif period == "last_6_months":
        end = today
        start = (today.replace(day=1) - timedelta(days=180)).replace(day=1)
        return start, end
    
    elif period == "current_year":
        start = today.replace(month=1, day=1)
        return start, today
    
    elif period == "last_year":
        start = today.replace(year=today.year - 1, month=1, day=1)
        end = today.replace(year=today.year - 1, month=12, day=31)
        return start, end
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")



@app.get("/api/collection/enums", response_model=EnumsResponse)
async def get_enums():
    return EnumsResponse(
        success=True,
        data={
            "services": [
                "app", "sensors", "field_service", "installations",
                "spare_parts", "general_service", "tires", "hardware", "training"
            ],
            "statuses": ["pending", "partially_paid", "paid", "overdue", "cancelled"],
            "branches": ["Q1", "Q2", "QT"],
            "periods": [
                "today", "yesterday", "current_week", "last_week",
                "current_month", "last_month", "last_3_months", "last_6_months",
                "current_year", "last_year"
            ]
        }
    )


# ===== COMPANIES ENDPOINT =====

@app.get("/api/companies", response_model=CompaniesListResponse)
async def get_companies():
    """Get all companies for selector."""
    try:
        companies = db.query("SELECT id, name FROM companies ORDER BY name")
        return CompaniesListResponse(
            success=True,
            data=[CompanyResponse(**company) for company in companies]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== COLLECTION CRUD =====

@app.get("/api/collection", response_model=CollectionListResponse)
async def list_collections(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    company_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    period: Optional[str] = Query(None, description="Period filter: today, yesterday, current_week, last_week, current_month, last_month, last_3_months, last_6_months, current_year, last_year"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None)
):
    try:
        offset = (page - 1) * limit
        
        where_conditions = ["is_deleted = 0"]
        params = []
        
        if period:
            from_date, to_date = get_period_dates(period)
        
        if company_id:
            where_conditions.append("company_id = %s")
            params.append(company_id)
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        if service:
            where_conditions.append("service = %s")
            params.append(service)
        
        if branch:
            where_conditions.append("branch = %s")
            params.append(branch)
        
        if from_date:
            where_conditions.append("invoice_date >= %s")
            params.append(from_date)
        
        if to_date:
            where_conditions.append("invoice_date <= %s")
            params.append(to_date)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM collection {where_clause}"
        count_result = db.query_one(count_query, tuple(params))
        total = count_result['total']
        
        # Get paginated data
        data_query = f"""
            SELECT * FROM collection
            {where_clause}
            ORDER BY invoice_date DESC, id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        collections = db.query(data_query, tuple(params))
        
        # Convert to response models
        collection_responses = [CollectionResponse(**collection) for collection in collections]
        
        return CollectionListResponse(
            success=True,
            data=collection_responses,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                total_pages=math.ceil(total / limit) if total > 0 else 0
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collection/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(collection_id: int):
    """Get a single collection by ID (excludes soft deleted)."""
    try:
        collection = db.query_one(
            "SELECT * FROM collection WHERE id = %s AND is_deleted = 0",
            (collection_id,)
        )
        
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return CollectionDetailResponse(
            success=True,
            data=CollectionResponse(**collection)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collection", response_model=MessageResponse, status_code=201)
async def create_collection(collection: CollectionCreate):
    """Create a new collection record."""
    try:
        query = """
            INSERT INTO collection (
                invoice_number, company_id, customer_name, user_id, service,
                invoice_date, due_date, amount, amount_paid, status,
                last_partial_payment_date, branch
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            collection.invoice_number,
            collection.company_id,
            collection.customer_name,
            collection.user_id,
            collection.service,
            collection.invoice_date,
            collection.due_date,
            collection.amount,
            collection.amount_paid,
            collection.status,
            collection.last_partial_payment_date,
            collection.branch
        )
        
        insert_id = db.execute(query, params)
        
        return MessageResponse(
            success=True,
            message=f"Collection created successfully with ID {insert_id}"
        )
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail="Invoice number already exists"
            )
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Invalid company_id or user_id"
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/collection/{collection_id}", response_model=MessageResponse)
async def update_collection(collection_id: int, collection: CollectionUpdate):
    """Update an existing collection record."""
    try:
        # Build dynamic UPDATE query
        update_fields = []
        params = []
        
        if collection.invoice_number is not None:
            update_fields.append("invoice_number = %s")
            params.append(collection.invoice_number)
        
        if collection.company_id is not None:
            update_fields.append("company_id = %s")
            params.append(collection.company_id)
        
        if collection.customer_name is not None:
            update_fields.append("customer_name = %s")
            params.append(collection.customer_name)
        
        if collection.user_id is not None:
            update_fields.append("user_id = %s")
            params.append(collection.user_id)
        
        if collection.service is not None:
            update_fields.append("service = %s")
            params.append(collection.service)
        
        if collection.invoice_date is not None:
            update_fields.append("invoice_date = %s")
            params.append(collection.invoice_date)
        
        if collection.due_date is not None:
            update_fields.append("due_date = %s")
            params.append(collection.due_date)
        
        if collection.amount is not None:
            update_fields.append("amount = %s")
            params.append(collection.amount)
        
        if collection.amount_paid is not None:
            update_fields.append("amount_paid = %s")
            params.append(collection.amount_paid)
        
        if collection.status is not None:
            update_fields.append("status = %s")
            params.append(collection.status)
        
        if collection.last_partial_payment_date is not None:
            update_fields.append("last_partial_payment_date = %s")
            params.append(collection.last_partial_payment_date)
        
        if collection.branch is not None:
            update_fields.append("branch = %s")
            params.append(collection.branch)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"""
            UPDATE collection SET {', '.join(update_fields)}
            WHERE id = %s AND is_deleted = 0
        """
        params.append(collection_id)
        
        affected_rows = db.execute(query, tuple(params))
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return MessageResponse(
            success=True,
            message="Collection updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail="Invoice number already exists"
            )
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Invalid company_id or user_id"
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collection/{collection_id}", response_model=MessageResponse)
async def soft_delete_collection(collection_id: int):
    """Soft delete a collection (sets is_deleted = 1)."""
    try:
        affected_rows = db.execute(
            "UPDATE collection SET is_deleted = 1 WHERE id = %s AND is_deleted = 0",
            (collection_id,)
        )
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return MessageResponse(
            success=True,
            message="Collection deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== BULK UPLOAD =====

@app.post("/api/collection/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_collections(file: UploadFile = File(...)):
    """Bulk upload collections from Excel or CSV file."""
    try:
        import pandas as pd
        
        # Read file
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Use CSV or Excel (.xlsx, .xls)"
            )
        
        # Validate required columns
        required_cols = [
            'invoice_number', 'company_id', 'customer_name', 'user_id',
            'service', 'invoice_date', 'due_date', 'amount', 'branch'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Process rows
        total_rows = len(df)
        inserted = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Prepare data
                amount_paid = row.get('amount_paid', 0.00)
                status = row.get('status', 'pending')
                last_partial_payment_date = row.get('last_partial_payment_date', None)
                
                # Convert dates
                invoice_date = pd.to_datetime(row['invoice_date']).date()
                due_date = pd.to_datetime(row['due_date']).date()
                
                if last_partial_payment_date and pd.notna(last_partial_payment_date):
                    last_partial_payment_date = pd.to_datetime(last_partial_payment_date).date()
                else:
                    last_partial_payment_date = None
                
                # Insert
                query = """
                    INSERT INTO collection (
                        invoice_number, company_id, customer_name, user_id, service,
                        invoice_date, due_date, amount, amount_paid, status,
                        last_partial_payment_date, branch
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    row['invoice_number'],
                    int(row['company_id']),
                    row['customer_name'],
                    int(row['user_id']),
                    row['service'],
                    invoice_date,
                    due_date,
                    float(row['amount']),
                    float(amount_paid),
                    status,
                    last_partial_payment_date,
                    row['branch']
                )
                
                db.execute(query, params)
                inserted += 1
                
            except Exception as e:
                errors.append(BulkUploadError(
                    row=idx + 2,  # +2 because 1-indexed and header row
                    error=str(e)
                ))
        
        return BulkUploadResponse(
            success=inserted > 0,
            total_rows=total_rows,
            inserted=inserted,
            failed=len(errors),
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lambda handler
handler = Mangum(app, lifespan="off")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
