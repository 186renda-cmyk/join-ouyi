import requests
import xml.etree.ElementTree as ET
import os

def submit_to_indexnow():
    # 配置信息
    host = "join-ouyi.top"
    key_file = "59e28037c6494a828856707850234123.txt"
    key_location = f"https://{host}/{key_file}"
    
    # 1. 读取 API Key
    try:
        with open(key_file, 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print(f"错误: 找不到密钥文件 {key_file}")
        return

    # 2. 从 sitemap.xml 读取所有 URL
    urls = []
    try:
        tree = ET.parse('sitemap.xml')
        root = tree.getroot()
        # 处理带有命名空间的 XML
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace).text
            if loc:
                urls.append(loc)
    except Exception as e:
        print(f"读取 sitemap.xml 出错: {e}")
        return

    if not urls:
        print("没有找到需要提交的 URL")
        return

    print(f"准备提交 {len(urls)} 个 URL...")
    for url in urls:
        print(f" - {url}")

    # 3. 构造 IndexNow 请求
    payload = {
        "host": host,
        "key": api_key,
        "keyLocation": key_location,
        "urlList": urls
    }

    # 4. 发送请求
    endpoint = "https://api.indexnow.org/indexnow"
    try:
        response = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json; charset=utf-8"})
        
        if response.status_code == 200:
            print("\n✅ 提交成功！必应已收到 URL 推送。")
        elif response.status_code == 202:
            print("\n✅ 提交成功！请求已被接受。")
        else:
            print(f"\n❌ 提交失败。状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 请求发送出错: {e}")

if __name__ == "__main__":
    submit_to_indexnow()
