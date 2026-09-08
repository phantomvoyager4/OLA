"""Groq-backed natural-language summary of a player's recent form.

The browser has already computed every number this needs, so the client posts a
small, strictly typed digest rather than making the server re-run ``pipeline()``
and spend Riot API quota a second time.

Two properties matter here:

* **No free text crosses the boundary.** Every field is numeric or a sanitised
  short identifier, and the prompt is assembled server-side, so a hostile client
  cannot steer the model or spend the key on arbitrary generation.
* **Failure is never fatal.** A missing key, an exhausted free tier or a slow
  upstream raises :class:`OverviewUnavailable`; the page simply hides the panel.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

try:
    from .riot_api import TtlCache
except ImportError:  # pragma: no cover - script vs package execution
    from riot_api import TtlCache

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT = (3.05, 20.0)

# Groq retires hosted models without notice, and a retired id answers 404 - which
# is how this panel first broke. Ship an ordered fallback list rather than a
# single id, so one retirement degrades to the next model instead of an outage.
# Set GROQ_MODEL in .env to pin one explicitly.
#
# Reasoning models (openai/gpt-oss-*) are last on purpose: they spend the token
# budget on hidden reasoning and return empty content unless given a much larger
# max_tokens, so they are a fallback rather than the default.
GROQ_MODEL_CANDIDATES = (
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b",
)

# Remembers which candidate actually answered, so a dead model is not retried
# on every request for the lifetime of the process.
_active_model: str | None = None

# The free tier is a per-key daily allowance shared by every visitor, so the
# cache is what makes this affordable rather than a nice-to-have.
OVERVIEW_TTL_SECONDS = 60 * 60
OVERVIEW_CACHE = TtlCache(max_entries=500)

MAX_SENTENCES = 4
MAX_OUTPUT_TOKENS = 220
TEMPERATURE = 0.3

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9 '._-]")


class OverviewUnavailable(RuntimeError):
    """Raised when no overview can be produced (no key, quota spent, upstream down)."""


class ModelUnusable(RuntimeError):
    """Raised when one specific model failed but another candidate may work.

    Covers a retired or misspelled model id and a reasoning model that returned
    nothing but hidden reasoning. Never used for quota or network faults, which
    would fail identically on every candidate.
    """


def load_groq_key():
    """Read GROQ_API_KEY from the environment or any project-level .env file."""
    return _load_env_key("GROQ_API_KEY")


def _load_env_key(name):
    """Load one key, mirroring how pipeline.load_api_key finds RIOT_API_KEY."""
    project_root = Path(__file__).resolve().parent.parent.parent
    env_candidates = [
        project_root / ".env",
        project_root / "venv" / ".env",
        project_root / ".venv" / ".env",
    ]

    load_dotenv(override=False)
    for env_file in env_candidates:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)

    raw_value = os.getenv(name)
    if raw_value is None:
        return None
    return raw_value.strip().strip('"').strip("'") or None


def _sanitize(value, limit=32):
    """Reduce a client-supplied label to a short, prompt-safe token."""
    cleaned = _UNSAFE_CHARS.sub("", str(value)).strip()[:limit]
    return cleaned or "Unknown"


class ProfileDigest(BaseModel):
    """The numbers the page already displays, in a shape the model can read.

    Bounds are deliberately generous but finite: they exist to keep nonsense out
    of the prompt, not to mirror Riot's own ranges.
    """

    tier: str = Field(default="UNRANKED", max_length=32)
    rank: str = Field(default="", max_length=8)
    league_points: int = Field(default=0, ge=0, le=10000)

    wins: int = Field(default=0, ge=0, le=10000)
    losses: int = Field(default=0, ge=0, le=10000)
    winrate: float = Field(default=0.0, ge=0.0, le=100.0)

    kda: float = Field(default=0.0, ge=0.0, le=100.0)
    cs_per_min: float = Field(default=0.0, ge=0.0, le=20.0)
    kill_participation: float = Field(default=0.0, ge=0.0, le=100.0)

    score_average: float = Field(default=0.0, ge=0.0, le=100.0)
    score_median: float = Field(default=0.0, ge=0.0, le=100.0)
    score_stddev: float = Field(default=0.0, ge=0.0, le=100.0)

    main_role: str = Field(default="UNKNOWN", max_length=16)
    top_champions: list[str] = Field(default_factory=list, max_length=5)

    games_analyzed: int = Field(default=0, ge=0, le=500)
    games_last_90_days: int = Field(default=0, ge=0, le=5000)
    avg_games_per_active_day: float = Field(default=0.0, ge=0.0, le=100.0)
    days_since_last_game: int | None = Field(default=None, ge=0, le=3650)

    @field_validator("tier", "rank", "main_role", mode="before")
    @classmethod
    def _clean_label(cls, value):
        return _sanitize(value, 32)

    @field_validator("top_champions", mode="before")
    @classmethod
    def _clean_champions(cls, value):
        if not isinstance(value, list):
            return []
        return [_sanitize(name, 24) for name in value[:5]]

    def cache_key(self, model):
        """Stable key over the digest's content, so identical form reuses a call.

        The model is part of the key: switching models should produce fresh
        prose rather than serving text the previous model wrote.
        """
        payload = json.dumps(self.model_dump(), sort_keys=True, default=str)
        return ("ai-overview", model, hashlib.sha256(payload.encode()).hexdigest())

    def as_prompt_facts(self):
        """Render the digest as the flat fact list handed to the model."""
        rank_text = f"{self.tier} {self.rank}".strip() or "UNRANKED"
        champions = ", ".join(self.top_champions) or "not enough data"
        if self.days_since_last_game is None:
            last_played = "unknown"
        elif self.days_since_last_game == 0:
            last_played = "today"
        else:
            last_played = f"{self.days_since_last_game} days ago"

        return "\n".join(
            [
                f"Rank: {rank_text} ({self.league_points} LP)",
                f"Ranked record: {self.wins}W/{self.losses}L, {self.winrate:.1f}% winrate",
                f"Games analysed: {self.games_analyzed}",
                f"Primary role: {self.main_role}",
                f"Most played champions: {champions}",
                f"Average KDA: {self.kda:.2f}",
                f"Average CS per minute: {self.cs_per_min:.2f}",
                f"Average kill participation: {self.kill_participation:.1f}%",
                f"Performance score average: {self.score_average:.1f} out of 100",
                f"Performance score median: {self.score_median:.1f}",
                f"Score consistency (std dev, lower is steadier): {self.score_stddev:.1f}",
                f"Games in the last 90 days: {self.games_last_90_days}",
                f"Average games per active day: {self.avg_games_per_active_day:.1f}",
                f"Last played: {last_played}",
            ]
        )


SYSTEM_PROMPT = (
    "You are a concise League of Legends performance analyst. "
    f"Write at most {MAX_SENTENCES} sentences of plain prose addressed to the player as 'you'. "
    "Use ONLY the numbers provided; never invent a statistic, champion, rank or match. "
    "Name one clear strength and one specific thing to work on. "
    "The performance score is a percentile against players in the same role across the games "
    "analysed, so 50 is average, and a high standard deviation means inconsistent games. "
    "No markdown, no bullet points, no headings, and no preamble such as 'Here is'. "
    "Do not repeat every number back; pick the ones that tell the story."
)


def _provider_message(response):
    """Pull the human-readable reason out of a Groq error body."""
    try:
        detail = response.json().get("error", {}).get("message")
    except ValueError:
        detail = None
    return detail or response.text[:200] or f"status {response.status_code}"


def _model_candidates():
    """Models to try, best first, starting from whichever last worked."""
    override = _load_env_key("GROQ_MODEL")
    if override:
        return (override,)
    if _active_model:
        rest = tuple(m for m in GROQ_MODEL_CANDIDATES if m != _active_model)
        return (_active_model,) + rest
    return GROQ_MODEL_CANDIDATES


def _call_model(api_key, model, facts):
    """One completion attempt against one model.

    Raises:
        ModelUnusable: this model cannot serve the request, but another might.
        OverviewUnavailable: the whole provider is unusable right now.
    """
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": facts},
                ],
            },
            timeout=GROQ_TIMEOUT,
        )
    except requests.RequestException as error:
        raise OverviewUnavailable(f"Could not reach the model provider: {error}") from error

    # Quota is shared across models, so retrying another one would only waste time.
    if response.status_code == 429:
        raise OverviewUnavailable("Free-tier quota is exhausted; try again later.")
    if response.status_code == 401:
        raise OverviewUnavailable("The configured GROQ_API_KEY was rejected.")
    if response.status_code in (400, 404):
        raise ModelUnusable(_provider_message(response))
    if response.status_code != 200:
        raise OverviewUnavailable(
            f"Model provider error ({response.status_code}): {_provider_message(response)}"
        )

    try:
        message = response.json()["choices"][0]["message"]
    except (ValueError, KeyError, IndexError) as error:
        raise OverviewUnavailable("Model provider returned an unreadable payload") from error

    text = " ".join(str(message.get("content") or "").split())
    if not text:
        # Typical of a reasoning model that spent the whole budget thinking.
        raise ModelUnusable("returned no content within the token budget")
    return text


def _request_completion(api_key, facts):
    """Return (text, model) from the first candidate that answers usefully."""
    global _active_model

    failures = []
    for model in _model_candidates():
        try:
            text = _call_model(api_key, model, facts)
        except ModelUnusable as error:
            logger.warning("Groq model %s unusable: %s", model, error)
            failures.append(f"{model} ({error})")
            continue

        if model != _active_model:
            logger.info("Using Groq model %s", model)
            _active_model = model
        return text, model

    raise OverviewUnavailable("No usable model. Tried: " + "; ".join(failures))


def generate_overview(digest: ProfileDigest):
    """Return a cached or freshly generated overview for *digest*.

    Raises:
        OverviewUnavailable: when the feature is not configured or upstream fails.
    """
    api_key = load_groq_key()
    if not api_key:
        raise OverviewUnavailable("AI overview is not configured on the server")

    expected_model = _model_candidates()[0]
    key = digest.cache_key(expected_model)
    cached = OVERVIEW_CACHE.get(key)
    if cached is not None:
        return {"overview": cached, "model": expected_model, "cached": True}

    overview, model = _request_completion(api_key, digest.as_prompt_facts())
    # Key on the model that actually answered, so a fallback result is not
    # stored under the model that failed.
    OVERVIEW_CACHE.set(digest.cache_key(model), overview, OVERVIEW_TTL_SECONDS)
    return {"overview": overview, "model": model, "cached": False}
