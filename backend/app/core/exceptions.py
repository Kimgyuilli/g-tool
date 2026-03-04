"""Custom exception classes for the Mail Organizer API."""

from __future__ import annotations

from fastapi import HTTPException


class UserNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="User not found")


class MessageNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Message not found")


class ClassificationNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Classification not found")


class AccountNotConnectedException(HTTPException):
    def __init__(self, provider: str = "Google") -> None:
        super().__init__(status_code=401, detail=f"{provider} account not connected")


class NotAuthorizedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Not authorized")


class ClassificationFailedException(HTTPException):
    def __init__(self, detail: str = "Classification failed") -> None:
        super().__init__(status_code=500, detail=detail)


class ExternalServiceException(HTTPException):
    def __init__(self, detail: str = "External service error") -> None:
        super().__init__(status_code=502, detail=detail)


class IMAPAuthenticationException(HTTPException):
    def __init__(self, detail: str = "IMAP authentication failed") -> None:
        super().__init__(status_code=400, detail=detail)
