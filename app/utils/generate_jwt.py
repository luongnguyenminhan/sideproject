"""
JWT Token Generation Utility

This file defines the GenerateJWToken class for creating and managing JWT tokens
including access tokens and refresh tokens.

Dependencies:
- PyJWT >= 2.0.0
- datetime

Author: Minh An
Last Modified: 21 Jan 2024
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from jwt import decode, encode  # explicit imports from PyJWT


class GenerateJWToken:
	@staticmethod
	def create_token(
		auth_claims: Dict[str, Any],
		secret_key: str,
		issuer: str,
		audience: str,
		token_validity_in_minutes: int,
		current_time: datetime,
	) -> str:
		payload = {
			'exp': current_time + timedelta(minutes=token_validity_in_minutes),
			'iat': current_time,
			'iss': issuer,
			'aud': audience,
			**auth_claims,
		}
		token = encode(payload, secret_key, algorithm='HS256')
		return token

	@staticmethod
	def create_refresh_token(
		auth_claims: Dict[str, Any],
		secret_key: str,
		issuer: str,
		audience: str,
		refresh_token_validity_in_days: int,
		current_time: datetime,
	) -> str:
		payload = {
			'exp': current_time + timedelta(days=refresh_token_validity_in_days),
			'iat': current_time,
			'iss': issuer,
			'aud': audience,
			**auth_claims,
		}
		refresh_token = encode(payload, secret_key, algorithm='HS256')
		return refresh_token

	@staticmethod
	def decode_token(token, secret_key: str, issuer: str, audience: str):
		claims = decode(token, secret_key, algorithms=['HS256'], audience=audience, issuer=issuer)
		return claims
