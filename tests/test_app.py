import pytest


def test_homepage_returns_successful_response(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'",
        ),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "same-origin"),
    ],
)
def test_security_headers_are_present(client, header, expected):
    response = client.get("/")

    assert response.headers.get(header) == expected
