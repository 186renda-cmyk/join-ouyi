import requests
import json

API_NEWS = "https://www.okx.com/api/v5/support/announcements?limit=5"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'x-locale': 'zh_CN',
    'x-utc': '8'
}

print("Testing OKX API for Chinese content...")
try:
    resp = requests.get(API_NEWS, headers=HEADERS, timeout=10)
    data = resp.json()
    
    # Check structure
    items = []
    if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
        if 'details' in data['data'][0]:
            items = data['data'][0]['details']
        else:
            items = data['data']
            
    for item in items[:3]:
        print(f"Title: {item.get('title')}")
        print(f"URL: {item.get('url')}")
        print("-" * 20)
        
except Exception as e:
    print(f"Error: {e}")
