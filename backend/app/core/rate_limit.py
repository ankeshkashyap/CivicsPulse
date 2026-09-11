import time
from typing import Dict, List
from fastapi import HTTPException, status

# Sliding window rate limit: max 5 submissions per 10 minutes (600 seconds)
COMPLAINT_RATE_LIMIT_MAX = 5
COMPLAINT_RATE_LIMIT_WINDOW_SECONDS = 600

# In-memory timestamp store: key -> list of float epoch timestamps
_complaint_timestamps: Dict[str, List[float]] = {}


def check_complaint_rate_limit(identifier: str) -> None:
    """
    Enforces a process-local sliding-window rate limit on complaint creation.
    Raises HTTP 429 Too Many Requests if the identifier exceeds the quota.
    
    Architectural Note:
    This limiter is process-local and in-memory for the single-node deployment.
    Distributed Redis coordination can be integrated in multi-worker environments.
    """
    now = time.time()
    cutoff = now - COMPLAINT_RATE_LIMIT_WINDOW_SECONDS

    # Clean old entries for this identifier
    timestamps = [ts for ts in _complaint_timestamps.get(identifier, []) if ts > cutoff]

    if len(timestamps) >= COMPLAINT_RATE_LIMIT_MAX:
        oldest_active = timestamps[0]
        retry_after = int(oldest_active + COMPLAINT_RATE_LIMIT_WINDOW_SECONDS - now) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. You may submit up to {COMPLAINT_RATE_LIMIT_MAX} complaints per {COMPLAINT_RATE_LIMIT_WINDOW_SECONDS // 60} minutes.",
            headers={"Retry-After": str(max(1, retry_after))},
        )

    timestamps.append(now)
    _complaint_timestamps[identifier] = timestamps


def reset_complaint_rate_limits() -> None:
    """Clears rate limit state for unit tests."""
    _complaint_timestamps.clear()
