from pathlib import Path
from fastapi.responses import FileResponse
import os
from typing import Annotated
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, StringConstraints

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


def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname=os.getenv("DB_NAME", "taskdb"),
        user=os.getenv("DB_USER", "taskadmin"),
        password=os.environ["TASK_DB_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def readiness():
    try:
        with connect_db() as conn:
            conn.execute("SELECT id FROM tasks LIMIT 1")
    except (psycopg.Error, KeyError):
        raise HTTPException(
            status_code=503,
            detail="Database unavailable or not configured",
        )
    return {"status": "ready"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    with connect_db() as conn:
        row = conn.execute(
            """
            INSERT INTO tasks (id, title, completed)
            VALUES (%s, %s, %s)
            RETURNING id, title, completed
            """,
            (str(uuid4()), task.title, False),
        ).fetchone()
    return row


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id, title, completed FROM tasks ORDER BY id"
        ).fetchall()
    return rows


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    with connect_db() as conn:
        row = conn.execute(
            "SELECT id, title, completed FROM tasks WHERE id = %s",
            (task_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, update: TaskUpdate):
    with connect_db() as conn:
        row = conn.execute(
            """
            UPDATE tasks
            SET title = %s, completed = %s
            WHERE id = %s
            RETURNING id, title, completed
            """,
            (update.title, update.completed, task_id),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    with connect_db() as conn:
        row = conn.execute(
            "DELETE FROM tasks WHERE id = %s RETURNING id",
            (task_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
@app.get("/", response_class=FileResponse, include_in_schema=False)
def frontend():
    page = Path(__file__).resolve().parent / "frontend" / "index.html"
    return FileResponse(page)