"""Exception types for CNBE-32."""


class CNBEError(Exception):
    """Base exception for CNBE-32 errors."""


class CNBEValueError(CNBEError, ValueError):
    """Raised when a CNBE-32 field value is outside its valid range."""


class CNBEDatabaseError(CNBEError):
    """Raised when the CNBE-32 database cannot be found or queried."""
