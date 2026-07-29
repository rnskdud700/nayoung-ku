import sys
import traceback
from config import DASHBOARD_HTML_PATH, LOGS_DIR
from database import init_db, record_article
from scrapers import YozmITScraper, NaverITScraper
from summarizer import summarize_article
from dashboard_builder import build_dashboard_html

def run_dashboard_pipeline():
    print("=" * 60)
    print("🚀 IT 뉴스 대시보드 데이터 수집 및 갱신 시작")
    print("=" * 60)
    
    # 1. DB 초기화
    print("\n[1/4] SQLite 데이터베이스 연결 확인 중...")
    init_db()
    print("   └─ DB 준비 완료 (sent_articles.db)")

    # 2. 요즘IT 수집 및 요약
    print("\n[2/4] 요즘IT 최신 기사 수집 중...")
    yozm_scraper = YozmITScraper()
    yozm_result = yozm_scraper.fetch_articles()
    
    print(f"   └─ 요즘IT 수집 완료: {len(yozm_result['articles'])}개 기사")
    for art in yozm_result['articles']:
        summary_data = summarize_article(art['title'], art['body'])
        art['background'] = summary_data['background']
        art['why'] = summary_data['why']
        art['so_what'] = summary_data['so_what']
        art['key_issues'] = summary_data['key_issues']
        art['insights'] = summary_data['insights']
        record_article(art['url'], art['title'], art['source'])
        print(f"      • {art['title'][:40]}... (요약 및 DB 기록 완료)")

    # 3. 네이버 IT/과학 헤드라인 수집 및 원문 기반 항목 추출
    print("\n[3/4] 네이버 IT/과학 헤드라인 수집 중...")
    naver_scraper = NaverITScraper()
    naver_result = naver_scraper.fetch_articles()

    print(f"   └─ 네이버 IT/과학 수집 완료: {len(naver_result['articles'])}개 기사")
    for art in naver_result['articles']:
        summary_data = summarize_article(art['title'], art['body'])
        art['background'] = summary_data['background']
        art['why'] = summary_data['why']
        art['so_what'] = summary_data['so_what']
        art['key_issues'] = summary_data['key_issues']
        art['insights'] = summary_data['insights']
        record_article(art['url'], art['title'], art['source'])
        print(f"      • {art['title'][:40]}... (요약 및 DB 기록 완료)")

    # 4. 원자적 dashboard.html 생성
    print("\n[4/4] dashboard.html 대시보드 원자적 갱신 중...")
    try:
        dashboard_path = build_dashboard_html(yozm_result, naver_result)
        print("\n" + "=" * 60)
        print("✅ 대시보드 갱신 완료!")
        print(f"📂 위치: {dashboard_path}")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ HTML 대시보드 갱신 실패! 기존 대시보드가 유지됩니다. 에러: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    run_dashboard_pipeline()
