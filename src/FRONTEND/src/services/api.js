export const API_BASE_URL = '/api';
const API_CACHE_VERSION = 'performance-metric-v1';

// Cache to survive Vite HMR (Hot Module Replacement) during development
// This prevents refetching data every time you save a file
const apiCache = window.__API_CACHE__ || (window.__API_CACHE__ = new Map());

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
  const { save, count, start = 0 } = options;
  const url = `${API_BASE_URL}/matches/${region}/${nickname}/${tag}?save=${save}&count=${count}&start=${start}&cacheVersion=${API_CACHE_VERSION}`;
  
  // Return cached data if available
  if (apiCache.has(url)) {
    console.log("Returning cached data for", url);
    return apiCache.get(url);
  }

  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.statusText}`);
  }
  
  const data = await response.json();
  
  // Save to cache
  apiCache.set(url, data);
  
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
