from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any
import json

from app.db import (
    insert_assignment,
    get_assignment,
    get_all_assignments
)
from app.services.storage import storage_service
from app.services.extract import text_extractor
from app.services.rag import rag_service

router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentCreate(BaseModel):
    title: str
    rubric: Dict[str, Any]


class AssignmentResponse(BaseModel):
    id: int
    title: str
    rubric: Dict[str, Any]
    created_at: str


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(assignment: AssignmentCreate):
    """Create a new assignment with rubric."""
    try:
        assignment_id = insert_assignment(
            title=assignment.title,
            rubric=assignment.rubric
        )
        
        created = get_assignment(assignment_id)
        return AssignmentResponse(
            id=created['id'],
            title=created['title'],
            rubric=created['rubric'],
            created_at=str(created['created_at'])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AssignmentResponse])
async def list_assignments():
    """List all assignments."""
    try:
        assignments = get_all_assignments()
        return [
            AssignmentResponse(
                id=a['id'],
                title=a['title'],
                rubric=a['rubric'],
                created_at=str(a['created_at'])
            )
            for a in assignments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment_detail(assignment_id: int):
    """Get assignment details."""
    assignment = get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return AssignmentResponse(
        id=assignment['id'],
        title=assignment['title'],
        rubric=assignment['rubric'],
        created_at=str(assignment['created_at'])
    )


@router.post("/{assignment_id}/references")
async def upload_reference_document(
    assignment_id: int,
    file: UploadFile = File(...)
):
    """Upload a reference document for an assignment and index it in RAG."""
    try:
        # Verify assignment exists
        assignment = get_assignment(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Read file
        file_data = await file.read()
        
        # Extract text
        text = text_extractor.extract_text(file_data, file.filename)
        
        # Index in RAG system
        chunk_count = rag_service.index_document(
            assignment_id=assignment_id,
            text=text,
            metadata={"filename": file.filename}
        )
        
        return {
            "message": "Reference document indexed successfully",
            "filename": file.filename,
            "chunks_created": chunk_count
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
