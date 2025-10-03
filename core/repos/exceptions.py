"""
Custom exceptions.

These exceptions are used to handle specific error cases in the repository layer.
"""

class AlreadyExists(Exception):
    """Raised when attempting to create a resource that already exists."""
    pass

class NotFound(Exception):
    """Raised when a requested resource cannot be found."""
    pass