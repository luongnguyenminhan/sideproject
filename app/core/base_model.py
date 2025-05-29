"""Base model"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, List, TypeVar

from fastapi import Body
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, String, func

from app.core.database import Base

T = TypeVar("T")


class Operator(str, Enum):
    """Enum for filter operations"""

    eq = "eq"  # Equal
    ne = "ne"  # Not equal
    lt = "lt"  # Less than
    lte = "lte"  # Less than or equal
    gt = "gt"  # Greater than
    gte = "gte"  # Greater than or equal
    contains = "contains"  # String contains
    startswith = "startswith"  # String starts with
    endswith = "endswith"  # String ends with
    in_list = "in"  # Value is in a list
    not_in = "not_in"  # Value is not in a list
    is_null = "is_null"  # Field is null
    is_not_null = "is_not_null"  # Field is not null


class Filter(BaseModel):
    """Filter model for dynamic filtering"""

    field: str = Field(..., description="Field name to filter on")
    operator: Operator = Field(..., description="Filter operation")
    value: Any = Field(..., description="Filter value")


class RequestSchema(BaseModel):
    """BaseRequest"""


class ResponseSchema(BaseModel):
    """ResponseSchema"""

    model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel):
    """APIResponse"""

    error_code: int | None = Body(default=1, description="Mã lỗi", examples=[0])
    message: str | None = Body(
        default=None, description="Thông báo lỗi", examples=["Thao tác thành công"]
    )
    description: str | None = Body(
        default=None, description="Chi tiết lỗi", examples=[""]
    )
    data: T | None = Body(default=None, description="Dữ liệu trả về")


class PagingInfo(BaseModel):
    """Thông tin phân trang"""

    total: int | None = Body(
        default=0, description="Tổng số lượng dữ liệu", examples=[100]
    )
    total_pages: int | None = Body(
        default=0, description="Tổng số trang", examples=[10]
    )
    page: int | None = Body(default=0, description="Trang hiện tại", examples=[1])
    page_size: int | None = Body(
        default=0, description="Số lượng dữ liệu mỗi trang", examples=[10]
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated Response"""

    items: List[T] | None = Body(default=[], description="Danh sách dữ liệu")
    paging: PagingInfo | None = Body(
        default=PagingInfo(), description="Thông tin phân trang"
    )


class BaseEntity(Base):
    """Base model class containing common fields and methods"""

    __abstract__ = True

    model_config = ConfigDict(arbitrary_types_allowed=True)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    create_date = Column(DateTime(timezone=True), default=func.now())
    update_date = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    def __iter__(self):
        for column in self.__table__.columns:
            yield column.name, getattr(self, column.name)

    def items(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }.items()

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def dict(self, include_relationships=False):
        """Convert model instance to dictionary with optional relationship handling"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (uuid.UUID, datetime)):
                value = str(value)
            result[column.name] = value

        # Only include relationships if explicitly requested
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                value = getattr(self, relationship.key)
                if value is not None:
                    if hasattr(value, "dict"):
                        result[relationship.key] = value.dict(
                            include_relationships=False
                        )  # Prevent deep recursion
                    elif isinstance(value, list):
                        result[relationship.key] = [
                            (
                                item.dict(include_relationships=False)
                                if hasattr(item, "dict")
                                else item
                            )
                            for item in value
                        ]
                    else:
                        result[relationship.key] = value
        return result


class FilterableRequestSchema(RequestSchema):
    """Base request schema with filtering capabilities"""

    page: int | None = Field(default=1, ge=1, description="Page number")
    page_size: int | None = Field(
        default=10, ge=1, description="Number of items per page"
    )
    filters: List[Filter] | None = Field(
        default=[], description="List of dynamic filters"
    )

    def model_dump(self, **kwargs):
        """Override to include all dynamic fields in the output"""
        data = super().model_dump(**kwargs)
        # Include any extra fields that were passed but not defined in the schema
        for key, value in self.__dict__.items():
            if key not in data and not key.startswith("_"):
                data[key] = value
        return data


class Pagination(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: List[T]
    total_count: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
