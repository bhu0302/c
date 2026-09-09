import requests


def push_to_external_system(
    payload,
    target_url,
    api_token=None
):
    """
    Push BP merge payload to external system.

    payload:
        Python dictionary containing retained/unretained BP data

    target_url:
        Target REST API URL

    api_token:
        Optional Bearer authentication token
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    try:

        response = requests.post(
            target_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        # Try reading JSON response
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        if response.ok:

            return {
                "success": True,
                "http_status": response.status_code,
                "message": "BP merge data pushed successfully",
                "response": response_data,
            }

        return {
            "success": False,
            "http_status": response.status_code,
            "message": "Target system rejected BP merge data",
            "response": response_data,
        }

    except requests.Timeout:

        return {
            "success": False,
            "http_status": None,
            "message": "Target system timeout",
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "http_status": None,
            "message": f"Connection error: {exc}",
        }

    except Exception as exc:

        return {
            "success": False,
            "http_status": None,
            "message": f"Unexpected error: {exc}",
        }