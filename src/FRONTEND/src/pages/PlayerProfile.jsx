import { useParams } from 'react-router-dom';

export default function PlayerProfile() {
  const { region, riotId } = useParams();
  
  // Extract nickname and tag from riotId (e.g., softmax-EUNE1)
  const lastDashIndex = riotId.lastIndexOf('-');
  const nickname = lastDashIndex !== -1 ? riotId.substring(0, lastDashIndex) : riotId;
  const tag = lastDashIndex !== -1 ? riotId.substring(lastDashIndex + 1) : '';

  // -----------------------------------------------------
  // PLACHOLDER DATA
  // -----------------------------------------------------
  const mockWinrate = "55.4%";
  const mockLevel = 185;
  const baseMatches = [
    { win: true, champ: 'Olaf', k: 11, d: 5, a: 6, duration: '31:00', type: 'Ranked Solo' },
    { win: false, champ: 'LeeSin', k: 4, d: 8, a: 12, duration: '28:14', type: 'Ranked Solo' },
    { win: true, champ: 'Olaf', k: 18, d: 2, a: 5, duration: '24:45', type: 'Ranked Solo' },
    { win: false, champ: 'Aatrox', k: 3, d: 9, a: 4, duration: '35:20', type: 'Ranked Solo' },
    { win: true, champ: 'Olaf', k: 9, d: 1, a: 14, duration: '21:10', type: 'Ranked Solo' },
  ];
  // Replicate array to have 20 matches for infinite scrolling appearance
  const mockMatches = [...baseMatches, ...baseMatches, ...baseMatches, ...baseMatches];

  const mockMasteries = [
    { name: 'Olaf', img: 'Olaf', points: '1,250,000', level: 10 },
    { name: 'Lee Sin', img: 'LeeSin', points: '850,000', level: 8 },
    { name: 'Aatrox', img: 'Aatrox', points: '420,000', level: 7 }
  ];

  const mockPings = [
    { name: 'Assist Me', value: 2.4, icon: 'front_hand' },
    { name: 'Danger', value: 1.1, icon: 'warning' },
    { name: 'Missing', value: 5.2, icon: 'question_mark' },
    { name: 'On My Way', value: 3.8, icon: 'directions_run' }
  ];

  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center">
      {/* Expanded to 1600px for full PC width, 2 columns on extra large screens */}
      <div className="w-full max-w-[1600px] px-6 grid grid-cols-1 xl:grid-cols-2 gap-8 items-start">
        
        {/* ========================================== */}
        {/* LEFT SIDE: Caller Data & Statistics          */}
        {/* ========================================== */}
        <div className="flex flex-col gap-6">
          
          {/* 1. TOP SECTION: General Info --- */}
          <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col md:flex-row items-center gap-6 shrink-0">
            <div className="w-24 h-24 rounded-full bg-surface-container-highest border-2 border-primary flex items-center justify-center overflow-hidden shadow-[0_0_15px_rgba(83,238,222,0.3)] shrink-0">
                <img src="https://ddragon.leagueoflegends.com/cdn/14.3.1/img/profileicon/6212.png" alt="Profile Icon" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col text-center md:text-left">
                <h1 className="text-4xl md:text-5xl font-headline font-bold text-on-surface">
                  {nickname} <span className="text-primary text-3xl">#{tag}</span>
                </h1>
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 mt-3 text-sm font-body text-on-surface-variant">
                  <span className="bg-surface-container-low px-3 py-1 rounded-md border border-outline-variant/30">
                    Level: <span className="text-on-surface font-bold">{mockLevel}</span>
                  </span>
                  <span className="bg-surface-container-low px-3 py-1 rounded-md border border-outline-variant/30">
                    Region: <span className="text-on-surface font-bold">{region}</span>
                  </span>
                </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full shrink-0">
            
            {/* 2. RANK, WINRATE AND W/L --- */}
            <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2 flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-4">
                 <div className="w-16 h-16 bg-surface-container-highest rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined text-4xl text-primary drop-shadow-[0_0_10px_rgba(83,238,222,0.5)]">military_tech</span>
                 </div>
                 <div className="text-center md:text-left">
                    <h2 className="font-headline font-bold text-2xl text-on-surface flex items-center gap-2">
                      Emerald II <span className="text-on-surface-variant font-normal text-lg">54 LP</span>
                    </h2>
                    <p className="text-sm text-outline">Ranked Solo</p>
                 </div>
              </div>
              <div className="text-center md:text-right">
                 <h2 className="font-headline font-bold text-3xl text-primary">{mockWinrate}</h2>
                 <p className="text-sm text-on-surface-variant font-bold mt-1">24W <span className="text-outline font-normal">-</span> 20L</p>
              </div>
            </div>

            {/* 3. RECENT MATCHES STATISTICS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2">
               <h2 className="font-headline font-bold text-xl text-on-surface mb-2">Recent Matches Statistics</h2>
               <p className="text-sm text-outline mb-4">Based on last 20 matches</p>
               <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                 <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                   <span className="text-sm text-on-surface-variant">Average CS/min</span>
                   <span className="text-2xl font-bold text-on-surface">6.8</span>
                 </div>
                 <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                   <span className="text-sm text-on-surface-variant">Vision Score/min</span>
                   <span className="text-2xl font-bold text-on-surface">1.2</span>
                 </div>
                 <div className="flex flex-col border-l-2 border-primary/50 pl-4 py-1">
                   <span className="text-sm text-on-surface-variant">Kill Participation</span>
                   <span className="text-2xl font-bold text-on-surface">52%</span>
                 </div>
               </div>
            </div>

            {/* 4. MASTERIES --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">Masteries</h2>
              <div className="flex flex-col gap-3">
                 {mockMasteries.map((champ, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low border border-outline-variant/20 hover:border-primary/50 transition-colors cursor-pointer">
                       <img src={`https://ddragon.leagueoflegends.com/cdn/14.3.1/img/champion/${champ.img}.png`} className="w-12 h-12 rounded-md" alt={champ.name} />
                       <div className="flex-1 flex flex-col">
                          <div className="flex justify-between items-center">
                            <p className="font-bold text-on-surface text-base">{champ.name}</p>
                            <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">Lvl {champ.level}</span>
                          </div>
                          <p className="text-xs text-on-surface-variant">{champ.points} PTS</p>
                       </div>
                    </div>
                 ))}
              </div>
            </div>

            {/* 5. TOP CHAMPIONS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">Top Champions</h2>
              <div className="flex flex-col gap-3">
                 {[
                   { name: 'Olaf', kda: '3.40 KDA', wr: '60% WR' },
                   { name: 'Lee Sin', img: 'LeeSin', kda: '2.80 KDA', wr: '52% WR' },
                   { name: 'Aatrox', kda: '2.10 KDA', wr: '48% WR' }
                 ].map((champ, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low border border-outline-variant/20 hover:border-primary/50 transition-colors cursor-pointer">
                       <img src={`https://ddragon.leagueoflegends.com/cdn/14.3.1/img/champion/${champ.img || champ.name}.png`} className="w-12 h-12 rounded-md" alt={champ.name} />
                       <div className="flex-1">
                          <p className="font-bold text-on-surface text-base">{champ.name}</p>
                          <p className="text-xs text-on-surface-variant">{champ.kda} • {champ.wr}</p>
                       </div>
                    </div>
                 ))}
              </div>
            </div>

            {/* 6. PINGS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6 md:col-span-2">
               <h2 className="font-headline font-bold text-xl text-on-surface mb-4">Communication <span className="text-sm font-normal text-outline">(Avg / Match)</span></h2>
               <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                 {mockPings.map((ping, i) => (
                    <div key={i} className="flex flex-col items-center justify-center p-4 bg-surface-container-low rounded-lg border border-outline-variant/30 text-center">
                       <span className="material-symbols-outlined text-outline mb-2 text-3xl opacity-80">{ping.icon}</span>
                       <span className="font-bold text-on-surface text-xl">{ping.value}</span>
                       <span className="text-xs text-on-surface-variant mt-1">{ping.name}</span>
                    </div>
                 ))}
               </div>
            </div>

          </div>
        </div>

        {/* ========================================== */}
        {/* RIGHT SIDE: Recent Matches Grid              */}
        {/* ========================================== */}
        <div className="flex flex-col gap-4 w-full">
          <div className="flex justify-between items-end mb-2 bg-surface/90 backdrop-blur-md pb-2 z-10">
             <h2 className="font-headline font-bold text-xl text-on-surface">Recent Matches</h2>
             <span className="text-xs text-outline font-bold tracking-widest bg-surface-container px-2 py-1 rounded">20 GAMES</span>
          </div>
          
          <div className="flex flex-col gap-3">
             {mockMatches.map((match, idx) => (
               <div 
                 key={idx} 
                 className={`glass-panel ghost-border rounded-xl p-5 flex flex-col md:flex-row items-center gap-4 transition-transform hover:translate-x-1 cursor-pointer 
                   ${match.win ? 'border-l-4 border-l-primary/80 bg-primary/5' : 'border-l-4 border-l-error/80 bg-error/5'}`}
               >
                  {/* Match Info */}
                  <div className="flex flex-col items-center md:items-start w-full md:w-28 shrink-0">
                     <p className={`text-sm font-bold ${match.win ? 'text-primary' : 'text-error'}`}>
                       {match.win ? 'VICTORY' : 'DEFEAT'}
                     </p>
                     <p className="text-xs text-outline mt-0.5">{match.type}</p>
                     <div className="w-12 md:w-full h-px bg-outline-variant/30 my-2"></div>
                     <p className="text-xs text-outline">{match.duration}</p>
                  </div>
                  
                  {/* Champ Icon */}
                  <div className="flex items-center gap-2 shrink-0">
                     <div className="relative">
                        <img src={`https://ddragon.leagueoflegends.com/cdn/14.3.1/img/champion/${match.champ}.png`} className="w-16 h-16 rounded-full border-2 border-surface-container shadow-sm" alt={match.champ} />
                        <div className="absolute -bottom-1 -right-1 bg-surface-container-highest rounded-full w-6 h-6 flex items-center justify-center text-[10px] border border-outline/30 font-bold">18</div>
                     </div>
                  </div>
                  
                  {/* KDA */}
                  <div className="flex flex-col items-center md:items-center py-2 md:py-0 w-full md:w-32 shrink-0">
                     <p className="font-headline font-bold text-xl tracking-wide text-on-surface">
                       {match.k} <span className="text-on-surface-variant font-normal">/</span> <span className="text-error">{match.d}</span> <span className="text-on-surface-variant font-normal">/</span> {match.a}
                     </p>
                     <p className="text-xs text-outline font-bold mt-1">
                       {((match.k + match.a) / (match.d || 1)).toFixed(2)} KDA
                     </p>
                  </div>
                  
                  {/* Items Grid */}
                  <div className="flex gap-1 flex-wrap w-full md:w-48 justify-center ml-auto">
                     {[...Array(6)].map((_, i) => (
                        <div key={i} className="w-9 h-9 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner"></div>
                     ))}
                  </div>
               </div>
             ))}
          </div>
        </div>

      </div>
    </main>
  );
}
