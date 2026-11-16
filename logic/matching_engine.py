"""
logic/matching_engine.py
────────────────────────
MatchingEngine — compares a newly-submitted 'found' item against every
pending 'lost' item in the database, using exact normalised comparison
plus difflib fuzzy matching to handle typos.
"""

from difflib import SequenceMatcher
from config import FUZZY_THRESHOLD, MATCH_WEIGHTS


def _normalise(text: str) -> str:
    """Strip and lowercase — prevents case/whitespace mismatches."""
    return text.strip().lower() if text else ""


def _similarity(a: str, b: str) -> float:
    """
    Return SequenceMatcher ratio in [0.0, 1.0].
    1.0 = identical strings, 0.0 = no common characters.
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


class MatchingEngine:
    """
    Stateless matching logic (no DB calls — receives plain dicts).

    Scoring model
    ─────────────
    weighted_score = category_sim * 0.40
                   + color_sim    * 0.35
                   + brand_sim    * 0.25

    If weighted_score >= FUZZY_THRESHOLD the items are considered a match.
    """

    @staticmethod
    def score_pair(lost: dict, found: dict) -> float:
        """
        Compute a [0, 1] similarity score between *lost* and *found* items.
        """
        cat_sim   = _similarity(lost.get("category", ""), found.get("category", ""))
        color_sim = _similarity(lost.get("color",    ""), found.get("color",    ""))
        brand_sim = _similarity(lost.get("brand",    ""), found.get("brand",    ""))

        weighted = (
            cat_sim   * MATCH_WEIGHTS["category"] +
            color_sim * MATCH_WEIGHTS["color"]    +
            brand_sim * MATCH_WEIGHTS["brand"]
        )
        return round(weighted, 4)

    @staticmethod
    def find_matches(found_item: dict, lost_items: list[dict],
                     threshold: float = FUZZY_THRESHOLD) -> list[dict]:
        """
        Compare *found_item* against every dict in *lost_items*.

        Parameters
        ----------
        found_item   : dict with keys category, color, brand, user_id, item_id
        lost_items   : list of dicts from db.get_all_lost_items()
        threshold    : minimum score to qualify as a match

        Returns
        -------
        List of dicts: {'lost_item': …, 'score': float}
        sorted descending by score, filtered by threshold.
        """
        results = []
        for lost in lost_items:
            # Skip items owned by the same user (can't match yourself)
            if lost.get("user_id") == found_item.get("user_id"):
                continue
            score = MatchingEngine.score_pair(lost, found_item)
            if score >= threshold:
                results.append({"lost_item": lost, "score": score})

        # Sort best match first
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @staticmethod
    def describe_match(lost: dict, found: dict) -> str:
        """
        Return a human-readable explanation of why two items were matched.
        Used in notifications.
        """
        lines = []
        for field in ("category", "color", "brand"):
            sim = _similarity(lost.get(field, ""), found.get(field, ""))
            status = (
                "exact match" if sim == 1.0 else
                f"{int(sim * 100)}% similar" if sim >= 0.5 else
                "differs"
            )
            lines.append(f"  • {field.capitalize()}: {status}")
        return "\n".join(lines)
