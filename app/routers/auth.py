from datetime import timedelta
from logging import Logger
from os import environ
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_database, get_preferences
from app.internal.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    get_user
)
from app.models.preferences import Preferences
from app.schemas.auth import NewUser, Token, UpdateUser, User


EXPIRATION_TIME = timedelta(days=7)


# Create sub router for all /auth API requests
auth_router = APIRouter(
    prefix='/auth',
    tags=['Authentication'],
)


@auth_router.post('/enable', dependencies=[Depends(get_current_user)])
def enable_authentication(
        request: Request,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> User:
    """
    Enable Authentication on this server. If there are no existing Users
    when enabled then a temporary User is created.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Enable auth globally
    preferences.require_auth = True
    preferences.commit()

    # Get current users
    users = db.query(models.user.User).all()
    if users:
        return users[0]

    # No existing Users, create temporary
    new_user = NewUser(username='admin', password='password')
    new_user = models.user.User(
        username=new_user.username,
        hashed_password=get_password_hash(new_user.password),
    )
    db.add(new_user)
    db.commit()
    log.warning(f'Created temporary User("admin", "password")')

    return new_user


@auth_router.post('/disable', dependencies=[Depends(get_current_user)])
def disable_authentication(
        request: Request,
        revoke_access: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Disable the Authentication requirement on this server.

    - revoke_access: Whether to revoke access from all existing Users.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Disable authentication requirement
    preferences.require_auth = False
    preferences.commit()
    log.warning(f'Disabling Authentication')

    # If revoking access, deleting existing User entries
    if revoke_access:
        log.warning(f'Revoking access from all existing Users')
        db.query(models.user.User).delete()
        db.commit()


@auth_router.post('/new-user', dependencies=[Depends(get_current_user)])
def add_new_user(
        request: Request,
        db: Session = Depends(get_database),
        new_user: NewUser = Body(...),
    ) -> User:
    """
    Add a new User - must be called by an already authenticated User.

    - new_user: New User details to give access to.
    """

    # Verify no User exists with this username
    existing = db.query(models.user.User)\
        .filter_by(username=new_user.username)\
        .first()
    if existing:
        raise HTTPException(
            status_code=422,
            detail='Username taken',
        )

    # Hash this Password, add to database
    user = models.user.User(
        username=new_user.username,
        hashed_password=get_password_hash(new_user.password),
    )
    db.add(user)
    db.commit()
    request.state.log.info(f'Created new User({new_user.username})')

    return user


@auth_router.delete('/user', dependencies=[Depends(get_current_user)])
def delete_user(
        request: Request,
        username: str = Query(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Delete the User with the given Username. If there are no remaining
    Users, authentication is globally disabled to prevent accidental
    lockout.

    - username: Username of the User to delete.
    """

    # Get contextual logger
    log = request.state.log

    # Find this User
    user = db.query(models.user.User).filter_by(username=username).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f'User "{username}" does not exist',
        )

    # Delete User
    db.delete(user)
    db.commit()
    log.info(f'Deleted User({username})')

    # If there are no more active Users, disable authentication to avoid L/O
    if len(db.query(models.user.User).all()) == 0:
        log.warning(f'No remaining active users - disabling authentication')
        preferences.require_auth = False
        preferences.commit()


@auth_router.get('/all', dependencies=[Depends(get_current_user)])
def get_all_usernames(db: Session = Depends(get_database)) -> list[str]:
    """Get the usernames of all Users in the database."""

    return [user.username for user in db.query(models.user.User).all()]


@auth_router.get('/active')
def get_active_username(
        user: Optional[User] = Depends(get_current_user),
    ) -> Optional[str]:
    """Get the username of the active User."""

    return None if user is None else user.username


@auth_router.post('/edit')
def update_user_credentials(
        request: Request,
        update_user: UpdateUser = Body(...),
        db: Session = Depends(get_database),
        user: Optional[User] = Depends(get_current_user),
    ) -> User:
    """
    Update the credentials of the current User.
    - update_user: New credentials to utilize for this User.
    """

    # Authorization is disabled, cannot edit credentials
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Cannot edit credentials while unauthorized'
        )

    # Get user
    user = get_user(db, user.username)

    # Verify new username does not conflict with existing user
    existing_user = db.query(models.user.User)\
        .filter_by(username=update_user.username)\
        .first()
    if existing_user and existing_user != user:
        raise HTTPException(
            status_code=422,
            detail='Username taken',
        )

    # Change username/password
    request.state.log.warning(f'Modified credentials for User({user.username})')
    user.username = update_user.username
    user.hashed_password = get_password_hash(update_user.password)
    db.commit()

    return user


@auth_router.post('/authenticate')
def login_for_access_token(
        request: Request,
        db: Session = Depends(get_database),
        form_data: OAuth2PasswordRequestForm = Depends(),
    ) -> Token:
    """
    Authenticate the given User and return an appropriate access token.

    - form_data: OAuth2 form with the username and password being
    authenticated.
    """

    # Authenticate User
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Create new access token for this User
    access_token = create_access_token(
        data={'sub': user.username, 'uid': user.hashed_password},
        expires_delta=EXPIRATION_TIME,
    )
    request.state.log.info(
        f'Authenticated User({user.username}) for {EXPIRATION_TIME}'
    )

    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }


@auth_router.post('/reset')
def reset_all_authentication(
        request: Request,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Reset all authentication of the current server. This requires the
    appropriate environment variable to be set in order to function.

    Intended only for testing setup and teardown.
    """

    if environ.get('TCM_TESTING', 'false') == 'TRUE':
        # Delete all Users from the database
        request.state.log.warning('Resetting all authentication')
        db.query(User).delete()
        db.commit()

        # Do not require authentication
        preferences.require_auth = False
        preferences.commit()
    else:
        raise HTTPException(
            status_code=401,
            detail='Unauthorized',
        )
