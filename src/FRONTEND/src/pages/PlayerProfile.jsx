import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getPlayerActivity, getPlayerData, getRateLimitStatus } from "../services/api";
import { Link, NavLink } from "react-router-dom";

const noIcon = "/icons/noicon.jpg";

const assistMeIcon = "/pings/assistMePings.png";
const allInIcon = "/pings/allInPings.png";
const enemyMissingIcon = "/pings/enemyMissingPings.png";
const enemyVisionIcon = "/pings/enemyVisionPings.png";
const needVisionIcon = "/pings/needVisionPings.png";
const onMyWayIcon = "/pings/onMyWayPings.png";
const pushIcon = "/pings/pushPings.png";
const retreatIcon = "/pings/retreatPings.png";

const unrankedIcon = "/tiers/unranked.png";
const ironIcon = "/tiers/iron.png";
const bronzeIcon = "/tiers/bronze.png";
const silverIcon = "/tiers/silver.png";
const goldIcon = "/tiers/gold.png";
const platinumIcon = "/tiers/platinum.png";
const emeraldIcon = "/tiers/emerald.png";
const diamondIcon = "/tiers/diamond.png";
const masterIcon = "/tiers/master.png";
const grandmasterIcon = "/tiers/grandmaster.png";
const challengerIcon = "/tiers/challenger.png";

const handleDuoClick = (playerName) => {
  if (!playerName || !playerName.includes('#')) return;
  const [nickname, tag] = playerName.split('#');
  const cleanTag = tag.replace('#', '');

  let extractedRegion = 'EUW';
  if (matchData && matchData.region) {
    extractedRegion = matchData.region;
  } else if (matchId && matchId.includes('_')) {
    extractedRegion = matchId.split('_')[0].replace(/[0-9]/g, '');
  }

  const cleanRegion = extractedRegion.replace(/\s+/g, '').toUpperCase();
  navigate(`/player/${cleanRegion}/${nickname}-${cleanTag}`);
};

const getPerformanceBadgeClass = (band) => {
  switch (String(band || '').toLowerCase()) {
    case 'remake':
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

const RateLimitIndicator = ({ status }) => {
  const [longUsed = 0, longLimit = 90] = String(status.longWindow || "0/90")
    .split("/")
    .map(Number);
  const usagePercent = Math.min(
    100,
    Math.round((longUsed / Math.max(1, longLimit)) * 100),
  );
  const isWarning = status.warning;

  return (
    <aside
      aria-live="polite"
      className={`fixed bottom-4 right-4 z-50 w-[calc(100%-2rem)] max-w-80 overflow-hidden rounded-xl border bg-surface-container/95 shadow-[0_12px_40px_rgba(0,0,0,0.45)] backdrop-blur-xl transition-colors ${
        isWarning ? "border-amber-400/50" : "border-primary/30"
      }`}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            isWarning
              ? "bg-amber-400/15 text-amber-300"
              : "bg-primary/15 text-primary"
          }`}
        >
          <span className="material-symbols-outlined text-xl">
            {isWarning ? "warning" : "speed"}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="truncate text-xs font-bold uppercase tracking-widest text-on-surface">
              Riot API Capacity
            </p>
            <span
              className={`text-xs font-bold ${
                isWarning ? "text-amber-300" : "text-primary"
              }`}
            >
              {status.initialized ? `${longUsed}/${longLimit}` : "Checking..."}
            </span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-container-highest">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isWarning ? "bg-amber-400" : "bg-primary"
              }`}
              style={{ width: `${status.initialized ? usagePercent : 0}%` }}
            />
          </div>
          <p className="mt-1.5 text-[11px] text-on-surface-variant">
            {!status.initialized
              ? "Waiting for the first API response"
              : isWarning
                ? `Approaching limit · budget resets in ~${status.resetSeconds}s`
                : `${usagePercent}% of the two-minute request budget used`}
          </p>
        </div>
      </div>
    </aside>
  );
};

