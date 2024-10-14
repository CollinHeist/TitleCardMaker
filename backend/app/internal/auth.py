from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from logging import getLogger, ERROR
from os import environ
from pathlib import Path
from secrets import token_hex
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences
from app.models.preferences import Preferences
from app.models.user import User as UserModel
from app.schemas.auth import User
from modules.Debug import log


__all__ = (
    'generate_secret_key', 'verify_password', 'get_password_hash', 'get_user',
    'get_current_user', 'authenticate_user', 'create_access_token',
)


ALGORITHM = 'HS256'

"""File where the private key is stored"""
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'
KEY_FILE = Path(__file__).parent.parent.parent / 'config' / '.key.txt'
if IS_DOCKER:
    KEY_FILE = Path('/config/.key.txt')

"""Only log passlib errors so that bcrypt.__version__ boot warning is ignored"""
getLogger('passlib').setLevel(ERROR)
oath2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/authenticate')
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def generate_secret_key() -> bytes:
    """
    Generate a new, random secret.

    Returns:
        A 16-character random hexstring.
    """

    return urlsafe_b64encode(token_hex(16).encode())


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify the given plaintext against the given hashed password.

    Args:
        plaintext: The plaintext password to verify.
        hashed: Hashstring to compare to.

    Returns:
        True if the hash of `plaintext` matches `hatched`. False
        otherwise.
    """

    return pwd_context.verify(plaintext, hashed)


def get_secret_key() -> bytes:
    """
    Get the secret key for all encryption. This reads the local key file
    if it exists, and generates a new one if it does not.

    Returns:
        Secret key (as a hexstring).
    """

    # File exists, read
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    # No file, generate and write new key
    key = generate_secret_key()
    KEY_FILE.write_bytes(key)
    log.info(f'Generated encrpytion key - wrote to "{KEY_FILE}"')

    return key


def get_password_hash(password: str) -> str:
    """
    Hash the given plaintext password.

    Args:
        password: The plaintext password to hash.

    Returns:
        The hash of `password`.
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

    return db.query(UserModel).filter_by(username=username).first()


_creds = {}
def get_current_user(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        token: str = Depends(oath2_scheme),
    ) -> Optional[User]:
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
        None if Authorization is disabled. Otherwise, the User with the
        encoded username.

    Raises:
        HTTPException (401): The credentials encoded in `token` do not
        correspond to a valid User.
    """

    # Do not authenticate if globally disabled
    if not preferences.require_auth:
        return None

    credential_exception = HTTPException(
        status_code=401,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    # Decode JWT, get encoded username
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username: Optional[str] = payload.get('sub')
        uid: Optional[str] = payload.get('uid')
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

    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def encrypt(plaintext: str) -> str:
    """
    Encrypt the given plaintext.

    Args:
        plaintext: Text to encrypt.

    Returns:
        Encrypted text.
    """

    return Fernet(get_secret_key()).encrypt(plaintext.encode()).decode()


def decrypt(encrypted_text: str) -> str:    
    """
    Decrypt the given encrypted text into plaintext.

    Args:
        encrypted_text: Text to decrypt.

    Returns:
        Plain decrypted text.
    """

    return Fernet(get_secret_key()).decrypt(encrypted_text).decode()
