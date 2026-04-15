import { useParams } from 'react-router-dom';

export default function PlayerProfile() {
  const { region, riotId } = useParams();
  
  // Extract nickname and tag from riotId (e.g., softmax-EUNE1)
  const lastDashIndex = riotId.lastIndexOf('-');
  const nickname = lastDashIndex !== -1 ? riotId.substring(0, lastDashIndex) : riotId;
  const tag = lastDashIndex !== -1 ? riotId.substring(lastDashIndex + 1) : '';

  return (
    <main className="min-h-screen pt-24 flex flex-col items-center">
      <div className="w-full max-w-4xl px-6 text-center">
        <h1 className="text-4xl font-headline font-bold text-on-surface mb-4">
          Player Profile
        </h1>
        <div className="glass-panel ghost-border rounded-lg p-8">
          <p className="text-xl text-on-surface-variant font-body">
            You are searching for:
          </p>
          <div className="mt-4 text-2xl text-primary font-bold">
            {nickname} #{tag} <span className="text-outline text-lg block mt-2">Region: {region}</span>
          </div>
          <p className="mt-8 text-outline text-sm italic">
            (This is a blank page placeholder. The backend analysis request will be handled here later.)
          </p>
        </div>
      </div>
    </main>
  );
}
