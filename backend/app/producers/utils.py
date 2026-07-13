from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def clear_utm_params(url: str) -> str:
    """Return URL with all UTM query params removed."""
    parsed = urlsplit(url)
    if not parsed.query:
        return url

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]

    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(filtered_query, doseq=True),
            parsed.fragment,
        )
    )
