import json
import os
import webbrowser

DB_FILE = 'okx_database.json'
REPORT_FILE = 'OKX_Full_Analytics.html'

def generate_dashboard():
    if not os.path.exists(DB_FILE): return

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # === 数据准备 ===
    # 1. 币种排行
    all_coins = list(db['coins'].values())
    all_coins.sort(key=lambda x: x['heat_score'], reverse=True)
    # top_coins = all_coins[:50] # Removed limit as requested
    top_coins = all_coins 

    # 将数据存储在全局变量中，避免 HTML 中的转义问题
    global_coins_data = {str(i): c for i, c in enumerate(top_coins)}
    
    # 2. 历史公告 (按时间倒序)
    history_news = sorted(db['news_history'], key=lambda x: x['date'], reverse=True)

    # 3. 统计数据
    stats = {
        'total_coins': len(all_coins),
        'total_news': len(history_news),
        'upcoming': len([c for c in all_coins if c['status'] == 'upcoming']),
        'high_heat': len([c for c in all_coins if c['heat_score'] > 100])
    }

    # === 生成 HTML 片段 ===
    
    # 历史时间轴 (Timeline)
    timeline_html = ""
    for news in history_news[:50]: # Expanded history limit to 50
        icon = "📢"
        color = "bg-light"
        if "上新" in news['category']: icon = "🚀"; color = "bg-success-subtle"
        if "挖矿" in news['category']: icon = "⛏️"; color = "bg-warning-subtle"
        if "下线" in news['category']: icon = "⚠️"; color = "bg-danger-subtle"
        
        related = "".join([f'<span class="badge bg-white text-dark border ms-1">{c}</span>' for c in news['related_coins']])
        
        timeline_html += f"""
        <div class="timeline-item p-3 mb-3 rounded {color} border-start border-4 border-secondary">
            <div class="d-flex justify-content-between">
                <small class="text-muted">{news['date']}</small>
                <span class="badge bg-dark">{news['category']}</span>
            </div>
            <div class="mt-2 fw-bold">{icon} {news['title']}</div>
            <div class="mt-2">{related}</div>
            <a href="{news['url']}" target="_blank" class="btn btn-sm btn-outline-secondary mt-2 w-100">
                <i class="fas fa-external-link-alt"></i> 查看完整公告
            </a>
        </div>
        """

    # 新板块：公告上新币种深度分析
    # 筛选出最近公告中的上新币种
    listing_coins_html = ""
    listing_coins_set = set()
    
    for news in history_news[:50]: # 最近 50 条公告
        if "上新" in news['category'] or "上线" in news['title']:
            for sym in news['related_coins']:
                if sym not in listing_coins_set:
                    listing_coins_set.add(sym)
                    
                    # 从数据库获取详细信息
                    c_data = next((c for c in all_coins if c['symbol'] == sym), None)
                    if c_data:
                        heat = c_data.get('heat_score', 0)
                        kws_count = len(c_data.get('keywords', []))
                        
                        # 找到对应的 global_id
                        global_id = next((k for k, v in global_coins_data.items() if v['symbol'] == sym), None)
                        
                        action_btn = ""
                        if global_id:
                            action_btn = f"""<button class="btn btn-sm btn-primary" onclick="openModal('{global_id}')">分析详情</button>"""
                        else:
                            # 即使没有挖掘数据，也提供一个搜索按钮
                            action_btn = f"""<a href="https://www.google.com/search?q={sym}+怎么买" target="_blank" class="btn btn-sm btn-outline-secondary">去 Google 搜</a>"""
                        
                        listing_coins_html += f"""
                        <div class="col-md-4 mb-3">
                            <div class="card h-100 border-success">
                                <div class="card-header bg-success text-white d-flex justify-content-between">
                                    <span class="fw-bold">{sym}</span>
                                    <span class="badge bg-light text-success">{heat} 🔥</span>
                                </div>
                                <div class="card-body">
                                    <p class="card-text small text-muted">来自公告: {news['title'][:20]}...</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="small">{kws_count} 个关键词</span>
                                        {action_btn}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """

    # 币种表格
    table_html = ""
    for idx, c in enumerate(top_coins):
        kws_html = "".join([f'<span class="badge bg-light text-dark border me-1">{k["kw"]}</span>' for k in c['keywords'][:3]])
        status_badge = '<span class="badge bg-warning text-dark">预热中</span>' if c['status'] == 'upcoming' else '<span class="badge bg-success">已上线</span>'
        
        # 决策辅助逻辑
        strategy = '<span class="badge bg-secondary">观望</span>'
        if c['status'] == 'upcoming':
            strategy = '<span class="badge bg-primary">🚀 抢跑埋词</span>'
        elif c['heat_score'] > 100:
            strategy = '<span class="badge bg-danger">🔥 蹭热度</span>'
        elif c['heat_score'] > 50:
            strategy = '<span class="badge bg-info text-dark">📈 潜力</span>'
            
        first_seen = c.get('first_seen', 'N/A')

        table_html += f"""
        <tr>
            <td>#{idx+1}</td>
            <td>
                <div class="fw-bold">{c['symbol']}</div>
            </td>
            <td>{status_badge}</td>
            <td class="text-danger fw-bold">{c['heat_score']} 🔥</td>
            <td>{strategy}</td>
            <td><small class="text-muted">{first_seen}</small></td>
            <td>{kws_html}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openModal('{idx}')">详情</button>
            </td>
        </tr>
        """

    # === HTML 模板 ===
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>OKX 全景分析大盘 Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background: #f0f2f5; font-family: 'Segoe UI', sans-serif; }}
        .sidebar {{ height: 100vh; overflow-y: auto; background: white; padding: 20px; border-right: 1px solid #ddd; }}
        .main {{ height: 100vh; overflow-y: auto; padding: 20px; }}
        .card {{ border: none; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .timeline-item {{ transition: transform 0.2s; }}
        .timeline-item:hover {{ transform: translateX(5px); }}
        .kpi-num {{ font-size: 2rem; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3 sidebar">
                <h5 class="fw-bold mb-4">📅 历史脉络 (Timeline)</h5>
                {timeline_html}
            </div>

            <div class="col-md-9 main">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 class="fw-bold">📊 OKX 垂直 SEO 指挥部 Pro</h2>
                        <span class="text-muted">全量数据模式 | 决策辅助已开启</span>
                    </div>
                    <span class="badge bg-dark p-2">DB: {DB_FILE}</span>
                </div>

                <div class="row mb-4">
                    <div class="col-md-3"><div class="card p-3 text-center"><div class="kpi-num text-primary">{stats['total_coins']}</div><small>收录币种 (无限制)</small></div></div>
                    <div class="col-md-3"><div class="card p-3 text-center"><div class="kpi-num text-success">{stats['upcoming']}</div><small>潜在机会 (未交易)</small></div></div>
                    <div class="col-md-3"><div class="card p-3 text-center"><div class="kpi-num text-danger">{stats['high_heat']}</div><small>高热度词</small></div></div>
                    <div class="col-md-3"><div class="card p-3 text-center"><div class="kpi-num text-info">{stats['total_news']}</div><small>历史公告归档</small></div></div>
                </div>

                <!-- 延伸板块：智能决策建议 -->
                <div class="card p-4 bg-primary-subtle border border-primary">
                    <h5 class="fw-bold mb-3 text-primary"><i class="fas fa-lightbulb"></i> 💡 智能决策建议 (Alpha Signals)</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>🚀 重点抢跑 (未上线 + 有热度)</h6>
                            <p class="small text-muted">这些币种尚未在 OKX 交易，但已经有了搜索热度，是埋伏 SEO 的绝佳机会。</p>
                            <div class="d-flex flex-wrap gap-2">
                                {"".join([f'<span class="badge bg-primary">{c["symbol"]} ({c["heat_score"]})</span>' for c in top_coins if c['status'] == 'upcoming' and c['heat_score'] > 0][:10]) or "暂无高热度新币"}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>🔥 流量收割 (已上线 + 超高热度)</h6>
                            <p class="small text-muted">全网热搜的 OKX 币种，适合写行情分析、价格预测类文章。</p>
                            <div class="d-flex flex-wrap gap-2">
                                {"".join([f'<span class="badge bg-danger">{c["symbol"]} ({c["heat_score"]})</span>' for c in top_coins if c['status'] == 'trading' and c['heat_score'] > 100][:10]) or "暂无爆发币种"}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 新板块：公告上新币种深度分析 -->
                <div class="card p-4">
                    <h5 class="fw-bold mb-3 text-success"><i class="fas fa-bullhorn"></i> 🚀 公告直达新币 (Listing Alpha)</h5>
                    <p class="text-muted small">来自最近公告提到的新币种，建议优先关注。</p>
                    <div class="row">
                        {listing_coins_html or '<div class="col-12 text-center text-muted">暂无近期上新公告</div>'}
                    </div>
                </div>

                <div class="card p-4">
                    <h5 class="fw-bold mb-3">🔥 全量价值币种排行榜</h5>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>排名</th>
                                    <th>币种</th>
                                    <th>状态</th>
                                    <th>热度</th>
                                    <th>策略建议</th>
                                    <th>首次收录</th>
                                    <th>关键词预览</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>{table_html}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="detailModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header"><h5 class="modal-title" id="mTitle"></h5><button class="btn-close" data-bs-dismiss="modal"></button></div>
                <div class="modal-body">
                    <button class="btn btn-dark w-100 mb-3" onclick="copyKws()">复制所有关键词</button>
                    <ul class="list-group" id="mList"></ul>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const modal = new bootstrap.Modal(document.getElementById('detailModal'));
        const globalData = {json.dumps(global_coins_data)};
        let currData = null;

        function openModal(id) {{
            currData = globalData[id];
            document.getElementById('mTitle').innerText = currData.symbol + " 流量详情";
            
            const list = document.getElementById('mList');
            list.innerHTML = "";
            currData.keywords.forEach(k => {{
                list.innerHTML += `<li class="list-group-item d-flex justify-content-between">
                    <span>${{k.kw}}</span> <span class="badge bg-secondary">${{k.score}}</span>
                </li>`;
            }});
            modal.show();
        }}

        function copyKws() {{
            const text = currData.keywords.map(k => k.kw).join("\\n");
            navigator.clipboard.writeText(text).then(() => alert("已复制"));
        }}
    </script>
</body>
</html>
    """

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"🎉 大盘已生成: {REPORT_FILE}")
    webbrowser.open('file://' + os.path.abspath(REPORT_FILE))

if __name__ == "__main__":
    generate_dashboard()
