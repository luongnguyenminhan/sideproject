"""
Filter Utilities

This module provides common filtering functions used across the application's data access layers.
It helps enforce DRY (Don't Repeat Yourself) principles by centralizing filtering logic.

Author: Minh An
Last Modified: 21 Apr 2025
Version: 1.0.0
"""

import logging
from typing import Any, TypeVar

from sqlalchemy import Column, String, cast
from sqlalchemy.orm.query import Query

logger = logging.getLogger(__name__)
T = TypeVar('T')


def apply_filter(query: Query, column: Column, operator: str, value: Any) -> Query:
	"""
	Applies a filter operation to a SQLAlchemy query based on the specified operator.

	Args:
	    query (Query): The SQLAlchemy query to filter
	    column (Column): The model column to apply the filter to
	    operator (str): The operator to use (eq, ne, gt, lt, contains, etc.)
	    value (Any): The value to filter by

	Returns:
	    Query: The filtered SQLAlchemy query

	Example:
	    query = query.session.query(User)
	    query = apply_filter(query, User.username, "contains", "john")
	"""
	if operator == 'eq':
		return query.filter(column == value)
	elif operator == 'ne':
		return query.filter(column != value)
	elif operator == 'gt':
		return query.filter(column > value)
	elif operator == 'gte':
		return query.filter(column >= value)
	elif operator == 'lt':
		return query.filter(column < value)
	elif operator == 'lte':
		return query.filter(column <= value)
	elif operator == 'contains':
		# Handle JSON fields differently if needed
		try:
			return query.filter(column.ilike(f'%{value}%'))
		except Exception:
			# For JSON or other complex types, try casting to string
			return query.filter(cast(column, String).ilike(f'%{value}%'))
	elif operator == 'startswith':
		return query.filter(column.ilike(f'{value}%'))
	elif operator == 'endswith':
		return query.filter(column.ilike(f'%{value}'))
	elif operator == 'in_list':
		if isinstance(value, list):
			return query.filter(column.in_(value))
	elif operator == 'not_in':
		if isinstance(value, list):
			return query.filter(~column.in_(value))
	elif operator == 'is_null':
		return query.filter(column is None)
	elif operator == 'is_not_null':
		return query.filter(column is not None)
	else:
		logger.warning(f'Unsupported operator: {operator}')

	# Return the original query if operator not supported
	return query


def apply_dynamic_filters(query: Query, model: Any, params: dict) -> Query:
	"""
	Applies dynamic filters from a parameters dictionary to a SQLAlchemy query.
	Handles both structured filters array and legacy direct parameter filtering.

	Args:
	    query (Query): The SQLAlchemy query to filter
	    model (Any): The model class that defines the columns
	    params (dict): Dictionary containing filtering parameters

	Returns:
	    Query: The filtered SQLAlchemy query

	Example:
	    query = session.query(User)
	    params = {
	        "filters": [{"field": "username", "operator": "contains", "value": "john"}],
	        "email": "example.com"  # Legacy direct filter
	    }
	    query = apply_dynamic_filters(query, User, params)
	"""
	logger = logging.getLogger(__name__)

	# Process structured filters if present
	filters = params.get('filters')
	if filters:
		for filter_item in filters:
			field_name = filter_item.get('field')
			operator = filter_item.get('operator')
			value = filter_item.get('value')
			if not hasattr(model, field_name):
				logger.warning(f'Ignoring filter for non-existent field: {field_name}')
				continue

			column = getattr(model, field_name)
			query = apply_filter(query, column, operator, value)
			logger.debug(f'Applied {operator} filter on {field_name}: {value}')

	# Process legacy direct filters (for backward compatibility)
	for key, value in params.items():
		# Skip pagination parameters and filters list
		if key in ['page', 'page_size', 'filters']:
			continue

		# Check if the key exists as a column in model
		if hasattr(model, key):
			column = getattr(model, key)

			# Apply different filters based on the parameter value
			if value is not None:
				if isinstance(value, str) and value.strip():
					# String fields: use LIKE for partial matching
					query = query.filter(column.like(f'%{value}%'))
					logger.debug(f'Applied LIKE filter on {key}: %{value}%')
				elif isinstance(value, (int, bool, float)) or (
					hasattr(value, '__enum__')  # For enum values
				):
					# Exact match for non-string types
					query = query.filter(column == value)
					logger.debug(f'Applied exact match filter on {key}: {value}')

	return query
