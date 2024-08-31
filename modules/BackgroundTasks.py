from io import StringIO
from logging import Logger
import sys
from typing import Any, Callable, Iterator, Literal, NamedTuple

from sqlalchemy.orm.session import Session

from app.database.session import Base as DatabaseBase, SessionLocal

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


    def __bool__(self) -> bool:
        """Whether this task queue has any pending tasks."""

        return len(self.tasks) > 0


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

class DependencyInjector:
    def __init__(self, args: tuple, kwargs: dict) -> None:
        """
        Initialize the injector for a function with the given arguments.
        Any SQL database connections will be removed and then re-
        injected with the `args` and `kwargs` properties of this object.

        Args:
            args: Positional arguments which will be passed to the
                wrapped function.
            kwargs: Keyword argument which will be passed to the wrapped
                function.
        """

        # Determine how many dependencies will require a Session be
        # instantiated
        is_dependency = lambda a: isinstance(a, (Session, DatabaseBase))
        self.multiple_db_dependencies = (
            sum(1 for arg in args if is_dependency(arg)) \
            + sum(1 for v in kwargs.values() if is_dependency(v))
            > 1
        )

        # Store data to reconstruct each type of dependency argument
        self._args: list[tuple[Literal['Database', 'Model', 'Other'], Any]] = []
        for arg in args:
            if isinstance(arg, Session):
                self._args.append(('Database', SessionLocal))
            elif isinstance(arg, DatabaseBase):
                self._args.append(('Model', (arg.__class__, arg.id)))
            else:
                self._args.append(('Other', arg))

        self._kwargs: dict[str, tuple[Literal['Database', 'Model', 'Other'], Any]] = {}
        for key, val in kwargs.items():
            if isinstance(val, Session):
                self._kwargs[key] = ('Database', SessionLocal)
            elif isinstance(val, DatabaseBase):
                self._kwargs[key] = ('Model', (val.__class__, val.id))
            else:
                self._kwargs[key] = ('Other', val)

    @property
    def args(self) -> tuple:
        """
        Post re-injected positional arguments with a re-initialized SQL
        DB connection (if present).
        """

        # Single (or no) DB connections, return post-injected args
        if not self.multiple_db_dependencies:
            args = []
            for arg_type, arg in self._args:
                if arg_type == 'Database':
                    args.append(SessionLocal())
                elif arg_type == 'Model':
                    obj_class, obj_id = arg
                    args.append(SessionLocal().query(obj_class).get(obj_id))
                else:
                    args.append(arg)

            return tuple(args)

        # More than one database connection, instantiate singular
        # Session for use by all associated Dependencies
        db = SessionLocal()
        args = []
        for arg_type, arg in self._args:
            if arg_type == 'Database':
                args.append(db)
            elif arg_type == 'Model':
                obj_class, obj_id = arg
                args.append(db.query(obj_class).get(obj_id))
            else:
                args.append(arg)

        return tuple(args)


    @property
    def kwargs(self) -> dict:
        """
        Post re-injected keyword arguments with a re-initialized SQL DB
        connection (if present).
        """

        # Single (or no) DB connections, return post-injected args
        if not self.multiple_db_dependencies:
            kwargs = {}
            for key, (arg_type, arg) in self._kwargs.items():
                if arg_type == 'Database':
                    kwargs[key] = SessionLocal()
                elif arg_type == 'Model':
                    obj_class, obj_id = arg
                    kwargs[key] = SessionLocal().query(obj_class).get(obj_id)
                else:
                    kwargs[key] = arg

            return kwargs

        # More than one database connection, instantiate singular
        # Session for use by all associated Dependencies
        db = SessionLocal()
        kwargs = {}
        for key, (arg_type, arg) in self._kwargs.items():
            if arg_type == 'Database':
                kwargs[key] = db
            elif arg_type == 'Model':
                obj_class, obj_id = arg
                kwargs[key] = db.query(obj_class).get(obj_id)
            else:
                kwargs[key] = arg

        return kwargs


P = ParamSpec('P')
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
        `starlette.background.BackgroundTasks.add_task` which adds
        better logging to uncaught exceptions in the wrapped task
        function.

        This also dynamically removes DB Session and associated objects
        which may be passed as arguments, and then replaces them with
        newly instanted Session connection when the Task is actually
        run. This allows for FastAPI injected dependencies (like
        `get_database`) to be passed into task functions directly. The
        same Session connection will be shared by all relevant arguments
        of the same task.

        >>> bg = BackgroundTasks() # Likely created via FastAPI dep.
        >>> db: Session = ...      # Likely also created via dep.
        >>> obj = db.query(Episode).first()
        >>> bg.add_task(my_func, db, obj) # Dynamically re-creates db
        """

        def new_func(injector: DependencyInjector) -> None:
            try:
                # Re-inject any Dependencies - e.g. the SQL DB Session
                args_, kwargs_ = injector.args, injector.kwargs
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
        # tasks queue; replace injected objects which may be from
        # FastAPI router dependencies - e.g. SQL DB Sessions - with an
        # injector which will instante a new DB Session when the Task is
        # actually run. Thisis required as of FastAPI v0.106.0 - see
        # https://github.com/fastapi/fastapi/releases/tag/0.106.0
        task = starlette.background.BackgroundTask(
            new_func,
            DependencyInjector(args, kwargs)
        )
        self.tasks.append(task)
        task_queue.add_task(task, func)

# Monkey-patch FastAPI injections
fastapi.BackgroundTasks.add_task = BackgroundTasks.add_task
fastapi.BackgroundTasks.__call__ = BackgroundTasks.__call__
log.trace('Patched FastAPI.BackgroundTasks')
