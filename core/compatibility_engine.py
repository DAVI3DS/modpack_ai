from __future__ import annotations

from collections import defaultdict
from typing import Callable


class CompatibilityEngine:
    def __init__(self) -> None:
        self.high_risk_limit_per_category = 1

    def select_compatible_mods(
        self,
        mods: list[dict],
        limit: int,
        dependency_loader: Callable[[str], dict | None],
    ) -> list[dict]:
        ranked = sorted(mods, key=lambda x: x.get("score", 0), reverse=True)
        selected: list[dict] = []
        selected_ids: set[str] = set()
        high_risk_count = defaultdict(int)

        def can_add(mod: dict) -> bool:
            if mod.get("project_id") in selected_ids:
                return False
            if mod.get("risk_level") == "high":
                cat = mod.get("technical_category")
                if high_risk_count[cat] >= self.high_risk_limit_per_category:
                    return False
            return True

        def add_with_dependencies(mod: dict):
            if mod.get("project_id") in selected_ids or len(selected) >= limit:
                return

            for dep_id in mod.get("dependencies", []):
                if dep_id in selected_ids:
                    continue
                dep_mod = dependency_loader(dep_id)
                if dep_mod and can_add(dep_mod):
                    add_with_dependencies(dep_mod)

            if len(selected) >= limit:
                return
            if not can_add(mod):
                return

            selected.append(mod)
            pid = mod.get("project_id")
            if pid:
                selected_ids.add(pid)
            if mod.get("risk_level") == "high":
                high_risk_count[mod.get("technical_category")] += 1

        for mod in ranked:
            if len(selected) >= limit:
                break
            if can_add(mod):
                add_with_dependencies(mod)

        return selected[:limit]

