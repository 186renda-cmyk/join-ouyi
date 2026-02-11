import requests
import time
import json
import os
from datetime import datetime

# ================= 配置区域 =================
# 监控间隔 (秒)
CHECK_INTERVAL = 60 

# OKX API (无需密钥，公共接口)
API_URL = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"

# 本地数据库 (用来存已知的币，防止重复报警)
DB_FILE = "known_coins.json"
# ===========================================

def load_known_coins():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_known_coins(coins):
    with open(DB_FILE, 'w') as f:
        json.dump(list(coins), f)

def get_okx_spot_coins():
    try:
        # 伪装成浏览器，虽然 OKX API 一般不封，但保险起见
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(API_URL, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data['code'] == '0':
                # 提取所有基础币种 (如 BTC-USDT -> BTC)
                coins = set()
                for item in data['data']:
                    base_ccy = item['baseCcy']
                    coins.add(base_ccy)
                return coins
    except Exception as e:
        print(f"⚠️ 网络请求失败: {e}")
    return None

def main():
    print("📡 OKX 闪电雷达启动！正在初始化数据库...")
    
    # 1. 第一次运行，先建立基准库
    current_coins = get_okx_spot_coins()
    if not current_coins:
        print("❌ 无法连接 OKX API，请检查网络 (可能需要代理)")
        return

    known_coins = load_known_coins()
    
    # 如果是第一次运行，把当前所有币存入库，不报警
    if not known_coins:
        print(f"✅ 初始化完成！当前收录 {len(current_coins)} 个币种。")
        print("👀 开始监控... (有新币上线我会立刻提示)")
        save_known_coins(current_coins)
        known_coins = current_coins
    else:
        # 如果库里有数据，检查是否有新增 (弥补关闭脚本期间的更新)
        new_on_start = current_coins - known_coins
        if new_on_start:
            print(f"🔥 [补录] 在你休息期间，OKX 上线了: {', '.join(new_on_start)}")
            known_coins.update(new_on_start)
            save_known_coins(known_coins)

    # 2. 循环监控
    while True:
        try:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 扫描中...", end="")
            latest_coins = get_okx_spot_coins()
            
            if latest_coins:
                # 找出新币 (最新列表 - 已知列表)
                new_coins = latest_coins - known_coins
                
                if new_coins:
                    print("\n" + "="*40)
                    print(f"🚨🚨🚨 发现新币上线！！！ 🚨🚨🚨")
                    for coin in new_coins:
                        print(f"🔥 币种: {coin}")
                        print(f"👉 写作建议: 赶紧写《{coin} 怎么买》、《{coin} 欧易充值教程》")
                    print("="*40)
                    
                    # 更新数据库
                    known_coins.update(new_coins)
                    save_known_coins(known_coins)
                    
                    # 【联动】自动把新币写入 seeds.txt，方便你直接跑 miner.py
                    with open("seeds.txt", "a") as f:
                        for coin in new_coins:
                            f.write(f"\n{coin} 怎么买")
                            f.write(f"\n{coin} 价格")
                    print("✅ 已自动添加到 seeds.txt，你可以直接去跑 miner.py 挖词了！")
                    
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 监控停止")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()