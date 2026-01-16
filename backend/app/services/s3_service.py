"""
S3 Service for handling file uploads and management.

This service provides a centralized interface for uploading, deleting,
and managing assets (images and videos) in S3-compatible storage.
"""

import os
import uuid
import mimetypes
from typing import Optional, Tuple, Dict, Any
from werkzeug.utils import secure_filename
from flask import current_app
import boto3
from botocore.exceptions import ClientError, BotoCoreError


class S3ServiceError(Exception):
    """Custom exception for S3 service errors."""
    pass


class S3Service:
    """Service for managing S3 file operations."""
    
    def __init__(self):
        """Initialize S3 client with configuration."""
        self.aws_access_key_id = current_app.config.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = current_app.config.get('AWS_REGION', 'us-east-1')
        self.bucket_name = current_app.config.get('S3_BUCKET_NAME', 'studio-os-assets')
        self.bucket_url = current_app.config.get('S3_BUCKET_URL', '')
        
        # File size limits
        self.max_image_size = current_app.config.get('MAX_IMAGE_SIZE', 10 * 1024 * 1024)
        self.max_video_size = current_app.config.get('MAX_VIDEO_SIZE', 100 * 1024 * 1024)
        
        # Allowed extensions
        self.allowed_image_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
        self.allowed_video_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', ['mp4', 'mov', 'avi', 'webm'])
        
        # Initialize S3 client
        self._s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize boto3 S3 client."""
        try:
            if self.aws_access_key_id and self.aws_secret_access_key:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
            else:
                # Use default credentials (IAM role, environment, etc.)
                self._s3_client = boto3.client('s3', region_name=self.aws_region)
            
            # Test connection by checking bucket
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                raise S3ServiceError(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise S3ServiceError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise S3ServiceError(f"Failed to initialize S3 client: {str(e)}")
        except BotoCoreError as e:
            raise S3ServiceError(f"Failed to initialize S3 client: {str(e)}")
        except Exception as e:
            # In development, allow missing credentials (will fail on actual upload)
            current_app.logger.warning(f"S3 client initialization warning: {str(e)}")
            if not current_app.config.get('DEBUG'):
                raise
    
    def _get_s3_client(self):
        """Get S3 client, initializing if necessary."""
        if self._s3_client is None:
            self._initialize_client()
        return self._s3_client
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _validate_file_type(self, filename: str, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file type based on extension.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        ext = self._get_file_extension(filename)
        
        if file_type == 'image':
            if ext not in self.allowed_image_extensions:
                return False, f"Invalid image type. Allowed: {', '.join(self.allowed_image_extensions)}"
        elif file_type == 'video':
            if ext not in self.allowed_video_extensions:
                return False, f"Invalid video type. Allowed: {', '.join(self.allowed_video_extensions)}"
        else:
            return False, f"Invalid file_type. Must be 'image' or 'video'"
        
        return True, None
    
    def _validate_file_size(self, file_size: int, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        max_size = self.max_image_size if file_type == 'image' else self.max_video_size
        max_size_mb = max_size / (1024 * 1024)
        
        if file_size > max_size:
            return False, f"File size exceeds maximum allowed size of {max_size_mb:.1f}MB"
        
        return True, None
    
    def validate_file(self, file, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload.
        
        Args:
            file: File object (from request.files)
            file_type: 'image' or 'video'
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "No file provided"
        
        # Validate file type
        is_valid, error = self._validate_file_type(file.filename, file_type)
        if not is_valid:
            return False, error
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        is_valid, error = self._validate_file_size(file_size, file_type)
        if not is_valid:
            return False, error
        
        return True, None
    
    def _generate_s3_key(self, studio_id: str, file_type: str, context: str, 
                        filename: str, class_id: Optional[str] = None) -> str:
        """
        Generate S3 key (path) for file.
        
        Args:
            studio_id: Studio ID
            file_type: 'image' or 'video'
            context: 'studio' or 'class'
            filename: Original filename
            class_id: Class ID (required if context='class')
        
        Returns:
            S3 key (path)
        """
        # Sanitize filename
        safe_filename = secure_filename(filename)
        
        # Generate unique identifier
        file_uuid = str(uuid.uuid4())
        
        # Build path based on context
        if context == 'studio':
            folder = 'photos' if file_type == 'image' else 'videos'
            key = f"studios/{studio_id}/{folder}/{file_uuid}-{safe_filename}"
        elif context == 'class':
            if not class_id:
                raise ValueError("class_id is required when context='class'")
            folder = 'images' if file_type == 'image' else 'videos'
            key = f"classes/{studio_id}/{class_id}/{folder}/{file_uuid}-{safe_filename}"
        else:
            raise ValueError(f"Invalid context: {context}. Must be 'studio' or 'class'")
        
        return key
    
    def upload_file(self, file, file_type: str, studio_id: str, 
                   context: str = 'studio', class_id: Optional[str] = None,
                   content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload file to S3.
        
        Args:
            file: File object (from request.files)
            file_type: 'image' or 'video'
            studio_id: Studio ID
            context: 'studio' or 'class'
            class_id: Class ID (required if context='class')
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Dict with 'url', 'key', 'type', 'size', 'content_type'
        
        Raises:
            S3ServiceError: If upload fails
        """
        # Validate file
        is_valid, error = self.validate_file(file, file_type)
        if not is_valid:
            raise S3ServiceError(error)
        
        # Generate S3 key
        try:
            s3_key = self._generate_s3_key(studio_id, file_type, context, file.filename, class_id)
        except ValueError as e:
            raise S3ServiceError(str(e))
        
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                # Default based on file type
                content_type = f"image/{self._get_file_extension(file.filename)}" if file_type == 'image' else f"video/{self._get_file_extension(file.filename)}"
        
        # Upload to S3
        try:
            s3_client = self._get_s3_client()
            # Build ExtraArgs without ACL if bucket doesn't support it
            extra_args = {
                'ContentType': content_type,
            }
            # Only add ACL if bucket supports it (some buckets have ACLs disabled)
            # Files will be accessible based on bucket policy instead
            # extra_args['ACL'] = 'public-read'
            
            s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            raise S3ServiceError(f"Failed to upload file to S3: {error_code} - {str(e)}")
        except Exception as e:
            raise S3ServiceError(f"Unexpected error during upload: {str(e)}")
        
        # Generate URL
        if self.bucket_url:
            # Use custom bucket URL (CDN, custom domain, etc.)
            url = f"{self.bucket_url.rstrip('/')}/{s3_key}"
        else:
            # Use standard S3 URL
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
        
        return {
            'url': url,
            'key': s3_key,
            'type': file_type,
            'size': file_size,
            'content_type': content_type,
            'filename': file.filename
        }
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 key (path) of file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            s3_client = self._get_s3_client()
            s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            current_app.logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error during delete: {str(e)}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for temporary access to private file.
        
        Args:
            s3_key: S3 key (path) of file
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL or None if generation fails
        """
        try:
            s3_client = self._get_s3_client()
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            current_app.logger.error(f"Failed to generate presigned URL: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            return None
    
    def is_s3_url(self, url: str) -> bool:
        """
        Check if URL is from our S3 bucket.
        
        Args:
            url: URL to check
        
        Returns:
            True if URL is from our S3 bucket
        """
        if not url:
            return False
        
        # Check if URL contains our bucket name or bucket URL
        bucket_url_patterns = [
            f"{self.bucket_name}.s3",
            self.bucket_url
        ]
        
        return any(pattern in url for pattern in bucket_url_patterns if pattern)
    
    def extract_s3_key_from_url(self, url: str) -> Optional[str]:
        """
        Extract S3 key from URL.
        
        Args:
            url: S3 URL
        
        Returns:
            S3 key or None if URL is not from our bucket
        """
        if not self.is_s3_url(url):
            return None
        
        # Extract key from URL
        # Format: https://bucket.s3.region.amazonaws.com/key
        # or: https://bucket-url/key
        try:
            if self.bucket_url and url.startswith(self.bucket_url):
                return url.replace(self.bucket_url.rstrip('/') + '/', '')
            elif f"{self.bucket_name}.s3" in url:
                # Standard S3 URL
                parts = url.split(f"{self.bucket_name}.s3")
                if len(parts) > 1:
                    key_part = parts[1].split('.amazonaws.com/')
                    if len(key_part) > 1:
                        return key_part[1]
        except Exception:
            pass
        
        return None
    
    def upload_buffer(self, buffer, s3_key: str, content_type: str) -> Optional[str]:
        """
        Upload a BytesIO buffer directly to S3.
        
        Args:
            buffer: BytesIO object with file data
            s3_key: Full S3 key (path/filename)
            content_type: MIME type of the file
        
        Returns:
            Public URL of the uploaded file, or None if failed
        """
        try:
            buffer.seek(0)  # Ensure buffer is at start
            s3_client = self._get_s3_client()
            
            extra_args = {
                'ContentType': content_type,
            }
            
            s3_client.upload_fileobj(
                buffer,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            if self.bucket_url:
                url = f"{self.bucket_url.rstrip('/')}/{s3_key}"
            else:
                url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            return url
            
        except Exception as e:
            current_app.logger.error(f"Failed to upload buffer to S3: {str(e)}")
            return None


# Singleton instance
_s3_service = None


def get_s3_service() -> S3Service:
    """Get S3 service instance (singleton)."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
