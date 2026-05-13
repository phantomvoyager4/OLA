 import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function Match() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('extended'); // 'extended' | 'compact'

  // Mock data for the match details to fill the UI
  const matchInfo = {
    result: 'Victory',
    duration: '32:15',
    date: 'Oct 24, 2023',
    gameMode: 'Ranked Solo',
  };

  // Expanded mock data with items, summoners, and runes
  const blueTeam = [

    { champ: 'Aatrox', name: 'TopDiff', kda: '5/2/10', cs: 220, gold: '14.5k', dmg: '22.3k', kp: '55%', items: ['bg-red-900', 'bg-slate-700', 'bg-gray-800', 'bg-red-800', '', '', 'bg-yellow-600'], summs: ['F', 'TP'], runes: ['Conq', 'Resolve'] },
    { champ: 'LeeSin', name: 'JunglePro', kda: '8/4/12', cs: 180, gold: '13.2k', dmg: '18.1k', kp: '74%', items: ['bg-red-700', 'bg-gray-800', 'bg-slate-700', '', '', '', 'bg-red-600'], summs: ['F', 'Sm'], runes: ['Conq', 'Insp'] },
    { champ: 'Ahri', name: 'MidFaker', kda: '10/1/8', cs: 250, gold: '16.1k', dmg: '35.4k', kp: '66%', items: ['bg-blue-600', 'bg-purple-700', 'bg-blue-400', 'bg-slate-600', 'bg-yellow-500', '', 'bg-red-600'], summs: ['F', 'Ig'], runes: ['Elec', 'Sorc'] },
    { champ: 'Jinx', name: 'AdcCarry', kda: '12/3/7', cs: 280, gold: '17.8k', dmg: '41.2k', kp: '70%', items: ['bg-yellow-400', 'bg-red-600', 'bg-gray-300', 'bg-red-500', 'bg-blue-300', 'bg-slate-700', 'bg-blue-800'], summs: ['F', 'H'], runes: ['LT', 'Insp'] },
    { champ: 'Thresh', name: 'SupportGod', kda: '1/5/22', cs: 35, gold: '8.4k', dmg: '7.8k', kp: '85%', items: ['bg-green-700', 'bg-gray-800', 'bg-blue-900', 'bg-slate-700', '', '', 'bg-red-600'], summs: ['F', 'Ex'], runes: ['Glac', 'Insp'] },
  ];

  const redTeam = [
    { champ: 'Ornn', name: 'TankMain', kda: '2/5/8', cs: 190, gold: '11.5k', dmg: '15.2k', kp: '45%', items: ['bg-slate-700', 'bg-blue-900', 'bg-gray-800', '', '', '', 'bg-yellow-600'], summs: ['F', 'TP'], runes: ['Grasp', 'Insp'] },
    { champ: 'Vi', name: 'Puncher', kda: '4/8/5', cs: 160, gold: '10.2k', dmg: '14.8k', kp: '40%', items: ['bg-red-800', 'bg-gray-800', 'bg-slate-700', 'bg-green-700', '', '', 'bg-red-600'], summs: ['F', 'Sm'], runes: ['Conq', 'Dom'] },
    { champ: 'Zed', name: 'ShadowNinja', kda: '7/6/4', cs: 210, gold: '13.1k', dmg: '28.5k', kp: '50%', items: ['bg-purple-800', 'bg-red-700', 'bg-gray-800', 'bg-slate-700', '', '', 'bg-red-600'], summs: ['F', 'Ig'], runes: ['Elec', 'Sorc'] },
    { champ: 'Aphelios', name: 'MoonWeapon', kda: '5/7/4', cs: 240, gold: '14.8k', dmg: '22.1k', kp: '40%', items: ['bg-yellow-400', 'bg-red-600', 'bg-gray-300', 'bg-slate-700', '', '', 'bg-blue-800'], summs: ['F', 'H'], runes: ['LT', 'Dom'] },
    { champ: 'Lulu', name: 'ShieldBot', kda: '0/7/9', cs: 20, gold: '7.4k', dmg: '6.5k', kp: '40%', items: ['bg-green-600', 'bg-gray-800', 'bg-purple-500', '', '', '', 'bg-red-600'], summs: ['F', 'Ex'], runes: ['Aery', 'Insp'] },
  ];

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
          <div className="text-center md:text-right z-10">
            <p className="text-sm font-bold text-outline-variant uppercase tracking-widest">{matchInfo.date}</p>
            <p className="text-sm text-on-surface-variant mt-1 font-body break-all max-w-[200px] opacity-60">Match ID: {matchId}</p>
          </div>
        </div>

        {/* Main Content: Toggles between Vertical Stack (Extended) and 2-Column Grid (Compact) */}
        {viewMode === 'extended' ? (
          <div className="flex flex-col gap-8 w-full mt-2">
            
            {/* Blue Team Full Width */}
            <div className="glass-panel ghost-border rounded-xl p-4 lg:p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-blue-500/30">
                <h2 className="text-2xl font-headline font-bold text-blue-400 uppercase tracking-widest">Blue Team</h2>
                <span className="text-sm font-bold text-blue-300 bg-blue-900/50 px-4 py-1.5 rounded-sm uppercase tracking-wider">Victory</span>
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
                      <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-blue-500/30 text-[10px] text-center font-bold">
                         {player.champ}
                      </div>
                      {/* Summs & Runes block */}
                      <div className="flex flex-col gap-1 shrink-0">
                        <div className="flex gap-1">
                          <div className="w-4 h-4 bg-yellow-500/80 rounded" title={player.summs[0]}></div>
                          <div className="w-4 h-4 bg-sky-500/80 rounded" title={player.summs[1]}></div>
                        </div>
                        <div className="flex gap-1">
                          <div className="w-4 h-4 rounded-full bg-green-500/80" title={player.runes[0]}></div>
                          <div className="w-4 h-4 rounded-full bg-teal-500/80" title={player.runes[1]}></div>
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
                      <div className="w-16 h-1 mt-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                        <div className="h-full bg-red-400" style={{ width: '60%' }}></div>
                      </div>
                    </div>

                    {/* CS */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="text-sm text-on-surface-variant">{player.cs}</div>
                      <div className="text-[10px] text-outline/60 mt-0.5">6.8 / min</div>
                    </div>

                    {/* Items Grid (6 slots + 1 trinket) */}
                    <div className="flex items-center justify-center gap-1 xl:gap-1.5 mx-auto">
                      {player.items.map((itemClass, slotIdx) => (
                        <div 
                          key={slotIdx} 
                          className={`w-7 h-7 xl:w-9 xl:h-9 rounded-md border border-outline-variant/20 shadow-inner flex shrink-0
                            ${itemClass ? itemClass : 'bg-surface-container-highest'} 
                            ${slotIdx === 6 ? 'rounded-full ml-1 w-6 h-6 xl:w-8 xl:h-8' : ''}`}
                        ></div>
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
                <span className="text-sm font-bold text-red-300 bg-red-900/50 px-4 py-1.5 rounded-sm uppercase tracking-wider">Defeat</span>
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
                      <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-red-500/30 text-[10px] text-center font-bold">
                         {player.champ}
                      </div>
                      {/* Summs & Runes block */}
                      <div className="flex flex-col gap-1 shrink-0">
                        <div className="flex gap-1">
                          <div className="w-4 h-4 bg-yellow-500/80 rounded" title={player.summs[0]}></div>
                          <div className="w-4 h-4 bg-sky-500/80 rounded" title={player.summs[1]}></div>
                        </div>
                        <div className="flex gap-1">
                          <div className="w-4 h-4 rounded-full bg-green-500/80" title={player.runes[0]}></div>
                          <div className="w-4 h-4 rounded-full bg-teal-500/80" title={player.runes[1]}></div>
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
                      <div className="w-16 h-1 mt-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                        <div className="h-full bg-red-400" style={{ width: '40%' }}></div>
                      </div>
                    </div>

                    {/* CS */}
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="text-sm text-on-surface-variant">{player.cs}</div>
                      <div className="text-[10px] text-outline/60 mt-0.5">6.1 / min</div>
                    </div>

                    {/* Items Grid (6 slots + 1 trinket) */}
                    <div className="flex items-center justify-center gap-1 xl:gap-1.5 mx-auto">
                      {player.items.map((itemClass, slotIdx) => (
                        <div 
                          key={slotIdx} 
                          className={`w-7 h-7 xl:w-9 xl:h-9 rounded-md border border-outline-variant/20 shadow-inner flex shrink-0
                            ${itemClass ? itemClass : 'bg-surface-container-highest'} 
                            ${slotIdx === 6 ? 'rounded-full ml-1 w-6 h-6 xl:w-8 xl:h-8' : ''}`}
                        ></div>
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
                <span className="text-sm font-bold text-blue-300 bg-blue-900/40 px-3 py-1 rounded-full">Victory</span>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="grid grid-cols-12 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2">
                  <div className="col-span-5">Player</div>
                  <div className="col-span-3 text-center">KDA</div>
                  <div className="col-span-2 text-center">CS</div>
                  <div className="col-span-2 text-end">Gold</div>
                </div>
                
                {blueTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-12 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/20 hover:bg-surface-container transition-colors">
                    <div className="col-span-5 flex items-center gap-3">
                      <div className="w-10 h-10 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-blue-500/20 overflow-hidden text-[10px] text-center font-bold">
                         {player.champ}
                      </div>
                      <span className="font-bold text-on-surface truncate">{player.name}</span>
                    </div>
                    <div className="col-span-3 text-center font-mono text-sm tracking-tight">{player.kda}</div>
                    <div className="col-span-2 text-center text-sm text-on-surface-variant">{player.cs}</div>
                    <div className="col-span-2 text-end text-sm text-secondary font-bold">{player.gold}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Red Team - Compact */}
            <div className="glass-panel ghost-border rounded-xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-red-500/30">
                <h2 className="text-2xl font-headline font-bold text-red-400 uppercase tracking-wide">Red Team</h2>
                <span className="text-sm font-bold text-red-300 bg-red-900/40 px-3 py-1 rounded-full">Defeat</span>
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="grid grid-cols-12 text-xs font-bold text-on-surface-variant uppercase px-4 pb-2">
                  <div className="col-span-5">Player</div>
                  <div className="col-span-3 text-center">KDA</div>
                  <div className="col-span-2 text-center">CS</div>
                  <div className="col-span-2 text-end">Gold</div>
                </div>
                
                {redTeam.map((player, idx) => (
                  <div key={idx} className="grid grid-cols-12 items-center bg-surface-container-low rounded-lg p-3 border border-outline-variant/20 hover:bg-surface-container transition-colors">
                    <div className="col-span-5 flex items-center gap-3">
                      <div className="w-10 h-10 bg-surface-container-highest rounded-full flex items-center justify-center shrink-0 border border-red-500/20 overflow-hidden text-[10px] text-center font-bold">
                         {player.champ}
                      </div>
                      <span className="font-bold text-on-surface truncate">{player.name}</span>
                    </div>
                    <div className="col-span-3 text-center font-mono text-sm tracking-tight">{player.kda}</div>
                    <div className="col-span-2 text-center text-sm text-on-surface-variant">{player.cs}</div>
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