import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


BASE_VIDEO_JSON = {
    "name": "video-canvas",
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration": 60,
    "layers": [],
}


async def test_create_video_project_success(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "My Project",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [
                "https://example.com/a.mp4",
                "https://example.com/b.mp4",
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert data["video_json"]["name"] == "video-canvas"
    assert len(data["clip_urls"]) == 2
    assert "id" in data


async def test_create_video_project_rejects_too_many_clips(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "Too Many Clips",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [f"https://example.com/{i}.mp4" for i in range(51)],
        },
    )
    assert response.status_code == 422


async def test_list_video_projects(
    client: AsyncClient,
    auth_headers: dict,
):
    create_response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "List Test",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [],
        },
    )
    assert create_response.status_code == 201

    response = await client.get("/api/videos/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "List Test"


async def test_get_video_project(
    client: AsyncClient,
    auth_headers: dict,
):
    create_response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "Get Test",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [],
        },
    )
    assert create_response.status_code == 201
    video_id = create_response.json()["id"]

    response = await client.get(
        f"/api/videos/{video_id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == video_id


async def test_update_video_project(
    client: AsyncClient,
    auth_headers: dict,
):
    create_response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "Before Update",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [],
        },
    )
    assert create_response.status_code == 201
    video_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/videos/{video_id}",
        headers=auth_headers,
        json={
            "name": "After Update",
            "clip_urls": ["https://example.com/new.mp4"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "After Update"
    assert data["clip_urls"] == ["https://example.com/new.mp4"]


async def test_delete_video_project(
    client: AsyncClient,
    auth_headers: dict,
):
    create_response = await client.post(
        "/api/videos/",
        headers=auth_headers,
        json={
            "name": "To Delete",
            "video_json": BASE_VIDEO_JSON,
            "clip_urls": [],
        },
    )
    assert create_response.status_code == 201
    video_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/videos/{video_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/videos/{video_id}", headers=auth_headers
    )
    assert get_response.status_code == 404
