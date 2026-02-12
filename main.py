import os
import math
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from models import (
    TireCreate, TireUpdate, TireResponse, TireListResponse, 
    TireDetailResponse, MessageResponse, ErrorResponse, 
    FiltersResponse, PaginationInfo
)
import database as db

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="CRUD Tires Catalog API",
    description="API for managing tires catalog",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== API ENDPOINTS =====

@app.get("/api/tires", response_model=TireListResponse)
async def list_tires(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    position: Optional[str] = Query(None)
):
    """List tires with pagination, search, and filters."""
    try:
        offset = (page - 1) * limit
        
        # Build WHERE conditions
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(brand LIKE %s OR model LIKE %s OR size LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        if brand:
            where_conditions.append("brand = %s")
            params.append(brand)
        
        if model:
            where_conditions.append("model = %s")
            params.append(model)
        
        if size:
            where_conditions.append("size = %s")
            params.append(size)
        
        if position:
            where_conditions.append("position = %s")
            params.append(position)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM tires_catalog {where_clause}"
        count_result = db.query_one(count_query, tuple(params))
        total = count_result['total']
        
        # Get paginated data
        data_query = f"""
            SELECT * FROM tires_catalog 
            {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        tires = db.query(data_query, tuple(params))
        
        # Convert to response models
        tire_responses = [TireResponse(**tire) for tire in tires]
        
        return TireListResponse(
            success=True,
            data=tire_responses,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                total_pages=math.ceil(total / limit)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tires/{tire_id}", response_model=TireDetailResponse)
async def get_tire(tire_id: int):
    """Get a single tire by ID."""
    try:
        tire = db.query_one("SELECT * FROM tires_catalog WHERE id = %s", (tire_id,))
        
        if not tire:
            raise HTTPException(status_code=404, detail="Tire not found")
        
        return TireDetailResponse(
            success=True,
            data=TireResponse(**tire)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tires", response_model=MessageResponse, status_code=201)
async def create_tire(tire: TireCreate):
    """Create a new tire."""
    try:
        query = """
            INSERT INTO tires_catalog (
                brand, model, size, layer_index, layers, max_pressure, min_pressure,
                max_depth, min_depth, wear_type, profitability, performance,
                temperature, speed, speed_number, braking, load_type, _load,
                road_type, terrain_type, position
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            tire.brand, tire.model, tire.size, tire.layer_index, tire.layers,
            tire.max_pressure, tire.min_pressure, tire.max_depth, tire.min_depth,
            tire.wear_type, tire.profitability, tire.performance, tire.temperature,
            tire.speed, tire.speed_number, tire.braking, tire.load_type, tire.load_value,
            tire.road_type, tire.terrain_type, tire.position
        )
        
        insert_id = db.execute(query, params)
        
        return MessageResponse(
            success=True,
            message=f"Tire created successfully with ID {insert_id}"
        )
    except Exception as e:
        # Handle duplicate key error
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail="A tire with this brand, model, size, and position already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tires/{tire_id}", response_model=MessageResponse)
async def update_tire(tire_id: int, tire: TireUpdate):
    """Update an existing tire."""
    try:
        query = """
            UPDATE tires_catalog SET
                brand = %s, model = %s, size = %s, layer_index = %s, layers = %s,
                max_pressure = %s, min_pressure = %s, max_depth = %s, min_depth = %s,
                wear_type = %s, profitability = %s, performance = %s, temperature = %s,
                speed = %s, speed_number = %s, braking = %s, load_type = %s, _load = %s,
                road_type = %s, terrain_type = %s, position = %s,
                updated_at = UNIX_TIMESTAMP() * 1000
            WHERE id = %s
        """
        
        params = (
            tire.brand, tire.model, tire.size, tire.layer_index, tire.layers,
            tire.max_pressure, tire.min_pressure, tire.max_depth, tire.min_depth,
            tire.wear_type, tire.profitability, tire.performance, tire.temperature,
            tire.speed, tire.speed_number, tire.braking, tire.load_type, tire.load_value,
            tire.road_type, tire.terrain_type, tire.position,
            tire_id
        )
        
        affected_rows = db.execute(query, params)
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Tire not found")
        
        return MessageResponse(
            success=True,
            message="Tire updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(
                status_code=409,
                detail="A tire with this brand, model, size, and position already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tires/{tire_id}", response_model=MessageResponse)
async def delete_tire(tire_id: int):
    """Delete a tire."""
    try:
        affected_rows = db.execute("DELETE FROM tires_catalog WHERE id = %s", (tire_id,))
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Tire not found")
        
        return MessageResponse(
            success=True,
            message="Tire deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filters", response_model=FiltersResponse)
async def get_filters():
    """Get unique values for filters."""
    try:
        brands = db.query("SELECT DISTINCT brand FROM tires_catalog ORDER BY brand")
        models = db.query("SELECT DISTINCT model FROM tires_catalog ORDER BY model")
        sizes = db.query("SELECT DISTINCT size FROM tires_catalog ORDER BY size")
        positions = db.query(
            "SELECT DISTINCT position FROM tires_catalog WHERE position IS NOT NULL ORDER BY position"
        )
        
        return FiltersResponse(
            success=True,
            data={
                "brands": [r['brand'] for r in brands],
                "models": [r['model'] for r in models],
                "sizes": [r['size'] for r in sizes],
                "positions": [r['position'] for r in positions]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Lambda handler
handler = Mangum(app, lifespan="off")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
