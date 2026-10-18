"""Prototype player-performance system for Riot match data.

This script builds a simple offline pipeline from the saved JSON snapshots:
- loads recent match data from src/ANALYSIS/data and data/example_data
- flattens player rows into a modeling table
- computes a role-adjusted performance score
- clusters player archetypes per role
- saves a few visualizations for inspection

The goal is not to be production-ready. It is a compact prototype that shows
how a website-facing performance system could work with the existing data. (!)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional visualization dependency
    plt = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ANALYSIS_DIR / "artifacts"


NUMERIC_FEATURES = [
    "kills",
    "deaths",
    "assists",
    "KDA",
    "killParticipation",
    "damagePerMinute",
    "goldPerMinute",
    "visionScorePerMinute",
    "soloKills",
    "cs_min",
    "wardsPlaced",
    "wardsKilled",
    "timeCCingOthers",
    "totalDamageDealtToChampions",
    "damageDealtToObjectives",
    "damageDealtToTurrets",
    "totalTimeSpentDead",
    "objectiveStolen",
]


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def parse_percent(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def load_match_payloads(paths: Sequence[Path]) -> list[dict]:
    records: list[dict] = []
    seen_match_ids: set[str] = set()

    for path in paths:
        if not path.exists():
            continue

        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            iterable: Iterable[dict] = payload.values()
        elif isinstance(payload, list):
            iterable = payload
        else:
            continue

        for match in iterable:
            if not isinstance(match, dict) or "players" not in match:
                continue

            match_id = (
                match.get("match_id")
                or match.get("metadata", {}).get("matchId")
                or path.stem
            )

            if match_id in seen_match_ids:
                continue

            seen_match_ids.add(match_id)
            records.append(match)

    return records


def discover_recent_json_files() -> list[Path]:
    search_dirs = [
        ANALYSIS_DIR / "data",
        PROJECT_ROOT / "data" / "example_data",
    ]

    files: list[Path] = []
    for directory in search_dirs:
        if directory.exists():
            files.extend(sorted(directory.glob("*.json")))
    return files


def flatten_players(matches: Sequence[dict]) -> pd.DataFrame:
    rows: list[dict] = []

    for match in matches:
        metadata = match.get("metadata", {}) or {}
        match_id = match.get("match_id") or metadata.get("matchId")
        duration_min = float(metadata.get("gameDuration_min") or 0.0)
        if not duration_min:
            duration_min = safe_div(metadata.get("gameDuration", 0), 60)

        for player in match.get("players", []):
            challenges = player.get("challenges", {}) or {}
            player_metadata = player.get("metadata", {}) or {}

            kills = float(player.get("kills", 0) or 0)
            deaths = float(player.get("deaths", 0) or 0)
            assists = float(player.get("assists", 0) or 0)
            gold_earned = float(player.get("goldEarned", 0) or 0)
            gold_spent = float(player.get("goldSpent", 0) or 0)
            damage_done = float(player.get("totalDamageDealtToChampions", 0) or 0)
            damage_taken = float(player.get("totalDamageTaken", 0) or 0)

            row = {
                "match_id": match_id,
                "teamPosition": player.get("teamPosition", "UNKNOWN"),
                "championName": player.get("championName", "Unknown"),
                "win": int(bool(player.get("win", False))),
                "tier": player_metadata.get("tier", "UNKNOWN"),
                "kills": kills,
                "deaths": deaths,
                "assists": assists,
                "KDA": float(player.get("KDA", safe_div(kills + assists, max(deaths, 1.0)))),
                "killParticipation": float(player.get("killParticipation", challenges.get("killParticipation", 0))),
                "damagePerMinute": float(player.get("damagePerMinute", challenges.get("damagePerMinute", 0))),
                "goldPerMinute": float(player.get("goldPerMinute", challenges.get("goldPerMinute", 0))),
                "visionScorePerMinute": float(
                    player.get("visionScorePerMinute", challenges.get("visionScorePerMinute", 0))
                ),
                "soloKills": float(player.get("soloKills", challenges.get("soloKills", 0)) or 0),
                "cs_min": float(player.get("cs_min", 0) or 0),
                "wardsPlaced": float(player.get("wardsPlaced", 0) or 0),
                "wardsKilled": float(player.get("wardsKilled", 0) or 0),
                "timeCCingOthers": float(player.get("timeCCingOthers", 0) or 0),
                "totalDamageDealtToChampions": damage_done,
                "damageDealtToObjectives": float(player.get("damageDealtToObjectives", 0) or 0),
                "damageDealtToTurrets": float(player.get("damageDealtToTurrets", 0) or 0),
                "totalTimeSpentDead": float(player.get("totalTimeSpentDead", 0) or 0),
                "objectiveStolen": float(player.get("objectiveStolen", player.get("objectivesStolen", 0)) or 0),
                "teamDamagePercentage": parse_percent(player.get("teamDamagePercentage")),
                "damageTakenOnTeamPercentage": parse_percent(player.get("damageTakenOnTeamPercentage")),
                "goldEarned": gold_earned,
                "goldSpent": gold_spent,
                "damageTaken": damage_taken,
                "gameDuration_min": duration_min,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["teamPosition"] = df["teamPosition"].fillna("UNKNOWN").replace("No data", "UNKNOWN")
    df["championName"] = df["championName"].fillna("Unknown")
    df["tier"] = df["tier"].fillna("UNKNOWN")
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["death_penalty"] = np.log1p(enriched["deaths"] + enriched["totalTimeSpentDead"] / 60.0)
    enriched["combat_efficiency"] = enriched["KDA"] + enriched["killParticipation"] / 100.0
    enriched["map_pressure"] = (
        enriched["damageDealtToObjectives"] / (enriched["gameDuration_min"] + 1.0)
        + enriched["damageDealtToTurrets"] / (enriched["gameDuration_min"] + 1.0)
    )
    enriched["vision_activity"] = enriched["visionScorePerMinute"] + 0.25 * enriched["wardsPlaced"]
    enriched["farm_pressure"] = enriched["cs_min"] + enriched["goldPerMinute"] / 100.0
    enriched["damage_share"] = enriched["teamDamagePercentage"]
    enriched["survival_rate"] = 1.0 / (1.0 + enriched["totalTimeSpentDead"] / 60.0)
    return enriched


def role_adjusted_score(df: pd.DataFrame) -> pd.Series:
    feature_weights = {
        "combat_efficiency": 0.22,
        "damagePerMinute": 0.18,
        "goldPerMinute": 0.10,
        "vision_activity": 0.14,
        "farm_pressure": 0.12,
        "map_pressure": 0.12,
        "timeCCingOthers": 0.06,
        "soloKills": 0.04,
        "damage_share": 0.06,
        "survival_rate": 0.05,
        "death_penalty": -0.12,
    }

    feature_frame = df[list(feature_weights.keys())].copy()

    def z_score(column: pd.Series) -> pd.Series:
        std = column.std(ddof=0)
        if not std or np.isnan(std):
            return column * 0.0
        return (column - column.mean()) / std

    z_scored = feature_frame.groupby(df["teamPosition"], dropna=False).transform(z_score)
    z_scored = z_scored.replace([np.inf, -np.inf], 0.0).fillna(0.0)

    composite = sum(z_scored[column] * weight for column, weight in feature_weights.items())
    role_percentile = composite.groupby(df["teamPosition"], dropna=False).rank(pct=True)
    return (role_percentile * 100).round(1)


def build_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    model_df = add_derived_features(df)
    model_df["performance_score"] = role_adjusted_score(model_df)
    model_df["performance_band"] = pd.cut(
        model_df["performance_score"],
        bins=[-0.1, 35, 55, 75, 100.1],
        labels=["low", "solid", "strong", "elite"],
    )
    return model_df


def cluster_archetypes(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    cluster_features = [
        "damagePerMinute",
        "goldPerMinute",
        "visionScorePerMinute",
        "killParticipation",
        "cs_min",
        "timeCCingOthers",
        "soloKills",
        "damageDealtToObjectives",
        "damageDealtToTurrets",
        "deaths",
    ]

    clustered = df.copy()
    clustered["archetype_cluster"] = -1

    for role, role_frame in clustered.groupby("teamPosition"):
        if len(role_frame) < 6:
            continue

        role_features = role_frame[cluster_features].copy()
        role_features = role_features.fillna(role_features.median(numeric_only=True))
        scaled = StandardScaler().fit_transform(role_features)

        clusters = max(2, min(n_clusters, len(role_frame) // 8 or 2))
        labels = KMeans(n_clusters=clusters, random_state=42, n_init=10).fit_predict(scaled)
        clustered.loc[role_frame.index, "archetype_cluster"] = labels

    return clustered


def plot_role_distribution(df: pd.DataFrame) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "role_distribution.png"
    if plt is None:
        path = OUTPUT_DIR / "role_distribution.txt"
        path.write_text("matplotlib is not installed in this environment.", encoding="utf-8")
        return path

    fig, ax = plt.subplots(figsize=(12, 6))
    df.boxplot(column="performance_score", by="teamPosition", ax=ax, grid=False, rot=25)
    ax.set_title("Role-adjusted performance score by position")
    ax.set_xlabel("Position")
    ax.set_ylabel("Score")
    fig.suptitle("")
    fig.tight_layout()

    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_correlation_heatmap(df: pd.DataFrame) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "correlation_heatmap.png"
    if plt is None:
        path = OUTPUT_DIR / "correlation_heatmap.txt"
        path.write_text("matplotlib is not installed in this environment.", encoding="utf-8")
        return path

    corr_features = [
        "kills",
        "deaths",
        "assists",
        "KDA",
        "killParticipation",
        "damagePerMinute",
        "goldPerMinute",
        "visionScorePerMinute",
        "cs_min",
        "timeCCingOthers",
        "performance_score",
    ]
    corr = df[corr_features].corr(numeric_only=True).fillna(0.0)

    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(corr.values, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(corr.index)))
    ax.set_yticklabels(corr.index)
    fig.colorbar(image, ax=ax, shrink=0.8)
    ax.set_title("Feature correlation heatmap")
    fig.tight_layout()

    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_pca_clusters(df: pd.DataFrame) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "pca_clusters.png"
    if plt is None:
        path = OUTPUT_DIR / "pca_clusters.txt"
        path.write_text("matplotlib is not installed in this environment.", encoding="utf-8")
        return path

    pca_features = [
        "damagePerMinute",
        "goldPerMinute",
        "visionScorePerMinute",
        "killParticipation",
        "cs_min",
        "timeCCingOthers",
        "soloKills",
        "damageDealtToObjectives",
        "damageDealtToTurrets",
        "deaths",
    ]
    working = df[df["archetype_cluster"] >= 0].copy()
    if working.empty:
        path = OUTPUT_DIR / "pca_clusters_skipped.txt"
        path.write_text("Not enough rows to produce archetype clusters.", encoding="utf-8")
        return path

    x = working[pca_features].fillna(working[pca_features].median(numeric_only=True))
    scaled = StandardScaler().fit_transform(x)
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(scaled)

    fig, ax = plt.subplots(figsize=(11, 7))
    scatter = ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=working["archetype_cluster"],
        cmap="tab10",
        alpha=0.8,
        s=28,
    )
    ax.set_title("Player archetypes projected to 2D PCA space")
    ax.set_xlabel("Principal component 1")
    ax.set_ylabel("Principal component 2")
    fig.colorbar(scatter, ax=ax, label="Cluster")
    fig.tight_layout()

    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


@dataclass
class PrototypeResult:
    dataframe: pd.DataFrame
    plot_paths: list[Path]


def run_prototype() -> PrototypeResult:
    files = discover_recent_json_files()
    matches = load_match_payloads(files)
    if not matches:
        raise RuntimeError("No match data found in the recent JSON snapshots.")

    df = flatten_players(matches)
    if df.empty:
        raise RuntimeError("No player rows could be extracted from the JSON snapshots.")

    model_df = build_model_frame(df)
    model_df = cluster_archetypes(model_df)

    plot_paths = [
        plot_role_distribution(model_df),
        plot_correlation_heatmap(model_df),
        plot_pca_clusters(model_df),
    ]

    return PrototypeResult(
        dataframe=model_df,
        plot_paths=plot_paths,
    )


if __name__ == "__main__":
    result = run_prototype()

    print("Prototype model complete")
    print(f"Rows used: {len(result.dataframe)}")
    print(f"Columns used: {len(result.dataframe.columns)}")
    print("\nSaved plots:")
    for path in result.plot_paths:
        print(f"  {path}")
