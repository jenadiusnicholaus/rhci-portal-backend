import io
import logging
import base64
import uuid
import time
import mimetypes
from django.core.files.base import ContentFile
from rest_framework import serializers

logger = logging.getLogger(__name__)

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class Base64AnyFileField(serializers.FileField):
    """Custom Base64 file field that accepts any file type with validation."""

    ALLOWED_TYPES = [
        "pdf",
        "jpeg",
        "png",
        "jpg",
        "doc",
        "docx",
    ]
    MIME_TYPES = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    # Standardized file size limits by document type (in bytes)
    DOCUMENT_SIZE_LIMITS = {
        # Valid document types from models.py
        'registration': 5 * 1024 * 1024,          # 5MB - Registration certificates
        'practice': 5 * 1024 * 1024,              # 5MB - Practice licenses
        'academic': 5 * 1024 * 1024,              # 5MB - Academic certificates
        'other': 5 * 1024 * 1024,                 # 5MB - Other supporting documents
        
        # Legacy document types (for backward compatibility)
        'roll_number_cert': 5 * 1024 * 1024,      # 5MB
        'practice_license': 5 * 1024 * 1024,      # 5MB
        'work_certificate': 5 * 1024 * 1024,      # 5MB
        'professional_cert': 5 * 1024 * 1024,    # 5MB
        'employment_letter': 3 * 1024 * 1024,    # 3MB
        'organization_cert': 5 * 1024 * 1024,      # 5MB
        'business_license': 5 * 1024 * 1024,      # 5MB
        'registration_cert': 5 * 1024 * 1024,     # 5MB
        'firm_documents': 10 * 1024 * 1024,      # 10MB
        'id_document': 2 * 1024 * 1024,           # 2MB
    }
    
    # Default maximum size
    DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(self, *args, **kwargs):
        self.allowed_types = kwargs.pop("allowed_types", None)
        self.max_file_size = kwargs.pop("max_file_size", self.DEFAULT_MAX_FILE_SIZE)
        self.document_type = kwargs.pop("document_type", None)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            # Handle empty string - return None to indicate no file
            if data == "" or data is None:
                return None

            if isinstance(data, str) and data.startswith("data:"):
                # Get format and base64 data from the dataURL
                format, datastr = data.split(";base64,")
                ext = format.split("/")[-1]

                # Generate random filename
                filename = f"{uuid.uuid4()}.{ext}"

                # Decode base64
                binary_data = base64.b64decode(datastr)

                # Validate file size - use document-type-specific limit if available
                file_size = len(binary_data)
                max_size = self.max_file_size
                
                # If document_type is provided, use specific limit for that document type
                if self.document_type and self.document_type in self.DOCUMENT_SIZE_LIMITS:
                    max_size = self.DOCUMENT_SIZE_LIMITS[self.document_type]
                
                if file_size > max_size:
                    max_size_mb = max_size / (1024 * 1024)
                    current_size_mb = file_size / (1024 * 1024)
                    document_type_info = f" for {self.document_type}" if self.document_type else ""
                    raise serializers.ValidationError(
                        {
                            "file_size": f"File size is {current_size_mb:.2f}MB. Maximum allowed size{document_type_info} is {max_size_mb:.0f}MB."
                        }
                    )

                # Check file type
                detected_file_type = None
                if HAS_MAGIC:
                    # Use python-magic if available
                    detected_file_type = magic.from_buffer(binary_data, mime=True)
                else:
                    # Fallback to mimetypes
                    detected_file_type, _ = mimetypes.guess_type(filename)

                # Get the file extension from the data URL format
                actual_extension = ext.lower()

                # Validate against allowed types if specified
                allowed_types = self.allowed_types or self.ALLOWED_TYPES
                if detected_file_type and detected_file_type not in [
                    self.MIME_TYPES.get(t, t) for t in allowed_types
                ]:
                    raise serializers.ValidationError(
                        {
                            "file_format": f"File format '{actual_extension}' is not allowed. Allowed formats: {', '.join(allowed_types)}. Detected type: {detected_file_type}"
                        }
                    )

                # Additional check for extension vs detected type mismatch
                expected_mime = self.MIME_TYPES.get(actual_extension)
                if (
                    expected_mime
                    and detected_file_type
                    and expected_mime != detected_file_type
                ):
                    raise serializers.ValidationError(
                        {
                            "file_format": f"File extension '{actual_extension}' doesn't match detected file type '{detected_file_type}'. Expected: {expected_mime}"
                        }
                    )

                return ContentFile(binary_data, name=filename)

            return super().to_internal_value(data)
        except serializers.ValidationError:
            # Re-raise validation errors as-is to preserve specific error messages
            raise
        except ValueError as e:
            logger.error(f"ValueError processing Base64 file: {e}")
            if "Invalid base64" in str(e):
                raise serializers.ValidationError(
                    {
                        "file_data": "Invalid base64 encoding. Please check your file data."
                    }
                ) from e
            raise serializers.ValidationError(
                {"file_data": f"Data processing error: {str(e)}"}
            ) from e
        except Exception as e:
            logger.error(f"Error processing Base64 file: {e}")
            raise serializers.ValidationError(
                {"file_upload": f"File upload failed: {str(e)}"}
            ) from e
