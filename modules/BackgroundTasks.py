from io import StringIO
from logging import Logger
import sys
from typing import Any, Callable, Iterator, NamedTuple

if sys.version_info >= (3, 10): # pragma: no cover
    from typing import ParamSpec
else: # pragma: no cover
    from typing_extensions import ParamSpec

import fastapi
from rich.console import Console
from rich.traceback import Traceback
import starlette.background

from modules.Debug2 import logger as log


class _Task(NamedTuple):
    id: int
    task: Callable


class TaskQueue:
    """
    This class encapsulates queued tasks which have yet to be executed.
    A "Task" is a unique ID of the `BackgroundTask` object yet executed,
    and the function which will be called.
    """

    def __init__(self) -> None:
        """Initialize a new (empty) task queue."""

        self.tasks: list[_Task] = []


    def __iter__(self) -> Iterator[_Task]:
        """Iterate through this object's pending tasks."""

        yield from self.tasks


    def add_task(self,
            task: starlette.background.BackgroundTask,
            task_function: Callable,
        ) -> None:
        """
        Add the given task to the queue, indicating it needs to be
        executed.

        Args:
            task: BackgroundTask to add to the queue.
            task_function: Function which will be executed when this
                task will finish.
        """

        self.tasks.append((id(task), task_function))


    def remove_task(self, task: starlette.background.BackgroundTask) -> None:
        """
        Remove the task from this queue. This should only be done after
        the task has finished executing.

        Args:
            task: BackgroundTask to remove.
        """

        found = False
        task_id = id(task)
        for index, (this_task_id, _) in enumerate(self.tasks):
            if task_id == this_task_id:
                found = True
                break

        if found:
            self.tasks.pop(index)
task_queue = TaskQueue()

"""
Which modules (and files) should be suppressed in traceback printing
"""
import alembic, anyio, fastapi, sqlalchemy, starlette, tmdbapis, tenacity
TracebackSuppressedPackages = [
    alembic,
    anyio,
    fastapi,
    sqlalchemy,
    starlette,
    tenacity,
    tmdbapis,
    'app-main.py',
]

P = ParamSpec("P")

class BackgroundTasks(starlette.background.BackgroundTasks):
    async def __call__(self) -> None:
        """
        "Call" this object - this runs all queued tasks and removes them
        from global task queue.
        """

        for task in self.tasks:
            await task()
            task_queue.remove_task(task)


    def add_task(self,
            func: Callable[P, Any],
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> None:
        """
        Modified implementation of
        `starlette.background.BackgroundTasks.add_task` which handles
        and adds better logging to uncaught exceptions in the
        encapsulated function.
        """

        def new_func(*args_: P.args, **kwargs_: P.kwargs) -> None:
            try:
                func(*args_, **kwargs_)
            except Exception:
                # Grab logger if present in kwargs of wrapped function
                logger = log
                if ('log' in kwargs_
                    and hasattr(kwargs_['log'], 'error')
                    and callable(kwargs_['log'].error)):
                    logger: Logger = kwargs['log']

                # Create Console to print rich Traceback
                console = Console(file=StringIO())
                console.print(
                    Traceback(
                        width=120,
                        show_locals=True,
                        locals_max_length=512,
                        locals_max_string=512,
                        extra_lines=2,
                        indent_guides=False,
                        suppress=TracebackSuppressedPackages,
                    )
                )

                # Log traceback of failed Task
                logger.error(
                    f'BackgroundTask {func.__name__}() failed:\n'
                    f'{console.file.getvalue()}'
                )

        # Original add_task creates a BackgroundTask object and adds to
        # tasks queue
        task = starlette.background.BackgroundTask(new_func, *args, **kwargs)
        self.tasks.append(task)
        task_queue.add_task(task, func)

# Monkey-patch FastAPI injections
fastapi.BackgroundTasks.add_task = BackgroundTasks.add_task
fastapi.BackgroundTasks.__call__ = BackgroundTasks.__call__
log.trace('Patched FastAPI.BackgroundTasks')
