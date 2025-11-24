"""
Shared exception handling for API routes.

Provides a decorator to translate repository/domain exceptions into HTTP responses,
avoiding duplicated try/except blocks in each endpoint.
"""

from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException
from pydantic import ValidationError

from core.repos.exceptions import AlreadyExists, NotFound


def handle_repo_exceptions(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to map domain exceptions to HTTP errors.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except AlreadyExists as e:
            raise HTTPException(status_code=409, detail=str(e))
        except (ValidationError, ValueError) as e:
            raise HTTPException(status_code=422, detail=str(e))

    return wrapper

