from curl_cffi import requests


def run(headers, user_input):
    """Get all recently accessed patients from Practice Fusion."""
    base_url = BASE_URL

    try:
        result = _call_api(base_url, headers)
        return result
    except Exception as e:
        return {'status_code': 500, 'body': {'error': str(e)}}

# === PRIVATE ===

def _call_api(base_url, headers):
    """Fetch recently accessed patients from the API."""
    request_headers = {
        "authorization": headers.get("Authorization", ""),
        "x-ehr-user-guid": headers.get("x-ehr-user-guid", ""),
        "x-practice-guid": headers.get("x-practice-guid", ""),
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer": f"{base_url}/apps/ehr/index.html",
        "pf-trace-info": "PX=pf",
    }

    response = requests.get(
        f"{base_url}/ChartingEndpoint/api/v2/Access/Recent",
        headers=request_headers,
        impersonate="chrome131",
        timeout=30
    )

    if response.status_code == 401:
        return {'status_code': 401, 'body': {'error': 'Session expired'}}

    if response.status_code == 302 or 'login' in response.url.lower():
        return {'status_code': 401, 'body': {'error': 'Session expired'}}

    try:
        result = response.json()
    except Exception:
        if 'login' in response.text.lower():
            return {'status_code': 401, 'body': {'error': 'Session expired'}}
        return {'status_code': response.status_code, 'body': {'error': 'Invalid response', 'raw': response.text[:500]}}

    return {'status_code': response.status_code, 'body': result}
