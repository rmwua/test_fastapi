from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field
from sqlalchemy import Enum, select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from models import PermissionType


class CreateUserRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    done: Optional[bool] = False


class TaskPermissionRequest(BaseModel):
    username: str = None
    permission: PermissionType = None


class CreateTaskRequest(TaskBase):
    permissions: Optional[List[TaskPermissionRequest]] = None


class TaskPermissionResponse(BaseModel):
    id: int
    user_id: int
    permission: PermissionType

    class Config:
        orm_mode = True


class TaskResponse(TaskBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    done: bool
    permissions: Optional[List["TaskPermissionResponse"]] = None
    class Config:
        orm_mode = True



