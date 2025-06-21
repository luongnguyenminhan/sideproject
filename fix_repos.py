"""
Script để tự động fix repositories và imports
"""

import os
import re
from pathlib import Path


def fix_repository_files():
	"""Fix all repository files to inherit from BaseRepo"""

	# Repository files cần fix
	repo_files = ['app/modules/chat/repository/file_repo.py', 'app/modules/chat/repository/conversation_repo.py', 'app/modules/agentic_rag/repository/global_kb_repo.py', 'app/modules/agentic_rag/repository/rag_repo.py', 'app/modules/agentic_rag/repository/kb_repo.py', 'app/modules/agent/repository/conversation_workflow_repo.py']

	for file_path in repo_files:
		if os.path.exists(file_path):
			print(f'Processing {file_path}')

			with open(file_path, 'r', encoding='utf-8') as f:
				content = f.read()

			# Add BaseRepo import if not exists
			if 'from app.core.base_repo import BaseRepo' not in content:
				# Find app.core.database import and add after it
				content = re.sub(r'(from app\.core\.database import get_db)', r'\1\nfrom app.core.base_repo import BaseRepo', content)

			# Fix class definition
			content = re.sub(r'class (\w+Repo[^(]*):', r'class \1(BaseRepo):', content)

			# Fix __init__ method to call super()
			content = re.sub(r'def __init__\(self, db: Session = Depends\(get_db\)\):\s*\n\s*self\.db = db', r'def __init__(self, db: Session = Depends(get_db)):\n\t\tsuper().__init__(db)', content)

			# Add import comments for external imports
			content = re.sub(r'^(from app\.[^m].*)', r'## IMPORT NGOÀI MODULE CẦN XỬ LÍ\n\1', content, flags=re.MULTILINE)

			with open(file_path, 'w', encoding='utf-8') as f:
				f.write(content)

			print(f'Fixed {file_path}')


if __name__ == '__main__':
	fix_repository_files()
