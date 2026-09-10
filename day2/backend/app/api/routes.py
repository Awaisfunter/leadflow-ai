"""
LeadFlow AI — FastAPI Routes
Exposes endpoints for lead processing, human approval, audit trail, and health check.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..config import get_settings
from ..schemas.models import LeadInput, PipelineResponse
from ..services.audit_logger import get_audit_trail
from ..services.pipeline import get_pipeline_result, handle_approval_action, run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["LeadFlow AI Pipeline"])


class ApprovalActionRequest(BaseModel):
    action: str = Field(..., description="APPROVE, REJECT, QUARANTINE, or EDIT")
    reviewer_id: str = Field(default="demo_user", description="Identifier of the human reviewer")
    notes: Optional[str] = Field(default=None, description="Optional reviewer justification notes")
    edited_body: Optional[str] = Field(default=None, description="Edited email draft text if edited")


@router.post(
    "/leads/process",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Inbound Lead",
    description="Accepts a raw inbound lead and executes the complete triage, enrichment, scoring, and drafting pipeline.",
)
async def process_lead_endpoint(payload: LeadInput) -> PipelineResponse:
    try:
        result = await run_pipeline(payload)
        return result
    except Exception as e:
        logger.error(f"Error processing lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process lead. Please review server logs for details.",
        )


@router.post(
    "/leads/{lead_id}/action",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Human Approval Decision",
    description="Records human approval, rejection, edit, or quarantine decision. Authorizes CRM dispatch upon approval.",
)
async def submit_approval_action(
    lead_id: str,
    payload: ApprovalActionRequest,
) -> PipelineResponse:
    try:
        updated = handle_approval_action(
            lead_id=lead_id,
            action=payload.action,
            reviewer_id=payload.reviewer_id,
            notes=payload.notes,
            edited_body=payload.edited_body,
        )
        return updated
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating approval state: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/leads/{lead_id}",
    response_model=PipelineResponse,
    summary="Get Lead Pipeline State",
)
async def get_lead_state(lead_id: str) -> PipelineResponse:
    result = get_pipeline_result(lead_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lead {lead_id} not found.")
    return result


@router.get(
    "/leads/{lead_id}/audit",
    summary="Get Append-only SQLite Audit Trail (v0)",
)
async def get_lead_audit_trail(lead_id: str):
    trail = get_audit_trail(lead_id)
    return {"lead_id": lead_id, "count": len(trail), "events": trail}


@router.get("/health", summary="Health Check")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "system": "LeadFlow AI v0",
        "llm_configured": settings.gemini_available,
        "mode": "hybrid_deterministic_llm",
    }
