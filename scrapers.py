import os
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from config import USER_AGENT, MAX_ARTICLES_PER_SOURCE
from database import is_article_recorded

class NewsScraper:
    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}
        self.browser_scraping = os.getenv('BROWSER_SCRAPING', '0') == '1'

    def _fetch_url(self, url: str, timeout: int = 10) -> str:
        """GitHub Actions에서는 실제 브라우저로, 로컬에서는 일반 요청으로 읽는다."""
        time.sleep(1.0)
        if self.browser_scraping:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=['--disable-dev-shm-usage', '--no-sandbox']
                )
                context = browser.new_context(
                    user_agent=self.headers['User-Agent'],
                    locale='ko-KR',
                    timezone_id='Asia/Seoul',
                    viewport={'width': 1365, 'height': 900},
                )
                page = context.new_page()
                page.goto(
                    url,
                    wait_until='domcontentloaded',
                    timeout=max(timeout, 30) * 1000
                )
                page.wait_for_timeout(1500)
                html = page.content()
                context.close()
                browser.close()
                return html

        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()
        return response.text

    def _fetch_reader_text(self, url: str, timeout: int = 30) -> str:
        """원본 사이트가 클라우드 실행 환경을 막을 때 읽기 전용 중계 경로를 쓴다."""
        target = url.replace('https://', 'http://', 1)
        reader_url = f"https://r.jina.ai/{target}"
        response = requests.get(
            reader_url,
            headers={**self.headers, 'Accept': 'text/plain'},
            timeout=timeout
        )
        response.raise_for_status()
        return response.text

