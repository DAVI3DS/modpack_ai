from __future__ import annotations

from .api_client import APIClient
from .mod_analyzer import KEYWORDS, ModAnalyzer
from .scoring_system import ScoringSystem
from .compatibility_engine import CompatibilityEngine


class PackGenerator:
    THEME_QUERY = {
        "Tecnologia": "technology tech automation",
        "Magia": "magic spells arcane",
        "Exploração": "adventure exploration world",
        "RPG": "rpg classes skills",
        "Vanilla+": "vanilla plus qol",
    }

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.analyzer = ModAnalyzer()
        self.scoring = ScoringSystem()
        self.compat_engine = CompatibilityEngine()

    def _progress(self, callback, value: int, message: str) -> None:
        if callback:
            callback(value, message)

    def _fetch_and_analyze(self, project: dict, mc_version: str, loader: str) -> dict | None:
        project_id = project.get("project_id") or project.get("id")
        if not project_id:
            return None

        versions = self.api.get_project_versions(project_id, mc_version, loader)
        if not versions:
            return None
        latest_version = versions[0]

        repo = self.api.extract_github_repo(project)
        issue_stats = {"open_issues": 0, "keyword_hits": 0, "keyword_count": {k: 0 for k in KEYWORDS}}
        if repo:
            issue_stats = self.api.get_github_issue_stats(repo, KEYWORDS)

        analyzed = self.analyzer.build_mod_profile(project, latest_version, issue_stats)
        analyzed["score"] = self.scoring.score_mod(analyzed)
        return analyzed

    def generate_pack(self, mc_version: str, loader: str, theme: str, limit: int, progress_callback=None) -> dict:
        self._progress(progress_callback, 5, "Conectando a API Modrinth...")

        query = self.THEME_QUERY.get(theme, theme)
        hits = self.api.search_mods(mc_version, loader, query, limit=max(limit * 4, 40))
        projects = hits[: max(limit * 3, 30)]

        self._progress(progress_callback, 20, f"{len(projects)} mods candidatos encontrados.")

        analyzed_mods: list[dict] = []
        for idx, project in enumerate(projects, start=1):
            mod = self._fetch_and_analyze(project, mc_version, loader)
            if mod:
                analyzed_mods.append(mod)
            p = 20 + int((idx / len(projects)) * 55)
            self._progress(progress_callback, min(p, 75), f"Analisando mods... {idx}/{len(projects)}")

        by_id = {m["project_id"]: m for m in analyzed_mods if m.get("project_id")}

        def dependency_loader(dep_project_id: str) -> dict | None:
            if dep_project_id in by_id:
                return by_id[dep_project_id]
            fetched = self.api.get_projects_bulk([dep_project_id])
            if not fetched:
                return None
            dep_project = fetched[0]
            analyzed = self._fetch_and_analyze(dep_project, mc_version, loader)
            if analyzed:
                by_id[dep_project_id] = analyzed
            return analyzed

        self._progress(progress_callback, 80, "Resolvendo dependencias e conflitos...")
        selected = self.compat_engine.select_compatible_mods(analyzed_mods, limit, dependency_loader)

        self._progress(progress_callback, 92, "Calculando score geral do modpack...")
        overall = self.scoring.overall_score(selected)

        self._progress(progress_callback, 100, "Concluido.")
        return {
            "config": {
                "minecraft_version": mc_version,
                "loader": loader,
                "theme": theme,
                "limit": limit,
            },
            "selected_mods": selected,
            "overall_score": overall,
            "total_candidates": len(analyzed_mods),
        }