export default function PlayerProfile() {
  const { region, riotId } = useParams();
  const navigate = useNavigate();

  // Extract nickname and tag from riotId (e.g., softmax-EUNE1)
  const lastDashIndex = riotId.lastIndexOf("-");
  const nickname =
    lastDashIndex !== -1 ? riotId.substring(0, lastDashIndex) : riotId;
  const tag = lastDashIndex !== -1 ? riotId.substring(lastDashIndex + 1) : "";

  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [extraDates, setExtraDates] = useState([]);
  const [loadedProfileKey, setLoadedProfileKey] = useState(null);
  const [nextMatchesStart, setNextMatchesStart] = useState(20);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreMatches, setHasMoreMatches] = useState(true);
  const [loadMoreError, setLoadMoreError] = useState(null);
  const [rateLimitStatus, setRateLimitStatus] = useState(() => getRateLimitStatus());
  const profileKey = `${region}/${nickname}/${tag}`;

  const handleDuoClick = (playerName) => {
    if (!playerName || !playerName.includes('#')) return;

    const [nickname, tag] = playerName.split('#');
    const cleanTag = tag.replace('#', '');
    const cleanRegion = (region || 'EUW').replace(/\s+/g, '').toUpperCase();

    navigate(`/player/${cleanRegion}/${nickname}-${cleanTag}`);
  };



  useEffect(() => {
    const handleRateLimitStatus = (event) => {
      const status = event.detail;
      setRateLimitStatus(status || getRateLimitStatus());
    };

    window.addEventListener("riot-rate-limit-status", handleRateLimitStatus);
    return () => window.removeEventListener("riot-rate-limit-status", handleRateLimitStatus);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        setPlayerData(null);
        setExtraDates([]);
        setLoadedProfileKey(null);
        setNextMatchesStart(20);
        setHasMoreMatches(true);
        setLoadMoreError(null);
        const data = await getPlayerData(region, nickname, tag, {
          save: false,
          count: 20,
          signal: controller.signal,
        });
        console.log("Fetched Player Data:", data);
        setPlayerData(data);
        setLoadedProfileKey(profileKey);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    if (region && nickname && tag) {
      fetchData();
    }

    return () => controller.abort();
  }, [region, nickname, tag, profileKey]);

  useEffect(() => {
    const controller = new AbortController();

    const fetchActivity = async () => {
      try {
        const activity = await getPlayerActivity(region, nickname, tag, {
          count: 40,
          start: 20,
          signal: controller.signal,
        });
        if (!controller.signal.aborted && Array.isArray(activity?.dates)) {
          setExtraDates(activity.dates);
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Failed to fetch player activity:", err);
        }
      }
    };

    if (
      loadedProfileKey === profileKey &&
      playerData &&
      Array.isArray(playerData) &&
      playerData.length > 0
    ) {
      fetchActivity();
    }

    return () => controller.abort();
  }, [playerData, loadedProfileKey, profileKey, region, nickname, tag]);

  const handleShowMore = async () => {
    if (loadingMore || !hasMoreMatches) return;

    setLoadingMore(true);
    setLoadMoreError(null);
    try {
      const extraData = await getPlayerData(region, nickname, tag, {
        save: false,
        count: 20,
        start: nextMatchesStart,
      });
      const newMatches = Array.isArray(extraData)
        ? extraData.filter((match) => match?.match_id && Array.isArray(match.players))
        : [];

      setPlayerData((previousData) => {
        const previousMatches = Array.isArray(previousData)
          ? previousData.filter((match) => match?.match_id && Array.isArray(match.players))
          : [];
        const summary = Array.isArray(previousData)
          ? previousData.find((entry) => entry?.stats)
          : null;
        const knownMatchIds = new Set(previousMatches.map((match) => match.match_id));
        const uniqueNewMatches = newMatches.filter(
          (match) => !knownMatchIds.has(match.match_id),
        );

        return summary
          ? [...previousMatches, ...uniqueNewMatches, summary]
          : [...previousMatches, ...uniqueNewMatches];
      });

      setNextMatchesStart((currentStart) => currentStart + 20);
      setHasMoreMatches(newMatches.length === 20);
    } catch (err) {
      setLoadMoreError(err.message || "Could not load more matches.");
    } finally {
      setLoadingMore(false);
    }
  };

  const ranks = [
    { name: "Unranked", icon: unrankedIcon },
    { name: "Iron", icon: ironIcon },
    { name: "Bronze", icon: bronzeIcon },
    { name: "Silver", icon: silverIcon },
    { name: "Gold", icon: goldIcon },
    { name: "Platinum", icon: platinumIcon },
    { name: "Emerald", icon: emeraldIcon },
    { name: "Diamond", icon: diamondIcon },
    { name: "Master", icon: masterIcon },
    { name: "Grandmaster", icon: grandmasterIcon },
    { name: "Challenger", icon: challengerIcon },
  ];

  let KDA_mean = 0;
  let CS_mean = 0;
  let KP_mean = 0;
  let needVisionPings_mean = 0;
  let enemyVisionPings_mean = 0;
  let allInPings_mean = 0;
  let pushPings_mean = 0;
  let assistMePings_mean = 0;
  let commandPings_mean = 0;
  let dangerPings_mean = 0;
  let enemyMissingPings_mean = 0;
  let onMyWayPings_mean = 0;
  let retreatPings_mean = 0;

  if (playerData && Array.isArray(playerData) && playerData.length > 0) {
    const stats = playerData.at(-1).stats;
    if (stats) {
      KDA_mean = stats.KDA;
      CS_mean = stats.CS;
      KP_mean = stats.KP;
      needVisionPings_mean = stats.needVisionPings;
      enemyVisionPings_mean = stats.enemyVisionPings;
      allInPings_mean = stats.allInPings;
      pushPings_mean = stats.pushPings;
      assistMePings_mean = stats.assistMePings;
      commandPings_mean = stats.commandPings;
      dangerPings_mean = stats.dangerPings;
      enemyMissingPings_mean = stats.enemyMissingPings;
      onMyWayPings_mean = stats.onMyWayPings;
      retreatPings_mean = stats.retreatPings;
    }
  }

  const mockPings = [
    { name: "Assist Me", value: assistMePings_mean, icon: assistMeIcon },
    { name: "Danger", value: dangerPings_mean, icon: retreatIcon },
    {
      name: "Enemy Missing",
      value: enemyMissingPings_mean,
      icon: enemyMissingIcon,
    },
    { name: "On My Way", value: onMyWayPings_mean, icon: onMyWayIcon },
    { name: "Push", value: pushPings_mean, icon: pushIcon },
    { name: "All In", value: allInPings_mean, icon: allInIcon },
    {
      name: "Enemy Vision",
      value: enemyMissingPings_mean,
      icon: enemyVisionIcon,
    },
    { name: "Need Vision", value: needVisionPings_mean, icon: needVisionIcon },
  ];

  // Extract Caller's Rank details
  let displayTierImg = unrankedIcon;
  let displayRankText = "Unranked";
  let displayLp = "";
  let wins = 0;
  let losses = 0;
  let winrate = "0.0%";
  let iconLink = noIcon;
  let level = 0;
  let masteries = [];
  let MatchesCD = [];
  let performanceAverage = 0;
  let performanceMedian = 0;
  let performanceStdDev = 0;
  let dates = [];
  let topDuoPlayers = [];

  if (playerData && Array.isArray(playerData) && playerData.length > 0) {
    const firstMatch = playerData[0];
    if (firstMatch && firstMatch.players) {
      const callerPlayer = firstMatch.players.find(
        (p) => p.caller === true || p.caller === "true",
      );
      if (callerPlayer && callerPlayer.metadata && callerPlayer.metadata.tier) {
        const tierStr = callerPlayer.metadata.tier; // e.g., "GOLD"
        const rankDiv = callerPlayer.metadata.rank; // e.g., "III"
        const lp = callerPlayer.metadata.leaguePoints; // e.g., 69
        wins = callerPlayer.metadata.wins;
        losses = callerPlayer.metadata.losses;
        winrate = callerPlayer.metadata.winrate;
        iconLink = callerPlayer.icon.image_path;
        level = callerPlayer.summonerLevel;
        masteries = [
          {
            name: callerPlayer.masteries[0].championName,
            img: callerPlayer.masteries[0].championIcon,
            points:
              callerPlayer.masteries[0].championPoints.toLocaleString("en-US"),
            level: callerPlayer.masteries[0].championLevel,
          },
          {
            name: callerPlayer.masteries[1].championName,
            img: callerPlayer.masteries[1].championIcon,
            points:
              callerPlayer.masteries[1].championPoints.toLocaleString("en-US"),
            level: callerPlayer.masteries[1].championLevel,
          },
          {
            name: callerPlayer.masteries[2].championName,
            img: callerPlayer.masteries[2].championIcon,
            points:
              callerPlayer.masteries[2].championPoints.toLocaleString("en-US"),
            level: callerPlayer.masteries[2].championLevel,
          },
        ];

        // Extract caller details from match

        let teammatesMap = {};

        Object.values(playerData).forEach((match, matchIndex) => {
          // extraDates already contains matches 20-59 fetched for the heatmap.
          // Only the initial page contributes dates here to avoid double-counting.
          if (matchIndex < 20 && match?.metadata?.gameDateDay) {
            dates.push(match.metadata.gameDateDay);
          }
          const callerPlayer = match.players?.find(
            (p) => p.caller === true || p.caller === "true",
          );

          if (callerPlayer) {
            match.players.forEach((p) => {
              if (
                p.username !== callerPlayer.username &&
                p.win === callerPlayer.win
              ) {
                if (!teammatesMap[p.username]) {
                  teammatesMap[p.username] = {
                    name: p.username,
                    icon: null,
                    wins: 0,
                    losses: 0,
                    total: 0,
                  };
                }
                teammatesMap[p.username].total += 1;
                teammatesMap[p.username].icon = p.icon?.image_path || noIcon; // Ensure icon path from latest match
                if (callerPlayer.win === true || callerPlayer.win === "true") {
                  teammatesMap[p.username].wins += 1;
                } else {
                  teammatesMap[p.username].losses += 1;
                }
              }
            });

            const itemsData = callerPlayer.items || [];
            const getItemImage = (index) =>
              itemsData[index]?.image_path || null;
            const getItemName = (index) => itemsData[index]?.name || null;

            const summonersData = callerPlayer.summoners || [];
            const getSummonerImage = (index) =>
              summonersData[index]?.image_path || null;
            const getSummonerName = (index) =>
              summonersData[index]?.name || null;

            const runesData = callerPlayer.runes || [];
            const styles = runesData.filter(r => r.group === 'Style');
            const primaryStyle = styles[0];
            const secondaryStyle = styles[1];
            // The main rune is the keystone from the primary style group
            const mainRuneItem = runesData.find(r => r.runeIconLink && r.group === primaryStyle?.name) || runesData.find(r => r.runeIconLink && r.group !== 'Stat Perk') || runesData[5];

            const isRemake =
              callerPlayer.gameEndedInEarlySurrender === true ||
              callerPlayer.gameEndedInEarlySurrender === "true";

            const MatchCallerData = {
              matchId: match.match_id || match.metadata?.matchId,
              date: match.metadata.gameDateDay,

              isRemake,


              win:
                typeof callerPlayer.win === "boolean"
                  ? callerPlayer.win
                  : callerPlayer.win === "true",

              champ: callerPlayer.championName,
              champimageLink: callerPlayer.championImageLink,
              mainRune: mainRuneItem?.runeIconLink,
              mainRuneName: mainRuneItem?.name,
              secondaryRune: secondaryStyle?.styleIconLink || runesData[4]?.styleIconLink,
              secondaryRuneName: secondaryStyle?.name || runesData[4]?.name,
              duration: match.metadata?.gameDuration_min
                ? match.metadata.gameDuration_min.toFixed(2).replace(".", ":")
                : "30:00",
              type: "Ranked Solo",
              k: callerPlayer.kills,
              d: callerPlayer.deaths,
              a: callerPlayer.assists,
              kda: callerPlayer.KDA,
              champLevel: callerPlayer.champLevel || 18,
              items: [
                getItemImage(0),
                getItemImage(1),
                getItemImage(2),
                getItemImage(3),
                getItemImage(4),
                getItemImage(5),
              ],
              itemsNames: [
                getItemName(0),
                getItemName(1),
                getItemName(2),
                getItemName(3),
                getItemName(4),
                getItemName(5),
              ],
              summoners: [getSummonerImage(0), getSummonerImage(1)],
              summonersNames: [getSummonerName(0), getSummonerName(1)],
              performanceScore: callerPlayer.performanceScore ?? callerPlayer.performance_score ?? null,
              performanceBand: callerPlayer.performanceBand ?? callerPlayer.performance_band ?? 'low',
            };

            MatchesCD.push(MatchCallerData);
          }
        });

        const performanceScores = MatchesCD
          .filter(match => {
            const isRemake =
              match.duration &&
              parseInt(match.duration.split(":")[0], 10) < 5;

            return (
              !isRemake &&
              match.performanceScore !== null &&
              match.performanceScore !== undefined
            );
          })
          .map(match => Number(match.performanceScore))
          .filter(score => !Number.isNaN(score));

        if (performanceScores.length > 0) {
          // Average
          performanceAverage =
            performanceScores.reduce((sum, score) => sum + score, 0) /
            performanceScores.length;

          // Median
          const sorted = [...performanceScores].sort((a, b) => a - b);
          const mid = Math.floor(sorted.length / 2);

          performanceMedian =
            sorted.length % 2 === 0
              ? (sorted[mid - 1] + sorted[mid]) / 2
              : sorted[mid];

          // Population standard deviation
          const variance =
            performanceScores.reduce(
              (sum, score) => sum + Math.pow(score - performanceAverage, 2),
              0
            ) / performanceScores.length;

          performanceStdDev = Math.sqrt(variance);
        }


        topDuoPlayers = Object.values(teammatesMap)
          .filter((p) => p.total > 2)
          .sort((a, b) => b.total - a.total || b.wins - a.wins);

        // Format label "Gold 3" or "Gold III"
        displayRankText = `${tierStr.charAt(0) + tierStr.slice(1).toLowerCase()} ${rankDiv}`;
        if (lp !== undefined) {
          displayLp = `${lp} LP`;
        }

        // Find matching icon
        const matchedRank = ranks.find(
          (r) => r.name.toLowerCase() === tierStr.toLowerCase(),
        );
        if (matchedRank) {
          displayTierImg = matchedRank.icon;
        }
      }
    }
  }

  // Combine with lazily loaded dates
  dates = dates.concat(extraDates);

  // Generate activity heatmap data from actual matches dates
  const dateCounts = {};
  dates.forEach((d) => {
    if (!d) return;
    try {
      const dateObj = new Date(d);
      const dateKey = dateObj.toDateString();
      dateCounts[dateKey] = (dateCounts[dateKey] || 0) + 1;
    } catch (e) { }
  });

  const today = new Date();
  // Calculate Activity Summary Details
  const activeDaysCount = Object.keys(dateCounts).length;
  const totalGamesInActiveDays = Object.values(dateCounts).reduce(
    (sum, count) => sum + count,
    0,
  );
  const avgGamesPerActiveDay =
    activeDaysCount > 0
      ? (totalGamesInActiveDays / activeDaysCount).toFixed(1)
      : 0;

  let daysSinceLastActivity = "N/A";
  if (dates.length > 0) {
    const validDates = dates
      .map((d) => new Date(d).getTime())
      .filter((t) => !isNaN(t));
    if (validDates.length > 0) {
      const maxDate = new Date(Math.max(...validDates));
      const diffTime = Math.abs(today - maxDate);
      daysSinceLastActivity = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    }
  }

  const mockHeatmap = Array.from({ length: 13 }, (_, colIndex) =>
    Array.from({ length: 7 }, (_, rowIndex) => {
      const daysAgo = (12 - colIndex) * 7 + (6 - rowIndex);
      const targetDate = new Date();
      targetDate.setDate(today.getDate() - daysAgo);
      const count = dateCounts[targetDate.toDateString()] || 0;

      // Format to YYYY-MM-DD
      const year = targetDate.getFullYear();
      const month = String(targetDate.getMonth() + 1).padStart(2, "0");
      const day = String(targetDate.getDate()).padStart(2, "0");
      const dateStr = `${year}-${month}-${day}`;

      return { count, dateStr };
    }),
  );

  if (loading) {
    return (
      <main className="min-h-screen pt-24 pb-12 flex flex-col items-center justify-center">
        <RateLimitIndicator status={rateLimitStatus} />
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <h2 className="mt-4 text-xl font-headline text-on-surface">
          Analyzing matches...
        </h2>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen pt-24 pb-12 flex flex-col gap-3 items-center justify-center">
        <RateLimitIndicator status={rateLimitStatus} />
        <h2 className="text-2xl font-headline text-error">
          Summoner not found!
        </h2>
        <p className="mt-2 text-on-surface-variant font-bold uppercase">
          {error}
        </p>
        <Link
          to="/"
          className="mt-1 px-2 py-0.5 text-lg bg-secondary text-black uppercase font-bold rounded-sm tracking-wider"
        >
          Try again
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center">
      <RateLimitIndicator status={rateLimitStatus} />
      {/* Expanded to 1600px for full PC width, 2 columns on extra large screens */}
      <div className="w-full max-w-400 px-6 grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        {/* ========================================== */}
        {/* LEFT SIDE: Caller Data & Statistics          */}
        {/* ========================================== */}
        <div className="flex flex-col gap-4">
          {/* 1. TOP SECTION: General Info --- */}
          <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col md:flex-row items-center gap-6 shrink-0">
            <div className="w-22 h-22 rounded-full bg-surface-container-highest flex items-center justify-center overflow-hidden shadow-primary/20 shrink-0">
              <img
                src={iconLink}
                alt="Profile Icon"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex flex-col text-center md:text-left">
              <h1 className="text-4xl md:text-5xl font-headline font-bold text-on-surface">
                {nickname} <span className="text-primary text-3xl">#{tag}</span>
              </h1>
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 mt-3 text-sm font-body text-on-surface-variant">
                <span className="bg-surface-container-low px-3 py-1 rounded-md border border-outline-variant/30">
                  Level:{" "}
                  <span className="text-on-surface font-bold">{level}</span>
                </span>
                <span className="bg-surface-container-low px-3 py-1 rounded-md border border-outline-variant/30">
                  Region:{" "}
                  <span className="text-on-surface font-bold">{region}</span>
                </span>
              </div>
            </div>
          </div>

          {/* 2. RANK, WINRATE AND W/L --- */}
          <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2 flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="w-18 h-18 bg-surface-container-highest rounded-full flex items-center justify-center overflow-hidden">
                <img
                  src={displayTierImg}
                  alt={displayRankText}
                  className="w-full h-full object-cover p-2 scale-1.4"
                />
              </div>
              <div className="text-center md:text-left">
                <h2 className="font-headline font-bold text-2xl text-on-surface flex items-center gap-2">
                  {displayRankText}{" "}
                  <span className="text-on-surface-variant font-normal text-lg">
                    {displayLp}
                  </span>
                </h2>
                <p className="text-sm text-outline">Ranked Solo/Duo</p>
              </div>
            </div>
            <div className="text-center md:text-right items-center">
              <h2 className={`font-headline font-bold text-3xl ${parseFloat(winrate) < 50 ? 'text-red-400' : 'text-green-400'}`}>
                {winrate}
              </h2>
              {/* <p className="text-sm text-on-surface-variant font-bold mt-1">{wins}W <span className="text-outline font-normal">-</span> {losses}L</p> */}
              <p className="text-sm text-on-surface-variant font-bold mt-1">
                {wins + losses}M • {wins}W{" "}
                <span className="text-outline font-normal">/</span> {losses}L
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full shrink-0">
            {/* 3. RECENT MATCHES STATISTICS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-2">
                Recent Statistics
              </h2>
              <p className="text-sm text-outline mb-4">Last 20 matches</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">
                    Average CS/min
                  </span>
                  <span className="text-2xl font-bold text-on-surface">
                    {CS_mean}
                  </span>
                </div>
                <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">KDA</span>
                  <span className="text-2xl font-bold text-on-surface">
                    {KDA_mean}
                  </span>
                </div>
                <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">
                    Kill Participation
                  </span>
                  <span className="text-2xl font-bold text-on-surface">
                    {KP_mean}%
                  </span>
                </div>
                <div className="flex flex-col border-l-2 border-secondary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">
                    Score Average
                  </span>
                  <span className={`text-2xl font-bold text-on-surface`} >
                    {performanceAverage.toFixed(1)}
                  </span>
                </div>
                <div className="flex flex-col border-l-2 border-secondary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">
                    Score Median
                  </span>
                  <span className={`text-2xl font-bold text-on-surface`}>
                    {performanceMedian.toFixed(1)}
                  </span>
                </div>
                <div className="flex flex-col border-l-2 border-secondary/50 pl-4 py-1">
                  <span className="text-sm text-on-surface-variant">
                    Score σ
                  </span>
                  <span className="text-2xl font-bold text-on-surface">
                    {performanceStdDev.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>
            {/* ACTIVITY HEATMAP & 90 DAY SUMMARY --- */}
            <div className="glass-panel px-12 ghost-border rounded-xl p-6 md:col-span-2 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Side: Activity Heatmap */}
              <div className="flex flex-col w-max mx-auto lg:mx-0">
                <div className="flex justify-between items-end mb-1">
                  <h2 className="font-headline font-bold text-xl text-on-surface">
                    Activity
                  </h2>
                  <span className="text-[11px] text-outline font-bold uppercase tracking-wide pb-1">
                    Past 91 Days
                  </span>
                </div>

                <div className="flex flex-col">
                  {/* Heatmap wrapper (w-max ensures container naturally fits its children width) */}
                  <div className="flex gap-2 pt-5 pb-2">
                    <div className="flex flex-col gap-0.9 text-[10px] text-outline justify-around font-bold uppercase tracking-wider pr-1">
                      <span>Mon</span>
                      <span>Tue</span>
                      <span>Wed</span>
                      <span>Thu</span>
                      <span>Fri</span>
                      <span>Sat</span>
                      <span>Sun</span>
                    </div>
                    <div className="flex gap-0.5">
                      {mockHeatmap.map((week, colIndex) => (
                        <div key={colIndex} className="flex flex-col gap-0.5">
                          {week.map((item, rowIndex) => {
                            const { count, dateStr } = item;
                            let bgClass =
                              "bg-surface-container-highest/40 border-outline-variant/10 border"; // 0 games
                            if (count > 0 && count <= 2)
                              bgClass =
                                "bg-primary/20 border-primary/20 border";
                            else if (count > 2 && count <= 5)
                              bgClass =
                                "bg-primary/50 border-primary/30 border";
                            else if (count > 5 && count <= 8)
                              bgClass =
                                "bg-primary/80 border-primary/50 border";
                            else if (count > 8)
                              bgClass =
                                "bg-primary border-primary border";

                            return (
                              <div
                                key={rowIndex}
                                className={`group relative w-3 h-3 md:w-4 md:h-4 rounded-sm transition-all duration-200 hover:ring-1 hover:ring-primary hover:scale-110 hover:z-20 ${bgClass}`}
                              >
                                {/* Custom Hover Tooltip */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex flex-col items-center w-max whitespace-nowrap bg-surface-container border border-outline-variant/30 py-1 px-2 rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                                  <span className="text-outline text-[10px] font-bold mb-0.5">
                                    {dateStr}
                                  </span>
                                  <span className="text-on-surface text-[10px] uppercase font-bold">
                                    {count} {count === 1 ? "game" : "games"}{" "}
                                    played
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Right-aligned Legend */}
                  <div className="flex items-center gap-1.5 self-end mt-1 text-[11px] text-outline font-medium">
                    <span>Less</span>
                    <div className="w-3 h-3 rounded-sm bg-surface-container-highest/40 border border-outline-variant/10"></div>
                    <div className="w-3 h-3 rounded-sm bg-primary/20 border border-primary/20"></div>
                    <div className="w-3 h-3 rounded-sm bg-primary/50 border border-primary/30"></div>
                    <div className="w-3 h-3 rounded-sm bg-primary/80 border border-primary/50"></div>
                    <div className="w-3 h-3 rounded-sm bg-primary"></div>
                    <span>More</span>
                  </div>
                </div>
              </div>

              {/* Right Side: Total Summary */}
              <div className="flex flex-col h-full">
                <div className="flex justify-between items-end mb-1">
                  <h2 className="font-headline font-bold text-xl text-on-surface">
                    90-Day Summary
                  </h2>
                </div>
                <div className="flex flex-col gap-3 pt-5 h-full">
                  <div className="bg-surface-container-low rounded-lg flex-1 border border-outline-variant/30 flex flex-col justify-center items-center py-2">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide text-center">
                      Avg Games / Active Day
                    </span>
                    <span className="font-headline font-bold text-3xl mt-1">
                      {avgGamesPerActiveDay}
                    </span>
                  </div>
                  <div className="bg-surface-container-low rounded-lg flex-1 border border-outline-variant/30 flex flex-col justify-center items-center py-2">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide text-center">
                      Days Since Last Activity
                    </span>
                    {daysSinceLastActivity === 0 ? (
                      <span className="font-headline font-bold text-xl mt-1 uppercase tracking-wide">
                        Active Today
                      </span>
                    ) : (
                      <span className="font-headline font-bold text-3xl text-on-surface mt-1">
                        {daysSinceLastActivity}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 4. MASTERIES --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">
                Masteries
              </h2>
              <div className="flex flex-col gap-3">
                {masteries.map((champ, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low border border-outline-variant/20 transition-colors cursor-pointer"
                  >
                    <img
                      src={champ.img}
                      className="w-12 h-12 rounded-md"
                      alt={champ.name}
                    />
                    <div className="flex-1 flex flex-col justify-between">
                      <div className="flex justify-between items-center">
                        <p className="font-bold text-on-surface text-base">
                          {champ.name}
                        </p>
                        <span className="text-xs font-bold text-primary bg-primary/8 py-0.5 rounded w-12 flex justify-center shrink-0">
                          {champ.level} lvl
                        </span>
                      </div>
                      <p className="text-xs text-on-surface-variant">
                        {champ.points} PTS
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 5. TOP DUO PLAYERS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">
                Duo Players{" "}
                <span className="text-sm font-normal text-outline">
                  ({MatchesCD.length} loaded matches)
                </span>
              </h2>
              <div className="flex flex-col gap-3">
                {topDuoPlayers.length > 0 ? (
                  topDuoPlayers.map((player, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low border border-outline-variant/20 transition-colors cursor-pointer hover:bg-surface-container-high hover:border-primary/50"
                      onClick={() => handleDuoClick(player.name)}
                    >
                      <img
                        src={player.icon}
                        className="w-12 h-12 rounded-md object-cover"
                        alt={player.name}
                      />
                      <div className="flex-1">
                        <p className="font-bold text-on-surface text-base">
                          {player.name}
                        </p>
                        <p className="text-xs text-on-surface-variant">
                          {((player.wins / player.total) * 100).toFixed(0)}% WR
                          • {player.wins}W / {player.losses}L •{" "}
                          {player.wins + player.losses} Matches
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-outline p-3">
                    No duo teammates found in recent matches.
                  </p>
                )}
              </div>
            </div>

            {/* 6. PINGS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">
                Communication{" "}
                <span className="text-sm font-normal text-outline">
                  (Avg / Match)
                </span>
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {mockPings.map((ping, i) => (
                  <div
                    key={i}
                    className="flex flex-col items-center justify-center p-4 bg-surface-container-low rounded-lg border border-outline-variant/30 text-center"
                  >
                    <img
                      src={ping.icon}
                      alt={`${ping.name} ping icon`}
                      className="w-10 h-10 mb-2 opacity-90 drop-shadow-md"
                    />
                    <span className="font-bold text-on-surface text-xl">
                      {ping.value}
                    </span>
                    <span className="text-xs text-on-surface-variant mt-1">
                      {ping.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ========================================== */}
        {/* RIGHT SIDE: Recent Matches Grid            */}
        {/* ========================================== */}
        <div className="flex flex-col gap-4 w-full">
          <div className="flex justify-between items-end mb-2 bg-surface/90 backdrop-blur-md pb-2 z-10">
            <h2 className="font-headline font-bold text-xl text-on-surface">
              Recent Matches
            </h2>
            <span className="text-sm text-outline font-bold tracking-widest bg-surface-container px-2 py-1 rounded">
              {MatchesCD.length} GAMES
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {(MatchesCD.length > 0 ? MatchesCD : mockMatches).map(
              (match, idx) => (
                <div
                  key={match.matchId || idx}
                  onClick={() => navigate(`/match/${match.matchId}`)}
                  className={`glass-panel ghost-border rounded-xl p-5 flex flex-col md:flex-row items-center gap-4 transition-transform hover:translate-x-1 cursor-pointer 
                   ${match.win ? "border-l-4 border-l-primary/80 bg-primary/5" : "border-l-4 border-l-error/80 bg-error/5"}`}
                >
                  {/* Match Info */}
                  <div className="flex flex-col items-center md:items-start w-full md:w-28 shrink-0">
                    {(() => {
                      const isRemake =
                        match.duration &&
                        parseInt(match.duration.split(":")[0], 10) < 5;

                      return (
                        <p
                          className={`text-sm font-bold ${isRemake
                            ? "text-gray-400"
                            : match.win
                              ? "text-secondary"
                              : "text-error"
                            }`}
                        >
                          {isRemake
                            ? "REMAKE"
                            : match.win
                              ? "VICTORY"
                              : "DEFEAT"}
                        </p>
                      );
                    })()}
                    <p className="text-xs text-outline mt-0.5">{match.type}</p>
                    <div className="w-12 md:w-full h-px bg-outline-variant/30 my-2"></div>
                    <p className="text-xs text-outline">{match.duration} min</p>
                    <p className="text-xs text-outline">{match.date}</p>
                  </div>

                  {/* Summoners & Champ Icon */}
                  <div className="flex items-center gap-2 shrink-0">
                    {/* Champ Icon */}
                    <div className="relative">
                      <img
                        src={match.champimageLink}
                        className="w-16 h-16 rounded-full border-2 border-surface-container shadow-sm"
                        alt={match.champ}
                      />
                      <div className="absolute -bottom-1 -right-1 bg-surface-container-highest rounded-full w-6 h-6 flex items-center justify-center text-[10px] border border-outline/30 font-bold">
                        {match.champLevel || 18}
                      </div>
                    </div>
                    {/* Summs & Runes block */}
                    <div className="flex gap-1 shrink-0">
                      <div className="flex flex-col gap-1">
                        <div className="group relative w-7 h-7 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner">
                          <img src={match.summoners[0]} className="w-full h-full rounded-md" />
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-max max-w-30 bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 text-center rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                            {match.summonersNames[0]}
                          </div>
                        </div>
                        <div className="group relative w-7 h-7 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner">
                          <img src={match.summoners[1]} className="w-full h-full rounded-md" />
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-max max-w-30 bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 text-center rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                            {match.summonersNames[1]}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <div className="group relative w-7 h-7 bg-black rounded-full border border-outline-variant/20 shadow-inner">
                          <img
                            src={match.mainRune}
                            className="w-full h-full object-cover transform rounded-full"
                          />
                          {match.mainRuneName && (
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-max max-w-30 bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 text-center rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                              {match.mainRuneName}
                            </div>
                          )}
                        </div>
                        <div className="group relative w-7 h-7 bg-black rounded-full border border-outline-variant/20 shadow-inner">
                          <img
                            src={match.secondaryRune}
                            className="w-full h-full object-cover p-1 rounded-full"
                          />
                          {match.secondaryRuneName && (
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-max max-w-30 bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 text-center rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                              {match.secondaryRuneName}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* KDA */}
                  <div className="flex flex-col items-center md:items-center py-2 md:py-0 w-full md:w-32 shrink-0">
                    <p className="font-headline font-bold text-xl tracking-wide text-on-surface">
                      {match.k}{" "}
                      <span className="text-on-surface-variant font-normal">
                        /
                      </span>{" "}
                      <span className="text-error">{match.d}</span>{" "}
                      <span className="text-on-surface-variant font-normal">
                        /
                      </span>{" "}
                      {match.a}
                    </p>
                    <p className="text-xs text-outline font-bold mt-1">
                      {match.kda !== undefined && match.kda !== null
                        ? parseFloat(match.kda) === 0
                          ? "0.00 KDA"
                          : `${parseFloat(match.kda).toFixed(2)} KDA`
                        : "KDA"}
                    </p>
                  </div>

                  {/* Performance Grid */}
                  <div className="flex flex-col gap-2 items-center pl-3">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Score</span>
                    {(() => {
                      const isRemake = match.duration && parseInt(match.duration.split(":")[0], 10) < 5;

                      const badgeBand = isRemake ? 'remake' : match.performanceBand;

                      const scoreDisplay = isRemake
                        ? '--'
                        : (match.performanceScore !== null && match.performanceScore !== undefined
                          ? Number(match.performanceScore).toFixed(0)
                          : '--');

                      return (
                        <span className={`inline-flex w-14 items-center justify-center rounded-full border px-2 py-0.5 text-[16px] font-bold ${getPerformanceBadgeClass(badgeBand)}`}>
                          {scoreDisplay}
                        </span>
                      );
                    })()}
                  </div>

                  {/* Items Grid */}
                  <div className="grid grid-cols-3 gap-1 w-max mx-auto md:ml-auto md:mx-0">
                    {match.items
                      ? match.items.map((itemImg, i) => (
                        <div
                          key={i}
                          className="group relative w-8 h-8 sm:w-10 sm:h-10 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner align-middle flex items-center justify-center"
                        >
                          {itemImg && (
                            <>
                              <img
                                src={itemImg}
                                alt="item"
                                className="w-full h-full object-cover rounded-md"
                              />
                              {/* Hover Tooltip */}
                              {match.itemsNames && match.itemsNames[i] && (
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-max max-w-30 bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 text-center rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-999 pointer-events-none">
                                  {match.itemsNames[i]}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      ))
                      : [...Array(6)].map((_, i) => (
                        <div
                          key={i}
                          className="w-8 h-8 sm:w-10 sm:h-10 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner"
                        ></div>
                      ))}
                  </div>
                  <span className="material-symbols-outlined color-primary">
                    keyboard_arrow_right
                  </span>
                </div>
              ),
            )}

            {loadMoreError && (
              <p className="text-sm text-error text-center py-2">
                {loadMoreError}
              </p>
            )}

            {hasMoreMatches ? (
              <button
                type="button"
                onClick={handleShowMore}
                disabled={loadingMore}
                className="mt-2 w-full rounded-xl border border-primary/30 bg-primary/10 px-5 py-3 font-headline text-sm font-bold uppercase tracking-widest text-primary transition-colors hover:bg-primary/20 disabled:cursor-wait disabled:opacity-60"
              >
                {loadingMore ? "Loading..." : "Show More"}
              </button>
            ) : (
              <p className="py-3 text-center text-sm font-bold text-outline">
                No more matches to show
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Back to Top Button */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className="mt-12 px-6 py-2 bg-surface-container-highest hover:bg-primary/20 text-on-surface hover:text-primary rounded-full transition-all border border-outline-variant/30 flex items-center gap-2 font-bold text-sm"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className="w-4 h-4"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4.5 15.75l7.5-7.5 7.5 7.5"
          />
        </svg>
        BACK TO TOP
      </button>
    </main>
  );
}
