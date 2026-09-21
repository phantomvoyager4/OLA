import { useEffect, useRef, useState } from 'react';
import { getPlayerSuggestions, SuggestionsThrottledError } from '../services/api';

// Wait for a 300 ms pause in typing before asking the backend...
const DEBOUNCE_MS = 300;
// ...but never hold a request back longer than this during continuous typing,
// so fast typists still see suggestions. Caps traffic at ~1 request/second.
const MAX_WAIT_MS = 1000;
const MIN_QUERY_LENGTH = 2;
const SUGGESTION_LIMIT = 8;
const CACHE_TTL_MS = 60_000;

// Shared by every search box on the page.
const suggestionCache = new Map();
let throttledUntil = 0;

const fold = (value) => value.trim().toLocaleLowerCase();
const cacheKey = (region, query) => `${region}|${query}`;

/** Same tiers as the backend: name prefix, later-word prefix, substring. */
const matchTier = (entry, query) => {
  const [rawName, ...rawTag] = query.split('#');
  const nameQuery = rawName.trim();
  const tagQuery = rawTag.join('#').trim();
  const name = fold(entry.name);

  if (tagQuery && !fold(entry.tag).startsWith(tagQuery)) return -1;
  if (name.startsWith(nameQuery)) return 0;
  if (name.includes(` ${nameQuery}`)) return 1;
  if (name.includes(nameQuery)) return 2;
  return -1;
};

/**
 * Serve a query from cache without a request when possible. A shorter
 * cached query that returned fewer than the limit is a complete result set,
 * and every longer query only narrows it, so it can be filtered locally.
 */
const readCache = (region, query) => {
  const now = Date.now();
  for (let length = query.length; length >= MIN_QUERY_LENGTH; length -= 1) {
    const prefix = query.slice(0, length);
    const cached = suggestionCache.get(cacheKey(region, prefix));
    if (!cached || now - cached.at > CACHE_TTL_MS) continue;
    if (length === query.length) return cached.results;
    if (cached.results.length >= SUGGESTION_LIMIT) return null;

    return cached.results
      .map((entry, rank) => ({ entry, rank, tier: matchTier(entry, query) }))
      .filter(({ tier }) => tier >= 0)
      .sort((a, b) => a.tier - b.tier || a.rank - b.rank)
      .map(({ entry }) => entry);
  }
  return null;
};

/**
 * Debounced, throttled Riot ID suggestions for a search box.
 *
 * Suggestions come from the backend's local index and never touch Riot, so
 * the limits here protect our own server: a 300 ms debounce with a 1 s max
 * wait, local narrowing of cached results, and a pause after a 429.
 *
 * @param {string} query - "name" or "name#tag"
 * @param {string} region - Region label from the search form
 * @param {Object} options - { enabled }
 * @returns {{ suggestions: Array, loading: boolean, query: string }}
 */
export default function usePlayerSuggestions(query, region, { enabled = true } = {}) {
  const [state, setState] = useState({ suggestions: [], loading: false, query: '' });
  const latestRef = useRef({ query: '', region });
  const pendingSinceRef = useRef(null);
  const inFlightRef = useRef(null);

  useEffect(() => () => inFlightRef.current?.abort(), []);

  useEffect(() => {
    const folded = fold(query);
    latestRef.current = { query: folded, region };

    if (!enabled || folded.length < MIN_QUERY_LENGTH) {
      pendingSinceRef.current = null;
      setState({ suggestions: [], loading: false, query: folded });
      return undefined;
    }

    const cached = readCache(region, folded);
    if (cached) {
      pendingSinceRef.current = null;
      setState({ suggestions: cached, loading: false, query: folded });
      return undefined;
    }

    setState((current) => ({ ...current, loading: true }));

    const now = Date.now();
    pendingSinceRef.current ??= now;
    const untilMaxWait = MAX_WAIT_MS - (now - pendingSinceRef.current);
    const delay = Math.max(0, Math.min(DEBOUNCE_MS, untilMaxWait), throttledUntil - now);

    const timer = setTimeout(async () => {
      pendingSinceRef.current = null;
      // A response for a shorter query may have landed while we waited.
      const landed = readCache(region, folded);
      if (landed) {
        setState({ suggestions: landed, loading: false, query: folded });
        return;
      }
      // A newer request supersedes the older one. Requests are deliberately
      // not aborted on every keystroke, or a max-wait request would never land.
      inFlightRef.current?.abort();
      const controller = new AbortController();
      inFlightRef.current = controller;

      try {
        const results = await getPlayerSuggestions(folded, region, {
          signal: controller.signal,
          limit: SUGGESTION_LIMIT,
        });
        suggestionCache.set(cacheKey(region, folded), { at: Date.now(), results });

        const latest = latestRef.current;
        if (latest.region !== region) return;
        const current = latest.query === folded ? results : readCache(region, latest.query);
        if (current) {
          setState({
            suggestions: current,
            loading: latest.query !== folded,
            query: latest.query,
          });
        }
      } catch (error) {
        if (error.name === 'AbortError') return;
        if (error instanceof SuggestionsThrottledError) {
          throttledUntil = Date.now() + error.retryAfterMs;
        }
        // Keep the last good suggestions on screen; they are still useful.
        setState((current) => ({ ...current, loading: false }));
      } finally {
        if (inFlightRef.current === controller) inFlightRef.current = null;
      }
    }, delay);

    return () => clearTimeout(timer);
  }, [query, region, enabled]);

  return state;
}
