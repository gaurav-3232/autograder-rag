from app.worker.celery_app import celery_app
from app.db import (
    get_submission, 
    update_submission_status, 
    insert_grade,
    get_assignment
)
from app.services.rag import rag_service
from app.services.llm import llm_service
import traceback


@celery_app.task(name='app.worker.tasks.grade_submission')
def grade_submission(submission_id: int):
    """
    Background task to grade a submission.
    
    Steps:
    1. Retrieve submission from database
    2. Get assignment and rubric
    3. Query RAG for relevant context
    4. Call LLM to grade
    5. Store grade in database
    """
    try:
        # Update status to grading
        update_submission_status(submission_id, 'grading')
        
        # Get submission
        submission = get_submission(submission_id)
        if not submission:
            raise Exception(f"Submission {submission_id} not found")
        
        # Get assignment
        assignment = get_assignment(submission['assignment_id'])
        if not assignment:
            raise Exception(f"Assignment {submission['assignment_id']} not found")
        
        # Extract data
        submission_text = submission['extracted_text']
        rubric = assignment['rubric']
        assignment_id = assignment['id']
        
        # Retrieve relevant context from RAG
        # Use first 500 chars of submission as query
        query_text = submission_text[:500] if len(submission_text) > 500 else submission_text
        context_chunks = rag_service.search_relevant_chunks(
            assignment_id=assignment_id,
            query=query_text,
            top_k=5
        )
        
        # Grade using LLM
        grading_result = llm_service.grade_submission(
            submission_text=submission_text,
            rubric=rubric,
            context_chunks=context_chunks
        )
        
        # Extract grading components
        score = grading_result['score']
        breakdown = grading_result['breakdown']
        feedback = grading_result['feedback']
        citations = grading_result['citations']
        
        # Store grade in database
        insert_grade(
            submission_id=submission_id,
            score=score,
            breakdown=breakdown,
            feedback=feedback,
            citations=citations
        )
        
        # Update status to done
        update_submission_status(submission_id, 'done')
        
        return {
            'status': 'success',
            'submission_id': submission_id,
            'score': score
        }
        
    except Exception as e:
        # Update status to error
        update_submission_status(submission_id, 'error')
        error_msg = f"Grading failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        return {
            'status': 'error',
            'submission_id': submission_id,
            'error': str(e)
        }
