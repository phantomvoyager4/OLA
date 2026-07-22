import { useEffect, useMemo, useState } from "react";
import { getTierList } from "../services/tierListApi";

const ROLES = [
  { value: "ALL", label: "All roles", icon: "grid_view" },
  { value: "TOP", label: "Top", icon: "shield" },
  { value: "JUNGLE", label: "Jungle", icon: "forest" },
  { value: "MIDDLE", label: "Mid", icon: "route" },
  { value: "BOTTOM", label: "Bot", icon: "my_location" },
  { value: "UTILITY", label: "Support", icon: "volunteer_activism" },
];

const TIER_ORDER = ["S", "A", "B", "C", "D"];
const TIER_STYLES = {
  S: {
    label: "Meta defining",
    badge: "border-primary/50 bg-primary/15 text-primary-fixed",
    glow: "from-primary/18",
  },
  A: {
    label: "Powerful picks",
    badge: "border-secondary/50 bg-secondary/10 text-secondary-fixed",
    glow: "from-secondary/12",
  },
  B: {
    label: "Strong and reliable",
    badge: "border-[#5f8edb]/40 bg-[#5f8edb]/10 text-[#92b7f0]",
    glow: "from-[#5f8edb]/10",
  },
  C: {
    label: "Situational picks",
    badge: "border-[#d49a55]/40 bg-[#d49a55]/10 text-[#e7b87b]",
    glow: "from-[#d49a55]/10",
  },
  D: {
    label: "Challenging in this meta",
    badge: "border-error/35 bg-error/10 text-on-error-container",
    glow: "from-error/8",
  },
};

const numberFormatter = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

const formatNumber = (value) => numberFormatter.format(Number(value) || 0);

const formatPercent = (value) => {
  if (value === null || value === undefined) return "--";
  return `${Number(value).toFixed(1)}%`;
};

const formatPatch = (patch) => {
  const value = String(patch || "Latest");
  if (value.toLowerCase() === "latest") return value;
  return value.toLowerCase().startsWith("v") ? value : `v${value}`;
};

const formatLastUpdated = (value) => {
  if (!value) return "Awaiting first snapshot";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

function ChampionPortrait({ champion }) {
  const [imageFailed, setImageFailed] = useState(false);
  const initials = champion.championName
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-md border border-outline-variant/40 bg-surface-container-highest">
      <div className="absolute inset-0 flex items-center justify-center font-headline text-sm font-bold text-on-surface-variant">
        {initials}
      </div>
      {champion.championImage && !imageFailed && (
        <img
          alt={`${champion.championName} portrait`}
          className="relative h-full w-full object-cover"
          loading="lazy"
          onError={() => setImageFailed(true)}
          src={champion.championImage}
        />
      )}
    </div>
  );
}

function Metric({ label, value, accent = false }) {
  return (
    <div className="min-w-19">
      <p className="mb-1 text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant md:hidden">
        {label}
      </p>
      <p className={`font-headline text-sm font-semibold ${accent ? "text-secondary-fixed" : "text-on-surface"}`}>
        {value}
      </p>
    </div>
  );
}

function ChampionRow({ champion, showRole }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-5 border-t border-outline-variant/10 px-5 py-5 transition-colors first:border-t-0 hover:bg-white/[0.025] md:grid-cols-[minmax(230px,1.7fr)_0.7fr_0.75fr_0.75fr_0.75fr_0.65fr] md:items-center md:px-7">
      <div className="col-span-2 flex min-w-0 items-center gap-4 md:col-span-1">
        <ChampionPortrait champion={champion} />
        <div className="min-w-0">
          <p className="truncate font-headline text-base font-bold uppercase tracking-tight text-on-surface">
            {champion.championName}
          </p>
          {showRole && (
            <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-on-surface-variant">
              {ROLES.find((role) => role.value === champion.role)?.label || champion.role}
            </p>
          )}
        </div>
      </div>
      <Metric label="Games" value={formatNumber(champion.games)} />
      <Metric label="Win rate" value={formatPercent(champion.winRate)} accent={champion.winRate >= 52} />
      <Metric label="Pick rate" value={formatPercent(champion.pickRate)} />
      <Metric label="Ban rate" value={formatPercent(champion.banRate)} />
      <Metric label="Score" value={champion.score === null ? "--" : champion.score.toFixed(1)} />
    </div>
  );
}

function TierSection({ tier, champions, showRole }) {
  const style = TIER_STYLES[tier];

  return (
    <section className="relative overflow-hidden rounded-xl border border-outline-variant/15 bg-surface-container">
      <div className={`pointer-events-none absolute inset-0 bg-gradient-to-r ${style.glow} via-transparent to-transparent`} />
      <div className="relative grid md:grid-cols-[150px_1fr]">
        <header className="border-b border-outline-variant/15 px-5 py-5 md:block md:border-b-0 md:border-r md:px-7">
          <div className="flex items-center gap-4 md:sticky md:top-24 md:flex-col md:items-start">
            <div className={`flex h-14 w-14 items-center justify-center rounded-lg border font-headline text-3xl font-black ${style.badge}`}>
              {tier}
            </div>
            <div>
              <p className="font-headline text-sm font-bold uppercase tracking-wider text-on-surface">Tier {tier}</p>
              <p className="mt-1 text-xs text-on-surface-variant">{style.label}</p>
            </div>
          </div>
        </header>

        <div className="relative min-w-0">
          <div className="hidden grid-cols-[minmax(230px,1.7fr)_0.7fr_0.75fr_0.75fr_0.75fr_0.65fr] px-7 py-3 text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant md:grid">
            <span>Champion</span>
            <span>Games</span>
            <span>Win rate</span>
            <span>Pick rate</span>
            <span>Ban rate</span>
            <span>Score</span>
          </div>
          {champions.map((champion) => (
            <ChampionRow champion={champion} key={champion.id} showRole={showRole} />
          ))}
        </div>
      </div>
    </section>
  );
}

