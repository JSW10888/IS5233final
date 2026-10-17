from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app, connect_db


@pytest.fixture
def client(monkeypatch):
    # Redirect this test process to the separate test database.
    monkeypatch.setenv("DB_NAME", "taskdb_test")

    with connect_db() as conn:
        database = conn.execute(
            "SELECT current_database() AS name"
        ).fetchone()

        assert database["name"] == "taskdb_test"
        conn.execute("DELETE FROM tasks")

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        with connect_db() as conn:
            conn.execute("DELETE FROM tasks")


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_task_lifecycle(client):
    # Create a task.
    response = client.post(
        "/tasks",
        json={"title": "Automated test task"},
    )

    assert response.status_code == 201
    task = response.json()
    task_id = task["id"]
    assert task["completed"] is False

    # Confirm the task was committed to PostgreSQL.
    with connect_db() as conn:
        saved_task = conn.execute(
            "SELECT title, completed FROM tasks WHERE id = %s",
            (task_id,),
        ).fetchone()

    assert saved_task == {
        "title": "Automated test task",
        "completed": False,
    }

    # Retrieve the task.
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json() == task

    # Confirm it appears in the list.
    response = client.get("/tasks")
    assert response.status_code == 200
    assert task in response.json()

    # Update the task.
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated task", "completed": True},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated task"
    assert response.json()["completed"] is True

    # Confirm the update persists in a subsequent request.
    response = client.get(f"/tasks/{task_id}")
    assert response.json()["title"] == "Updated task"
    assert response.json()["completed"] is True

    # Delete the task.
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_invalid_title(client, title):
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 422
    assert client.get("/tasks").json() == []


def test_unknown_task(client):
    task_id = str(uuid4())

    assert client.get(f"/tasks/{task_id}").status_code == 404

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Missing task", "completed": True},
    )
    assert response.status_code == 404

    assert client.delete(f"/tasks/{task_id}").status_code == 404