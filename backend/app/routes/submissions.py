from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db import (
    insert_submission,
    get_submission,
    get_submissions_by_assignment,
    get_grade_by_submission,
    get_assignment
)
from app.services.storage import storage_service
from app.services.extract import text_extractor
from app.worker.tasks import grade_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    filename: str
    status: str
    score: Optional[int] = None
    feedback: Optional[str] = None
    created_at: str


class GradeResponse(BaseModel):
    id: int
    submission_id: int
    score: int
    breakdown: Dict[str, Any]
    feedback: str
    citations: List[Dict[str, Any]]
    created_at: str


@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    assignment_id: int,
    file: UploadFile = File(...)
):
    """Upload a submission for grading."""
    try:
        # Verify assignment exists
        assignment = get_assignment(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Read file
        file_data = await file.read()
        
        # Upload to MinIO
        s3_key = storage_service.upload_file(file_data, file.filename)
        
        # Extract text
        extracted_text = text_extractor.extract_text(file_data, file.filename)
        
        # Insert into database
        submission_id = insert_submission(
            assignment_id=assignment_id,
            filename=file.filename,
            s3_key=s3_key,
            extracted_text=extracted_text
        )
        
        # Enqueue grading task
        grade_submission.delay(submission_id)
        
        # Get submission
        submission = get_submission(submission_id)
        
        return SubmissionResponse(
            id=submission['id'],
            assignment_id=submission['assignment_id'],
            filename=submission['filename'],
            status=submission['status'],
            created_at=str(submission['created_at'])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignment/{assignment_id}", response_model=List[SubmissionResponse])
async def list_submissions(assignment_id: int):
    """List all submissions for an assignment."""
    try:
        submissions = get_submissions_by_assignment(assignment_id)
        return [
            SubmissionResponse(
                id=s['id'],
                assignment_id=s['assignment_id'],
                filename=s['filename'],
                status=s['status'],
                score=s.get('score'),
                feedback=s.get('feedback'),
                created_at=str(s['created_at'])
            )
            for s in submissions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission_detail(submission_id: int):
    """Get submission details."""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Try to get grade
    grade = get_grade_by_submission(submission_id)
    
    return SubmissionResponse(
        id=submission['id'],
        assignment_id=submission['assignment_id'],
        filename=submission['filename'],
        status=submission['status'],
        score=grade['score'] if grade else None,
        feedback=grade['feedback'] if grade else None,
        created_at=str(submission['created_at'])
    )


@router.get("/{submission_id}/grade", response_model=GradeResponse)
async def get_grade(submission_id: int):
    """Get grade details for a submission."""
    grade = get_grade_by_submission(submission_id)
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    return GradeResponse(
        id=grade['id'],
        submission_id=grade['submission_id'],
        score=grade['score'],
        breakdown=grade['breakdown'],
        feedback=grade['feedback'],
        citations=grade['citations'],
        created_at=str(grade['created_at'])
    )
