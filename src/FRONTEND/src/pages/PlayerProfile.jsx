import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getPlayerData } from '../services/api';

import noIcon from "../../../../data/static/icons/noicon.jpg";

import assistMeIcon from "../../../../data/static/pings/assistMePings.png";
import allInIcon from "../../../../data/static/pings/allInPings.png";
import enemyMissingIcon from "../../../../data/static/pings/enemyMissingPings.png";
import enemyVisionIcon from "../../../../data/static/pings/enemyVisionPings.png";
import needVisionIcon from "../../../../data/static/pings/needVisionPings.png";
import onMyWayIcon from "../../../../data/static/pings/onMyWayPings.png";
import pushIcon from "../../../../data/static/pings/pushPings.png";
import retreatIcon from "../../../../data/static/pings/retreatPings.png";

import unrankedIcon from "../../../../data/static/tiers/unranked.png";
import ironIcon from "../../../../data/static/tiers/iron.png";
import bronzeIcon from "../../../../data/static/tiers/bronze.png";
import silverIcon from "../../../../data/static/tiers/silver.png";
import goldIcon from "../../../../data/static/tiers/gold.png";
import platinumIcon from "../../../../data/static/tiers/platinum.png";
import emeraldIcon from "../../../../data/static/tiers/emerald.png";
import diamondIcon from "../../../../data/static/tiers/diamond.png";
import masterIcon from "../../../../data/static/tiers/master.png";
import grandmasterIcon from "../../../../data/static/tiers/grandmaster.png";
import challengerIcon from "../../../../data/static/tiers/challenger.png";



