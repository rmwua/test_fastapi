import datetime
import enum
from typing import List

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Double, DateTime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from database import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(225))

    todos = relationship('Todos', back_populates='owner')


class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(225))
    description = Column(String(225))
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now())
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship('Users', back_populates='todos')
    done = Column(Boolean, default=False)
    permissions = relationship("TaskPermission", back_populates="task")


class PermissionType(enum.Enum):
    read = "read"
    update = "update"


class TaskPermission(Base):
    __tablename__ = 'task_permissions'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('todos.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    permission = Column(ENUM(PermissionType))
    task = relationship("Todos", back_populates="permissions")
