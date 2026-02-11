import requests
import json
import time
import re
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

DB_FILE = 'okx_database.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_suggestions(query):
    results = []
    try: # Google
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={query}&hl=zh-CN"
        r = requests.get(url, headers=HEADERS, timeout=2)
        if r.status_code == 200:
            suggs = json.loads(r.text)[1]
            for w in suggs: results.append({'kw': w, 'src': 'Google'})
    except: pass
    try: # Bing
        url = f"https://api.bing.com/qsonhs.aspx?q={query}&mkt=zh-CN"
        r = requests.get(url, headers=HEADERS, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if 'AS' in data and 'Results' in data['AS']:
                suggs = [item['Txt'] for item in data['AS']['Results'][0]['Suggests']]
                for w in suggs: results.append({'kw': w, 'src': 'Bing'})
    except: pass
    return results

def mine_coin(symbol):
    # 针对性探测
    seeds = [f"{symbol} 怎么买", f"{symbol} 价格", f"{symbol} 欧易"]
    
    unique_kws = {}
    heat = 0
    
    for seed in seeds:
        suggs = get_suggestions(seed)
        for item in suggs:
            kw = item['kw']
            # 清洗
            if symbol.lower() not in kw.lower(): continue
            has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', kw))
            
            if has_chinese or item['src'] == 'Google': # Google 权重高
                if kw not in unique_kws:
                    score = 10
                    if "怎么买" in kw or "教程" in kw: score += 50
                    if "欧易" in kw: score += 30
                    
                    unique_kws[kw] = {
                        'kw': kw,
                        'src': item['src'],
                        'score': score
                    }
                    heat += score
        time.sleep(0.2)
        
    return list(unique_kws.values()), heat

def run_miner():
    if not os.path.exists(DB_FILE): return
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    # 筛选挖掘目标：优先挖“未交易”的(新币) 和 “热度为0”的(没挖过)
    # 为了效率，每次只挖 100 个最有潜力的
    targets = []
    for sym, data in db['coins'].items():
        if data['status'] == 'upcoming' or data['heat_score'] == 0:
            targets.append(sym)
    
    # 如果目标太多，截取前100个，防止跑太久
    targets = targets[:100]
    
    print(f"⛏️  开始挖掘 {len(targets)} 个重点币种...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_sym = {executor.submit(mine_coin, sym): sym for sym in targets}
        completed = 0
        for future in as_completed(future_to_sym):
            sym = future_to_sym[future]
            completed += 1
            try:
                kws, heat = future.result()
                # 更新数据库
                if kws:
                    db['coins'][sym]['keywords'] = kws
                    db['coins'][sym]['heat_score'] = heat
                    print(f"\r[{completed}/{len(targets)}] 更新: {sym} (热度 {heat})", end="")
            except: pass
            
    # 保存回数据库
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 挖掘完成！数据已回写至 {DB_FILE}")
    print("👉 请运行 3_Analytics_Dashboard.py 生成全景大屏")

if __name__ == "__main__":
    run_miner()