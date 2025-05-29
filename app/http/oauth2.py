from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

from app.core.config import SECRET_KEY, TOKEN_AUDIENCE, TOKEN_ISSUER, ALGORITHM
from app.exceptions.exception import UnauthorizedException
from app.middleware.translation_manager import _
from app.utils.generate_jwt import GenerateJWToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(data: str = Depends(oauth2_scheme)):
    """
    Trích xuất thông tin người dùng từ JWT token.
    """
    try:
        jwt_generator = GenerateJWToken()
        payload = jwt_generator.decode_token(
            data, SECRET_KEY, TOKEN_ISSUER, TOKEN_AUDIENCE
        )
        return payload
    except Exception as e:
        print(f"Unexpected error in get_current_user: {e}")
        raise UnauthorizedException(_("token_verification_failed")) from e


def verify_websocket_token(token: str) -> dict:
    """
    Verify JWT token for WebSocket connections using the same JWT generator
    Returns user info if valid, raises exception if invalid
    """
    try:
        print(
            f"\033[94m[verify_websocket_token] Verifying token: {token[:20]}...\033[0m"
        )

        # Use the same JWT generator as the rest of the application
        jwt_generator = GenerateJWToken()
        payload = jwt_generator.decode_token(
            token, SECRET_KEY, TOKEN_ISSUER, TOKEN_AUDIENCE
        )

        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        print(
            f"\033[94m[verify_websocket_token] Token payload - user_id: {user_id}, email: {email}, role: {role}\033[0m"
        )

        if user_id is None or email is None:
            print(
                f"\033[91m[verify_websocket_token] ERROR: Invalid token payload - missing user_id or email\033[0m"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        print(f"\033[92m[verify_websocket_token] Token verification successful\033[0m")
        return {"user_id": user_id, "email": email, "role": role}

    except UnauthorizedException as e:
        print(f"\033[91m[verify_websocket_token] ERROR: Unauthorized - {e}\033[0m")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    except Exception as e:
        print(
            f"\033[91m[verify_websocket_token] ERROR: Token verification failed - {e}\033[0m"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )
