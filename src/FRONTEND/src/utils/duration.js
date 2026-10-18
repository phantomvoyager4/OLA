// Game length in seconds from match metadata. Matches saved before
// gameDuration_sec existed store gameDuration_min as minutes.seconds (27.09 = 27:09).
export const gameDurationSeconds = (metadata) => {
  if (metadata?.gameDuration_sec != null) return Number(metadata.gameDuration_sec);
  const legacy = Number(metadata?.gameDuration_min || 0);
  const minutes = Math.floor(legacy);
  return minutes * 60 + Math.round((legacy - minutes) * 100);
};

export const formatGameDuration = (metadata, fallback = '00:00') => {
  const seconds = gameDurationSeconds(metadata);
  if (!seconds) return fallback;
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
};
