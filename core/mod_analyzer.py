from __future__ import annotations

from datetime import datetime, timezone

from .scoring_system import HIGH_RISK, MEDIUM_RISK


KEYWORDS = ["crash", "incompatibility", "mixin", "rendering", "packet"]


def days_since(date_str: str | None) -> int:
    if not date_str:
        return 9999
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return 9999
    return (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days


class ModAnalyzer:
    def classify_technical_category(self, project: dict) -> str:
        blob = " ".join(
            [
                project.get("title", ""),
                project.get("slug", ""),
                project.get("description", ""),
                " ".join(project.get("categories", []) or []),
            ]
        ).lower()

        if any(k in blob for k in ["render", "shader", "renderer"]):
            return "render_engine"
        if any(k in blob for k in ["network", "packet", "protocol", "sync"]):
            return "network_core"
        if any(k in blob for k in ["light", "lighting"]):
            return "lighting_engine"
        if any(k in blob for k in ["worldgen", "biome", "terrain", "dimension"]):
            return "worldgen"
        if any(k in blob for k in ["qol", "quality of life", "ui", "hud", "minimap"]):
            return "qol"
        return "gameplay"

    def risk_level_for_category(self, category: str) -> str:
        if category in HIGH_RISK:
            return "high"
        if category in MEDIUM_RISK:
            return "medium"
        return "low"

    def normalize_dependencies(self, version: dict) -> list[str]:
        deps = []
        for dep in version.get("dependencies", []) or []:
            if dep.get("dependency_type") != "required":
                continue
            project_id = dep.get("project_id")
            if project_id:
                deps.append(project_id)
        return deps

    def build_mod_profile(self, project: dict, version: dict, issue_stats: dict) -> dict:
        category = self.classify_technical_category(project)
        risk = self.risk_level_for_category(category)

        updated = version.get("date_published") or project.get("updated")
        issue_hits = issue_stats.get("keyword_hits", 0)
        return {
            "project_id": project.get("project_id") or project.get("id"),
            "slug": project.get("slug", "unknown"),
            "title": project.get("title", "Unknown Mod"),
            "description": project.get("description", ""),
            "downloads": int(project.get("downloads", 0) or 0),
            "open_issues": int(issue_stats.get("open_issues", 0) or 0),
            "keyword_hits": int(issue_hits or 0),
            "keyword_breakdown": issue_stats.get("keyword_count", {k: 0 for k in KEYWORDS}),
            "days_since_update": days_since(updated),
            "last_updated": updated,
            "technical_category": category,
            "risk_level": risk,
            "conflict_history": issue_hits > 0,
            "dependencies": self.normalize_dependencies(version),
            "version_id": version.get("id"),
            "version_number": version.get("version_number"),
        }