function TierListSkeleton() {
  return (
    <div aria-label="Loading tier list" className="space-y-4" role="status">
      {["S", "A", "B"].map((tier, tierIndex) => (
        <div className="overflow-hidden rounded-xl border border-outline-variant/15 bg-surface-container" key={tier}>
          <div className="grid md:grid-cols-[150px_1fr]">
            <div className="border-b border-outline-variant/10 p-6 md:border-b-0 md:border-r">
              <div className="h-14 w-14 animate-pulse rounded-lg bg-surface-container-highest" />
            </div>
            <div className="divide-y divide-outline-variant/10 px-6">
              {Array.from({ length: tierIndex === 0 ? 3 : 2 }).map((_, rowIndex) => (
                <div className="flex items-center gap-4 py-5" key={rowIndex}>
                  <div className="h-12 w-12 animate-pulse rounded-md bg-surface-container-highest" />
                  <div className="h-4 w-36 animate-pulse rounded bg-surface-container-highest" />
                  <div className="ml-auto hidden h-4 w-2/5 animate-pulse rounded bg-surface-container-highest md:block" />
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ filtered = false }) {
  return (
    <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container/60 px-6 py-16 text-center">
      <span className="material-symbols-outlined mb-4 text-4xl text-primary">{filtered ? "search_off" : "hourglass_empty"}</span>
      <h2 className="font-headline text-xl font-bold text-on-surface">
        {filtered ? "No champions match these filters" : "The first tier-list snapshot is not ready yet"}
      </h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed text-on-surface-variant">
        {filtered
          ? "Try another role or clear the champion search."
          : "Run the EUW Master+ collector, then refresh this page to display the generated ranking."}
      </p>
    </div>
  );
}

export default function TierList() {
  const [tierList, setTierList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedRole, setSelectedRole] = useState("ALL");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    const loadTierList = async () => {
      setLoading(true);
      setError("");

      try {
        setTierList(await getTierList({ signal: controller.signal }));
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message || "Unable to load the tier list.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };

    loadTierList();
    return () => controller.abort();
  }, [reloadKey]);

  const filteredChampions = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return (tierList?.champions || []).filter((champion) => {
      const matchesRole = selectedRole === "ALL" || champion.role === selectedRole;
      const matchesSearch = !query || champion.championName.toLocaleLowerCase().includes(query);
      return matchesRole && matchesSearch;
    });
  }, [search, selectedRole, tierList]);

  const groupedChampions = useMemo(
    () => Object.fromEntries(TIER_ORDER.map((tier) => [
      tier,
      filteredChampions
        .filter((champion) => champion.tier === tier)
        .sort((left, right) => (right.score ?? -1) - (left.score ?? -1)),
    ])),
    [filteredChampions],
  );

  const hasData = (tierList?.champions.length || 0) > 0;
  const region = tierList?.region || "EUW";
  const rank = (tierList?.rank || "MASTER+").replaceAll("_", " ");

  return (
    <main className="relative min-h-screen overflow-hidden px-5 pb-20 pt-28 md:px-8">
      <div className="pointer-events-none absolute left-1/2 top-0 h-120 w-240 -translate-x-1/2 rounded-full bg-primary/8 blur-[140px]" />
      <div className="relative mx-auto max-w-7xl">
        <header className="mb-10 border-b border-outline-variant/20 pb-9">
          <div className="mb-5 flex flex-wrap items-center gap-3 text-[10px] font-bold uppercase tracking-[0.2em]">
            <span className="rounded-full border border-secondary/30 bg-secondary/10 px-3 py-1.5 text-secondary-fixed">
              Data-driven meta
            </span>
            <span className="text-on-surface-variant">Ranked Solo</span>
            <span className="h-1 w-1 rounded-full bg-outline" />
            <span className="text-on-surface-variant">Latest patch</span>
          </div>
          <div className="flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
            <div>
              <h1 className="max-w-4xl font-headline text-4xl font-bold tracking-[-0.04em] text-on-surface sm:text-5xl lg:text-6xl">
                {region.toUpperCase()} {rank} <span className="text-primary-fixed">Champion Tier List</span>
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-on-surface-variant md:text-base">
                Ranked from real high-elo matches, with sample-aware scoring across every role. Use win, pick and ban rates together—not a single noisy metric.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:flex">
              <div className="rounded-lg border border-outline-variant/20 bg-surface-container px-4 py-3">
                <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Patch</p>
                <p className="mt-1 font-headline text-sm font-bold text-primary-fixed">{formatPatch(tierList?.patch)}</p>
              </div>
              <div className="rounded-lg border border-outline-variant/20 bg-surface-container px-4 py-3">
                <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Matches</p>
                <p className="mt-1 font-headline text-sm font-bold text-on-surface">
                  {tierList?.sampleMatches === null || tierList?.sampleMatches === undefined
                    ? "--"
                    : formatNumber(tierList.sampleMatches)}
                </p>
              </div>
            </div>
          </div>
        </header>

        <section className="mb-7 rounded-xl border border-outline-variant/15 bg-surface-container-low p-3">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2" aria-label="Filter by role">
              {ROLES.map((role) => {
                const active = selectedRole === role.value;
                return (
                  <button
                    aria-pressed={active}
                    className={`flex cursor-pointer items-center gap-2 rounded-md border px-3.5 py-2.5 font-headline text-xs font-bold transition-all ${
                      active
                        ? "border-primary/40 bg-primary/15 text-primary-fixed shadow-[0_0_18px_rgba(158,36,230,0.12)]"
                        : "border-transparent bg-surface-container text-on-surface-variant hover:border-outline-variant/40 hover:text-on-surface"
                    }`}
                    key={role.value}
                    onClick={() => setSelectedRole(role.value)}
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[17px]">{role.icon}</span>
                    {role.label}
                  </button>
                );
              })}
            </div>

            <label className="relative block w-full xl:w-72">
              <span className="sr-only">Search champion</span>
              <span className="material-symbols-outlined pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[19px] text-on-surface-variant">search</span>
              <input
                className="w-full rounded-md border border-outline-variant/25 bg-surface-container py-2.5 pl-11 pr-4 text-sm text-on-surface outline-none transition-colors placeholder:text-outline focus:border-primary/60"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search champion"
                type="search"
                value={search}
              />
            </label>
          </div>
        </section>

        {loading && <TierListSkeleton />}

        {!loading && error && (
          <div className="rounded-xl border border-error/30 bg-error/5 px-6 py-14 text-center">
            <span className="material-symbols-outlined mb-4 text-4xl text-error">cloud_off</span>
            <h2 className="font-headline text-xl font-bold text-on-surface">Tier list could not be loaded</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm text-on-surface-variant">{error}</p>
            <button
              className="mt-6 cursor-pointer rounded-md bg-primary px-5 py-2.5 font-headline text-xs font-bold uppercase tracking-wider text-on-primary transition-all hover:bg-primary-fixed-dim"
              onClick={() => setReloadKey((value) => value + 1)}
              type="button"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && !hasData && <EmptyState />}
        {!loading && !error && hasData && filteredChampions.length === 0 && <EmptyState filtered />}

        {!loading && !error && filteredChampions.length > 0 && (
          <div className="space-y-4">
            {TIER_ORDER.map((tier) => (
              groupedChampions[tier].length > 0 && (
                <TierSection
                  champions={groupedChampions[tier]}
                  key={tier}
                  showRole={selectedRole === "ALL"}
                  tier={tier}
                />
              )
            ))}
          </div>
        )}

        {!loading && !error && hasData && (
          <footer className="mt-7 border-t border-outline-variant/20 pt-5 text-on-surface-variant">
            <div className="flex flex-col gap-2 text-[10px] uppercase tracking-[0.16em] sm:flex-row sm:items-center sm:justify-between">
              <p>
                Showing <span className="font-bold text-on-surface">{filteredChampions.length}</span> champion-role entries
              </p>
              <p>
                Last updated <span className="font-semibold normal-case tracking-normal text-on-surface">{formatLastUpdated(tierList.lastUpdated)}</span>
              </p>
            </div>
            <p className="mt-5 max-w-5xl border-t border-outline-variant/10 pt-4 text-[9px] leading-relaxed text-outline">
              Open League Analyzer is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
            </p>
          </footer>
        )}
      </div>
    </main>
  );
}
