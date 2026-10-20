import { useEffect, useRef, useState } from "react";
import {
  getKdaColorClass,
  getKpColorClass,
  getMatchScore,
  getPerformanceBadgeClass,
  summarizeScores,
} from "../utils/performance";

const PLOT_HEIGHT = 128;
const PAD = { top: 8, right: 8, bottom: 10, left: 28 };
const SVG_HEIGHT = PAD.top + PLOT_HEIGHT + PAD.bottom;
const GRID_SCORES = [0, 25, 50, 75, 100];
const LABELED_SCORES = [0, 50, 100];
const TOOLTIP_WIDTH = 232;
const TOOLTIP_OFFSET = 14;

const ROLE_LABELS = {
  TOP: "Top",
  JUNGLE: "Jungle",
  MIDDLE: "Mid",
  BOTTOM: "Bot",
  UTILITY: "Support",
};

const yForScore = (score) =>
  PAD.top + (1 - Math.min(Math.max(score, 0), 100) / 100) * PLOT_HEIGHT;

function GameTooltip({ game, score, left }) {
  const result = game.isRemake ? "REMAKE" : game.win ? "VICTORY" : "DEFEAT";
  const resultClass = game.isRemake
    ? "text-gray-400"
    : game.win
      ? "text-secondary"
      : "text-error";
  const band = game.isRemake ? "remake" : score === null ? "unscored" : game.performanceBand;
  const kda = Number(game.kda);
  const kp = Number(game.kp);
  const csMin = Number(game.csMin);

  return (
    <div
      className="pointer-events-none absolute top-1/2 z-50 -translate-y-1/2 rounded-lg border border-outline-variant/30 bg-surface-container p-3 shadow-[0_6px_20px_rgba(0,0,0,0.45)]"
      style={{ left, width: TOOLTIP_WIDTH }}
    >
      <div className="flex items-center gap-2.5">
        <img
          src={game.champimageLink}
          alt=""
          className="h-9 w-9 shrink-0 rounded-full border border-outline-variant/30"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold text-on-surface">{game.champ}</p>
          <p className="truncate text-[10px] font-medium text-outline">
            {[ROLE_LABELS[game.role] || game.role, game.duration].filter(Boolean).join(" · ")}
          </p>
        </div>
        <span
          className={`inline-flex w-11 shrink-0 items-center justify-center rounded-full border px-1.5 py-0.5 text-sm font-bold ${getPerformanceBadgeClass(band)}`}
        >
          {score === null ? "--" : score.toFixed(0)}
        </span>
      </div>

      <div className="mt-2.5 flex items-center justify-between">
        <div className="flex gap-1">
          {game.summoners.map((image, i) =>
            image ? (
              <img
                key={i}
                src={image}
                alt={game.summonersNames[i] || ""}
                className="h-5 w-5 rounded border border-outline-variant/20"
              />
            ) : (
              <div
                key={i}
                className="h-5 w-5 rounded border border-outline-variant/20 bg-surface-container-highest"
              />
            ),
          )}
        </div>
        <span className="ml-2 flex-1 text-[10px] font-medium text-outline">{game.date}</span>
        <span className={`text-xs font-bold ${resultClass}`}>{result}</span>
      </div>

      <div className="mt-2.5 grid grid-cols-4 gap-1 border-t border-outline-variant/30 pt-2.5">
        <div className="flex flex-col">
          <span className="text-xs font-bold text-on-surface">
            {game.k}/<span className="text-error">{game.d}</span>/{game.a}
          </span>
          <span className="text-[9px] font-bold uppercase tracking-wider text-outline">K/D/A</span>
        </div>
        <div className="flex flex-col">
          <span className={`text-xs font-bold ${getKdaColorClass(kda)}`}>
            {Number.isFinite(kda) ? kda.toFixed(2) : "--"}
          </span>
          <span className="text-[9px] font-bold uppercase tracking-wider text-outline">KDA</span>
        </div>
        <div className="flex flex-col">
          <span className={`text-xs font-bold ${getKpColorClass(kp)}`}>
            {Number.isFinite(kp) ? `${kp.toFixed(0)}%` : "--"}
          </span>
          <span className="text-[9px] font-bold uppercase tracking-wider text-outline">KP</span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-bold text-on-surface">
            {Number.isFinite(csMin) ? csMin.toFixed(1) : "--"}
          </span>
          <span className="text-[9px] font-bold uppercase tracking-wider text-outline">CS/min</span>
        </div>
      </div>
    </div>
  );
}

