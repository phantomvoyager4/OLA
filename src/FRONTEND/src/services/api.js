export const API_BASE_URL = '/api';
const API_CACHE_VERSION = 'performance-metric-v1';

// Cache to survive Vite HMR (Hot Module Replacement) during development
// This prevents refetching data every time you save a file
const apiCache = window.__API_CACHE__ || (window.__API_CACHE__ = new Map());

const defaultRateLimitStatus = {
  warning: false,
  shortWindow: "0/18",
  longWindow: "0/90",
  resetSeconds: 0,
  initialized: false,
};

export const getRateLimitStatus = () => (
  window.__RIOT_RATE_LIMIT_STATUS__ || defaultRateLimitStatus
);

const dispatchRateLimitStatus = (status) => {
  window.__RIOT_RATE_LIMIT_STATUS__ = status;
  window.dispatchEvent(new CustomEvent("riot-rate-limit-status", { detail: status }));
};

const publishRateLimitStatus = (response) => {
  const shortWindow = response.headers.get("X-Riot-Rate-Limit-Short");
  const longWindow = response.headers.get("X-Riot-Rate-Limit-Long");
  if (!shortWindow && !longWindow) return;

  dispatchRateLimitStatus({
    warning: response.headers.get("X-Riot-Rate-Limit-Warning") === "approaching",
    shortWindow,
    longWindow,
    resetSeconds: Number(response.headers.get("X-Riot-Rate-Limit-Reset") || 0),
    initialized: true,
  });
};

const publishCachedRateLimitStatus = () => {
  dispatchRateLimitStatus(getRateLimitStatus());
};

export const refreshRateLimitStatus = async (options = {}) => {
  const response = await fetch(`${API_BASE_URL}/rate-limit`, {
    signal: options.signal,
  });
  publishRateLimitStatus(response);
  if (!response.ok) {
    throw new Error(`Failed to refresh rate limit status: ${response.statusText}`);
  }
  return getRateLimitStatus();
};

/**
 * Fetches player data and recent matches from the backend.
 * 
 * @param {string} region - The region of the player (e.g., EUW, NA)
 * @param {string} nickname - The player's in-game name
 * @param {string} tag - The player's tagline (e.g., EUNE1)
 * @param {Object} options - Additional query parameters
 * @param {boolean} options.save - Whether to save the data on the backend
 * @param {number} options.count - Number of matches to fetch
 * @param {number} options.start - Offset for matches to fetch
 * @returns {Promise<Object>} The player and matches data
 */
export const getPlayerData = async (region, nickname, tag, options = { save: false, count: 20, start: 0 }) => {
  const { save, count, start = 0, signal } = options;
  const url = `${API_BASE_URL}/matches/${region}/${nickname}/${tag}?save=${save}&count=${count}&start=${start}&cacheVersion=${API_CACHE_VERSION}`;
  
  // Return cached data if available
  if (apiCache.has(url)) {
    console.log("Returning cached data for", url);
    publishCachedRateLimitStatus();
    return apiCache.get(url);
  }

  const response = await fetch(url, { signal });
  publishRateLimitStatus(response);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.statusText}`);
  }
  
  const data = await response.json();
  
  // Save to cache
  apiCache.set(url, data);
  
  return data;
};

/** Fetches only the match dates needed to extend the activity heatmap. */
export const getPlayerActivity = async (region, nickname, tag, options = {}) => {
  const { count = 40, start = 20, signal } = options;
  const url = `${API_BASE_URL}/activity/${region}/${nickname}/${tag}?count=${count}&start=${start}&cacheVersion=${API_CACHE_VERSION}`;

  if (apiCache.has(url)) {
    console.log("Returning cached data for", url);
    publishCachedRateLimitStatus();
    return apiCache.get(url);
  }

  const response = await fetch(url, { signal });
  publishRateLimitStatus(response);
  if (!response.ok) {
    throw new Error(`Failed to fetch activity: ${response.statusText}`);
  }

  const data = await response.json();
  apiCache.set(url, data);
  return data;
};

/** Thrown when the backend's per-client suggestion throttle rejects a call. */
export class SuggestionsThrottledError extends Error {
  constructor(retryAfterSeconds) {
    super('Too many suggestion requests');
    this.retryAfterMs = Math.max(1, retryAfterSeconds) * 1000;
  }
}

/**
 * Riot ID autocomplete served from the backend's local player index.
 * Costs no Riot API quota. Not cached here: usePlayerSuggestions keeps its
 * own short-lived cache so new players show up without a reload.
 *
 * @param {string} query - "name" or "name#tag", at least 2 characters
 * @param {string} region - Region label from the search form (e.g. EUW)
 * @param {Object} options - { signal, limit }
 * @returns {Promise<Array<{name: string, tag: string, platform: string}>>}
 */
export const getPlayerSuggestions = async (query, region, options = {}) => {
  const { signal, limit = 8 } = options;
  const params = new URLSearchParams({ q: query, platform: region, limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/players/suggest?${params}`, { signal });

  if (response.status === 429) {
    throw new SuggestionsThrottledError(Number(response.headers.get('Retry-After') || 1));
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch suggestions: ${response.statusText}`);
  }

  const data = await response.json();
  return Array.isArray(data?.suggestions) ? data.suggestions : [];
};

/**
 * Reports whether the server has an AI provider key configured.
 * Lets the profile skip the overview panel instead of showing a failed one.
 *
 * @returns {Promise<boolean>} True when overviews can be generated
 */
export const getOverviewAvailability = async (options = {}) => {
  const url = `${API_BASE_URL}/overview/status`;

  if (apiCache.has(url)) {
    return apiCache.get(url);
  }

  const response = await fetch(url, { signal: options.signal });
  if (!response.ok) return false;

  const data = await response.json();
  const available = Boolean(data?.available);
  // Only a positive answer is cached, so adding the key and reloading is enough
  // to turn the panel on without clearing the HMR-surviving cache.
  if (available) apiCache.set(url, available);
  return available;
};

/**
 * Generates a short natural-language summary of a player's recent form.
 * The digest is built in the browser from data already on screen, so this
 * costs no Riot API quota.
 *
 * @param {Object} digest - Numeric profile summary matching the backend schema
 * @param {Object} options - { signal }
 * @returns {Promise<{overview: string, model: string, cached: boolean}>}
 */
export const getPlayerOverview = async (digest, options = {}) => {
  const body = JSON.stringify(digest);
  const cacheKey = `${API_BASE_URL}/overview:${body}`;

  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey);
  }

  const response = await fetch(`${API_BASE_URL}/overview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    signal: options.signal,
  });

  if (!response.ok) {
    const detail = await response
      .json()
      .then((payload) => payload?.detail)
      .catch(() => null);
    throw new Error(detail || `Failed to generate overview: ${response.statusText}`);
  }

  const data = await response.json();
  apiCache.set(cacheKey, data);
  return data;
};

/**
 * Retrieves a specific match from the cached player data.
 * Useful for displaying match details without refetching the API.
 * 
 * @param {string} matchId - The match ID to look for
 * @returns {Object|null} The match data if found, null otherwise
 */
export const getCachedMatch = (matchId) => {
  for (const data of apiCache.values()) {
    if (Array.isArray(data)) {
      const match = data.find(m => m.match_id === matchId || m.metadata?.matchId === matchId);
      if (match) return match;
    }
  }
  return null;
};
