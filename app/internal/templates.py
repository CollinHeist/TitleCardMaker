from typing import Any, Literal, Optional, Union

from fastapi import HTTPException

import app.models as models
from app.routers.fonts import get_font
from app.schemas.series import Template

from modules.Debug import log


