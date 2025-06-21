"""
Script để fix imports trong modules
"""

import os
import re
from pathlib import Path


def fix_imports_in_modules():
	"""Fix imports trong tất cả modules"""

	modules_dir = Path('app/modules')

	# Lặp qua tất cả .py files trong modules
	for py_file in modules_dir.rglob('*.py'):
		if py_file.name == '__init__.py':
			continue

		print(f'Processing {py_file}')

		with open(py_file, 'r', encoding='utf-8') as f:
			content = f.read()

		original_content = content

		# Comment các import ngoài module (from app.xxx nhưng không phải from app.modules.current_module)
		lines = content.split('\n')
		new_lines = []

		# Lấy tên module hiện tại
		current_module = None
		parts = py_file.parts
		if 'modules' in parts:
			module_idx = parts.index('modules')
			if module_idx + 1 < len(parts):
				current_module = parts[module_idx + 1]

		for line in lines:
			# Nếu là import từ app. nhưng không phải từ module hiện tại
			if re.match(r'^from app\.', line) and current_module and f'app.modules.{current_module}' not in line and 'app.modules' not in line:
				# Kiểm tra xem đã có comment chưa
				if not line.strip().startswith('## IMPORT NGOÀI MODULE'):
					new_lines.append('## IMPORT NGOÀI MODULE CẦN XỬ LÍ')
					new_lines.append(line)
				else:
					new_lines.append(line)
			else:
				new_lines.append(line)

		content = '\n'.join(new_lines)

		# Chuyển import trong module thành relative
		if current_module:
			# Tìm và thay thế imports trong cùng module
			pattern = f'from app\.modules\.{current_module}\.'
			replacement = 'from .'
			content = re.sub(pattern, replacement, content)

			# Tìm imports từ các module khác trong modules
			for other_line in content.split('\n'):
				if re.match(r'^from app\.modules\.(\w+)\.', other_line):
					if '## IMPORT NGOÀI MODULE' not in content.split('\n')[content.split('\n').index(other_line) - 1]:
						content = content.replace(other_line, f'## IMPORT NGOÀI MODULE CẦN XỬ LÍ - Cross module import\n{other_line}')

		# Chỉ ghi file nếu có thay đổi
		if content != original_content:
			with open(py_file, 'w', encoding='utf-8') as f:
				f.write(content)
			print(f'Fixed imports in {py_file}')


if __name__ == '__main__':
	fix_imports_in_modules()
