import requests
import json

API_NEWS = "https://www.okx.com/api/v5/support/announcements?limit=5"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

try:
    print("Requesting OKX API...")
    resp = requests.get(API_NEWS, headers=HEADERS, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        if 'data' in data and len(data['data']) > 0:
            print("First item structure:")
            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
        else:
            print("No data found or empty data list.")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
