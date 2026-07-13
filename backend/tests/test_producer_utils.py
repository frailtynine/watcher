import pytest

from app.producers.utils import clear_utm_params


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://example.com/news?utm_source=google&utm_medium=cpc&id=42",
            "https://example.com/news?id=42",
        ),
        (
            "https://example.com/news?id=42&utm_campaign=spring",
            "https://example.com/news?id=42",
        ),
        (
            "https://example.com/news?ID=42&UtM_Source=x&utm_content=y",
            "https://example.com/news?ID=42",
        ),
        (
            "https://example.com/news?foo=bar#section",
            "https://example.com/news?foo=bar#section",
        ),
        (
            "https://example.com/news#section",
            "https://example.com/news#section",
        ),
    ],
)
def test_clear_utm_params(url: str, expected: str):
    assert clear_utm_params(url) == expected