class YozmITScraper(NewsScraper):
    """요즘IT 최신 기사 수집기"""
    def fetch_articles(self) -> Dict[str, Any]:
        result = {
            'source': '요즘IT',
            'articles': [],
            'failed_articles': [],
            'error': None,
            'attempted': 0
        }
        
        list_url = 'https://yozm.wishket.com/magazine/list/develop/'
        use_reader = False
        try:
            html = self._fetch_url(list_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            link_elements = soup.select('a[href*="/magazine/detail/"]')
            seen_urls = set()
            candidate_links = []
            
            for a in link_elements:
                href = a.get('href', '')
                if not href or '/magazine/detail/' not in href:
                    continue
                full_url = href if href.startswith('http') else f"https://yozm.wishket.com{href}"
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                title_el = a.select_one('.item-title') or a.select_one('.title') or a
                title = title_el.text.strip()
                
                if not title or len(title) < 5 or title.startswith("스크랩") or title.startswith("성장 습관"):
                    continue
                    
                candidate_links.append((title, full_url))

            # 요즘IT가 GitHub 서버 주소를 차단하면 읽기 전용 텍스트 경로에서
            # 같은 공개 목록을 가져온다. 별도의 키나 로그인은 사용하지 않는다.
            if not candidate_links:
                reader_text = self._fetch_reader_text(list_url)
                markdown_links = re.findall(
                    r'\[([^\]\n]{5,180})\]\((https?://yozm\.wishket\.com)?'
                    r'(/magazine/detail/\d+/?)\)',
                    reader_text
                )
                for title, origin, path in markdown_links:
                    clean_title = re.sub(r'\s+', ' ', title).strip()
                    full_url = f"https://yozm.wishket.com{path}"
                    if full_url in seen_urls or len(clean_title) < 5:
                        continue
                    seen_urls.add(full_url)
                    candidate_links.append((clean_title, full_url))
                use_reader = bool(candidate_links)

            result['attempted'] = len(candidate_links)

            for title, url in candidate_links:
                if len(result['articles']) >= MAX_ARTICLES_PER_SOURCE:
                    break
                    
                try:
                    if use_reader:
                        body_text = self._fetch_reader_text(url)
                        if len(body_text) < 200:
                            raise ValueError('읽기 전용 본문 분량 부족')
                        result['articles'].append({
                            'title': title,
                            'url': url,
                            'body': body_text,
                            'source': '요즘IT'
                        })
                        continue

                    detail_html = self._fetch_url(url)
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')

                    # 목록 카드의 카테고리·작성자 문구가 섞이지 않도록
                    # 상세 페이지에 표시된 실제 기사 제목을 우선 사용한다.
                    detail_title_el = (
                        detail_soup.select_one('h1') or
                        detail_soup.select_one('.article-title') or
                        detail_soup.select_one('.news-title')
                    )
                    if detail_title_el:
                        exact_title = detail_title_el.get_text(" ", strip=True)
                        if len(exact_title) >= 5:
                            title = exact_title
                    
                    paragraphs = [
                        p.text.strip() for p in detail_soup.find_all('p') 
                        if len(p.text.strip()) > 20 and not p.text.strip().startswith("요즘IT")
                    ]
                    
                    if not paragraphs:
                        body_el = (
                            detail_soup.select_one('.news-content') or
                            detail_soup.select_one('.article-body') or
                            detail_soup.select_one('article')
                        )
                        if body_el:
                            paragraphs = [body_el.text.strip()]
                    
                    body_text = "\n".join(paragraphs)
                    if len(body_text) < 50:
                        result['failed_articles'].append({
                            'title': title,
                            'url': url,
                            'reason': '본문 텍스트 추출 부족'
                        })
                        continue

                    result['articles'].append({
                        'title': title,
                        'url': url,
                        'body': body_text,
                        'source': '요즘IT'
                    })
                except Exception as e:
                    reason = f"상세 페이지 접근 실패 ({str(e)})"
                    result['failed_articles'].append({
                        'title': title,
                        'url': url,
                        'reason': reason
                    })

        except Exception as e:
            result['error'] = f"요즘IT 목록 페이지 접속 실패: {str(e)}"

        return result


class NaverITScraper(NewsScraper):
    """네이버 IT/과학 (Section 105) 최신 기사 수집기"""
    def fetch_articles(self) -> Dict[str, Any]:
        result = {
            'source': '네이버 IT/과학',
            'articles': [],
            'failed_articles': [],
            'error': None,
            'attempted': 0
        }
        
        section_url = 'https://news.naver.com/section/105'
        try:
            html = self._fetch_url(section_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            links = soup.select('a[href*="/article/"]')
            seen_urls = set()
            candidate_links = []
            
            for a in links:
                href = a.get('href', '')
                title = a.text.strip()
                if not href or '/article/' not in href:
                    continue
                if len(title) < 8 or title.startswith("동영상") or title.startswith("포토"):
                    continue
                
                full_url = href if href.startswith('http') else f"https://n.news.naver.com{href}"
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                candidate_links.append((title, full_url))

            result['attempted'] = len(candidate_links)

            for title, url in candidate_links:
                if len(result['articles']) >= MAX_ARTICLES_PER_SOURCE:
                    break
                    
                try:
                    detail_html = self._fetch_url(url)
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')

                    detail_title_el = (
                        detail_soup.select_one('#title_area span') or
                        detail_soup.select_one('#title_area') or
                        detail_soup.select_one('.media_end_head_headline')
                    )
                    if detail_title_el:
                        exact_title = detail_title_el.get_text(" ", strip=True)
                        if len(exact_title) >= 5:
                            title = exact_title
                    
                    article_body = (
                        detail_soup.select_one('#newsct_article') or
                        detail_soup.select_one('#articleBodyContents') or
                        detail_soup.select_one('article')
                    )
                    
                    if not article_body:
                        result['failed_articles'].append({
                            'title': title,
                            'url': url,
                            'reason': '본문 영역 파싱 실패'
                        })
                        continue

                    body_text = article_body.text.strip()
                    if len(body_text) < 50:
                        result['failed_articles'].append({
                            'title': title,
                            'url': url,
                            'reason': '본문 분량 부족 (50자 미만)'
                        })
                        continue

                    result['articles'].append({
                        'title': title,
                        'url': url,
                        'body': body_text,
                        'source': '네이버 IT/과학'
                    })
                except Exception as e:
                    reason = f"상세 페이지 접근 실패 ({str(e)})"
                    result['failed_articles'].append({
                        'title': title,
                        'url': url,
                        'reason': reason
                    })

        except Exception as e:
            result['error'] = f"네이버 IT/과학 섹션 접근 실패: {str(e)}"

        return result
