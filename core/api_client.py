from __future__ import annotations

import hashlib
import os
from urllib.parse import urlparse

import requests

from .cache_manager import CacheManager


class APIClient:
    MODRINTH_BASE = "https://api.modrinth.com/v2"
    GITHUB_BASE = "https://api.github.com"

    def __init__(self, cache: CacheManager, timeout: int = 20):
        self.cache = cache
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "modpack-stability-ai/1.0"})
        self.github_token = os.getenv("GITHUB_TOKEN")

    def _cache_key(self, url: str, params: dict | None) -> str:
        raw = f"{url}|{params or {}}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_json(self, url: str, params: dict | None = None, ttl_hours: int = 12):
        key = self._cache_key(url, params)
        cached = self.cache.get(key, ttl_seconds=ttl_hours * 3600)
        if cached is not None:
            return cached

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        self.cache.set(key, data)
        return data

    def search_mods(self, mc_version: str, loader: str, theme: str, limit: int = 100) -> list[dict]:
        facets = [[f"categories:{loader.lower()}"], [f"versions:{mc_version}"]]
        params = {
            "query": theme,
            "facets": str(facets).replace("'", '"'),
            "limit": min(max(limit, 10), 100),
            "index": "downloads",
        }
        data = self.get_json(f"{self.MODRINTH_BASE}/search", params=params, ttl_hours=6)
        return data.get("hits", [])

    def get_project_versions(self, project_id: str, mc_version: str, loader: str) -> list[dict]:
        params = {
            "loaders": f'["{loader.lower()}"]',
            "game_versions": f'["{mc_version}"]',
        }
        return self.get_json(
            f"{self.MODRINTH_BASE}/project/{project_id}/version",
            params=params,
            ttl_hours=8,
        )

    def get_projects_bulk(self, project_ids: list[str]) -> list[dict]:
        if not project_ids:
            return []
        params = {"ids": str(project_ids).replace("'", '"')}
        return self.get_json(f"{self.MODRINTH_BASE}/projects", params=params, ttl_hours=12)

    def extract_github_repo(self, project: dict) -> str | None:
        candidates = [
            project.get("source_url"),
            project.get("issues_url"),
            project.get("wiki_url"),
            project.get("discord_url"),
            project.get("homepage_url"),
        ]
        for url in candidates:
            if not url or "github.com" not in url:
                continue
            parsed = urlparse(url)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        return None

    def get_github_issue_stats(self, repo: str, keywords: list[str]) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        url = f"{self.GITHUB_BASE}/repos/{repo}/issues"
        params = {"state": "open", "per_page": 100}
        key = self._cache_key(url, params)
        cached = self.cache.get(key, ttl_seconds=6 * 3600)
        if cached is not None:
            return cached

        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        if response.status_code >= 400:
            fallback = {"open_issues": 0, "keyword_hits": 0, "keyword_count": {k: 0 for k in keywords}}
            self.cache.set(key, fallback)
            return fallback

        issues = response.json()
        total = 0
        keyword_count = {k: 0 for k in keywords}
        for issue in issues:
            if "pull_request" in issue:
                continue
            total += 1
            text = f"{issue.get('title', '')} {issue.get('body', '')}".lower()
            for k in keywords:
                if k in text:
                    keyword_count[k] += 1

        data = {
            "open_issues": total,
            "keyword_hits": sum(keyword_count.values()),
            "keyword_count": keyword_count,
        }
        self.cache.set(key, data)
        return data

