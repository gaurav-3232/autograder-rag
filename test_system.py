#!/usr/bin/env python3
"""
Test script for AutoGrader RAG system
Demonstrates API usage and validates the system is working
"""

import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"


def test_health():
    """Test API health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    assert response.status_code == 200
    print("✅ Health check passed")
    return True


def create_test_assignment():
    """Create a test assignment"""
    print("\n📝 Creating test assignment...")
    
    rubric = {
        "introduction": {
            "description": "Clear introduction with thesis statement",
            "max_points": 20
        },
        "analysis": {
            "description": "Deep analysis with supporting evidence",
            "max_points": 40
        },
        "conclusion": {
            "description": "Strong conclusion that synthesizes main points",
            "max_points": 20
        },
        "citations": {
            "description": "Proper citations and bibliography",
            "max_points": 20
        }
    }
    
    data = {
        "title": "Essay on Climate Change",
        "rubric": rubric
    }
    
    response = requests.post(f"{API_BASE}/assignments/", json=data)
    assert response.status_code == 200
    
    assignment = response.json()
    print(f"✅ Assignment created with ID: {assignment['id']}")
    return assignment


def upload_reference(assignment_id):
    """Upload a reference document"""
    print(f"\n📚 Uploading reference document for assignment {assignment_id}...")
    
    # Create a simple reference document
    reference_text = """
    Climate Change: Key Points
    
    Climate change refers to long-term shifts in global temperatures and weather patterns.
    The primary cause is human activities, particularly burning fossil fuels.
    
    Key impacts include:
    - Rising global temperatures
    - Melting ice caps and glaciers
    - Rising sea levels
    - More extreme weather events
    
    Mitigation strategies:
    - Renewable energy adoption
    - Energy efficiency improvements
    - Carbon capture technologies
    - Reforestation efforts
    
    Citations are essential in academic writing to:
    - Give credit to original authors
    - Allow readers to verify information
    - Demonstrate research depth
    - Avoid plagiarism
    """
    
    # Save to temporary file
    ref_file = Path("/tmp/reference.txt")
    ref_file.write_text(reference_text)
    
    with open(ref_file, 'rb') as f:
        files = {'file': ('reference.txt', f, 'text/plain')}
        response = requests.post(
            f"{API_BASE}/assignments/{assignment_id}/references",
            files=files
        )
    
    assert response.status_code == 200
    result = response.json()
    print(f"✅ Reference uploaded: {result['chunks_created']} chunks indexed")
    return True


def submit_assignment(assignment_id):
    """Submit a test assignment"""
    print(f"\n📤 Submitting work for assignment {assignment_id}...")
    
    # Create a sample submission
    submission_text = """
    Climate Change: A Critical Analysis
    
    Introduction
    Climate change represents one of the most pressing challenges facing humanity today.
    This essay examines the causes, impacts, and potential solutions to this global crisis.
    
    Analysis
    Human activities, particularly the burning of fossil fuels, have released enormous
    quantities of greenhouse gases into the atmosphere. This has led to a warming planet
    with far-reaching consequences including rising sea levels, more frequent extreme
    weather events, and disrupted ecosystems.
    
    The scientific consensus is clear: we must act now to mitigate these impacts through
    renewable energy adoption, improved energy efficiency, and sustainable practices.
    
    Conclusion
    Climate change is not a future problem but a current crisis requiring immediate action.
    By transitioning to renewable energy and implementing sustainable practices, we can
    work toward a more stable climate future.
    
    References
    Smith, J. (2023). Climate Science Today. Academic Press.
    """
    
    # Save to temporary file
    sub_file = Path("/tmp/submission.txt")
    sub_file.write_text(submission_text)
    
    with open(sub_file, 'rb') as f:
        files = {'file': ('submission.txt', f, 'text/plain')}
        response = requests.post(
            f"{API_BASE}/submissions/?assignment_id={assignment_id}",
            files=files
        )
    
    assert response.status_code == 200
    submission = response.json()
    print(f"✅ Submission created with ID: {submission['id']}")
    return submission


def wait_for_grading(submission_id, max_wait=60):
    """Wait for grading to complete"""
    print(f"\n⏳ Waiting for grading to complete...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE}/submissions/{submission_id}")
        submission = response.json()
        
        status = submission['status']
        print(f"   Status: {status}")
        
        if status == 'done':
            print("✅ Grading complete!")
            return True
        elif status == 'error':
            print("❌ Grading failed")
            return False
        
        time.sleep(3)
    
    print("⚠️  Grading timeout")
    return False


def get_grade(submission_id):
    """Get and display grade"""
    print(f"\n📊 Fetching grade for submission {submission_id}...")
    
    response = requests.get(f"{API_BASE}/submissions/{submission_id}/grade")
    
    if response.status_code != 200:
        print("❌ Grade not found")
        return None
    
    grade = response.json()
    
    print("\n" + "="*60)
    print("GRADE REPORT")
    print("="*60)
    print(f"\n🎯 Score: {grade['score']}")
    print(f"\n📋 Breakdown:")
    print(json.dumps(grade['breakdown'], indent=2))
    print(f"\n💬 Feedback:")
    print(grade['feedback'])
    print(f"\n📚 Citations:")
    print(json.dumps(grade['citations'], indent=2))
    print("="*60)
    
    return grade


def main():
    """Run all tests"""
    print("🧪 AutoGrader RAG System Test")
    print("="*60)
    
    try:
        # Test health
        test_health()
        
        # Create assignment
        assignment = create_test_assignment()
        assignment_id = assignment['id']
        
        # Upload reference
        upload_reference(assignment_id)
        
        # Small delay to ensure indexing completes
        time.sleep(2)
        
        # Submit assignment
        submission = submit_assignment(assignment_id)
        submission_id = submission['id']
        
        # Wait for grading
        if wait_for_grading(submission_id):
            # Get and display grade
            get_grade(submission_id)
            
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
        else:
            print("\n❌ Grading failed or timed out")
            print("Check worker logs for details")
            
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
