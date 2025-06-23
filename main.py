"""
Main function
"""

import os
import sys

import uvicorn

# Add the project root to the Python path to ensure imports work in Docker
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
	sys.path.append(current_dir)

from app import create_app

app = create_app()


if __name__ == '__main__':
	uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
