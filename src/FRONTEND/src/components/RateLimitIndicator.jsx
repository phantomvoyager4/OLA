import { useEffect, useState } from "react";
import { getRateLimitStatus, refreshRateLimitStatus } from "../services/api";

const AUTO_COLLAPSE_MS = 20_000;

export default function RateLimitIndicator() {
  const [status, setStatus] = useState(() => getRateLimitStatus());
  const [expanded, setExpanded] = useState(true);
  const [autoCollapseEnabled, setAutoCollapseEnabled] = useState(true);

  useEffect(() => {
    const handleRateLimitStatus = (event) => {
      setStatus(event.detail || getRateLimitStatus());
    };

    window.addEventListener("riot-rate-limit-status", handleRateLimitStatus);
    return () => window.removeEventListener("riot-rate-limit-status", handleRateLimitStatus);
  }, []);

  useEffect(() => {
    if (!autoCollapseEnabled) return undefined;

    const timer = window.setTimeout(() => {
      setExpanded(false);
      setAutoCollapseEnabled(false);
    }, AUTO_COLLAPSE_MS);

    return () => window.clearTimeout(timer);
  }, [autoCollapseEnabled]);

  useEffect(() => {
    const controller = new AbortController();
    const refresh = () => {
      refreshRateLimitStatus({ signal: controller.signal }).catch((error) => {
        if (error.name !== "AbortError") {
          console.error("Failed to refresh Riot API rate limit status:", error);
        }
      });
    };

    refresh();
    const interval = window.setInterval(refresh, 1_000);
    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, []);

  const collapse = () => {
    setExpanded(false);
    setAutoCollapseEnabled(false);
  };

  const expand = () => {
    setExpanded(true);
    setAutoCollapseEnabled(false);
  };

  const [longUsed = 0, longLimit = 90] = String(status.longWindow || "0/90")
    .split("/")
    .map(Number);
  const usagePercent = Math.min(
    100,
    Math.round((longUsed / Math.max(1, longLimit)) * 100),
  );
  const isWarning = status.warning;
  const isSafe = status.initialized && !isWarning;

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={expand}
        aria-label="Expand Riot API status"
        className={`group fixed bottom-5 right-0 z-50 flex h-12 w-10 items-center justify-center rounded-l-xl border border-r-0 bg-surface-container/95 shadow-[0_10px_30px_rgba(0,0,0,0.4)] backdrop-blur-xl transition-all hover:w-12 ${
          isWarning
            ? "border-amber-400/50 text-amber-300"
            : isSafe
              ? "border-emerald-400/40 text-emerald-300"
              : "border-primary/30 text-primary"
        }`}
      >
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-0.5">
          keyboard_arrow_left
        </span>
        {status.initialized && (
          <span
            className={`absolute right-1.5 top-1.5 h-2 w-2 rounded-full ${
              isWarning
                ? "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"
                : "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]"
            }`}
          />
        )}
      </button>
    );
  }

  return (
    <aside
      aria-live="polite"
      className={`fixed bottom-4 right-4 z-50 w-[calc(100%-2rem)] max-w-80 overflow-hidden rounded-xl border bg-surface-container/95 shadow-[0_12px_40px_rgba(0,0,0,0.45)] backdrop-blur-xl transition-colors ${
        isWarning
          ? "border-amber-400/50"
          : isSafe
            ? "border-emerald-400/40"
            : "border-primary/30"
      }`}
    >
      <button
        type="button"
        onClick={collapse}
        aria-label="Collapse Riot API status"
        className="absolute right-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-md text-on-surface-variant transition-colors hover:bg-surface-container-highest hover:text-on-surface"
      >
        <span className="material-symbols-outlined text-lg">close</span>
      </button>

      <div className="flex items-center gap-3 px-4 py-3 pr-10">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            isWarning
              ? "bg-amber-400/15 text-amber-300"
              : isSafe
                ? "bg-emerald-400/15 text-emerald-300"
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
                isWarning
                  ? "text-amber-300"
                  : isSafe
                    ? "text-emerald-300"
                    : "text-primary"
              }`}
            >
              {status.initialized ? `${longUsed}/${longLimit}` : "Checking..."}
            </span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-container-highest">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isWarning
                  ? "bg-amber-400"
                  : isSafe
                    ? "bg-emerald-400"
                    : "bg-primary"
              }`}
              style={{ width: `${status.initialized ? usagePercent : 0}%` }}
            />
          </div>
          <p className="mt-1.5 text-[11px] text-on-surface-variant">
            {!status.initialized
              ? "Waiting for the first API response"
              : isWarning
                ? `Approaching limit - budget resets in ~${status.resetSeconds}s`
                : `Free to go - ${usagePercent}% of request budget used`}
          </p>
        </div>
      </div>
    </aside>
  );
}
