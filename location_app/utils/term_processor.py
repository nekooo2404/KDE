import re
from typing import Dict, List, Tuple

from .city_catalog import LOCATION_TERMS
from .world_city_dataset import WorldCityDataset, normalize_search_text, tokenize_search_text


class TweetTermProcessor:
    def __init__(self, world_city_dataset: WorldCityDataset | None = None):
        self.world_city_dataset = world_city_dataset or WorldCityDataset()
        self.location_terms = LOCATION_TERMS
        self.curated_phrase_terms = sorted(
            [term for term in self.location_terms if " " in term],
            key=len,
            reverse=True,
        )

    def extract_term_locations(self, tweet: str) -> Tuple[List[str], List[Dict]]:
        tweet_without_urls = re.sub(r"https?://\S+", " ", tweet or "")
        normalized_tweet = normalize_search_text(tweet_without_urls)
        matched_terms: List[str] = []
        matched_term_keys = set()
        curated_term_locations_added = set()
        term_locations: List[Dict] = []

        for phrase in self.curated_phrase_terms:
            if self._contains_phrase(normalized_tweet, phrase):
                matched_terms.append(phrase)
                matched_term_keys.add(phrase)
                term_locations.append(
                    {
                        "term": phrase,
                        "canonical_city": self.location_terms[phrase]["city"],
                        **self.location_terms[phrase],
                    }
                )
                curated_term_locations_added.add(phrase)

        tokens = tokenize_search_text(normalized_tweet)
        token_positions_used = set()

        for size in range(self.world_city_dataset.max_alias_words, 0, -1):
            for start in range(len(tokens) - size + 1):
                span = range(start, start + size)
                if any(position in token_positions_used for position in span):
                    continue

                alias = " ".join(tokens[start:start + size])
                city_indices = self.world_city_dataset.candidate_indices_for_alias(alias)
                if not city_indices:
                    continue

                if alias not in matched_term_keys:
                    matched_terms.append(alias)
                    matched_term_keys.add(alias)

                token_positions_used.update(span)
                term_locations.extend(
                    self.world_city_dataset.build_term_locations(alias, city_indices)
                )

        for token in tokens:
            if token in self.location_terms:
                if token not in matched_term_keys:
                    matched_terms.append(token)
                    matched_term_keys.add(token)
                if token in curated_term_locations_added:
                    continue
                term_locations.append(
                    {
                        "term": token,
                        "canonical_city": self.location_terms[token]["city"],
                        **self.location_terms[token],
                    }
                )
                curated_term_locations_added.add(token)

        return matched_terms, term_locations

    def extract_terms(self, tweet: str) -> List[str]:
        matched_terms, _ = self.extract_term_locations(tweet)
        return matched_terms

    def get_term_locations(self, terms: List[str]) -> List[Dict]:
        return [
            {"term": term, **self.location_terms[term]}
            for term in terms
            if term in self.location_terms
        ]

    def _contains_phrase(self, normalized_tweet: str, phrase: str) -> bool:
        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
        return bool(re.search(pattern, normalized_tweet))
