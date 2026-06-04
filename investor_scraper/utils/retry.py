"""
Retry mechanism with exponential backoff and circuit breaker pattern.
"""

import time
from typing import Callable, Any, TypeVar, Optional
from functools import wraps
from datetime import datetime, timedelta
from config import SCRAPER_CONFIG, CIRCUIT_BREAKER_CONFIG
from core.exceptions import CircuitBreakerOpenError
from utils.logger import get_logger


logger = get_logger(__name__)
T = TypeVar("T")


class CircuitBreaker:
    """
    Circuit breaker pattern for handling failing services.
    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(self, name: str):
        self.name = name
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0

    def record_success(self):
        """Record a successful request."""
        if self.state != "closed":
            logger.info(f"🟢 Circuit breaker {self.name}: recovered to CLOSED")
        self.state = "closed"
        self.failure_count = 0
        self.half_open_attempts = 0

    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if (
            self.failure_count
            >= CIRCUIT_BREAKER_CONFIG["failure_threshold"]
        ):
            self.state = "open"
            logger.warning(
                f"🔴 Circuit breaker {self.name}: OPEN "
                f"(failed {self.failure_count}x)"
            )

    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if recovery timeout has passed
            time_since_failure = datetime.utcnow() - self.last_failure_time
            if (
                time_since_failure
                >= timedelta(
                    seconds=CIRCUIT_BREAKER_CONFIG["recovery_timeout"]
                )
            ):
                self.state = "half_open"
                self.half_open_attempts = 0
                logger.info(f"🟡 Circuit breaker {self.name}: HALF_OPEN (recovery attempt)")
                return True
            return False

        if self.state == "half_open":
            if (
                self.half_open_attempts
                >= CIRCUIT_BREAKER_CONFIG["half_open_attempts"]
            ):
                return False
            self.half_open_attempts += 1
            return True

        return False

    def check_open(self):
        """Raise exception if circuit is open."""
        if self.state == "open" and self.can_execute():
            return  # Attempting recovery

        if self.state == "open":
            raise CircuitBreakerOpenError(
                f"Circuit breaker {self.name} is OPEN"
            )


# Global circuit breakers per scraper
_circuit_breakers = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create circuit breaker for a scraper."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]


def retry_with_backoff(
    max_retries: int = SCRAPER_CONFIG["max_retries"],
    backoff_factor: float = SCRAPER_CONFIG["backoff_factor"],
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"⚠️  {func.__name__} failed "
                            f"(attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {wait_time:.1f}s: {str(e)}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"❌ {func.__name__} failed after "
                            f"{max_retries + 1} attempts: {str(e)}"
                        )

            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def with_circuit_breaker(circuit_breaker_name: str):
    """
    Decorator to add circuit breaker pattern to a function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            breaker = get_circuit_breaker(circuit_breaker_name)

            try:
                breaker.check_open()
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise

        return wrapper

    return decorator
