from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.postgres_manager import postgres_manager
from src.models.lead_model import Lead
from src.schemas.lead_schema import LeadCreate, LeadUpdate, LeadResponse, LeadList

router = APIRouter()

@router.post("/leads", response_model=LeadResponse, summary="Create a new lead")
async def create_lead(lead_data: LeadCreate):
    """
    Create a new lead entry.
    Args:
        lead_data (LeadCreate): Payload containing lead information.
    Returns:
        LeadResponse: Details of the created lead.
    """
    try:
        with postgres_manager.get_session() as session:
            new_lead = Lead(**lead_data.dict())
            session.add(new_lead)
            session.commit()
            session.refresh(new_lead)
            return LeadResponse.from_orm(new_lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lead: {str(e)}")

@router.get("/leads/{lead_id}", response_model=LeadResponse, summary="Get lead details")
async def get_lead(lead_id: int):
    """
    Fetch details of a specific lead by ID.
    Args:
        lead_id (int): ID of the lead to fetch.
    Returns:
        LeadResponse: Details of the lead.
    """
    try:
        with postgres_manager.get_session() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            return LeadResponse.from_orm(lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lead: {str(e)}")

@router.put("/leads/{lead_id}", response_model=LeadResponse, summary="Update lead details")
async def update_lead(lead_id: int, lead_data: LeadUpdate):
    """
    Update an existing lead.
    Args:
        lead_id (int): ID of the lead to update.
        lead_data (LeadUpdate): Payload containing updated lead information.
    Returns:
        LeadResponse: Updated lead details.
    """
    try:
        with postgres_manager.get_session() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            for key, value in lead_data.dict(exclude_unset=True).items():
                setattr(lead, key, value)
            session.commit()
            session.refresh(lead)
            return LeadResponse.from_orm(lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating lead: {str(e)}")

@router.get("/leads", response_model=LeadList, summary="List all leads")
async def list_leads(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    List all leads with pagination.
    Args:
        page (int): Page number.
        size (int): Number of items per page.
    Returns:
        LeadList: Paginated list of leads.
    """
    try:
        with postgres_manager.get_session() as session:
            query = session.query(Lead)
            total = query.count()
            leads = query.offset((page - 1) * size).limit(size).all()
            return LeadList(
                items=[LeadResponse.from_orm(lead) for lead in leads],
                total=total,
                page=page,
                size=size,
                pages=(total // size) + (1 if total % size > 0 else 0)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing leads: {str(e)}")

@router.delete("/leads/{lead_id}", summary="Delete a lead")
async def delete_lead(lead_id: int):
    """
    Delete a lead by ID.
    Args:
        lead_id (int): ID of the lead to delete.
    Returns:
        dict: Confirmation of lead deletion.
    """
    try:
        with postgres_manager.get_session() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            session.delete(lead)
            session.commit()
            return {"status": "success", "message": "Lead deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting lead: {str(e)}")
