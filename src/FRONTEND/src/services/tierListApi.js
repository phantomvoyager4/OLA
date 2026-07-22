const TIER_LIST_URL = "/api/tier-list";

const firstDefined = (...values) =>
  values.find((value) => value !== undefined && value !== null && value !== "");

const numberOrNull = (value) => {
  if (value === undefined || value === null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const normalizeRole = (role) => {
  const normalized = String(role || "UNKNOWN").toUpperCase();
  const aliases = {
    ADC: "BOTTOM",
    BOT: "BOTTOM",
    MID: "MIDDLE",
    SUPPORT: "UTILITY",
    SUP: "UTILITY",
  };

  return aliases[normalized] || normalized;
};

const normalizeTier = (tier) => {
  const normalized = String(tier || "D").toUpperCase().replaceAll("+", "");
  return ["S", "A", "B", "C", "D"].includes(normalized) ? normalized : "D";
};

const extractChampionRows = (payload) => {
  if (Array.isArray(payload)) return payload;

  const directRows = firstDefined(
    payload?.champions,
    payload?.results,
    payload?.entries,
    payload?.tierList,
    payload?.tier_list,
    Array.isArray(payload?.data) ? payload.data : null,
  );

  if (Array.isArray(directRows)) return directRows;

  const tiers = payload?.tiers || payload?.data?.tiers;
  if (!tiers || typeof tiers !== "object") return [];

  return Object.entries(tiers).flatMap(([tier, champions]) =>
    Array.isArray(champions)
      ? champions.map((champion) => ({ ...champion, tier: champion.tier || tier }))
      : [],
  );
};

const normalizeChampion = (champion, index) => {
  const championName = String(
    firstDefined(champion.championName, champion.champion_name, champion.name, "Unknown"),
  );
  const championId = firstDefined(
    champion.championId,
    champion.champion_id,
    champion.id,
    championName,
  );

  return {
    id: `${championId}-${normalizeRole(champion.role)}-${index}`,
    championId,
    championName,
    championImage: firstDefined(
      champion.championImage,
      champion.champion_image,
      champion.imageUrl,
      champion.image_url,
      champion.icon,
      champion.icon_url,
      "",
    ),
    role: normalizeRole(firstDefined(champion.role, champion.position, champion.teamPosition)),
    tier: normalizeTier(champion.tier),
    score: numberOrNull(firstDefined(champion.score, champion.tierScore, champion.tier_score)),
    games: numberOrNull(
      firstDefined(champion.games, champion.gamesPlayed, champion.games_played, champion.matches),
    ) || 0,
    wins: numberOrNull(champion.wins),
    winRate: numberOrNull(firstDefined(champion.winRate, champion.win_rate)),
    pickRate: numberOrNull(firstDefined(champion.pickRate, champion.pick_rate)),
    banRate: numberOrNull(firstDefined(champion.banRate, champion.ban_rate)),
  };
};

export const normalizeTierListResponse = (payload) => {
  const metadata = payload?.meta || payload?.metadata || payload?.data?.meta || {};
  const champions = extractChampionRows(payload).map(normalizeChampion);

  return {
    region: String(firstDefined(payload?.region, metadata.region, "EUW")),
    rank: String(firstDefined(payload?.rank, payload?.rankGroup, payload?.rank_group, metadata.rank, "MASTER+")),
    patch: String(
      firstDefined(payload?.patch, payload?.latestPatch, payload?.latest_patch, metadata.patch, "Latest"),
    ),
    lastUpdated: firstDefined(
      payload?.lastUpdated,
      payload?.last_updated,
      payload?.generatedAt,
      payload?.generated_at,
      metadata.lastUpdated,
      metadata.last_updated,
      metadata.generatedAt,
      metadata.generated_at,
      null,
    ),
    sampleMatches: numberOrNull(
      firstDefined(
        payload?.sample?.matches,
        payload?.sampleMatches,
        payload?.sample_matches,
        payload?.matchesAnalyzed,
        payload?.matches_analyzed,
        metadata.sampleMatches,
        metadata.sample_matches,
      ),
    ),
    sampleParticipants: numberOrNull(
      firstDefined(payload?.sample?.participants, metadata.sample?.participants),
    ),
    samplePlayers: numberOrNull(
      firstDefined(payload?.sample?.players, metadata.sample?.players),
    ),
    champions,
  };
};

export const getTierList = async ({ signal } = {}) => {
  const response = await fetch(TIER_LIST_URL, { signal });

  if (!response.ok) {
    let message = "Unable to load the tier list.";

    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.message || message;
    } catch {
      // The generic message is more useful than an HTML/proxy error response.
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return normalizeTierListResponse(await response.json());
};
