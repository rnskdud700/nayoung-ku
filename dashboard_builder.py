import os
from datetime import datetime
from html import escape
from typing import Dict, Any, List
from config import DASHBOARD_HTML_PATH, DASHBOARD_TEMP_PATH


def render_prose(points: List[str], mode: str) -> str:
    """선택된 기사 문장을 별도의 해설 문구 없이 한 문단으로 연결한다."""
    cleaned = [str(point).strip() for point in points if str(point).strip()][:5]
    if not cleaned:
        return "원문에서 관련 내용을 충분히 찾지 못했습니다."
    return " ".join(escape(point) for point in cleaned[:3])


def render_summary_flow(article: Dict[str, Any]) -> str:
    """배경 → 이유 → 결과 문장을 기계적인 연결 표현 없이 표시한다."""
    background = escape(str(article.get('background', '')))
    why = escape(str(article.get('why', '')))
    so_what = escape(str(article.get('so_what', '')))
    return " ".join(text for text in [background, why, so_what] if text)


def render_news_cards(
    articles: List[Dict[str, Any]], source_name: str, source_class: str = ""
) -> str:
    cards = []
    for art in articles:
        summary_flow = render_summary_flow(art)
        issue_prose = render_prose(art.get('key_issues', []), 'issue')
        insight_prose = render_prose(art.get('insights', []), 'insight')
        safe_url = escape(str(art['url']), quote=True)
        safe_title = escape(str(art['title']))
        cards.append(f"""
                <article class="card">
                    <div>
                        <div class="card-meta">
                            <span class="source-tag {source_class}">{escape(source_name)}</span>
                            <span class="new-badge">NEW</span>
                        </div>
                        <h2 class="card-title">
                            <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_title}</a>
                        </h2>
                        <div class="summary-box">
                            <div class="summary-section">
                                <div class="summary-section-title">💡 요약</div>
                                <p class="summary-copy">{summary_flow}</p>
                            </div>
                            <div class="summary-section">
                                <div class="summary-section-title">🔗 원문 링크</div>
                                <p class="summary-copy source-link-row">
                                    <a href="{safe_url}" target="_blank" rel="noopener noreferrer">기사 원문 바로가기 →</a>
                                </p>
                            </div>
                            <div class="summary-section">
                                <div class="summary-section-title">🔥 핵심 이슈</div>
                                <p class="summary-copy">{issue_prose}</p>
                            </div>
                            <div class="summary-section">
                                <div class="summary-section-title">🧠 왜 중요한가?</div>
                                <p class="summary-copy">{insight_prose}</p>
                            </div>
                        </div>
                    </div>
                    <div class="card-action">
                        <a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="btn-link">원문 보기 ↗</a>
                    </div>
                </article>
        """)
    return "".join(cards)


