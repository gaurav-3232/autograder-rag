import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()


def get_connection():
    """Create a new database connection."""
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        autocommit=False
    )


@contextmanager
def get_db_cursor(dictionary=True):
    """Context manager for database operations."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def init_database():
    """Initialize database schema."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        rubric JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at)
    );

    CREATE TABLE IF NOT EXISTS submissions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        assignment_id INT NOT NULL,
        filename VARCHAR(255) NOT NULL,
        s3_key VARCHAR(500) NOT NULL,
        extracted_text LONGTEXT,
        status ENUM('queued', 'grading', 'done', 'error') DEFAULT 'queued',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
        INDEX idx_assignment_id (assignment_id),
        INDEX idx_status (status),
        INDEX idx_created_at (created_at)
    );

    CREATE TABLE IF NOT EXISTS grades (
        id INT AUTO_INCREMENT PRIMARY KEY,
        submission_id INT NOT NULL UNIQUE,
        score INT NOT NULL,
        breakdown JSON NOT NULL,
        feedback TEXT NOT NULL,
        citations JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
        INDEX idx_submission_id (submission_id),
        INDEX idx_created_at (created_at)
    );
    """
    
    with get_db_cursor() as cursor:
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)


def execute_query(query: str, params: tuple = None, fetch_one: bool = False, 
                  fetch_all: bool = False) -> Optional[Any]:
    """Execute a SQL query with parameters."""
    with get_db_cursor() as cursor:
        cursor.execute(query, params or ())
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            return cursor.lastrowid


def insert_assignment(title: str, rubric: dict) -> int:
    """Insert a new assignment."""
    query = """
        INSERT INTO assignments (title, rubric)
        VALUES (%s, %s)
    """
    import json
    return execute_query(query, (title, json.dumps(rubric)))


def get_assignment(assignment_id: int) -> Optional[Dict]:
    """Get assignment by ID."""
    query = "SELECT * FROM assignments WHERE id = %s"
    result = execute_query(query, (assignment_id,), fetch_one=True)
    if result:
        import json
        result['rubric'] = json.loads(result['rubric'])
    return result


def get_all_assignments() -> List[Dict]:
    """Get all assignments."""
    query = "SELECT * FROM assignments ORDER BY created_at DESC"
    results = execute_query(query, fetch_all=True)
    import json
    for result in results:
        result['rubric'] = json.loads(result['rubric'])
    return results


def insert_submission(assignment_id: int, filename: str, s3_key: str, 
                     extracted_text: str) -> int:
    """Insert a new submission."""
    query = """
        INSERT INTO submissions (assignment_id, filename, s3_key, extracted_text, status)
        VALUES (%s, %s, %s, %s, 'queued')
    """
    return execute_query(query, (assignment_id, filename, s3_key, extracted_text))


def get_submission(submission_id: int) -> Optional[Dict]:
    """Get submission by ID."""
    query = "SELECT * FROM submissions WHERE id = %s"
    return execute_query(query, (submission_id,), fetch_one=True)


def get_submissions_by_assignment(assignment_id: int) -> List[Dict]:
    """Get all submissions for an assignment."""
    query = """
        SELECT s.*, g.score, g.feedback 
        FROM submissions s
        LEFT JOIN grades g ON s.id = g.submission_id
        WHERE s.assignment_id = %s
        ORDER BY s.created_at DESC
    """
    return execute_query(query, (assignment_id,), fetch_all=True)


def update_submission_status(submission_id: int, status: str):
    """Update submission status."""
    query = "UPDATE submissions SET status = %s WHERE id = %s"
    execute_query(query, (status, submission_id))


def insert_grade(submission_id: int, score: int, breakdown: dict, 
                feedback: str, citations: list) -> int:
    """Insert a new grade."""
    query = """
        INSERT INTO grades (submission_id, score, breakdown, feedback, citations)
        VALUES (%s, %s, %s, %s, %s)
    """
    import json
    return execute_query(query, (
        submission_id,
        score,
        json.dumps(breakdown),
        feedback,
        json.dumps(citations)
    ))


def get_grade_by_submission(submission_id: int) -> Optional[Dict]:
    """Get grade for a submission."""
    query = "SELECT * FROM grades WHERE submission_id = %s"
    result = execute_query(query, (submission_id,), fetch_one=True)
    if result:
        import json
        result['breakdown'] = json.loads(result['breakdown'])
        result['citations'] = json.loads(result['citations'])
    return result
