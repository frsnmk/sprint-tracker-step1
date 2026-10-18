import sqlite3

from fastapi.testclient import TestClient


def make(client: TestClient, **fields: object) -> dict:
    payload = {"name": "Goal", **fields}
    response = client.post("/goals", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- create ---

def test_create_minimal(client: TestClient) -> None:
    response = client.post("/goals", json={"name": "Ship v1"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ship v1"
    assert body["status"] == "planned"
    assert body["description"] is None
    assert body["start_date"] is None and body["end_date"] is None
    assert body["created_at"] and body["updated_at"]
    assert body["deleted_at"] is None


def test_create_full(client: TestClient) -> None:
    body = make(
        client, description="d", status="active", start_date="2026-01-01", end_date="2026-03-01"
    )
    assert body["status"] == "active"
    assert body["start_date"] == "2026-01-01"
    assert body["end_date"] == "2026-03-01"


def test_create_requires_name(client: TestClient) -> None:
    assert client.post("/goals", json={}).status_code == 422


def test_create_rejects_blank_name(client: TestClient) -> None:
    assert client.post("/goals", json={"name": "   "}).status_code == 422


def test_create_rejects_invalid_status(client: TestClient) -> None:
    assert client.post("/goals", json={"name": "x", "status": "bogus"}).status_code == 422


def test_create_rejects_invalid_date(client: TestClient) -> None:
    assert client.post("/goals", json={"name": "x", "start_date": "not-a-date"}).status_code == 422


def test_create_rejects_end_before_start(client: TestClient) -> None:
    response = client.post(
        "/goals", json={"name": "x", "start_date": "2026-05-01", "end_date": "2026-01-01"}
    )
    assert response.status_code == 422


# --- list ---

def test_list_empty(client: TestClient) -> None:
    response = client.get("/goals")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_filter_status(client: TestClient) -> None:
    make(client, name="A", status="active")
    make(client, name="B", status="done")
    body = client.get("/goals", params={"status": "done"}).json()
    assert [g["name"] for g in body["items"]] == ["B"]
    assert body["total"] == 1


def test_list_filter_q_case_insensitive(client: TestClient) -> None:
    make(client, name="Learn FastAPI")
    make(client, name="Other")
    body = client.get("/goals", params={"q": "fastapi"}).json()
    assert [g["name"] for g in body["items"]] == ["Learn FastAPI"]


def test_list_filter_date_ranges(client: TestClient) -> None:
    make(client, name="Early", start_date="2026-01-01", end_date="2026-02-01")
    make(client, name="Late", start_date="2026-06-01", end_date="2026-07-01")
    by_start = client.get("/goals", params={"start_from": "2026-03-01"}).json()
    assert [g["name"] for g in by_start["items"]] == ["Late"]
    by_end = client.get("/goals", params={"end_to": "2026-03-01"}).json()
    assert [g["name"] for g in by_end["items"]] == ["Early"]


def test_list_combined_filters(client: TestClient) -> None:
    make(client, name="Alpha", status="active")
    make(client, name="Alpine", status="done")
    body = client.get("/goals", params={"q": "alp", "status": "active"}).json()
    assert [g["name"] for g in body["items"]] == ["Alpha"]


def test_list_pagination(client: TestClient) -> None:
    for i in range(5):
        make(client, name=f"G{i}")
    body = client.get("/goals", params={"limit": 2, "offset": 1}).json()
    assert [g["name"] for g in body["items"]] == ["G1", "G2"]
    assert body["total"] == 5 and body["limit"] == 2 and body["offset"] == 1


def test_list_hides_deleted_unless_requested(client: TestClient) -> None:
    goal = make(client, name="Gone")
    client.delete(f"/goals/{goal['id']}")
    assert client.get("/goals").json()["total"] == 0
    body = client.get("/goals", params={"include_deleted": "true"}).json()
    assert body["total"] == 1 and body["items"][0]["deleted_at"] is not None


def test_list_rejects_invalid_params(client: TestClient) -> None:
    assert client.get("/goals", params={"status": "bogus"}).status_code == 422
    assert client.get("/goals", params={"limit": 0}).status_code == 422
    assert client.get("/goals", params={"limit": 201}).status_code == 422
    assert client.get("/goals", params={"offset": -1}).status_code == 422
    assert client.get("/goals", params={"start_from": "nope"}).status_code == 422


# --- get by id ---

def test_get_by_id(client: TestClient) -> None:
    goal = make(client, name="Find me")
    response = client.get(f"/goals/{goal['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Find me"


def test_get_missing_is_404(client: TestClient) -> None:
    assert client.get("/goals/999").status_code == 404


def test_get_deleted_is_404(client: TestClient) -> None:
    goal = make(client)
    client.delete(f"/goals/{goal['id']}")
    assert client.get(f"/goals/{goal['id']}").status_code == 404


def test_get_non_integer_id_is_422(client: TestClient) -> None:
    assert client.get("/goals/abc").status_code == 422


# --- update ---

def test_patch_partial(client: TestClient) -> None:
    goal = make(client, name="Old", description="keep", status="planned")
    response = client.patch(f"/goals/{goal['id']}", json={"name": "New", "status": "done"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New" and body["status"] == "done"
    assert body["description"] == "keep"
    assert body["updated_at"] >= goal["updated_at"]
    assert body["created_at"] == goal["created_at"]


def test_patch_null_clears_field(client: TestClient) -> None:
    goal = make(client, description="to clear", start_date="2026-01-01")
    body = client.patch(
        f"/goals/{goal['id']}", json={"description": None, "start_date": None}
    ).json()
    assert body["description"] is None and body["start_date"] is None


def test_patch_missing_is_404(client: TestClient) -> None:
    assert client.patch("/goals/999", json={"name": "x"}).status_code == 404


def test_patch_deleted_is_404(client: TestClient) -> None:
    goal = make(client)
    client.delete(f"/goals/{goal['id']}")
    assert client.patch(f"/goals/{goal['id']}", json={"name": "x"}).status_code == 404


def test_patch_empty_body_is_422(client: TestClient) -> None:
    goal = make(client)
    assert client.patch(f"/goals/{goal['id']}", json={}).status_code == 422


def test_patch_null_name_is_422(client: TestClient) -> None:
    goal = make(client)
    assert client.patch(f"/goals/{goal['id']}", json={"name": None}).status_code == 422


def test_patch_blank_name_is_422(client: TestClient) -> None:
    goal = make(client)
    assert client.patch(f"/goals/{goal['id']}", json={"name": " "}).status_code == 422


def test_patch_invalid_status_is_422(client: TestClient) -> None:
    goal = make(client)
    assert client.patch(f"/goals/{goal['id']}", json={"status": "bogus"}).status_code == 422


def test_patch_end_before_start_in_body_is_422(client: TestClient) -> None:
    goal = make(client)
    response = client.patch(
        f"/goals/{goal['id']}", json={"start_date": "2026-05-01", "end_date": "2026-01-01"}
    )
    assert response.status_code == 422


def test_patch_end_before_stored_start_is_422(client: TestClient) -> None:
    goal = make(client, start_date="2026-05-01")
    response = client.patch(f"/goals/{goal['id']}", json={"end_date": "2026-01-01"})
    assert response.status_code == 422
    assert client.get(f"/goals/{goal['id']}").json()["end_date"] is None


# --- delete ---

def test_delete_soft_deletes(client: TestClient, conn: sqlite3.Connection) -> None:
    goal = make(client)
    response = client.delete(f"/goals/{goal['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/goals/{goal['id']}").status_code == 404
    row = conn.execute("SELECT deleted_at FROM goals WHERE id = ?", (goal["id"],)).fetchone()
    assert row is not None and row["deleted_at"] is not None


def test_delete_missing_is_404(client: TestClient) -> None:
    assert client.delete("/goals/999").status_code == 404


def test_delete_twice_is_404(client: TestClient) -> None:
    goal = make(client)
    assert client.delete(f"/goals/{goal['id']}").status_code == 204
    assert client.delete(f"/goals/{goal['id']}").status_code == 404


def test_delete_non_integer_id_is_422(client: TestClient) -> None:
    assert client.delete("/goals/abc").status_code == 422
