def no_data_response(message: str, data=None):
    return {
        "status": "no_data",
        "message": message,
        "data": data,
    }


def error_response(message: str, error: str | None = None, data=None):
    payload = {
        "status": "error",
        "message": message,
        "data": data,
    }

    if error:
        payload["error"] = error

    return payload