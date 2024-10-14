from signal import SIGINT, raise_signal
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.database.session import engine
from app.dependencies import get_preferences
from app.internal.auth import get_current_user
from app.internal.backup import (
    backup_data,
    delete_backup,
    delete_old_backups,
    list_available_backups,
    restore_backup,
)
from app.schemas.preferences import SystemBackup
from modules.BackgroundTasks import task_queue
from modules.Debug import Logger, log
from modules.Debug2 import ACTIVE_WEBSOCKETS


# Create sub router for all /backups API requests
backup_router = APIRouter(
    prefix='/backups',
    tags=['Backups'],
    dependencies=[Depends(get_current_user)],
)


@backup_router.get('/all')
def get_available_system_backups(request: Request) -> list[SystemBackup]:
    """Get a list detailing all the available system backups."""

    return list_available_backups(log=request.state.log)


@backup_router.post('/backup')
def perform_backup(request: Request) -> None:
    """Perform a backup of the SQL database and global settings."""

    backup_data(get_preferences().current_version, log=request.state.log)


@backup_router.post('/restore/{folder}')
async def restore_from_backup(
        request: Request,
        folder: str,
        bypass: bool = Query(default=False),
    ) -> None:
    """

    - bypass: Whether to bypass the "lock" if there are currently any
    running or pending tasks.
    """

    # Get contextual logger
    log: Logger = request.state.log

    if task_queue or engine.pool.checkedout() > 0: # type: ignore
        if bypass:
            log.warning('Restoring from backup while there are pending '
                        'operations - performing backup to prevent data loss')
            log.trace(f'TaskQueue: {task_queue}\nPool: {engine.pool}')
            backup_data(get_preferences().current_version, log=log)
        else:
            raise HTTPException(
                status_code=400,
                detail='There are pending Background Tasks/Database Connections'
            )

    # Restore from backup
    restore_backup(folder, log=log)

    # Kill any active websockets
    for connection in list(ACTIVE_WEBSOCKETS):
        try:
            log.debug(f'Killing WebSocket.. {connection}')
            await connection.close()
        finally:
            ACTIVE_WEBSOCKETS.remove(connection)

    # Raise a signal interrupt to kill the server
    log.info('Please shut down TitleCardMaker for these changes to take effect')
    raise_signal(SIGINT)


@backup_router.delete('/outdated')
def delete_outdated_backups(request: Request) -> None:
    """
    Delete all backups older than the globally configured retention
    policy. This is adjusted with the `TCM_BACKUP_RETENTION` environment
    variable (integer number of days).
    """

    delete_old_backups(log=request.state.log)


@backup_router.delete('/backup/{folder}')
def delete_backup_folder(request: Request, folder: str) -> None:
    """
    Delete the backup data located in the given folder.

    - folder: Folder to delete.
    """

    delete_backup(folder, log=request.state.log)
