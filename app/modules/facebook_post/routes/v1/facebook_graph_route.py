
from fastapi import APIRouter
from app.middleware.translation_manager import _


route = APIRouter(prefix='/facebook-graph', tags=['Facebook Graph API'])
