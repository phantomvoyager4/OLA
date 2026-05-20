 import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getCachedMatch } from '../services/api';

export default function Match() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('extended'); // 'extended' | 'compact'
  const [matchData, setMatchData] = useState(null);

  useEffect(() => {
    // Attempt to load from cache
    const cachedData = getCachedMatch(matchId);
    if (cachedData) {
      setMatchData(cachedData);
    }
  }, [matchId]);

  if (!matchData) {
    return (
      <main className="min-h-screen pt-24 pb-12 flex flex-col items-center justify-center">
        <h2 className="text-2xl font-headline text-error mb-4">Match data not found.</h2>
        <p className="text-on-surface-variant mb-6 text-center max-w-md">
          Please navigate back to the profile and ensure the matches are loaded.
        </p>
        <button 
          onClick={() => navigate(-1)}
          className="px-6 py-2 bg-primary text-on-primary font-bold rounded hover:opacity-90 transition-all"
        >
          Go Back
        </button>
      </main>
    );
  }

  const caller = matchData.players.find(p => String(p.caller) === "true" || p.caller === true) || matchData.players[0];
  
  const matchInfo = {
    result: caller?.win ? 'Victory' : 'Defeat',
    duration: matchData.metadata?.gameDuration_min ? String(matchData.metadata.gameDuration_min.toFixed(2)).replace('.', ':') : '00:00',
    date: matchData.metadata?.gameDate || 'Unknown Date',
    gameMode: matchData.metadata?.gameType === 'MATCHED_GAME' ? 'Ranked Solo' : 'Ranked Solo',
  };

  const formatPlayer = (p) => {
    const cs = Number(p.totalMinionsKilled || 0) + Number(p.neutralMinionsKilled || 0);
    const durationMin = matchData.metadata?.gameDuration_min || 1;
    const items = (p.items || []).map(i => i?.image_path || null);
    // Pad items to 7 slots (6 standard + 1 trinket)
    while (items.length < 7) items.push(null);
    return {
      champIcon: p.championImageLink,
      name: p.username,
      kda: `${p.kills}/${p.deaths}/${p.assists}`,
      cs: cs,
      csMin: p.cs_min?.toFixed(1) || 0,
      gold: p.goldEarned ? (p.goldEarned / 1000).toFixed(1) + 'k' : '0k',
      dmg: p.damagePerMinute ? ((p.damagePerMinute * durationMin) / 1000).toFixed(1) + 'k' : '-',
      kp: p.killParticipation ? p.killParticipation + '%' : '-',
      items: items,
      summs: (p.summoners || []).slice(0, 2).map(s => s?.image_path || null),
      runes: [
        p.runes?.[5]?.runeIconLink || null, // Main Keystone Rune
        p.runes?.[4]?.styleIconLink || null // Secondary Style Tree
      ],
      win: p.win,
    };
  };

  const blueTeamRaw = matchData.players.filter(p => String(p.teamId) === '100');
  const redTeamRaw = matchData.players.filter(p => String(p.teamId) === '200');

  const blueTeam = blueTeamRaw.map(formatPlayer);
  const redTeam = redTeamRaw.map(formatPlayer);

  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center">
      {/* Container expanded to 1600px max-width to allow plenty of space */}
      <div className="w-full max-w-[1600px] px-6 lg:px-8 flex flex-col gap-6">
        {/* Navigation / Header */}
        <div className="flex items-center justify-between w-full">
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-primary font-bold hover:decoration-primary cursor-pointer transition-all hover:scale-105"
          >
            <span className="material-symbols-outlined">arrow_back</span>
            Back to Profile
          </button>
          
          <div className="flex items-center gap-2 bg-surface-container-highest p-1 rounded-lg">
            <button 
              onClick={() => setViewMode('compact')}
              className={`p-2 flex items-center justify-center rounded-md transition-all ${viewMode === 'compact' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}
              title="Compact View"
            >
              <span className="material-symbols-outlined text-xl">view_column_2</span>
            </button>
            <button 
              onClick={() => setViewMode('extended')}
              className={`p-2 flex items-center justify-center rounded-md transition-all ${viewMode === 'extended' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}
              title="Extended View"
            >
              <span className="material-symbols-outlined text-xl">view_list</span>
            </button>
          </div>
        </div>

        {/* Top Summary Banner */}
        <div className={`glass-panel ghost-border rounded-xl p-8 relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6 ${matchInfo.result === 'Victory' ? 'bg-gradient-to-r from-blue-900/40 via-surface to-surface' : 'bg-gradient-to-r from-red-900/40 via-surface to-surface'}`}>
          <div className="flex flex-col items-center md:items-start gap-1 z-10">
            <h1 className={`text-4xl lg:text-5xl font-headline font-bold uppercase drop-shadow-lg ${matchInfo.result === 'Victory' ? 'text-secondary' : 'text-red-400'}`}>
              {matchInfo.result}
            </h1>
            <p className="text-xl text-on-surface-variant font-body">
              {matchInfo.gameMode} <span className="mx-2 text-outline/50">•</span> <span className="text-on-surface">{matchInfo.duration}</span>
            </p>
          </div>
          <div className="flex flex-col items-center">
            <p className="text-sm font-bold text-primary uppercase tracking-widest">{matchInfo.date}</p>
            <p className="text-sm text-secondary mt-1 font-body break-all max-w-[200px] opacity-60">Match ID: {matchId}</p>
          </div>
        </div>

        {/* Main Content: Toggles between Vertical Stack (Extended) and 2-Column Grid (Compact) */}
        {viewMode === 'extended' ? (
          <div className="flex flex-col gap-8 w-full mt-2">
            
            {/* Blue Team Full Width */}
            <div className="glass-panel ghost-border rounded-xl p-4 lg:p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-blue-500/30">
                <h2 className="text-2xl font-headline font-bold text-blue-400 uppercase tracking-widest">Blue Team</h2>
                <span className={`text-sm font-bold px-4 py-1.5 rounded-sm uppercase tracking-wider ${blueTeam[0]?.win ? 'text-green-300 bg-green-900/50' : 'text-red-300 bg-red-900/50'}`}>
                  {blueTeam[0]?.win ? 'Victory' : 'Defeat'}
                </span>
              </div>
              
              <div className="flex flex-col gap-2 min-w-max md:min-w-0 overflow-x-auto pb-4 md:pb-0">
                <div className="grid grid-cols-[3fr_1.5fr_1.5fr_1.5fr_3fr_1.5fr] md:grid-cols-[1fr_repeat(5,_auto)] xl:grid-cols-[20%_15%_10%_10%_25%_10%] gap-4 lg:gap-6 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2 whitespace-nowrap">
                  <div>Player</div>
                  <div className="text-center">KDA</div>
                  <div className="text-center">Damage</div>
                  <div className="text-center">CS</div>
                  <div className="text-center">Items</div>
                  <div className="text-end">Gold</div>
                </div>
                
                {blueTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-[3fr_1.5fr_1.5fr_1.5fr_3fr_1.5fr] md:grid-cols-[1fr_repeat(5,_auto)] xl:grid-cols-[20%_15%_10%_10%_25%_10%] gap-4 lg:gap-6 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/10 hover:bg-surface-container transition-all">
                    {/* Player Info (Champ, Spells, Runes, Name) */}
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-blue-500/30 overflow-hidden">
                         <img src={player.champIcon} alt={player.name} className="w-full h-full object-cover" />
                      </div>
                      {/* Summs & Runes block */}
                      <div className="flex gap-1 shrink-0">
                        <div className="flex flex-col gap-1">
                          {player.summs[0] ? <img src={player.summs[0]} className="w-4 h-4 rounded" /> : <div className="w-4 h-4 bg-surface-container-highest rounded"></div>}
                          {player.summs[1] ? <img src={player.summs[1]} className="w-4 h-4 rounded" /> : <div className="w-4 h-4 bg-surface-container-highest rounded"></div>}
                        </div>
                        <div className="flex flex-col gap-1">
                          {player.runes[0] ? <img src={player.runes[0]} className="w-4 h-4 rounded-full bg-black" /> : <div className="w-4 h-4 bg-surface-container-highest rounded-full"></div>}
                          {player.runes[1] ? <img src={player.runes[1]} className="w-4 h-4 rounded-full bg-black" /> : <div className="w-4 h-4 bg-surface-container-highest rounded-full"></div>}
                        </div>
                      </div>
                      <span className="font-bold text-on-surface truncate ml-1">{player.name}</span>
                    </div>
                    
                    {/* KDA & KP */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="font-mono text-sm tracking-tight font-bold text-on-surface">{player.kda}</div>
                      <div className="text-xs text-on-surface-variant/70 mt-0.5">KP: {player.kp}</div>
                    </div>

                    {/* Damage */}
                    <div className="flex flex-col items-center justify-center">
                      <div className="text-sm font-bold text-on-surface">{player.dmg}</div>
                      <div className="w-16 h-1 mt-1.5 bg-surface-container-highest rounded-full overflow-hidden flex">
                        <div className="h-full bg-red-400" style={{ width: '60%' }}></div>
                      </div>
                    </div>

                    {/* CS */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="text-sm text-on-surface-variant">{player.cs}</div>
                      <div className="text-[10px] text-outline/60 mt-0.5">{player.csMin} / min</div>
                    </div>

                    {/* Items Grid (6 slots + 1 trinket) */}
                    <div className="flex items-center justify-center gap-1 xl:gap-1.5 mx-auto">
                      {player.items.map((itemLink, slotIdx) => (
                        <div 
                          key={slotIdx} 
                          className={`w-7 h-7 xl:w-9 xl:h-9 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner flex shrink-0 overflow-hidden
                            ${slotIdx === 6 ? 'rounded-full ml-1 w-6 h-6 xl:w-8 xl:h-8' : ''}`}
                        >
                          {itemLink && <img src={itemLink} className="w-full h-full object-cover" />}
                        </div>
                      ))}
                    </div>

                    {/* Gold */}
                    <div className="text-end text-sm text-secondary font-bold flex items-center justify-end gap-1">
                      {player.gold}
                      <span className="material-symbols-outlined text-[14px] text-yellow-500">toll</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Red Team Full Width */}
            <div className="glass-panel ghost-border rounded-xl p-4 lg:p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-red-500/30">
                <h2 className="text-2xl font-headline font-bold text-red-400 uppercase tracking-widest">Red Team</h2>
                <span className={`text-sm font-bold px-4 py-1.5 rounded-sm uppercase tracking-wider ${redTeam[0]?.win ? 'text-green-300 bg-green-900/50' : 'text-red-300 bg-red-900/50'}`}>
                  {redTeam[0]?.win ? 'Victory' : 'Defeat'}
                </span>
              </div>
              
              <div className="flex flex-col gap-2 min-w-max md:min-w-0 overflow-x-auto pb-4 md:pb-0">
                <div className="grid grid-cols-[3fr_1.5fr_1.5fr_1.5fr_3fr_1.5fr] md:grid-cols-[1fr_repeat(5,_auto)] xl:grid-cols-[20%_15%_10%_10%_25%_10%] gap-4 lg:gap-6 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2 whitespace-nowrap">
                  <div>Player</div>
                  <div className="text-center">KDA</div>
                  <div className="text-center">Damage</div>
                  <div className="text-center">CS</div>
                  <div className="text-center">Items</div>
                  <div className="text-end">Gold</div>
                </div>
                
                {redTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-[3fr_1.5fr_1.5fr_1.5fr_3fr_1.5fr] md:grid-cols-[1fr_repeat(5,_auto)] xl:grid-cols-[20%_15%_10%_10%_25%_10%] gap-4 lg:gap-6 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/10 hover:bg-surface-container transition-all">
                    {/* Player Info (Champ, Spells, Runes, Name) */}
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-red-500/30 overflow-hidden">
                         <img src={player.champIcon} alt={player.name} className="w-full h-full object-cover" />
                      </div>
                      {/* Summs & Runes block */}
                      <div className="flex gap-1 shrink-0">
                        <div className="flex flex-col gap-1">
                          {player.summs[0] ? <img src={player.summs[0]} className="w-4 h-4 rounded" /> : <div className="w-4 h-4 bg-surface-container-highest rounded"></div>}
                          {player.summs[1] ? <img src={player.summs[1]} className="w-4 h-4 rounded" /> : <div className="w-4 h-4 bg-surface-container-highest rounded"></div>}
                        </div>
                        <div className="flex flex-col gap-1">
                          {player.runes[0] ? <img src={player.runes[0]} className="w-4 h-4 rounded-full bg-black" /> : <div className="w-4 h-4 bg-surface-container-highest rounded-full"></div>}
                          {player.runes[1] ? <img src={player.runes[1]} className="w-4 h-4 rounded-full bg-black" /> : <div className="w-4 h-4 bg-surface-container-highest rounded-full"></div>}
                        </div>
                      </div>
                      <span className="font-bold text-on-surface truncate ml-1">{player.name}</span>
                    </div>
                    
                    {/* KDA & KP */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="font-mono text-sm tracking-tight font-bold text-on-surface">{player.kda}</div>
                      <div className="text-xs text-on-surface-variant/70 mt-0.5">KP: {player.kp}</div>
                    </div>

                    {/* Damage */}
                    <div className="flex flex-col items-center justify-center">
                      <div className="text-sm font-bold text-on-surface">{player.dmg}</div>
                      <div className="w-16 h-1 mt-1.5 bg-surface-container-highest rounded-full overflow-hidden flex">
                        <div className="h-full bg-red-400" style={{ width: '40%' }}></div>
                      </div>
                    </div>

                    {/* CS */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="text-sm text-on-surface-variant">{player.cs}</div>
                      <div className="text-[10px] text-outline/60 mt-0.5">{player.csMin} / min</div>
                    </div>

                    {/* Items Grid (6 slots + 1 trinket) */}
                    <div className="flex items-center justify-center gap-1 xl:gap-1.5 mx-auto">
                      {player.items.map((itemLink, slotIdx) => (
                        <div 
                          key={slotIdx} 
                          className={`w-7 h-7 xl:w-9 xl:h-9 bg-surface-container-highest rounded-md border border-outline-variant/20 shadow-inner flex shrink-0 overflow-hidden
                            ${slotIdx === 6 ? 'rounded-full ml-1 w-6 h-6 xl:w-8 xl:h-8' : ''}`}
                        >
                          {itemLink && <img src={itemLink} className="w-full h-full object-cover" />}
                        </div>
                      ))}
                    </div>

                    {/* Gold */}
                    <div className="text-end text-sm text-secondary font-bold flex items-center justify-end gap-1">
                      {player.gold}
                      <span className="material-symbols-outlined text-[14px] text-yellow-500">toll</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full mt-2">
            
            {/* Blue Team - Compact */}
            <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-blue-500/30">
                <h2 className="text-2xl font-headline font-bold text-blue-400 uppercase tracking-wide">Blue Team</h2>
                <span className={`text-sm font-bold px-3 py-1 rounded-full ${blueTeam[0]?.win ? 'text-green-300 bg-green-900/50' : 'text-red-300 bg-red-900/40'}`}>
                  {blueTeam[0]?.win ? 'Victory' : 'Defeat'}
                </span>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="grid grid-cols-12 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2">
                  <div className="col-span-4">Player</div>
                  <div className="col-span-3 text-center">KDA</div>
                  <div className="col-span-2 text-center">DMG</div>
                  <div className="col-span-1 text-center">CS</div>
                  <div className="col-span-2 text-end">Gold</div>
                </div>
                
                {blueTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-12 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/20 hover:bg-surface-container transition-colors">
                    <div className="col-span-4 flex items-center gap-3">
                      <div className="w-10 h-10 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-blue-500/20 overflow-hidden text-[10px] text-center font-bold">
                         <img src={player.champIcon} alt={player.name} className="w-full h-full object-cover" />
                      </div>
                      <span className="font-bold text-on-surface truncate">{player.name}</span>
                    </div>
                    <div className="col-span-3 text-center font-mono text-sm tracking-tight">{player.kda}</div>
                    <div className="col-span-2 text-center text-sm font-bold text-blue-400">{player.dmg}</div>
                    <div className="col-span-1 text-center text-sm text-on-surface-variant">{player.cs}</div>
                    <div className="col-span-2 text-end text-sm text-secondary font-bold">{player.gold}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Red Team - Compact */}
            <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-red-500/30">
                <h2 className="text-2xl font-headline font-bold text-red-400 uppercase tracking-wide">Red Team</h2>
                <span className={`text-sm font-bold px-3 py-1 rounded-full ${redTeam[0]?.win ? 'text-green-300 bg-green-900/50' : 'text-red-300 bg-red-900/40'}`}>
                  {redTeam[0]?.win ? 'Victory' : 'Defeat'}
                </span>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="grid grid-cols-12 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2">
                  <div className="col-span-4">Player</div>
                  <div className="col-span-3 text-center">KDA</div>
                  <div className="col-span-2 text-center">DMG</div>
                  <div className="col-span-1 text-center">CS</div>
                  <div className="col-span-2 text-end">Gold</div>
                </div>
                
                {redTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-12 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/20 hover:bg-surface-container transition-colors">
                    <div className="col-span-4 flex items-center gap-3">
                      <div className="w-10 h-10 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-red-500/20 overflow-hidden text-[10px] text-center font-bold">
                         <img src={player.champIcon} alt={player.name} className="w-full h-full object-cover" />
                      </div>
                      <span className="font-bold text-on-surface truncate">{player.name}</span>
                    </div>
                    <div className="col-span-3 text-center font-mono text-sm tracking-tight">{player.kda}</div>
                    <div className="col-span-2 text-center text-sm font-bold text-red-400">{player.dmg}</div>
                    <div className="col-span-1 text-center text-sm text-on-surface-variant">{player.cs}</div>
                    <div className="col-span-2 text-end text-sm text-secondary font-bold">{player.gold}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

      </div>
    </main>
  );
}