from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, StringConstraints

app = FastAPI(title="Task Manager API")

TaskTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
    ),
]


class TaskCreate(BaseModel):
    title: TaskTitle


class TaskUpdate(BaseModel):
    title: TaskTitle
    completed: bool


class Task(BaseModel):
    id: str
    title: str
    completed: bool = False


# Temporary storage. Step 3 will replace this with PostgreSQL.
tasks: dict[str, Task] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    new_task = Task(
        id=str(uuid4()),
        title=task.title,
    )
    tasks[new_task.id] = new_task
    return new_task


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, update: TaskUpdate):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_task = Task(
        id=task_id,
        title=update.title,
        completed=update.completed,
    )
    tasks[task_id] = updated_task
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks[task_id]
    return Response(status_code=204)
