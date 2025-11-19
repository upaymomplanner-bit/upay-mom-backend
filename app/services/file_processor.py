from fastapi import UploadFile, HTTPException


class FileProcessor:
    """Service for processing and validating uploaded files."""

    ALLOWED_EXTENSIONS = {".txt", ".pdf"}
    MIME_TYPE_MAP = {"txt": "text/plain", "pdf": "application/pdf"}

    @staticmethod
    def validate_file(file: UploadFile, max_size: int) -> None:
        """
        Validate uploaded file type and size.

        Args:
            file: The uploaded file
            max_size: Maximum allowed file size in bytes

        Raises:
            HTTPException: If file is invalid
        """
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_ext = file.filename.lower().split(".")[-1]
        if f".{file_ext}" not in FileProcessor.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}",
            )

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """
        Get MIME type from filename extension.

        Args:
            filename: Name of the file

        Returns:
            MIME type string
        """
        file_ext = filename.lower().split(".")[-1]
        return FileProcessor.MIME_TYPE_MAP.get(file_ext, "application/octet-stream")
