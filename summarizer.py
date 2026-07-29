import re
from collections import Counter
from typing import List, Tuple, Dict

PERSPECTIVE_KEYWORDS = [
    '말했다', '전했다', '지적했다', '강조했다', '평가했다', '전망된다', '주장했다',
    '밝혔다', '설명했다', '분석했다', '필자', '생각한다', '시각', '관점', '의견',
    '전망이다', '보았다', '덧붙였다', '제안했다'
]

RISK_KEYWORDS = [
    '우려', '한계', '제약', '고려', '문제', '위험', '주의', '단점', '부담',
    '걸림돌', '과제', '지적', '아쉬움', '복잡', '손실', '어려움', '부작용'
]

ISSUE_KEYWORDS = [
    '영향', '변화', '도입', '시장', '기술', '데이터', '비용', '보안', '성능',
    '경쟁', '사용자', '개발자', '기업', '산업', '문제', '한계', '위험', '과제'
]

INSIGHT_KEYWORDS = [
    '필요가 있다', '필요하다', '필요합니다', '해야 한다', '해야 합니다',
    '중요하다', '중요합니다', '주의해야', '고려해야', '고려할', '기억해야',
    '잊지 말아야', '교훈', '깨달', '회고', '돌이켜', '제안한다', '권한다',
    '바람직', '과제로', '관건', '핵심은', '결국', '생각합니다', '생각한다',
    '배웠습니다', '알게 됐', '알게 되었', '느꼈습니다'
]

NOISE_PATTERNS = [
    r'^[0-9]{4}\.[0-9]{2}\.[0-9]{2}',
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    r'저작권자', r'무단전재', r'재배포 금지', r'기자', r'구독하기', r'좋아요',
    r'http[s]?://\S+'
]

def clean_sentence(text: str) -> str:
    """문장 정제 (공백, 기호 정리 및 노이즈 제거)"""
    text = re.sub(r'\s+', ' ', text).strip()
    # 숫자 목록 번호 정리 (e.g. 1. 2.)
    text = re.sub(r'^[0-9]+[\.\)]\s*', '', text)
    return text

def is_noise_sentence(sent: str) -> bool:
    """광고, 저작권, 이메일 등 노이즈 문장 판별"""
    if len(sent) < 15 or len(sent) > 250:
        return True
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, sent, re.IGNORECASE):
            return True
    return False

def split_sentences(text: str) -> List[str]:
    """본문을 문장 단위로 분할"""
    # 줄바꿈과 종결 어미(. ! ?) 기준으로 분할
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    cleaned = []
    for s in raw_sentences:
        s_clean = clean_sentence(s)
        if s_clean and not is_noise_sentence(s_clean):
            cleaned.append(s_clean)
    return cleaned

def extract_words(text: str) -> List[str]:
    """간단한 단어 추출 (2자 이상 한글/영문 단어)"""
    return [w.lower() for w in re.findall(r'[가-힣a-zA-Z0-9]{2,}', text)]

def sentence_similarity(sent1: str, sent2: str) -> float:
    """두 문장 간의 단어 집합 자카드 유사도 계산 (중복 검사용)"""
    w1 = set(extract_words(sent1))
    w2 = set(extract_words(sent2))
    if not w1 or not w2:
        return 0.0
    intersection = w1.intersection(w2)
    union = w1.union(w2)
    return len(intersection) / len(union)


def concise_quote(sentence: str, limit: int = 220) -> str:
    """원문 문장을 인용에 적합한 길이로 정리하되 의미를 새로 만들지 않는다."""
    sentence = clean_sentence(sentence).strip(' "\'“”‘’')
    if len(sentence) <= limit:
        return sentence
    shortened = sentence[:limit].rsplit(' ', 1)[0].rstrip('.,!? ')
    return shortened + "…"


def framed_source_sentence(sentence: str, purpose: str) -> str:
    """원문을 그대로 인용하고 설명 문구만 정중한 합니다체로 통일한다."""
    quote = concise_quote(sentence)
    if purpose == 'issue':
        return f'원문에서는 “{quote}”라고 문제를 설명했습니다.'
    if purpose == 'insight':
        return f'원문에서는 “{quote}”라는 관점과 제안을 확인할 수 있습니다.'
    return f'원문에서는 “{quote}”라고 설명했습니다.'


