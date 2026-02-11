import requests
import json
import os
import re
from datetime import datetime

# ================= 配置 =================
DB_FILE = 'okx_database.json'  # 永久数据库
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'x-locale': 'zh_CN', # 尝试强制中文 locale
    'x-utc': '8'
}

# OKX API
API_SPOT = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"
API_NEWS = "https://www.okx.com/api/v5/support/announcements?limit=100" # 一次抓100条历史

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'coins': {}, 'news_history': []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_text(text):
    # 策略 1: 提取括号内的内容 (通常是全称，如 Zama)
    brackets = re.findall(r'\((.*?)\)', text)
    
    # 策略 2: 提取大写字母组成的 Token Symbol (如 ZAMA, ESP)
    # 排除常见的非币种大写词
    filter_words = {
        'OKX', 'USDT', 'USDC', 'API', 'APP', 'WEB3', 'WALLET', 'LISTING', 'SUPPORT', 'DELISTING', 
        'SYSTEM', 'UPDATE', 'FEE', 'TOKEN', 'PAIRS', 'GROUP', 'ADVANCE', 'NOTICE', 'USD', 'BTC', 'ETH'
    }
    
    # 匹配连续的2个以上大写字母，且前后不是小写字母（避免匹配到单词中间的部分）
    candidates = re.findall(r'\b[A-Z0-9]{2,}\b', text)
    
    keywords = set(brackets + candidates)
    
    # 清洗：去除在过滤列表中的词，去除纯数字
    valid_coins = []
    for w in keywords:
        w_upper = w.strip().upper()
        if w_upper not in filter_words and not w_upper.isdigit():
            valid_coins.append(w_upper)
            
    return valid_coins

def run_collector():
    print("⏳ 启动【时光机】搜集系统...")
    db = load_db()
    
    # 1. 更新币种列表 (现货)
    print("   -> 同步 OKX 交易对...")
    try:
        resp = requests.get(API_SPOT, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            for item in resp.json()['data']:
                symbol = item['baseCcy']
                if symbol not in db['coins']:
                    db['coins'][symbol] = {
                        'symbol': symbol,
                        'status': 'trading',
                        'first_seen': datetime.now().strftime("%Y-%m-%d"),
                        'keywords': [], # 留给miner填
                        'heat_score': 0
                    }
    except Exception as e:
        print(f"❌ 币种同步失败: {e}")

    # 2. 回溯历史公告 (抓取脉络)
    print("   -> 抓取 OKX 历史公告 (构建时间轴)...")
    try:
        resp = requests.get(API_NEWS, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            # 修复：API 返回结构变更，数据在 data[0]['details'] 中
            api_resp = resp.json()
            news_data = []
            
            if 'data' in api_resp and isinstance(api_resp['data'], list) and len(api_resp['data']) > 0:
                # 尝试获取第一项中的 details
                first_item = api_resp['data'][0]
                if isinstance(first_item, dict) and 'details' in first_item:
                    news_data = first_item['details']
            
            # 兜底：如果 data 本身就是 details (旧结构)
            if not news_data and 'data' in api_resp and isinstance(api_resp['data'], list):
                 # 检查是否直接是公告列表
                 if len(api_resp['data']) > 0 and 'title' in api_resp['data'][0]:
                     news_data = api_resp['data']
                
            new_count = 0
            
            # 使用字典索引，允许覆盖旧数据（如语言更新）
            history_map = {n['url']: n for n in db['news_history']}
            
            for item in reversed(news_data): # 倒序处理
                # 增强健壮性
                if not isinstance(item, dict): continue
                url = item.get('url')
                if not url: continue
                    
                title = item.get('title', 'No Title')
                p_time = item.get('pTime')
                
                # 简单分类
                category = "📢 公告"
                if "上线" in title or "List" in title: category = "🚀 上新"
                if "Delist" in title or "下线" in title: category = "⚠️ 下线"
                if "Jumpstart" in title or "挖矿" in title: category = "⛏️ 挖矿"
                
                # 提取关联币种
                related_coins = clean_text(title)
                
                # 时间处理
                try:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    if p_time:
                        date_str = datetime.fromtimestamp(int(p_time)/1000).strftime("%Y-%m-%d")
                except:
                    date_str = datetime.now().strftime("%Y-%m-%d")

                # 更新或新增 (Key 是 URL)
                history_map[url] = {
                    'title': title,
                    'date': date_str,
                    'category': category,
                    'related_coins': related_coins,
                    'url': url
                }
                
                # 如果公告里出现了新币，也加到 coins 库里
                for coin in related_coins:
                    if coin not in db['coins']:
                        db['coins'][coin] = {
                            'symbol': coin,
                            'status': 'upcoming',
                            'first_seen': date_str,
                            'keywords': [],
                            'heat_score': 0
                        }
                new_count += 1
            
            # 将 map 还原回 list
            db['news_history'] = sorted(list(history_map.values()), key=lambda x: x['date'], reverse=True)
            
            print(f"   -> 已处理 {new_count} 条公告 (含更新)。")
            
    except Exception as e:
        print(f"❌ 公告抓取失败: {e}")

    # 保存
    save_db(db)
    print(f"✅ 数据库更新完毕！当前收录 {len(db['coins'])} 个币种，{len(db['news_history'])} 条历史脉络。")
    print("👉 请运行 2_Database_Miner.py")

if __name__ == "__main__":
    run_collector()