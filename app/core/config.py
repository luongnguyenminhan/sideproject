import json
import os
from functools import lru_cache

from dotenv import load_dotenv  # type: ignore
from pydantic import BaseModel

load_dotenv()

PROJECT_NAME = 'CGSEM.AI'
API_V1_STR = '/api/v1'
API_V2_STR = '/api/v2'
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '11minhan')
DB_HOST = os.getenv('DB_HOST', 'host.docker.internal')

# Force host.docker.internal when running in Docker
# DB_HOST = 'host.docker.internal'

DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'fproject')
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

SQLALCHEMY_DATABASE_URI = DATABASE_URL

SERVICE = 'gemini'
MODEL_NAME = 'model/gemini-2.0-flash-exp'

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Google OAuth Settings
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), 'client-secret.json')
with open(CLIENT_SECRET_FILE) as f:
	google_creds = json.load(f)['web']

GOOGLE_CLIENT_ID = google_creds['client_id']
GOOGLE_CLIENT_SECRET = google_creds['client_secret']
# Update the redirect URI to support Next.js frontend
GOOGLE_REDIRECT_URI = 'http://localhost:8000/api/v1/auth/google/callback'

# Frontend redirect URLs for OAuth flows - callback server on port 3000
FRONTEND_SUCCESS_URL = os.getenv('FRONTEND_SUCCESS_URL', 'http://127.0.0.1:5500/auth/google/callback')
FRONTEND_ERROR_URL = os.getenv('FRONTEND_ERROR_URL', 'http://127.0.0.1:5500/auth?error=true')

# JWT Settings
SECRET_KEY = os.getenv('SECRET_KEY', '-extremely-secret-and-very-long-key')
TOKEN_ISSUER = os.getenv('TOKEN_ISSUER', 'frecord-api')
TOKEN_AUDIENCE = os.getenv('TOKEN_AUDIENCE', 'frecord-client')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

FERNET_KEY = os.getenv('FERNET_KEY', '4pI2ZAxB7X8N9sM5R8k_AfF4PLbJnvYsV2gJJei8BjI=')

# Facebook Graph API Settings
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '102602521717131')
FACEBOOK_GRAPH_API_VERSION = os.getenv('FACEBOOK_GRAPH_API_VERSION', 'v22.0')
FACEBOOK_GRAPH_BASE_URL = f'https://graph.facebook.com/{FACEBOOK_GRAPH_API_VERSION}'

# MinIO Settings
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'cgsem')
MINIO_SECURE = False  # Using boolean instead of string

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')


class Settings(BaseModel):
	PROJECT_NAME: str = PROJECT_NAME
	API_V1_STR: str = API_V1_STR
	API_V2_STR: str = API_V2_STR
	DATABASE_URL: str = DATABASE_URL
	SQLALCHEMY_DATABASE_URI: str = SQLALCHEMY_DATABASE_URI

	# JWT Settings
	SECRET_KEY: str = SECRET_KEY
	TOKEN_ISSUER: str = TOKEN_ISSUER
	TOKEN_AUDIENCE: str = TOKEN_AUDIENCE
	ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES
	REFRESH_TOKEN_EXPIRE_DAYS: int = REFRESH_TOKEN_EXPIRE_DAYS

	# Frontend URLs
	FRONTEND_SUCCESS_URL: str = FRONTEND_SUCCESS_URL
	FRONTEND_ERROR_URL: str = FRONTEND_ERROR_URL

	# MinIO Settings
	MINIO_ENDPOINT: str = MINIO_ENDPOINT
	MINIO_ACCESS_KEY: str = MINIO_ACCESS_KEY
	MINIO_SECRET_KEY: str = MINIO_SECRET_KEY
	MINIO_BUCKET_NAME: str = MINIO_BUCKET_NAME
	MINIO_SECURE: bool = MINIO_SECURE
	CELERY_BROKER_URL: str = CELERY_BROKER_URL
	CELERY_RESULT_BACKEND: str = CELERY_RESULT_BACKEND

	# Facebook Graph API Settings
	FACEBOOK_ACCESS_TOKEN: str = FACEBOOK_ACCESS_TOKEN
	FACEBOOK_PAGE_ID: str = FACEBOOK_PAGE_ID
	FACEBOOK_GRAPH_API_VERSION: str = FACEBOOK_GRAPH_API_VERSION
	FACEBOOK_GRAPH_BASE_URL: str = FACEBOOK_GRAPH_BASE_URL


@lru_cache()
def get_settings():
	return Settings()
