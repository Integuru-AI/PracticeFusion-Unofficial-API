from curl_cffi import requests


def run(headers, user_input):
    """Get all recently accessed patients from Practice Fusion."""
    base_url = BASE_URL

    response = requests.get(
        f"{base_url}/ChartingEndpoint/api/v2/Access/Recent",
        headers={
            "authorization": headers.get("Authorization", ""),
            "x-ehr-user-guid": headers.get("x-ehr-user-guid", ""),
            "x-practice-guid": headers.get("x-practice-guid", ""),
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": f"{base_url}/apps/ehr/index.html",
            "origin": base_url,
            "pf-trace-info": "PX=pf",
            "cookie": headers.get("Cookie", ""),
        },
        impersonate="chrome131",
        timeout=30,
    )

    if response.status_code == 401:
        return {"status_code": 401, "body": {"error": "Session expired"}}

    try:
        body = response.json()
    except Exception:
        return {
            "status_code": response.status_code,
            "body": {"error": "Failed to parse response", "raw": response.text[:500]},
        }

    return {"status_code": response.status_code, "body": body}
