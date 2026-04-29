 import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const [nickname, setNickname] = useState('');
  const [tag, setTag] = useState('');
  const [region, setRegion] = useState('EUW');
  const navigate = useNavigate();

  const handleAnalyze = () => {
    if (!nickname || !tag) return;
    
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
      <main className="min-h-screen pt-16 flex flex-col items-center justify-center relative overflow-hidden">
        {/* Clean Gradient Background Effects */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="w-200 h-200 rounded-full bg-primary/8 blur-[120px]"></div>
        </div>

        {/* Search Section (The Core) */}
        <div className="w-full max-w-4xl px-6 relative z-10 text-center flex flex-col gap-12">
          <div className="space-y-4">
            <h1 className="font-headline text-5xl md:text-7xl font-bold headline-tracking text-on-surface">
              OPEN LEAGUE <span className="text-primary">ANALYZER</span>
            </h1>
            <p className="font-body text-on-surface-variant text-lg md:text-xl max-w-2xl mx-auto">
              Precise data analytics for the modern summoner. Track performance,
              analyze metrics, and forge your legacy.
            </p>
          </div>
          <div className="w-full glass-panel ghost-border rounded-lg p-2 md:p-4 flex flex-col md:flex-row items-stretch gap-2">
            <div className="flex-1 flex flex-col md:flex-row items-center gap-2">
              {/* Nickname Input */}
              <div className="relative flex-grow w-full">
                <input
                  className="w-full bg-surface-container-low border-none focus:ring-1 focus:ring-primary rounded-sm text-on-surface placeholder:text-outline p-4 font-headline tracking-widest text-sm"
                  placeholder="Nickname"
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                />
              </div>
              {/* Tag Input */}
              <div className="relative w-full md:w-40">
                <input
                  className="w-full bg-surface-container-low border-none focus:ring-1 focus:ring-primary rounded-sm text-on-surface placeholder:text-outline p-4 font-headline text-sm"
                  placeholder="#TAG"
                  type="text"
                  value={tag}
                  onChange={(e) => setTag(e.target.value)}
                />
              </div>
              {/* Region Select */}
              <div className="relative w-full md:w-64 md:w-80">
                <select 
                  className="custom-select-appearance w-full bg-surface-container-low border-none focus:ring-1 focus:ring-primary rounded-sm text-on-surface p-4 pr-10 font-headline text-sm cursor-pointer"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  <option value="EUW">EUW</option>
                  <option value="EUNE">EUNE</option> 
                  <option value="NA">NA</option>
                  <option value="Middle East">Middle East</option>
                  <option value="Oceania">Oceania</option>
                  <option value="Korea">Korea</option>
                  <option value="Japan">Japan</option>
                  <option value="Brazil">Brazil</option>
                  <option value="LAS">LAS</option>
                  <option value="LAN">LAN</option>
                  <option value="Russia">Russia</option>
                  <option value="Türkiye">Türkiye</option>
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
              className="bg-primary-container text-on-primary-container hover:shadow-[0_0_10px_rgba(83,238,222,0.4)] transition-all cursor-pointer duration-300 font-headline font-bold px-8 py-4 rounded-lg flex items-center justify-center gap-2 active:scale-95"
            >
              <span className="material-symbols-outlined">insert_chart</span>{" "}
              ANALYZE
            </button>
          </div>
        </div>

        {/* Recent Archives */}
        <div className="w-full max-w-4xl px-6 mt-24 relative z-10 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-outline-variant/30 pb-2">
            <h2 className="font-headline text-sm font-bold text-on-surface tracking-widest">
              Popular Players 
            </h2>
            <button className="text-primary text-xs font-bold tracking-widest hover:underline transition-all">
              VIEW ALL
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { name: "Hide on bush", rank: "Challenger • 1205 LP" },
              { name: "Agurin", rank: "Challenger • 1560 LP" },
              { name: "Thebausffs", rank: "Master • 244 LP" }
            ].map((player, i) => (
              <div key={i} className="glass-panel ghost-border rounded-lg p-4 flex items-center justify-between hover:border-primary/50 transition-colors cursor-pointer group">
                <div>
                  <p className="font-headline font-bold text-on-surface text-lg">{player.name}</p>
                  <p className="font-body text-xs text-on-surface-variant">{player.rank}</p>
                </div>
                <span className="material-symbols-outlined text-sm text-outline group-hover:text-primary transition-colors">history</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Side Navigation Shell (Hidden on Landing per UX Goal, but structurally available if needed) */}
      <aside className="hidden h-screen w-64 fixed left-0 top-0 bg-[#0b0f0f] border-r border-[#151b1a]/15 flex flex-col py-6 px-4 gap-8 z-40">
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