function LegendItem({ children, label, value }) {
  return (
    <span className="flex items-center gap-1.5">
      <svg width="16" height="8" aria-hidden="true">
        {children}
      </svg>
      {label} <span className="font-bold text-on-surface">{value}</span>
    </span>
  );
}

// `games` arrive newest first, as the API returns them; the chart reads left to right.
export default function PerformanceChart({ games, selectedMatchId, onSelect }) {
  const containerRef = useRef(null);
  const [width, setWidth] = useState(0);
  const [hoverIndex, setHoverIndex] = useState(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const observer = new ResizeObserver(([entry]) => {
      setWidth(entry.contentRect.width);
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const timeline = [...games].reverse();
  const scores = timeline.map(getMatchScore);
  const scoredValues = scores.filter((score) => score !== null);
  const hasScores = scoredValues.length > 0;
  const { average, median, stdDev } = summarizeScores(scoredValues);
  const wins = timeline.filter((game) => !game.isRemake && game.win).length;
  const losses = timeline.filter((game) => !game.isRemake && !game.win).length;

  const plotLeft = PAD.left;
  const plotRight = Math.max(width - PAD.right, plotLeft);
  const step = (plotRight - plotLeft) / timeline.length;
  const xForIndex = (index) => plotLeft + step * (index + 0.5);

  const linePath = scores
    .map((score, index) => (score === null ? null : `${xForIndex(index)},${yForScore(score)}`))
    .filter(Boolean)
    .map((point, i) => `${i === 0 ? "M" : "L"}${point}`)
    .join(" ");

  const bandTop = yForScore(average + stdDev);
  const bandBottom = yForScore(average - stdDev);

  const hovered = hoverIndex !== null ? timeline[hoverIndex] : null;
  let tooltipLeft = 0;
  if (hovered) {
    const x = xForIndex(hoverIndex);
    tooltipLeft =
      x < width / 2
        ? Math.min(x + TOOLTIP_OFFSET, width - TOOLTIP_WIDTH)
        : Math.max(x - TOOLTIP_OFFSET - TOOLTIP_WIDTH, 0);
  }

  return (
    <div className="@container">
      <div ref={containerRef} className="relative" style={{ height: SVG_HEIGHT }}>
        {!hasScores && (
          <p className="flex h-full items-center justify-center text-sm text-outline">
            No scored games in the recent matches.
          </p>
        )}
        {hasScores && width > 0 && (
          <svg
            width={width}
            height={SVG_HEIGHT}
            className="block overflow-visible"
            role="group"
            aria-label="Performance score per game, oldest to latest"
            onPointerLeave={() => setHoverIndex(null)}
          >
            {GRID_SCORES.map((score) => (
              <line
                key={score}
                x1={plotLeft}
                x2={plotRight}
                y1={yForScore(score)}
                y2={yForScore(score)}
                className="stroke-outline-variant/40"
                strokeWidth="1"
              />
            ))}
            {LABELED_SCORES.map((score) => (
              <text
                key={score}
                x={plotLeft - 8}
                y={yForScore(score)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-outline text-[10px] font-bold tabular-nums"
              >
                {score}
              </text>
            ))}

            <rect
              x={plotLeft}
              y={bandTop}
              width={plotRight - plotLeft}
              height={bandBottom - bandTop}
              className="fill-secondary-fixed/10"
            />
            <line
              x1={plotLeft}
              x2={plotRight}
              y1={yForScore(median)}
              y2={yForScore(median)}
              className="stroke-on-surface/80"
              strokeWidth="2"
              strokeDasharray="0.1 4"
              strokeLinecap="round"
            />
            <line
              x1={plotLeft}
              x2={plotRight}
              y1={yForScore(average)}
              y2={yForScore(average)}
              className="stroke-secondary-fixed"
              strokeWidth="1.5"
              strokeDasharray="6 4"
            />

            {hovered && (
              <line
                x1={xForIndex(hoverIndex)}
                x2={xForIndex(hoverIndex)}
                y1={PAD.top}
                y2={PAD.top + PLOT_HEIGHT}
                className="stroke-outline"
                strokeWidth="1"
              />
            )}

            <path
              d={linePath}
              fill="none"
              className="stroke-primary-fixed"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />

            {timeline.map((game, index) => {
              const score = scores[index];
              const x = xForIndex(index);
              const isSelected = game.matchId === selectedMatchId;

              if (score === null) {
                return (
                  <circle
                    key={game.matchId || index}
                    cx={x}
                    cy={PAD.top + PLOT_HEIGHT + 6}
                    r="3"
                    fill="none"
                    className={isSelected ? "stroke-primary-fixed" : "stroke-outline"}
                    strokeWidth="1.5"
                  />
                );
              }

              return (
                <g key={game.matchId || index}>
                  {isSelected && (
                    <circle cx={x} cy={yForScore(score)} r="10" className="fill-primary-fixed/25" />
                  )}
                  <circle
                    cx={x}
                    cy={yForScore(score)}
                    r={isSelected ? 6 : hoverIndex === index ? 5.5 : 4.5}
                    className={`fill-primary-fixed`}
                    strokeWidth="1.25"
                  />
                </g>
              );
            })}

            {timeline.map((game, index) => {
              const score = scores[index];
              const result = game.isRemake ? "remake" : game.win ? "victory" : "defeat";
              return (
                <rect
                  key={game.matchId || index}
                  x={plotLeft + step * index}
                  y={0}
                  width={step}
                  height={SVG_HEIGHT}
                  fill="transparent"
                  role="button"
                  tabIndex={0}
                  aria-label={`${game.champ} ${result}, score ${score === null ? "none" : score.toFixed(0)}. Show this game in the match list.`}
                  className="cursor-pointer outline-none"
                  onPointerEnter={() => setHoverIndex(index)}
                  onFocus={() => setHoverIndex(index)}
                  onBlur={() => setHoverIndex(null)}
                  onClick={() => onSelect(game.matchId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(game.matchId);
                    }
                  }}
                />
              );
            })}
          </svg>
        )}

        {hovered && width > 0 && (
          <GameTooltip game={hovered} score={scores[hoverIndex]} left={tooltipLeft} />
        )}
      </div>

      {hasScores && (
        <div className="mt-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-2" style={{ paddingLeft: PAD.left }}>
          <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Oldest</span>
          {/* Narrow panels give the legend its own row under the axis ends. */}
          <div className="order-last flex w-full flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[11px] font-medium text-on-surface-variant @md:order-0 @md:w-auto">
            <LegendItem label="Avg" value={average.toFixed(1)}>
              <line x1="0" x2="16" y1="4" y2="4" className="stroke-secondary-fixed" strokeWidth="1.5" strokeDasharray="6 4" />
            </LegendItem>
            <LegendItem label="Median" value={median.toFixed(1)}>
              <line x1="2" x2="15" y1="4" y2="4" className="stroke-on-surface/80" strokeWidth="2" strokeDasharray="0.1 4" strokeLinecap="round" />
            </LegendItem>
            <LegendItem label="±1σ" value={stdDev.toFixed(1)}>
              <rect x="1" y="0" width="14" height="8" rx="2" className="fill-secondary-fixed/20" />
            </LegendItem>
            <LegendItem label="Win" value={wins}>
              <circle cx="8" cy="4" r="3" className="fill-primary-fixed stroke-secondary" strokeWidth="1" />
            </LegendItem>
            <LegendItem label="Loss" value={losses}>
              <circle cx="8" cy="4" r="3" className="fill-primary-fixed stroke-error" strokeWidth="0.5" />
            </LegendItem>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-outline">Latest</span>
        </div>
      )}
    </div>
  );
}
