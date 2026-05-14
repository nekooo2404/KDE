"""
Keyword extraction from tweet/social media text for location prediction.

Pipeline:
  1. Strip URLs, @mentions, emoji, punctuation
  2. Keep #hashtag words (remove #)
  3. Remove EN + VI stopwords
  4. Return unique keywords, longer (more specific) first
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

# ---------------------------------------------------------------------------
# Stopword lists
# ---------------------------------------------------------------------------

EN_STOPWORDS: frozenset[str] = frozenset({
    # Articles / prepositions
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'out',
    # Verbs
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'shall', 'can', 'go', 'went', 'come', 'came', 'see', 'saw', 'get', 'got',
    'make', 'made', 'take', 'took', 'look', 'know', 'think', 'feel', 'want',
    'need', 'love', 'like', 'say', 'said', 'just', 'also', 'back', 'well',
    # Pronouns
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your',
    'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
    # Determiners
    'this', 'that', 'these', 'those', 'all', 'each', 'every', 'both',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only',
    'same', 'so', 'than', 'too', 'very', 'even', 'much', 'many',
    # Question words
    'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
    # Time / generic
    'day', 'time', 'new', 'old', 'big', 'small', 'long', 'own', 'right',
    'still', 'after', 'before', 'here', 'there', 'then', 'now', 'way',
    'because', 'while', 'already',
    # Twitter noise
    'rt', 'via', 'cc', 'dm', 'lol', 'omg', 'imo', 'tbh', 'lmao',
    'wtf', 'smh', 'fyi', 'btw', 'irl', 'afk', 'brb', 'thx', 'ty', 'amp',
    # Numbers as words
    'one', 'two', 'three', 'four', 'five',
})

VI_STOPWORDS: frozenset[str] = frozenset({
    # Copula / connectors
    'là', 'và', 'của', 'có', 'trong', 'được', 'cho', 'với', 'các', 'này',
    'đó', 'khi', 'từ', 'một', 'đã', 'đang', 'sẽ', 'thì', 'mà', 'vì',
    'nên', 'nhưng', 'hay', 'hoặc', 'những', 'về', 'theo', 'như',
    'vào', 'ra', 'lên', 'xuống', 'qua', 'lại', 'đi', 'đến',
    'không', 'chưa', 'chỉ', 'còn', 'rồi', 'thật', 'cũng', 'đều', 'rất',
    'làm', 'nói', 'thấy', 'biết', 'muốn', 'cần', 'phải', 'hơn',
    'nhất', 'quá', 'lắm', 'nhiều', 'ít',
    # Pronouns
    'tôi', 'bạn', 'mình', 'chúng', 'họ', 'nó', 'đây', 'kia',
    # Time
    'ngày', 'hôm', 'giờ', 'năm', 'tháng', 'tuần', 'sau', 'trước', 'nay',
    # Generic adjectives
    'to', 'nhỏ', 'mới', 'cũ', 'tốt', 'đẹp', 'xấu',
    # Sentence particles
    'ạ', 'ơi', 'nhé', 'nha', 'à', 'ừ', 'uh', 'ah',
})

# ---------------------------------------------------------------------------
# Emoji / symbol remover
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002500-\U00002BEF"   # chinese/japanese chars
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"
    "\u3030"
    "]+",
    flags=re.UNICODE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract location-relevant keywords from tweet/social media text.

    Returns a list of unique, cleaned keyword strings, longer first.
    """
    if not text:
        return []

    # 1. Remove URLs
    text = re.sub(r'https?://\S+', ' ', text)
    # 2. Remove @mentions
    text = re.sub(r'@\w+', ' ', text)
    # 3. Remove emojis
    text = _EMOJI_RE.sub(' ', text)
    # 4. Keep hashtag words (strip #)
    text = re.sub(r'#(\w+)', r'\1', text)
    # 5. Replace punctuation / special chars (keep unicode letters + digits)
    text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', ' ', text, flags=re.UNICODE)

    # Tokenize: split on whitespace
    tokens = text.split()

    seen: set[str] = set()
    keywords: List[str] = []

    for token in tokens:
        token_lower = token.lower().strip()

        if len(token_lower) < min_length:
            continue
        if token_lower.isdigit():
            continue
        if token_lower in EN_STOPWORDS:
            continue
        if token_lower in VI_STOPWORDS:
            continue
        if token_lower in seen:
            continue

        seen.add(token_lower)
        keywords.append(token)   # preserve original casing

    # Sort: longer = more specific → higher priority
    keywords.sort(key=len, reverse=True)
    return keywords


def keywords_to_query(keywords: List[str]) -> str:
    """Join extracted keywords into a single embedding query string."""
    return ' '.join(keywords)
