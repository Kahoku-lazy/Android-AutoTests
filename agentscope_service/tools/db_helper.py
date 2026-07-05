"""Database helper — bridges async AgentScope tools with synchronous Django ORM.

AgentScope 2.0 runs tool .call() methods in an async event loop. Django ORM
operations are synchronous and cannot be called directly from async context
without raising: "You cannot call this from an async context - use a thread
or sync_to_async."

This module provides `run_sync()` — a thin wrapper around asgiref's
sync_to_async that executes synchronous Django ORM code in a thread pool,
with a timeout to prevent zombie tasks from blocking the agent forever.

Usage:
    from .db_helper import run_sync

    # For querysets:
    devices = await run_sync(lambda: list(Device.objects.filter(status='online')))

    # For single objects:
    device = await run_sync(lambda: Device.objects.filter(serial=serial).first())

    # For create/update:
    record = await run_sync(lambda: TestRunRecord.objects.create(**fields))

Note: On timeout or error, run_sync RAISES an exception (does not return a
string). Callers should wrap in try/except if they want to return a graceful
error message to the AI; otherwise the exception propagates to AgentScope
which reports it as a tool failure.
"""
import asyncio
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger('agentscope')

# Default timeout: 8 seconds. Must be below AgentScope's 10s background-task
# threshold to prevent zombie tasks from blocking the message bus.
_DEFAULT_TIMEOUT = 8.0


class DBOperationTimeout(TimeoutError):
    """Raised when a DB operation exceeds the timeout limit."""


def run_sync(func, timeout=_DEFAULT_TIMEOUT):
    """Run a synchronous callable in a thread, returning an awaitable.

    Wraps sync_to_async with a timeout guard. On timeout or error, raises
    an exception (does NOT return a string), so callers receive the correct
    type or an exception — never a silent type mismatch.

    Args:
        func: A zero-argument callable (typically a lambda wrapping Django ORM code).
        timeout: Maximum seconds to wait before raising DBOperationTimeout.

    Returns:
        The return value of func, awaited from the calling async context.

    Raises:
        DBOperationTimeout: If the operation exceeds `timeout` seconds.
        Exception: Any exception raised by func itself.

    Example:
        devices = await run_sync(lambda: list(Device.objects.all()))
    """
    async def _wrapped():
        coro = sync_to_async(func, thread_sensitive=True)()
        return await asyncio.wait_for(coro, timeout=timeout)

    return _wrapped()
