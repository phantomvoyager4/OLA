import { createElement, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const popularPlayers = [
  { name: 'Hide on bush', tier: 'Challenger', lp: '1205 LP', tone: 'challenger' },
  { name: 'Agurin', tier: 'Challenger', lp: '1560 LP', tone: 'challenger' },
  { name: 'Thebausffs', tier: 'Master', lp: '244 LP', tone: 'master' },
];

function HomeReveal({ as: Component = 'div', delay = 0, className = '', children }) {
  return createElement(
    Component,
    {
      className: `home-reveal ${className}`,
      'data-home-reveal': true,
      style: { '--home-reveal-delay': `${delay}ms` },
    },
    children,
  );
}

export default function Home() {
  const [nickname, setNickname] = useState('');
  const [tag, setTag] = useState('');
  const [region, setRegion] = useState('EUW');
  const pageRef = useRef(null);
  const navigate = useNavigate();
  const isSearchReady = Boolean(nickname.trim() && tag.trim());

  useEffect(() => {
    const revealItems = pageRef.current?.querySelectorAll('[data-home-reveal]');

    if (!revealItems?.length) return undefined;

    if (!('IntersectionObserver' in window)) {
      revealItems.forEach((item) => item.classList.add('is-visible'));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -6% 0px' },
    );

    revealItems.forEach((item) => observer.observe(item));

    return () => observer.disconnect();
  }, []);

  const handleAnalyze = () => {
    if (!isSearchReady) return;

    // Clean up inputs (remove # from tag if included)
    const cleanTag = tag.replace('#', '');
    // Standardize URL by removing spaces and making uppercase
    const cleanRegion = region.replace(/\s+/g, '').toUpperCase();

    // Navigate to the player profile React route using React Router.
    // The PlayerProfile component itself will handle the backend data fetch.
    navigate(`/player/${cleanRegion}/${nickname}-${cleanTag}`);
  };

  return (
    <>
      <main ref={pageRef} className="home-page min-h-screen pt-16 flex flex-col items-center justify-center relative overflow-hidden">
        {/* Clean Gradient Background Effects */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="home-ambient-glow home-ambient-glow-primary"></div>
          <div className="home-ambient-glow home-ambient-glow-secondary"></div>
        </div>

        {/* Search Section (The Core) */}
        <div className="w-full max-w-4xl px-6 relative z-10 text-center flex flex-col gap-12">
          <div className="space-y-4 pb-6">
            <HomeReveal
              as="h1"
              delay={100}
              className="font-headline text-5xl md:text-7xl font-bold headline-tracking text-text-home"
            >
              OPEN LEAGUE <span className="text-title-text">ANALYZER</span>
            </HomeReveal>
            <HomeReveal
              as="p"
              delay={230}
              className="font-body text-text-home text-lg md:text-xl max-w-2xl mx-auto"
            >
              Precise data analytics for the modern summoner. Track performance,
              analyze metrics, and forge your legacy.
            </HomeReveal>
          </div>
          <HomeReveal
            delay={360}
            className="home-search-reveal home-search-panel w-full glass-panel ghost-border rounded-xl p-2 md:p-4 flex flex-col md:flex-row items-stretch gap-2"
          >
            <div className="flex-1 flex flex-col md:flex-row items-center gap-2">
              {/* Nickname Input */}
              <div
                className="home-search-control relative grow w-full"
                style={{ '--control-delay': '470ms' }}
              >
                <input
                  className="home-search-input w-full bg-surface-container-low border-none focus:outline-none rounded-md text-on-surface placeholder:text-outline p-4 font-headline tracking-widest text-sm"
                  placeholder="Nickname"
                  type="text"
                  value={nickname}
                  onChange={(e) => {
                    const value = e.target.value;

                    const match = value.match(/^(.+?)\s*#\s*(.+)$/);

                    if (match) {
                      setNickname(match[1].trim());
                      setTag(match[2].trim());
                    } else {
                      setNickname(value);
                    }
                  }}
                />
              </div>
              {/* Tag Input */}
              <div
                className="home-search-control relative w-full md:w-40"
                style={{ '--control-delay': '550ms' }}
              >
                <input
                  className="home-search-input w-full bg-surface-container-low border-none focus:outline-none rounded-md text-on-surface placeholder:text-outline p-4 font-headline tracking-widest text-sm"
                  placeholder="#TAG"
                  type="text"
                  value={tag}
                  onChange={(e) => setTag(e.target.value)}
                />
              </div>
              {/* Region Select */}
              <div
                className="home-search-control relative w-full md:w-80"
                style={{ '--control-delay': '630ms' }}
              >
                <select
                  className="home-search-input custom-select-appearance w-full bg-surface-container-low border-none focus:outline-none rounded-md text-on-surface p-4 pr-10 font-headline text-sm cursor-pointer" value={region}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  <option value="EUW">EUW</option>
                  <option value="EUNE">EUNE</option>
                  <option value="NA">NA</option>
                  <option value="Middle East">Middle East</option>
                  <option value="OC1">Oceania</option>
                  <option value="KR">Korea</option>
                  <option value="JP">Japan</option>
                  <option value="BR">Brazil</option>
                  <option value="LAS">LAS</option>
                  <option value="LAN">LAN</option>
                  <option value="RU">Russia</option>
                  <option value="TR">Türkiye</option>
                  <option value="Southeast Asia">Southeast Asia</option>
                  <option value="Taiwan">Taiwan</option>
                  <option value="Vietnam">Vietnam</option>
                </select>
                <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                  expand_more
                </span>
              </div>
            </div>
            {/* Search Button */}
            <button
              onClick={handleAnalyze}
              disabled={!isSearchReady}
              className={`home-search-control home-analyze-button ${isSearchReady ? 'is-ready' : ''} font-headline font-bold px-8 py-4 rounded-lg flex items-center justify-center gap-2`}
              style={{ '--control-delay': '710ms' }}
            >
              <span className="material-symbols-outlined">insert_chart</span>{" "}
              ANALYZE
            </button>
          </HomeReveal>
        </div>

        {/* Recent Archives */}
        <div className="w-full max-w-4xl px-6 mt-24 relative z-10 flex flex-col gap-4">
          <HomeReveal
            delay={80}
            className="flex items-center justify-between border-b border-outline-variant/30 pb-2"
          >
            <h2 className="font-headline text-sm font-bold text-on-surface tracking-widest">
              Popular Players
            </h2>
            <button className="text-on-surface text-xs font-bold tracking-widest hover:underline transition-all cursor-pointer">
              VIEW ALL
            </button>
          </HomeReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {popularPlayers.map((player, i) => (
              <HomeReveal
                key={player.name}
                delay={170 + i * 100}
                className=""
              >
                <div className={`home-player-card home-player-card-${player.tone} glass-panel ghost-border rounded-xl p-4 flex items-center justify-between cursor-pointer group`}>
                  <div>
                    <span className="home-rank-badge">
                      <span className="home-rank-dot" />
                      {player.tier}
                    </span>
                    <p className="mt-3 font-headline font-bold text-on-surface text-lg">{player.name}</p>
                    <p className="mt-0.5 font-body text-xs text-on-surface-variant">{player.lp}</p>
                  </div>
                  <span className="home-player-arrow material-symbols-outlined">
                    arrow_forward
                  </span>
                </div>
              </HomeReveal>
            ))}
          </div>
        </div>
      </main>

      {/* Side Navigation Shell (Hidden on Landing per UX Goal, but structurally available if needed) */}
      <aside className="hidden h-screen w-64 fixed left-0 top-0 bg-[#0b0f0f] border-r border-[#151b1a]/15 flex-col py-6 px-4 gap-8 z-40">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-sm bg-surface-container flex items-center justify-center">
            <span className="material-symbols-outlined text-primary">shield</span>
          </div>
          <div>
            <p className="text-on-surface font-headline font-bold text-sm">
              Summoner
            </p>
            <p className="text-on-surface-variant font-body text-xs">
              Challenger Rank
            </p>
          </div>
        </div>
        <nav className="flex flex-col gap-2">
          <div className="flex items-center gap-3 p-3 text-[#a8acab] hover:bg-[#151b1a] hover:text-[#53eede] rounded-sm transition-all duration-200 cursor-pointer">
            <span className="material-symbols-outlined">dashboard</span>
            <span className="font-headline font-medium">Dashboard</span>
          </div>
          <div className="flex items-center gap-3 p-3 text-[#a8acab] hover:bg-[#151b1a] hover:text-[#53eede] rounded-sm transition-all duration-200 cursor-pointer">
            <span className="material-symbols-outlined">leaderboard</span>
            <span className="font-headline font-medium">Leaderboards</span>
          </div>
          <div className="flex items-center gap-3 p-3 text-[#a8acab] hover:bg-[#151b1a] hover:text-[#53eede] rounded-sm transition-all duration-200 cursor-pointer">
            <span className="material-symbols-outlined">shield</span>
            <span className="font-headline font-medium">Champions</span>
          </div>
        </nav>
        <div className="mt-auto p-4 bg-primary/5 rounded-lg border border-primary/10">
          <p className="text-primary font-headline text-xs font-bold mb-2">
            PRO ANALYTICS
          </p>
          <p className="text-on-surface-variant text-[10px] leading-relaxed mb-4">
            Unlock deep-core matchup data and heatmaps.
          </p>
          <button className="w-full py-2 bg-primary text-on-primary text-[10px] font-bold rounded-sm uppercase tracking-widest">
            Upgrade Now
          </button>
        </div>
      </aside>
    </>
  );
}
