from datetime import datetime
from typing import Annotated, List
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import aliased
from sqlalchemy.sql.operators import or_

import models
from auth import get_current_user
from database import db_dependency
from schemas import CreateTaskRequest, TaskResponse

router = APIRouter(
    prefix="/todo",
    tags=["todo"],
)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(db: db_dependency,
                user: user_dependency,
                create_task_request: CreateTaskRequest):
    try:
        new_task = models.Todos(
            title=create_task_request.title,
            description=create_task_request.description,
            owner_id=user["id"],
            done=create_task_request.done
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        if create_task_request.permissions:
            for permission_request in create_task_request.permissions:
                exists, user_id = get_user_id_by_username(permission_request.username, db)
                if not exists:
                    continue
                permission = models.TaskPermission(
                    task_id=new_task.id,
                    user_id=user_id,
                    permission=permission_request.permission
                )
                db.add(permission)
            db.commit()
    except Exception as e:
        raise e


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[TaskResponse])
def view_todos(db: db_dependency,
               user: user_dependency):
    user_id = user["id"]
    TaskPermissionAlias = aliased(models.TaskPermission)
    try:
        tasks_query = db.query(models.Todos).outerjoin(
            TaskPermissionAlias,
            or_(
                models.Todos.owner_id == user_id,
                TaskPermissionAlias.task_id == models.Todos.id
            )
        ).filter(
            or_(
                models.Todos.owner_id == user_id,
                TaskPermissionAlias.user_id == user_id
            )
        ).distinct()

        tasks = tasks_query.all()
        # Получение прав доступа для задач
        task_ids = [task.id for task in tasks]
        permissions = db.query(models.TaskPermission).filter(models.TaskPermission.task_id.in_(task_ids)).all()

        # Создание словаря прав доступа для быстрого доступа
        permissions_dict = {}
        for permission in permissions:
            if permission.task_id not in permissions_dict:
                permissions_dict[permission.task_id] = []
            permissions_dict[permission.task_id].append(permission)

        # Добавление прав доступа к списку задач только владельцу задачи
        for task in tasks:
            if task.owner_id == user["id"]:
                task.permissions = permissions_dict.get(task.id, [])
            else:
                task.permissions = [
                    perm for perm in permissions_dict.get(task.id, [])
                    if perm.user_id == user_id
                ]

        return tasks
    except Exception as e:
        raise e


@router.put("/{task_id}", status_code=status.HTTP_200_OK, response_model=TaskResponse)
def update_task(
        task_id: int,
        update_task_request: CreateTaskRequest,
        db: db_dependency,
        user: user_dependency
):
    user_id = user["id"]
    task = db.query(models.Todos).filter(
        models.Todos.id == task_id
    ).outerjoin(
        models.TaskPermission,
        models.TaskPermission.task_id == models.Todos.id
    ).filter(
        (models.Todos.owner_id == user_id) |
        ((models.TaskPermission.user_id == user_id) & (
                    models.TaskPermission.permission == models.PermissionType.update))
    ).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task does not exist or not enough permissions")

    for key, value in update_task_request.dict().items():
        if key != "permissions":
            setattr(task, key, value)
    task.updated_task = datetime.now()
    if update_task_request.permissions is not None:
        if task.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update permissions")

        db.query(models.TaskPermission).filter(models.TaskPermission.task_id == task_id).delete()
        db.commit()

        for permission_request in update_task_request.permissions:
            exists, user_id = get_user_id_by_username(permission_request.username, db)
            if not exists:
                continue
            permission = models.TaskPermission(
                task_id=task.id,
                user_id=user_id,
                permission=permission_request.permission
            )
            db.add(permission)
        db.commit()

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
        task_id: int,
        db: db_dependency,
        user: user_dependency):
    try:
        task = db.query(models.Todos).filter(models.Todos.id == task_id, models.Todos.owner_id == user["id"]).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task does not exist or not enough permissions")

        db.delete(task)
        db.commit()
        return {"detail": "Task deleted successfully"}
    except Exception as e:
        raise e


def get_user_id_by_username(username, db):
    try:
        user = db.query(models.Users).filter(models.Users.username == username).first()
        if not user:
            return False, username
        return True, user.id
    except Exception as e:
        print(f"Error retrieving user by username: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")