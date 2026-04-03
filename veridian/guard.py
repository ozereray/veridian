import time
import asyncio
import functools
import inspect
from typing import Callable, Type, Tuple
from .logger import get_logger

logger = get_logger()

def guard(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    fallback=None,
):
    def decorator(func: Callable):
        # Fonksiyonun async olup olmadığını kontrol et
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exc = None
                for attempt in range(1, max_retries + 1):
                    try:
                        result = await func(*args, **kwargs)
                        if attempt > 1:
                            logger.info(f"'{func.__name__}' succeeded on attempt {attempt}")
                        return result
                    except exceptions as e:
                        last_exc = e
                        logger.warning(f"'{func.__name__}' attempt {attempt}/{max_retries} failed: {e}")
                        if attempt < max_retries:
                            await asyncio.sleep(delay) # Async bekleme
                
                logger.error(f"'{func.__name__}' exhausted all {max_retries} retries.")
                if fallback is not None:
                    return fallback
                if last_exc is not None:
                    raise last_exc
                raise RuntimeError("Execution failed without raising an exception.")
            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exc = None
                for attempt in range(1, max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        if attempt > 1:
                            logger.info(f"'{func.__name__}' succeeded on attempt {attempt}")
                        return result
                    except exceptions as e:
                        last_exc = e
                        logger.warning(f"'{func.__name__}' attempt {attempt}/{max_retries} failed: {e}")
                        if attempt < max_retries:
                            time.sleep(delay) # Normal bekleme
                
                logger.error(f"'{func.__name__}' exhausted all {max_retries} retries.")
                if fallback is not None:
                    return fallback
                if last_exc is not None:
                    raise last_exc
                raise RuntimeError("Execution failed without raising an exception.")
            return sync_wrapper

    return decorator