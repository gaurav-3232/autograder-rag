from minio import Minio
from minio.error import S3Error
from io import BytesIO
from app.config import get_settings
import uuid

settings = get_settings()


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_file(self, file_data: bytes, filename: str) -> str:
        """Upload a file and return its S3 key."""
        file_extension = filename.split('.')[-1] if '.' in filename else 'txt'
        s3_key = f"{uuid.uuid4()}.{file_extension}"
        
        try:
            self.client.put_object(
                self.bucket,
                s3_key,
                BytesIO(file_data),
                length=len(file_data),
                content_type=self._get_content_type(file_extension)
            )
            return s3_key
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")
    
    def download_file(self, s3_key: str) -> bytes:
        """Download a file from storage."""
        try:
            response = self.client.get_object(self.bucket, s3_key)
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")
    
    def delete_file(self, s3_key: str):
        """Delete a file from storage."""
        try:
            self.client.remove_object(self.bucket, s3_key)
        except S3Error as e:
            print(f"Error deleting file: {e}")
    
    def _get_content_type(self, extension: str) -> str:
        """Get content type based on file extension."""
        content_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
        }
        return content_types.get(extension.lower(), 'application/octet-stream')


storage_service = StorageService()
