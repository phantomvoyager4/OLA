import { Link } from "react-router-dom";

export default function Prediction() {
  return (
    <main>
      <div className="absolute top-1/4 left-1/8 w-96 h-96 bg-primary/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/8 w-96 h-96 bg-secondary/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-24 left-8 md:left-12 z-20">
        <Link
          to="/"
          className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-bold tracking-tight"
        >
          <span className="material-symbols-outlined">arrow_back</span>
          Back
        </Link>
      </div>
      <div className="text-4xl font-body text-center pt-115">
        There is nothing here yet.
      </div>
    </main>
  );
}
