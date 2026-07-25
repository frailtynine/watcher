from pydantic import BaseModel, Field


class DownloadRequest(BaseModel):
    link: str = Field(..., min_length=1, max_length=2048)


class DownloadResponse(BaseModel):
    urls: list[str]


class DownloadDeleteRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=4096)


class DownloadPreviewItem(BaseModel):
    media_id: int
    thumbnail_url: str | None = None
    media_type: str = "unknown"


class DownloadPreviewResponse(BaseModel):
    items: list[DownloadPreviewItem]


class DownloadSingleRequest(BaseModel):
    link: str = Field(..., min_length=1, max_length=2048)
    media_id: int


class DownloadSingleResponse(BaseModel):
    url: str
