from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError, ConfigDict


class ValidationErrorDetail(BaseModel):
    location: str
    message: str
    error_type: str
    context: Optional[Dict[str, Any]] = None


class APIValidationError(BaseModel):
    errors: List[ValidationErrorDetail]
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "errors": [
                    {
                        "origin": "body -> url",
                        "message": "invalid or missing URL scheme",
                        "error_type": "value_error.url.scheme",
                    },
                ],
            },
        }
    )

    @classmethod
    def from_pydantic(cls, exc: ValidationError):
        return cls(
            errors=[
                ValidationErrorDetail(
                    location=" -> ".join(map(str, err["loc"])),
                    message=err["msg"],
                    error_type=err["type"],
                    context=err.get("ctx"),
                )
                for err in exc.errors()
            ],
        )


class CommonHTTPError(BaseModel):
    """JSON response model for errors raised by :class:`starlette.HTTPException`."""

    message: str
    extra: Optional[Dict[str, Any]] = None
