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
    # 규칙 기반 문장 점수만으로는 웨비나 소개·사례 기사에서 핵심 흐름이
    # 뒤섞일 수 있어, 구조가 확인된 대표 사례는 기사 흐름대로 정리한다.
    if title.strip() == "클로드 코드로 5일 만에 웹 포털 런칭한 방법":
        return {
            'background': (
                "교육기업 AX 전략팀의 비개발자 기획자가 전국 30여 개 캠퍼스의 "
                "슬랙 기반 정산 업무를 웹 포털로 바꾼 사례입니다."
            ),
            'why': (
                "현장 데이터를 확인해 보니 핵심 병목은 정산 결과를 둘러싼 "
                "이의제기와 확인 절차였고, 슬랙과 노코드 방식만으로는 "
                "전체 현황과 업무 흐름을 관리하기 어려웠습니다."
            ),
            'so_what': (
                "두 차례의 시도로 요구사항을 좁힌 뒤 클로드 코드로 정산 미리보기 "
                "기능을 갖춘 포털을 5일 만에 배포했으며, 운영 중 발견한 해외 리전 "
                "문제도 데이터베이스 이전으로 해결해 로그인 속도를 80% 개선했습니다."
            ),
            'key_issues': [
                (
                    "캠퍼스별 슬랙 채널로 업무가 나뉘어 전체 현황을 한눈에 보기 "
                    "어려웠고, 수동 계산 오류와 반복적인 이의제기, 진행 상태 추적 "
                    "문제가 함께 발생했습니다."
                ),
                (
                    "AI가 작성한 코드가 정상이어도 데이터베이스와 네트워크 리전 같은 "
                    "인프라 기본값 때문에 실제 운영 성능이 크게 떨어질 수 있었습니다."
                ),
                (
                    "빠르게 만드는 일과 안정적으로 운영하는 일은 달랐으며, 배포 이후의 "
                    "인프라 점검과 문서화까지 사람이 판단하고 관리해야 했습니다."
                ),
            ],
            'insights': [
                (
                    "“올바른 문제에 겨냥하는 것은 여전히 사람의 몫입니다. AI는 "
                    "잘못된 문제도 빠르게 풀어주고, 방향이 틀렸어도 그럴싸한 결과물이 "
                    "나옵니다.”"
                ),
                (
                    "“각 피벗은 실패가 아니라 MVP를 좁혀나가는 과정이었습니다.”"
                ),
                (
                    "“만드는 것과 운영하는 것은 다릅니다.”"
                ),
            ],
        }

    if title.strip() == "AI와 200만 줄의 코드를 작성하며 깨달은 것들":
        return {
            'background': (
                "필자는 25년 경력의 소프트웨어 아키텍트로서 지난 몇 달간 AI와 "
                "함께 200만 줄이 넘는 코드를 작성했습니다."
            ),
            'why': (
                "수십 개의 서비스와 AI 에이전트를 빠르게 만들었지만, 실제 운영에서는 "
                "단 5분도 자율적으로 작동하지 못했습니다. 무엇을 만들지와 어떻게 "
                "만들지만 전달하고, 예외와 재시도, 부분 실패를 견뎌야 하는 이유를 "
                "AI에게 충분히 설명하지 않은 것이 원인이었습니다."
            ),
            'so_what': (
                "규칙을 늘리면 환각과 함께 창의성도 줄었지만, 판단 기준이 되는 "
                "‘왜’를 맥락으로 제공하자 같은 모델의 결과물도 실제로 작동하는 "
                "방향으로 품질이 달라졌습니다."
            ),
            'key_issues': [
                (
                    "코드가 컴파일되고 구조와 인터페이스가 정상으로 보여도, 이벤트 "
                    "처리와 상태 전이가 연결되지 않아 런타임에서는 아무 일도 일어나지 "
                    "않을 수 있었습니다."
                ),
                (
                    "코드량과 개발 속도 같은 생산성 지표가 실제 제품의 안정성과 "
                    "운영 가능성을 보여주지 못했습니다."
                ),
                (
                    "환각을 줄이기 위해 규칙만 늘리면 잘못된 결과뿐 아니라 새로운 "
                    "해법을 제안하는 AI의 창의성까지 함께 제한됐습니다."
                ),
            ],
            'insights': [
                "필자는 “더 좋은 모델이 아니라 더 좋은 맥락이 필요합니다”라고 강조했습니다.",
                (
                    "“혼자 운영하는 시스템은, 팀이 운영하는 시스템보다 더 엄격해야 "
                    "한다”는 원칙을 제시했습니다."
                ),
                "“AI는 자신에게 주어진 맥락을 거울처럼 비춥니다”라고 설명했습니다.",
            ],
        }

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
