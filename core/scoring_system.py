from __future__ import annotations

HIGH_RISK = {"render_engine", "network_core", "lighting_engine"}
MEDIUM_RISK = {"worldgen"}


class ScoringSystem:
    def score_mod(self, mod: dict) -> int:
        score = 50

        update_days = mod.get("days_since_update", 9999)
        if update_days <= 90:
            score += 20
        elif update_days <= 180:
            score += 10
        elif update_days > 365:
            score -= 20

        downloads = max(mod.get("downloads", 0), 0)
        if downloads > 0:
            import math

            score += min(20, int(math.log10(downloads + 1) * 5))

        open_issues = max(mod.get("open_issues", 0), 0)
        ratio = (open_issues / max(downloads, 1)) * 10000
        if ratio <= 0.5:
            score += 15
        elif ratio <= 2:
            score += 8
        elif ratio <= 5:
            score += 0
        elif ratio <= 10:
            score -= 8
        else:
            score -= 15

        keyword_hits = max(mod.get("keyword_hits", 0), 0)
        score -= min(15, keyword_hits * 3)

        category = mod.get("technical_category", "gameplay")
        if category in HIGH_RISK:
            score -= 12
        elif category in MEDIUM_RISK:
            score -= 6
        elif category == "qol":
            score += 2
        else:
            score -= 2

        if mod.get("conflict_history", False):
            score -= 8

        return max(0, min(100, score))

    def overall_score(self, mods: list[dict]) -> int:
        if not mods:
            return 0

        base = sum(m.get("score", 0) for m in mods) / len(mods)
        high_risk_count = sum(1 for m in mods if m.get("risk_level") == "high")
        if high_risk_count > 3:
            base -= min(15, (high_risk_count - 3) * 3)

        return max(0, min(100, int(round(base))))

