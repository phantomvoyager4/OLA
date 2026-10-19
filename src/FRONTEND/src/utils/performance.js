export const getPerformanceBadgeClass = (band) => {
  switch (String(band || '').toLowerCase()) {
    case 'remake':
    case 'unscored':
      return 'bg-gray-500/10 text-gray-400 border-gray-400/20';
    case 'elite':
      return 'bg-amber-500/20 text-amber-300 border-amber-400/40';
    case 'strong':
      return 'bg-green-500/20 text-green-300 border-green-400/40';
    case 'solid':
      return 'bg-blue-500/20 text-blue-300 border-blue-400/40';
    default:
      return 'bg-red-500/20 text-red-300 border-red-400/40';
  }
};

// KDA between 1 and 2 stays neutral on purpose.
export const getKdaColorClass = (kda) => {
  const value = Number(kda);
  if (!Number.isFinite(value)) return 'text-on-surface';
  if (value > 3) return 'text-amber-300';
  if (value >= 2) return 'text-green-400';
  if (value < 1) return 'text-red-400';
  return 'text-on-surface';
};

export const getKpColorClass = (kp) => {
  const value = Number(kp);
  if (!Number.isFinite(value)) return 'text-on-surface';
  if (value > 60) return 'text-amber-300';
  if (value >= 30) return 'text-green-400';
  return 'text-red-400';
};

// Remakes and unscored games have no score and are left out of score stats.
export const getMatchScore = (match) => {
  if (match.isRemake || match.performanceScore === null || match.performanceScore === undefined) {
    return null;
  }
  const score = Number(match.performanceScore);
  return Number.isNaN(score) ? null : score;
};

// Uses the population standard deviation.
export const summarizeScores = (scores) => {
  if (scores.length === 0) return { average: 0, median: 0, stdDev: 0 };

  const average = scores.reduce((sum, score) => sum + score, 0) / scores.length;

  const sorted = [...scores].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  const median =
    sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];

  const variance =
    scores.reduce((sum, score) => sum + Math.pow(score - average, 2), 0) / scores.length;

  return { average, median, stdDev: Math.sqrt(variance) };
};