def summarize_article(title: str, body_text: str) -> Dict[str, object]:
    """
    기사 원문에서 요약, 핵심 이슈, 회고성 인사이트를 각각 추출한다.
    새로운 의견이나 문장은 생성하지 않는다.
    """
    sentences = split_sentences(body_text)
    
    if not sentences:
        # 본문 분할 실패시 제목 기반 기본 메시지
        return {
            'background': "기사 본문에서 배경 설명을 충분히 찾지 못했습니다.",
            'why': "기사 본문에서 원인을 충분히 찾지 못했습니다.",
            'so_what': "기사 본문에서 영향과 결론을 충분히 찾지 못했습니다.",
            'key_issues': ["기사 본문에서 핵심 이슈를 충분히 찾지 못했습니다."],
            'insights': ["원문에서 명시적인 회고·제안 문장을 찾지 못했습니다."]
        }

    title_words = set(extract_words(title))
    all_words = extract_words(body_text)
    word_counts = Counter(all_words)

    # 문장별 중요도 점수 계산
    scored_sentences: List[Tuple[float, int, str]] = []
    total_sents = len(sentences)

    for idx, sent in enumerate(sentences):
        words = extract_words(sent)
        if not words:
            continue
            
        # 1. 위치 가중치 (기사 앞쪽 문장에 높은 점수 부여)
        position_score = (total_sents - idx) / total_sents * 1.5
        
        # 2. 제목 단어 포함 점수
        title_overlap = sum(2.0 for w in words if w in title_words)
        
        # 3. 주요 단어 빈도 점수
        freq_score = sum(word_counts[w] for w in words) / len(words)
        
        total_score = position_score + title_overlap + freq_score
        scored_sentences.append((total_score, idx, sent))

    # 점수 높은 순으로 정렬
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    # 중복되지 않는 핵심 문장 5개 선택
    selected_sentences: List[Tuple[int, str]] = []
    for score, original_idx, sent in scored_sentences:
        # 이미 선택된 문장과의 유사도 검사
        is_duplicate = False
        for _, sel_sent in selected_sentences:
            if sentence_similarity(sent, sel_sent) > 0.45:
                is_duplicate = True
                break
        
        if not is_duplicate:
            selected_sentences.append((original_idx, sent))
            if len(selected_sentences) >= 5:
                break

    # 5개 미만인 경우 나머지 문장으로 채우기
    if len(selected_sentences) < 5:
        for score, original_idx, sent in scored_sentences:
            if not any(original_idx == idx for idx, _ in selected_sentences):
                selected_sentences.append((original_idx, sent))
                if len(selected_sentences) >= 5:
                    break

    # 기사 원래 순서대로 재정렬하여 가독성 유지
    selected_sentences.sort(key=lambda x: x[0])
    summary_points = [sent for _, sent in selected_sentences]

    def first_distinct_candidate(
        keyword_groups: List[List[str]], excluded: List[str]
    ) -> str:
        for keywords in keyword_groups:
            for sent in sentences:
                if sent.rstrip().endswith('?'):
                    continue
                if not any(keyword in sent for keyword in keywords):
                    continue
                if any(sentence_similarity(sent, item) > 0.45 for item in excluded):
                    continue
                return sent
        for sent in summary_points:
            if sent.rstrip().endswith('?'):
                continue
            if not any(sentence_similarity(sent, item) > 0.45 for item in excluded):
                return sent
        return title

    background_source = summary_points[0] if summary_points else title
    why_source = first_distinct_candidate(
        [
            ['때문', '원인', '이유'],
            ['문제', '한계', '비효율', '어려움', '제약', '부족'],
            ['배경', '위해', '따라', '면서'],
        ],
        [background_source],
    )
    so_what_source = first_distinct_candidate(
        [
            ['따라서', '결국'],
            ['필요', '중요', '해야', '제안'],
            ['영향', '전망', '변화', '수 있습니다', '수 있다'],
        ],
        [background_source, why_source],
    )

    def extract_keyword_sentences(keywords: List[str], limit: int = 5) -> List[str]:
        matches: List[str] = []
        for sent in sentences:
            if not any(keyword in sent for keyword in keywords):
                continue
            if any(sentence_similarity(sent, existing) > 0.45 for existing in matches):
                continue
            matches.append(sent)
            if len(matches) >= limit:
                break
        return matches

    key_issues = extract_keyword_sentences(RISK_KEYWORDS)
    key_issues = [concise_quote(sent) for sent in key_issues[:5]]
    if not key_issues:
        key_issues = ["원문에서 명시적으로 설명한 문제를 찾지 못했습니다."]

    insights = extract_keyword_sentences(INSIGHT_KEYWORDS)
    insights = [concise_quote(sent) for sent in insights[:5]]
    if not insights:
        insights = ["원문에서 명시적인 회고·제안 문장을 찾지 못했습니다."]

    return {
        'background': concise_quote(background_source),
        'why': concise_quote(why_source),
        'so_what': concise_quote(so_what_source),
        'key_issues': key_issues[:5],
        'insights': insights[:5]
    }