export default function PlayerProfile() {
  const { region, riotId } = useParams();
  
  // Extract nickname and tag from riotId (e.g., softmax-EUNE1)
  const lastDashIndex = riotId.lastIndexOf('-');
  const nickname = lastDashIndex !== -1 ? riotId.substring(0, lastDashIndex) : riotId;
  const tag = lastDashIndex !== -1 ? riotId.substring(lastDashIndex + 1) : '';

  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getPlayerData(region, nickname, tag, { save: false, count: 20 });
        console.log("Fetched Player Data:", data);
        setPlayerData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (region && nickname && tag) {
      fetchData();
    }
  }, [region, nickname, tag]);

  // -----------------------------------------------------
  // PLACHOLDER DATA
  // -----------------------------------------------------
  const baseMatches = [
    { win: true, champ: 'Olaf', k: 11, d: 5, a: 6, duration: '31:00', type: 'Ranked Solo' },
    { win: false, champ: 'LeeSin', k: 4, d: 8, a: 12, duration: '28:14', type: 'Ranked Solo' },
    { win: true, champ: 'Olaf', k: 18, d: 2, a: 5, duration: '24:45', type: 'Ranked Solo' },
    { win: false, champ: 'Aatrox', k: 3, d: 9, a: 4, duration: '35:20', type: 'Ranked Solo' },
    { win: true, champ: 'Olaf', k: 9, d: 1, a: 14, duration: '21:10', type: 'Ranked Solo' },
  ];
  // Replicate array to have 20 matches for infinite scrolling appearance
  const mockMatches = [...baseMatches, ...baseMatches, ...baseMatches, ...baseMatches];
  const mockPings = [
        { name: 'Assist Me', value: 2.4, icon: assistMeIcon },
        { name: 'Danger', value: 1.1, icon: retreatIcon }, // Note: Using retreat icon for danger
        { name: 'Enemy Missing', value: 5.2, icon: enemyMissingIcon },
        { name: 'On My Way', value: 3.8, icon: onMyWayIcon },
        { name: 'Push', value: 3.8, icon: pushIcon },
        { name: 'All In', value: 3.8, icon: allInIcon },
        { name: 'Enemy Vision', value: 3.8, icon: enemyVisionIcon },
        { name: 'Need Vision', value: 3.8, icon: needVisionIcon }
      ];

  const ranks = [
    { name: 'Unranked', icon: unrankedIcon },
    { name: 'Iron', icon: ironIcon },
    { name: 'Bronze', icon: bronzeIcon },
    { name: 'Silver', icon: silverIcon },
    { name: 'Gold', icon: goldIcon },
    { name: 'Platinum', icon: platinumIcon },
    { name: 'Emerald', icon: emeraldIcon },
    { name: 'Diamond', icon: diamondIcon },
    { name: 'Master', icon: masterIcon },
    { name: 'Grandmaster', icon: grandmasterIcon },
    { name: 'Challenger', icon: challengerIcon }
  ];

  // Extract Caller's Rank details
  let displayTierImg = unrankedIcon;
  let displayRankText = "Unranked";
  let displayLp = "";
  let wins = 0;
  let losses = 0
  let winrate = "0.0%";
  let iconLink = noIcon;
  let level = 0;
  let masteries = []

  if (playerData && Array.isArray(playerData) && playerData.length > 0) {
    const firstMatch = playerData[0];
    if (firstMatch && firstMatch.players) {
      const callerPlayer = firstMatch.players.find(p => p.caller === true || p.caller === "true");
      
      if (callerPlayer && callerPlayer.metadata && callerPlayer.metadata.tier) {
        const tierStr = callerPlayer.metadata.tier; // e.g., "GOLD"
        const rankDiv = callerPlayer.metadata.rank; // e.g., "III"
        const lp = callerPlayer.metadata.leaguePoints; // e.g., 69
        wins = callerPlayer.metadata.wins
        losses = callerPlayer.metadata.losses
        winrate = callerPlayer.metadata.winrate
        iconLink = callerPlayer.icon.image_path
        level = callerPlayer.summonerLevel
        masteries = [
        { name: callerPlayer.masteries[0].championName , img: callerPlayer.masteries[0].championIcon, points: callerPlayer.masteries[0].championPoints, level: callerPlayer.masteries[0].championLevel},
        { name: callerPlayer.masteries[1].championName , img: callerPlayer.masteries[1].championIcon, points: callerPlayer.masteries[1].championPoints, level: callerPlayer.masteries[1].championLevel},
        { name: callerPlayer.masteries[2].championName , img: callerPlayer.masteries[2].championIcon, points: callerPlayer.masteries[2].championPoints, level: callerPlayer.masteries[2].championLevel},
      ];


        // Format label "Gold 3" or "Gold III"
        displayRankText = `${tierStr.charAt(0) + tierStr.slice(1).toLowerCase()} ${rankDiv}`;
        if (lp !== undefined) {
          displayLp = `${lp} LP`;
        }
        
        // Find matching icon
        const matchedRank = ranks.find(r => r.name.toLowerCase() === tierStr.toLowerCase());
        if (matchedRank) {
          displayTierImg = matchedRank.icon;
        }
      }
    }
  }

  // Generate stable mock heatmap data (13 weeks * 7 days for approx 90 days)
  const mockHeatmap = Array.from({ length: 13 }, () => 
    Array.from({ length: 7 }, () => {
      const rand = Math.random();
      if (rand < 0.4) return 0; // 40% chance of 0 games
      if (rand < 0.7) return Math.floor(Math.random() * 3) + 1; // 1-3 games
      if (rand < 0.9) return Math.floor(Math.random() * 4) + 4; // 4-7 games
      return Math.floor(Math.random() * 4) + 8; // 8-11 games
    })
  );

  if (loading) {
    return (
      <main className="min-h-screen pt-24 pb-12 flex flex-col items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <h2 className="mt-4 text-xl font-headline text-on-surface">Analyzing matches...</h2>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen pt-24 pb-12 flex flex-col items-center justify-center">
        <h2 className="text-2xl font-headline text-error">Summoner not found!</h2>
        <p className="mt-2 text-on-surface-variant font-bold uppercase">{error}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center">
      {/* Expanded to 1600px for full PC width, 2 columns on extra large screens */}
      <div className="w-full max-w-400 px-6 grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        
        {/* ========================================== */}
        {/* LEFT SIDE: Caller Data & Statistics          */}
        {/* ========================================== */}
        <div className="flex flex-col gap-6">
          
          {/* 1. TOP SECTION: General Info --- */}
          <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col md:flex-row items-center gap-6 shrink-0">
            <div className="w-24 h-24 rounded-full bg-surface-container-highest flex items-center justify-center overflow-hidden shadow-[0_0_4px_rgba(,0,0,1)] shrink-0">
                <img src={iconLink} alt="Profile Icon" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col text-center md:text-left">
                <h1 className="text-4xl md:text-5xl font-headline font-bold text-on-surface">
                  {nickname} <span className="text-primary text-3xl">#{tag}</span>
                </h1>
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 mt-3 text-sm font-body text-on-surface-variant">
                  <span className="bg-surface-container-low px-3 py-1 rounded-md border border-outline-variant/30">
                    Level: <span className="text-on-surface font-bold">{level}</span>
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
                 <div className="w-18 h-18 bg-surface-container-highest rounded-full flex items-center justify-center overflow-hidden">
                    <img src={displayTierImg} alt={displayRankText} className="w-full h-full object-cover p-2" />
                 </div>
                 <div className="text-center md:text-left">
                    <h2 className="font-headline font-bold text-2xl text-on-surface flex items-center gap-2">
                      {displayRankText} <span className="text-on-surface-variant font-normal text-lg">{displayLp}</span>
                    </h2>
                    <p className="text-sm text-outline">Ranked Solo/Duo</p>
                 </div>
              </div>
              <div className="text-center md:text-right">
                 <h2 className="font-headline font-bold text-3xl text-primary">{winrate}</h2>
                 <p className="text-sm text-on-surface-variant font-bold mt-1">{wins}W <span className="text-outline font-normal">-</span> {losses}L</p>
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
            {/* NEW: ACTIVITY HEATMAP & 90 DAY SUMMARY --- */}
            <div className="glass-panel px-12 ghost-border rounded-xl p-6 md:col-span-2 grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Left Side: Activity Heatmap */}
              <div className="flex flex-col w-max mx-auto lg:mx-0">
                <div className="flex justify-between items-end mb-1">
                  <h2 className="font-headline font-bold text-xl text-on-surface">Activity</h2>
                  <span className="text-[11px] text-outline font-bold uppercase tracking-wide pb-1">
                    Past 91 Days
                  </span>
                </div>
                
                <div className="flex flex-col">
                  {/* Heatmap wrapper (w-max ensures container naturally fits its children width) */}
                  <div className="flex gap-2 pt-5 pb-2">
                    <div className="flex flex-col gap-1 text-[10px] text-outline justify-around font-bold uppercase tracking-wider pr-1">
                      <span>Mon</span>
                      <span>Wed</span>
                      <span>Fri</span>
                    </div>
                    <div className="flex gap-0.5">
                      {mockHeatmap.map((week, colIndex) => (
                        <div key={colIndex} className="flex flex-col gap-0.5">
                          {week.map((count, rowIndex) => {
                            let bgClass = "bg-surface-container-highest/40 border-outline-variant/10 border"; // 0 games
                            if (count > 0 && count <= 2) bgClass = "bg-primary/20 border-primary/20 border";
                            else if (count > 2 && count <= 5) bgClass = "bg-primary/50 border-primary/30 border shadow-[0_0_5px_rgba(83,238,222,0.2)]";
                            else if (count > 5 && count <= 8) bgClass = "bg-primary/80 border-primary/50 border shadow-[0_0_8px_rgba(83,238,222,0.3)]";
                            else if (count > 8) bgClass = "bg-primary border-primary border shadow-[0_0_10px_rgba(83,238,222,0.5)]";
                            
                            return (
                              <div 
                                key={rowIndex} 
                                className={`group relative w-3 h-3 md:w-4 md:h-4 rounded-sm transition-all duration-200 hover:ring-1 hover:ring-primary hover:scale-110 hover:z-20 ${bgClass}`} 
                              >
                                {/* Custom Hover Tooltip */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-max whitespace-nowrap bg-surface-container border border-outline-variant/30 text-on-surface text-[10px] uppercase font-bold py-1 px-2 rounded shadow-[0_4px_15px_rgba(0,0,0,0.5)] z-[999] pointer-events-none">
                                  {count} games played
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
                    <div className="w-3 h-3 rounded-sm bg-primary shadow-[0_0_5px_rgba(83,238,222,0.4)]"></div>
                    <span>More</span>
                  </div>
                </div>
              </div>

              {/* Right Side: Total Summary */}
              <div className="flex flex-col justify-center">
                <div className="flex justify-between items-end mb-4">
                  <h2 className="font-headline font-bold text-xl text-on-surface">90-Day Summary</h2>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/30 flex flex-col justify-center items-center">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide">Total Games</span>
                    <span className="font-headline font-bold text-2xl text-on-surface mt-1">42</span>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/30 flex flex-col justify-center items-center">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide">Win Rate</span>
                    <span className="font-headline font-bold text-2xl text-primary mt-1">62%</span>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/30 flex flex-col justify-center items-center">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide">Avg KDA</span>
                    <span className="font-headline font-bold text-2xl text-on-surface mt-1">2.8</span>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/30 flex flex-col justify-center items-center">
                    <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wide">CS / Min</span>
                    <span className="font-headline font-bold text-2xl text-on-surface mt-1">6.9</span>
                  </div>
                </div>
              </div>

            </div>
            



            {/* 4. MASTERIES --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">Masteries</h2>
              <div className="flex flex-col gap-3">
                 {masteries.map((champ, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low border border-outline-variant/20 hover:border-primary/50 transition-colors cursor-pointer">
                       <img src={champ.img} className="w-12 h-12 rounded-md" alt={champ.name} />
                       <div className="flex-1 flex flex-col justify-between">
                          <div className="flex justify-between items-center">
                            <p className="font-bold text-on-surface text-base">{champ.name}</p>
                            <span className="text-xs font-bold text-primary bg-primary/8 py-0.5 rounded w-12 flex justify-center shrink-0">Lvl {champ.level}</span>
                          </div>
                          <p className="text-xs text-on-surface-variant">{champ.points} PTS</p>
                       </div>
                    </div>
                 ))}
              </div>
            </div>

            {/* 5. TOP CHAMPIONS --- */}
            <div className="glass-panel ghost-border rounded-xl p-6">
              <h2 className="font-headline font-bold text-xl text-on-surface mb-4">Top Champions <span className="text-sm font-normal text-outline">(this season)</span></h2>
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
                       <img src={ping.icon} alt={`${ping.name} ping icon`} className="w-10 h-10 mb-2 opacity-90 drop-shadow-md" />
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
                  <div className="grid grid-cols-3 gap-1 w-max mx-auto md:ml-auto md:mx-0">
                     {[...Array(6)].map((_, i) => (
                        <div key={i} className="w-8 h-8 sm:w-10 sm:h-10 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner"></div>
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