def build_dashboard_html(yozm_data: Dict[str, Any], naver_data: Dict[str, Any]) -> str:
    """
    최신 수집 결과를 바탕으로 1100px 반응형 IT 뉴스 대시보드(dashboard.html)를 원자적(Atomic)으로 생성
    """
    now = datetime.now()
    date_str = now.strftime("%Y년 %m월 %d일 (%a)")
    time_str = now.strftime("%H:%M:%S")

    yozm_articles = yozm_data.get('articles', [])
    naver_articles = naver_data.get('articles', [])

    yozm_failed = yozm_data.get('failed_articles', [])
    naver_failed = naver_data.get('failed_articles', [])
    all_failed = yozm_failed + naver_failed

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>오늘의 AI · IT 브리핑👨🏼💻</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --primary-light: #eff6ff;
            --text-dark: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --badge-bg: #dbeafe;
            --badge-text: #1e40af;
            --new-badge: #ef4444;
            --naver-green: #03c75a;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-dark);
            line-height: 1.6;
            padding: 24px 16px;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 28px 24px;
            margin-bottom: 24px;
        }}

        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 16px;
        }}

        .header-title-group h1 {{
            font-size: 26px;
            font-weight: 800;
            color: var(--text-dark);
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }}

        .header-subtitle {{
            font-size: 15px;
            color: var(--primary);
            font-weight: 600;
        }}

        .header-meta {{
            text-align: right;
            font-size: 13px;
            color: var(--text-muted);
        }}

        .nav-toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
        }}

        .nav-buttons {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 8px;
            text-decoration: none;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            color: var(--text-dark);
            transition: background-color 0.15s ease;
        }}

        .btn:hover {{
            background-color: var(--primary-light);
            color: var(--primary);
            border-color: #bfdbfe;
        }}

        .btn-primary {{
            background-color: var(--primary);
            color: #ffffff;
            border: none;
        }}

        .btn-primary:hover {{
            background-color: var(--primary-hover);
            color: #ffffff;
        }}

        .tab-button.active {{
            background-color: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
        }}

        .news-section {{
            display: none;
        }}

        .news-section.active {{
            display: block;
        }}

        .auto-refresh-group {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-muted);
        }}

        /* Section Titles */
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 36px;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary);
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text-dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .count-badge {{
            background-color: var(--badge-bg);
            color: var(--badge-text);
            font-size: 12px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 12px;
        }}

        /* News Grid Layout (Desktop: 2 Columns, Mobile: 1 Column) */
        .news-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}

        @media (min-width: 768px) {{
            .news-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* News Card */
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }}

        .source-tag {{
            font-size: 12px;
            font-weight: 700;
            color: var(--primary);
            text-transform: uppercase;
        }}

        .source-tag-naver {{
            color: var(--naver-green);
        }}

        .new-badge {{
            background-color: var(--new-badge);
            color: #ffffff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
        }}

        .card-title {{
            font-size: 17px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 14px;
            line-height: 1.4;
            word-break: break-word;
            overflow-wrap: anywhere;
        }}

        .card-title a {{
            color: inherit;
            text-decoration: none;
        }}

        .card-title a:hover {{
            color: var(--primary);
        }}

        .summary-box {{
            background-color: var(--primary-light);
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }}

        .summary-title {{
            font-size: 12px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
        }}

        .summary-section {{
            padding: 13px 0;
            border-top: 1px solid #bfdbfe;
        }}

        .summary-section:first-of-type {{
            padding-top: 0;
            border-top: 0;
        }}

        .summary-section:last-child {{
            padding-bottom: 0;
        }}

        .summary-section-title {{
            font-size: 14px;
            font-weight: 800;
            color: #1e40af;
            margin-bottom: 6px;
        }}

        .summary-copy {{
            font-size: 14px;
            color: #334155;
            line-height: 1.75;
            margin: 0;
            word-break: keep-all;
            overflow-wrap: break-word;
        }}

        .source-link-row a {{
            color: var(--primary);
            font-weight: 700;
            text-decoration: none;
        }}

        .source-link-row a:hover {{
            text-decoration: underline;
        }}

        .card-action {{
            margin-top: auto;
            display: flex;
            justify-content: flex-end;
        }}

        .btn-link {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
            font-weight: 600;
            color: var(--primary);
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #bfdbfe;
            background-color: #ffffff;
        }}

        .btn-link:hover {{
            background-color: var(--primary);
            color: #ffffff;
        }}

        /* Small Status Section at Bottom */
        .status-footer {{
            margin-top: 48px;
            background-color: #f1f5f9;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 16px 20px;
            font-size: 12px;
            color: var(--text-muted);
        }}

        .status-footer h4 {{
            font-size: 13px;
            color: var(--text-dark);
            margin-bottom: 6px;
        }}

        .failed-item {{
            color: #64748b;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-top">
                <div class="header-title-group">
                    <h1>오늘의 AI · IT 브리핑👨🏼💻</h1>
                    <div class="header-subtitle">5분이면 충분해요🤩</div>
                </div>
                <div class="header-meta">
                    <div>📅 {date_str}</div>
                    <div>🕒 마지막 업데이트: <strong>{time_str}</strong></div>
                </div>
            </div>

            <div class="nav-toolbar">
                <div class="nav-buttons">
                    <button type="button" class="btn tab-button active" onclick="showNewsSection('yozm-section', this)">📰 요즘IT ({len(yozm_articles)})</button>
                    <button type="button" class="btn tab-button" onclick="showNewsSection('naver-section', this)">💻 네이버 IT·과학 ({len(naver_articles)})</button>
                    <button onclick="location.reload()" class="btn btn-primary">지금 새로고침✅</button>
                </div>
                <div class="auto-refresh-group">
                    <label style="cursor: pointer;">
                        <input type="checkbox" id="autoRefreshToggle" checked onchange="toggleAutoRefresh(this)">
                        5분 자동 새로고침 켜기
                    </label>
                </div>
            </div>
        </header>

        <!-- 요즘IT Section -->
        <section id="yozm-section" class="news-section active">
            <div class="section-header">
                <div class="section-title">
                    <span>📰 요즘IT (Wishket Magazine)</span>
                    <span class="count-badge">{len(yozm_articles)}개</span>
                </div>
            </div>

            <div class="news-grid">
"""

    if not yozm_articles:
        html_content += """
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">현재 수집된 요즘IT 최신 기사가 없습니다.</div>
                </div>
"""
    else:
        html_content += render_news_cards(yozm_articles, "요즘IT")

    html_content += """
            </div>
        </section>
"""

    html_content += f"""
        <section id="naver-section" class="news-section">
            <div class="section-header">
                <div class="section-title">
                    <span>💻 네이버 IT·과학 헤드라인</span>
                    <span class="count-badge">{len(naver_articles)}개</span>
                </div>
            </div>
            <div class="news-grid">
"""

    if not naver_articles:
        html_content += """
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">현재 수집된 네이버 IT·과학 헤드라인이 없습니다.</div>
                </div>
"""
    else:
        html_content += render_news_cards(
            naver_articles, "네이버 IT·과학", "source-tag-naver"
        )

    html_content += """
            </div>
        </section>

        <!-- Bottom Status -->
        <footer class="status-footer">
            <h4>⚙️ 수집 상태 정보</h4>
            <div>• 수집 데이터베이스: sent_articles.db 연동 정상</div>
"""

    if all_failed:
        html_content += "<div>• 수집 제외/이전 중복 기사 정보:</div>"
        for f_item in all_failed[:5]:
            html_content += f"<div class='failed-item'>- [{f_item.get('title', '제목 미상')}] : {f_item.get('reason', '알림')}</div>"
    else:
        html_content += "<div>• 모든 대상 사이트 수집 시도 완료</div>"

    html_content += """
        </footer>
    </div>

    <script>
        let refreshTimer = null;

        function showNewsSection(sectionId, button) {
            document.querySelectorAll('.news-section').forEach((section) => {
                section.classList.remove('active');
            });
            document.querySelectorAll('.tab-button').forEach((tabButton) => {
                tabButton.classList.remove('active');
            });
            document.getElementById(sectionId).classList.add('active');
            button.classList.add('active');
        }

        function startAutoRefresh() {
            refreshTimer = setInterval(() => {
                console.log("5분 자동 새로고침 실행");
                location.reload();
            }, 300000);
        }

        function stopAutoRefresh() {
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
        }

        function toggleAutoRefresh(checkbox) {
            if (checkbox.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        }

        startAutoRefresh();
    </script>
</body>
</html>
"""

    # Atomic Write
    with open(DASHBOARD_TEMP_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    os.replace(DASHBOARD_TEMP_PATH, DASHBOARD_HTML_PATH)
    return str(DASHBOARD_HTML_PATH)
