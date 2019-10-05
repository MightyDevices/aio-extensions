import asyncio as aio
import contextlib

# wait for tasks to end and cancel those that are still pending
async def wait_cancel_others(fs, *args, **kwargs):
    # this may throw exceptions when cancelled
    try:
        # return the set of done and pending tasks
        return await aio.wait(fs, *args, **kwargs)
    # cleanup
    finally:
        # cancel all the tasks that are not done
        for task in [t for t in fs if not t.done()]:
            # cancel the task
            task.cancel()
            # this will throw cancelled error when we do the await
            with contextlib.suppress(aio.CancelledError):
                await task
