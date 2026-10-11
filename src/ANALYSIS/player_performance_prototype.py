"""Prototype player-performance system for Riot match data.

This script builds a simple offline pipeline from the saved JSON snapshots:
- loads recent match data from src/ANALYSIS/data and data/example_data
- flattens player rows into a modeling table
- computes a role-adjusted performance score
- trains a lightweight classifier for a high-performance label
- clusters player archetypes per role
- saves a few visualizations for inspection

The goal is not to be production-ready. It is a compact prototype that shows
how a website-facing performance system could work with the existing data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

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

CLASSIFIER_NUMERIC_FEATURES = NUMERIC_FEATURES + [
    "damageTakenOnTeamPercentage",
    "goldEarned",
    "goldSpent",
    "damageTaken",
    "gameDuration_min",
    "death_penalty",
    "combat_efficiency",
    "map_pressure",
    "vision_activity",
    "farm_pressure",
    "damage_share",
    "survival_rate",
]

CLASSIFIER_FEATURE_COLUMNS = CLASSIFIER_NUMERIC_FEATURES + ["teamPosition"]


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
    model_df["high_performer"] = (model_df["performance_score"] >= 70).astype(int)
    model_df["performance_band"] = pd.cut(
        model_df["performance_score"],
        bins=[-0.1, 35, 55, 75, 100.1],
        labels=["low", "solid", "strong", "elite"],
    )
    return model_df


def make_classification_pipeline() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, CLASSIFIER_NUMERIC_FEATURES),
            ("cat", categorical_pipeline, ["teamPosition"]),
        ],
        remainder="drop",
    )

    classifier = LogisticRegression(max_iter=3000, class_weight="balanced")
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])


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


def fit_classifier(df: pd.DataFrame):
    feature_frame = df.copy()
    model = make_classification_pipeline()

    x = feature_frame[CLASSIFIER_FEATURE_COLUMNS]
    y = feature_frame["high_performer"]

    stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)

    probability = None
    if hasattr(model.named_steps["classifier"], "predict_proba"):
        probability = model.predict_proba(x_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "report": classification_report(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
    }
    if probability is not None and len(np.unique(y_test)) > 1:
        metrics["roc_auc"] = roc_auc_score(y_test, probability)

    return model, metrics, (x_test, y_test, y_pred)


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


def plot_classifier_coefficients(model: Pipeline) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "classifier_coefficients.png"
    if plt is None:
        path = OUTPUT_DIR / "classifier_coefficients.txt"
        path.write_text("matplotlib is not installed in this environment.", encoding="utf-8")
        return path

    classifier = model.named_steps["classifier"]
    feature_names = model.named_steps["preprocessor"].get_feature_names_out()

    coefficients = classifier.coef_[0]
    coef_frame = pd.DataFrame({"feature": feature_names, "coefficient": coefficients})
    coef_frame = coef_frame.sort_values("coefficient", key=lambda s: s.abs(), ascending=False).head(12)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#2a9d8f" if value >= 0 else "#e76f51" for value in coef_frame["coefficient"]]
    ax.barh(coef_frame["feature"][::-1], coef_frame["coefficient"][::-1], color=colors[::-1])
    ax.set_title("Top classifier coefficients")
    ax.set_xlabel("Impact on high-performance probability")
    fig.tight_layout()

    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


@dataclass
class PrototypeResult:
    dataframe: pd.DataFrame
    model: Pipeline
    metrics: dict
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
    model, metrics, _ = fit_classifier(model_df)

    plot_paths = [
        plot_role_distribution(model_df),
        plot_correlation_heatmap(model_df),
        plot_pca_clusters(model_df),
        plot_classifier_coefficients(model),
    ]

    return PrototypeResult(
        dataframe=model_df,
        model=model,
        metrics=metrics,
        plot_paths=plot_paths,
    )


def predict_player_performance(model: Pipeline, row: pd.Series) -> dict:
    sample = add_derived_features(pd.DataFrame([row]))[CLASSIFIER_FEATURE_COLUMNS]
    probability = float(model.predict_proba(sample)[0, 1]) if hasattr(model.named_steps["classifier"], "predict_proba") else float(model.predict(sample)[0])
    score = round(probability * 100, 1)

    if score >= 80:
        band = "elite"
    elif score >= 60:
        band = "strong"
    elif score >= 40:
        band = "solid"
    else:
        band = "low"

    return {
        "performance_probability": round(probability, 3),
        "performance_score": score,
        "performance_band": band,
    }


if __name__ == "__main__":
    result = run_prototype()

    print("Prototype model complete")
    print(f"Rows used: {len(result.dataframe)}")
    print(f"Columns used: {len(result.dataframe.columns)}")
    print("Metrics:")
    print(f"  accuracy: {result.metrics['accuracy']:.3f}")
    print(f"  f1: {result.metrics['f1']:.3f}")
    if "roc_auc" in result.metrics:
        print(f"  roc_auc: {result.metrics['roc_auc']:.3f}")
    print("\nClassification report:")
    print(result.metrics["report"])
    print("\nSaved plots:")
    for path in result.plot_paths:
        print(f"  {path}")
