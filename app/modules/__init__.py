"""Init module
Load routes in all modules
"""

import importlib
import os
import pkgutil
from typing import Annotated

from fastapi import APIRouter, Depends, Header


def get_language(lang: Annotated[str, Header()] = 'vi'):
	"""
	Set header language vi/en
	Default: vi
	"""
	return lang


route = APIRouter(dependencies=[Depends(get_language)])
package = 'app.modules'

# Duyệt qua từng module trong `modules` (ví dụ: users, products, ...)
for finder, module_name, ispkg in pkgutil.iter_modules([package.replace('.', '/')]):
	print(f'Loading module: {module_name}, is package: {ispkg}, finder: {finder}')
	module_path = f'{package}.{module_name}.routes'

	try:
		# Lấy danh sách thư mục trong `routes/`
		routes_dir = f'{module_path.replace(".", "/")}'
		version_folders = [d for d in os.listdir(routes_dir) if os.path.isdir(f'{routes_dir}/{d}') and d.startswith('v')]
		for version_name in version_folders:
			version_path = f'{module_path}.{version_name}'

			# Duyệt tất cả file trong v1, v2 (vd: user_route.py, authen_route.py)
			for _, route_name, _ in pkgutil.iter_modules([f'{version_path.replace(".", "/")}']):
				route_module_path = f'{version_path}.{route_name}'
				try:
					module = importlib.import_module(route_module_path)

					if hasattr(module, 'route'):
						# Lấy tên route (bỏ `_route` nếu có)
						print(f'/{version_name}{module.route.prefix}')
						route.include_router(module.route, prefix=f'/{version_name}')
						print(f'✅ Loaded {route_module_path}')

				except ModuleNotFoundError as e:
					print(f'⚠️ Module {route_module_path} not found: {e}')
					pass

	except FileNotFoundError as e:
		print(f'⚠️ Folder {module_path} not found: {e}')
		pass


# for finder, name, ispkg in pkgutil.iter_modules([package.replace(".", "/")]):
#     try:
#         module = importlib.import_module(f"{package}.{name}.routes.index")

#         if hasattr(module, "route"):
#             route.include_router(module.route)
#     except ModuleNotFoundError as e:
#         print(e)
#         pass
