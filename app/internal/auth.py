from datetime import datetime, timedelta
from secrets import token_hex
from typing import Literal, Optional, Union

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

from sqlalchemy.orm import Session

from app import models
from app.dependencies import get_database, get_preferences
from app.models.preferences import Preferences
from app.schemas.auth import User


ALGORITHM = 'HS256'
SECRET_KEY = '360f8406f24d5bdd0ff24693e71e025f'

oath2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/authenticate')
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def generate_secret_key() -> str:
    """
    Generate a new, random secret 16.

    Returns:
        A 16-character random hexstring.
    """

    return token_hex(16)


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify the given plaintext against the given hashed password.

    Args:
        plaintext: The plaintext password to verify.
        hashed: Hashstring to compare to.

    Returns:
        True if the hash of `plaintext` matches `hatched`; False
        otherwise.
    """

    return pwd_context.verify(plaintext, hashed)


def get_password_hash(password: str) -> str:
    """
    Hash the given plaintext password.

    Args:
        password: The plaintext password to hash.

    Returns:
        The hashed `password`.
    """

    return pwd_context.hash(password)


def get_user(db: Session, username: str) -> Optional[User]:
    """
    Query the database for the `User` with the given username.

    Args:
        db: Database to query.
        username: Name of the User to query for.

    Returns:
        User with the matching Username; `None` if no matching User
        exists.
    """

    return db.query(models.user.User).filter_by(username=username).first()


_creds = {}
def get_current_user(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        token: str = Depends(oath2_scheme),
    ) -> Union[User, Literal[True]]:
    """
    Dependency to get the User whose username matches the given token.
    If Authorization is globally disabled, then no validation is
    performed.

    Args:
        db: Session to query for Users.
        preferences: Global Preferences.
        token: OAuth2 JWT whose data is the encrypted username of the
            active User.

    Returns:
        True if Authorization is disabled. Otherwise, the User with the
        encoded username.

    Raises:
        HTTPException (401) if the credentials encoded in `token` do not
        correspond to a valid User.
    """

    # Do not authenticate if globally disabled
    if not preferences.require_auth:
        return True

    credential_exception = HTTPException(
        status_code=401,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    # Decode JWT, get encoded username
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        uid: str = payload.get('uid')
    except JWTError as exc:
        raise credential_exception from exc

    # If username or UID are missing, raise 401
    if username is None or uid is None:
        raise credential_exception

    # If credentials are not cached or don't match, query DB
    if ((user := _creds.get(username)) is None
        or user.hashed_password != uid):
        # User not cached, nor in database, raise 401
        if (user := get_user(db, username)) is None:
            raise credential_exception

        # Add User to cache, verify phash
        _creds[username] = user
        if user.hashed_password != uid:
            raise credential_exception

    # Credentials are cached and match
    return user


def authenticate_user(
        db: Session,
        username: str,
        password: str,
    ) -> Optional[User]:
    """
    Authenticate the given credentials, returning the associated User.

    Args:
        db: Database with Users to query.
        username: Username of the User to authenticate.
        password: Plaintext password to authenticate.

    Returns:
        The User with the given username and password. None if there are
        no matches.
    """

    # If there is no User or the password does not match, return None
    if (user := get_user(db, username)) is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
    """
    Create an encoded JWT with the given data.

    Args:
        data: Data to encode in the JWT.
        expires_delta: How long the token is valid for. If not provided,
            the token is valid for 7 days.

    Returns:
        JWT string of the encoded data and expiration date.
    """

    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(days=7)

    to_encode = data.copy()
    to_encode.update({'exp': expires})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
