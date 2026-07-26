import OlaLogo from '../../../../data/static/logo/ola logo _3.svg';

export default function Footer({ compact = false }) {
  return (
    <footer
      className={`ola-footer relative z-30 w-full shrink-0 bg-transparent ${
        compact ? 'ola-footer-compact' : ''
      }`}
    >
      <div
        aria-hidden="true"
        className="ola-footer-line mx-auto h-px w-[calc(100%-2rem)] max-w-7xl"
      />

      <div
        className={`grid items-center gap-4 px-5 sm:px-8 lg:grid-cols-[minmax(260px,0.8fr)_minmax(420px,1.2fr)] lg:gap-10 ${
          compact ? 'py-3' : 'py-5'
        }`}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="ola-footer-logo-shell flex h-11 w-11 shrink-0 items-center justify-center rounded-xl">
            <img
              alt="Open League Analyzer"
              className="h-9 w-9 object-contain"
              src={OlaLogo}
            />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <p className="font-headline text-xs font-bold uppercase tracking-[0.16em] text-on-surface">
                Open League Analyzer
              </p>
            </div>
            <p className="mt-1 text-[10px] tracking-wide text-on-surface-variant">
              &copy; {new Date().getFullYear()} OLA &mdash; Data-driven League insights.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2.5 lg:justify-self-end">
          <p className="max-w-2xl text-[10px] leading-relaxed text-on-surface-variant/85">
            Open League Analyzer isn&apos;t endorsed by Riot Games and doesn&apos;t
            reflect the views or opinions of Riot Games or anyone officially involved
            in producing or managing Riot Games properties. Riot Games and all
            associated properties are trademarks or registered trademarks of Riot
            Games, Inc.
          </p>
        </div>
      </div>
    </footer>
  );
}
