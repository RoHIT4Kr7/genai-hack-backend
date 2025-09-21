"""
Completely minimal auth router with zero external dependencies beyond FastAPI stdlib.
This is designed to prove deployment and endpoint registration.
"""

from fastapi import APIRouter
from datetime import datetime
import os
import json

# Create router - no external dependencies
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/ping")
def auth_ping():
    """Canary endpoint to prove which revision is serving traffic"""
    return {
        "status": "success",
        "auth_implementation": "zero_deps_v1",
        "revision": os.getenv("K_REVISION", "unknown"),
        "service": os.getenv("K_SERVICE", "unknown"),
        "timestamp": datetime.utcnow().isoformat(),
        "message": "ZERO_DEPS_ROUTER_DEPLOYED_2025_09_22",
        "test_result": "ENDPOINT_DEFINITELY_WORKING",
    }


@router.get("/test")
def auth_test():
    """Secondary test endpoint"""
    return {
        "status": "working",
        "implementation": "zero_dependencies",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/debug")
def auth_debug():
    """Debug endpoint with basic environment info"""
    return {
        "environment_vars": {
            "K_REVISION": os.getenv("K_REVISION", "not_set"),
            "K_SERVICE": os.getenv("K_SERVICE", "not_set"),
        },
        "timestamp": datetime.utcnow().isoformat(),
        "message": "MINIMAL_ROUTER_ACTIVE",
    }
