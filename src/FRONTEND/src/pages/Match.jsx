 import { useParams, useNavigate } from 'react-router-dom';

export default function Match() {
  const { matchId } = useParams();
  const navigate = useNavigate();

  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center">
      <div className="w-full max-w-4xl px-6 flex flex-col gap-6">
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-primary self-start font-bold hover:decoration-primary cursor-pointer"
        >
          <span className="material-symbols-outlined">arrow_back</span>
          Back
        </button>

        <div className="glass-panel ghost-border rounded-xl p-8 text-center flex flex-col items-center justify-center gap-4">
          <span className="material-symbols-outlined text-6xl text-primary drop-shadow-[0_0_10px_rgba(83,238,222,0.5)]">
            analytics
          </span>
          <h1 className="text-4xl font-headline font-bold text-on-surface">Match Details</h1>
          <p className="text-xl text-on-surface-variant font-body mb-4">
            ID: <span className="font-bold text-primary">{matchId}</span>
          </p>
          
          <div className="w-full bg-surface-container-low rounded-lg p-6 border border-outline-variant/30 text-left">
            <p className="text-on-surface-variant mb-2">This is a placeholder for the advanced match statistics page.</p>
            <ul className="text-sm text-outline list-disc list-inside ml-4 space-y-1">
              <li>Detailed player breakdown</li>
              <li>Damage graphs and heatmaps</li>
              <li>Objective control timeline</li>
              <li>Gold advantage charts</li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
}