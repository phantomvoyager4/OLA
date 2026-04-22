export const API_BASE_URL = '/api';

/**
 * Fetches player data and recent matches from the backend.
 * 
 * @param {string} region - The region of the player (e.g., EUW, NA)
 * @param {string} nickname - The player's in-game name
 * @param {string} tag - The player's tagline (e.g., EUNE1)
 * @param {Object} options - Additional query parameters
 * @param {boolean} options.save - Whether to save the data on the backend
 * @param {number} options.count - Number of matches to fetch
 * @returns {Promise<Object>} The player and matches data
 */
export const getPlayerData = async (region, nickname, tag, options = { save: false, count: 20 }) => {
  const { save, count } = options;
  const url = `${API_BASE_URL}/matches/${region}/${nickname}/${tag}?save=${save}&count=${count}`;
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.statusText}`);
  }
  
  return await response.json();
};
