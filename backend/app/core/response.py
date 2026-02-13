from typing import Any


def api_response(status: str, message: str, data: Any | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "data": data if data is not None else {},
    }
