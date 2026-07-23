import { createElement, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import DockerLogo from "../../../../data/static/programming_logos/docker.svg";
import FastApiLogo from "../../../../data/static/programming_logos/fastapi.svg";
import PythonLogo from "../../../../data/static/programming_logos/python.svg";
import ReactLogo from "../../../../data/static/programming_logos/reactjs.svg";
import RiotLogo from "../../../../data/static/riot_logo.svg";

const stack = [
  {
    logo: ReactLogo,
    logoAlt: "React logo",
    label: "Interface",
    title: "React 19",
    description: "Fast, component-driven views styled for every screen.",
    accent: "purple",
    tags: ["Vite 8", "Tailwind CSS 4"],
  },
  {
    logo: PythonLogo,
    logoAlt: "Python logo",
    label: "Analytics core",
    title: "Python 3.12",
    description:
      "Transforms raw match signals into role-aware metrics, weighted scores and percentiles.",
    accent: "python",
    tags: ["Pandas", "Scikit-learn"],
  },
  {
    logo: FastApiLogo,
    logoAlt: "FastAPI logo",
    label: "API layer",
    title: "FastAPI",
    description:
      "Typed endpoints coordinate concurrent requests, caching and the analysis pipeline.",
    accent: "green",
    tags: ["Uvicorn", "Concurrency"],
  },
  {
    logo: RiotLogo,
    logoAlt: "Riot Games logo",
    logoClass: "tech-logo-riot",
    label: "Data source",
    title: "Riot Games API",
    description: "Live match, ranked and mastery data—cached and rate-aware.",
    accent: "purple",
    tags: ["TTL cache", "Safe retries"],
  },
  {
    logo: DockerLogo,
    logoAlt: "Docker logo",
    label: "Environment",
    title: "Docker",
    description:
      "Keeps the frontend and backend environment reproducible and easy to run together.",
    accent: "purple",
    tags: ["Docker Compose", "Portable setup"],
  },
];

const orbitNodes = [
  {
    key: "react",
    title: "React",
    logo: ReactLogo,
  },
  {
    key: "python",
    title: "Python",
    logo: PythonLogo,
  },
  {
    key: "fastapi",
    title: "FastAPI",
    logo: FastApiLogo,
  },
  {
    key: "docker",
    title: "Docker",
    logo: DockerLogo,
  },
  {
    key: "riot",
    title: "Riot Data",
    logo: RiotLogo,
    logoClass: "tech-logo-riot",
  },
  {
    key: "model",
    title: "Evaluation Model",
    mark: "f(x)",
  },
];

const pipeline = [
  {
    number: "1",
    title: "Search",
    description: "A Riot ID and region start a focused profile request.",
    icon: "search",
  },
  {
    number: "2",
    title: "Collect",
    description: "The API fetches matches concurrently and reuses cached data.",
    icon: "cloud_download",
  },
  {
    number: "3",
    title: "Analyze in Python",
    description:
      "Python extracts performance signals and standardizes them within each in-game role.",
    icon: "query_stats",
  },
  {
    number: "4",
    title: "Score & explain",
    description:
      "Explicit weights become an OLA percentile that the interface makes easy to read.",
    icon: "insights",
  },
];

function Reveal({ as: Component = "div", delay = 0, className = "", children }) {
  return createElement(
    Component,
    {
      className: `tech-reveal ${className}`,
      "data-tech-reveal": true,
      style: { "--reveal-delay": `${delay}ms` },
    },
    children,
  );
}

export default function TechStack() {
  const pageRef = useRef(null);

  useEffect(() => {
    const revealItems = pageRef.current?.querySelectorAll("[data-tech-reveal]");

    if (!revealItems?.length) return undefined;

    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -7% 0px" },
    );

    revealItems.forEach((item) => observer.observe(item));

    return () => observer.disconnect();
  }, []);

  return (
    <main
      ref={pageRef}
      className="tech-page min-h-screen overflow-hidden bg-surface"
    >
      <div className="tech-aurora tech-aurora-primary" aria-hidden="true" />
      <div className="tech-aurora tech-aurora-secondary" aria-hidden="true" />
      <div className="tech-grid" aria-hidden="true" />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-6 pb-24 pt-28 sm:px-8 lg:px-12 lg:pb-32 lg:pt-36">
        <Reveal delay={40}>
          <Link
            to="/"
            className="group inline-flex items-center gap-2 text-sm font-bold text-on-surface-variant transition-colors hover:text-secondary"
          >
            <span className="material-symbols-outlined text-[19px] transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>
            Back to analyzer
          </Link>
        </Reveal>

        <section className="grid min-h-140 items-center gap-14 py-16 lg:grid-cols-[1.18fr_0.82fr] lg:py-20">
          <div>

            <Reveal
              as="h1"
              delay={210}
              className="max-w-4xl font-headline text-5xl font-bold leading-[0.96] tracking-[-0.055em] text-on-surface sm:text-6xl md:text-7xl lg:text-[5.4rem]"
            >
              Built to make
              <span className="tech-gradient-text block">performance visible.</span>
            </Reveal>

            <Reveal
              as="p"
              delay={320}
              className="mt-7 max-w-3xl text-base leading-8 text-on-surface-variant sm:text-lg"
            >
              OLA turns live Riot data into role-aware insights players can
              understand at a glance - without hiding the logic behind the score.
            </Reveal>

            <Reveal delay={420} className="mt-9 flex flex-wrap gap-3">
              <a
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-3 font-headline text-sm font-bold text-white transition-all hover:-translate-y-0.5 hover:bg-primary-fixed-dim hover:shadow-[0_12px_35px_rgba(158,36,230,0.25)]"
              >
                Explore the pipeline
                <span className="material-symbols-outlined text-[19px]">
                  arrow_downward
                </span>
              </a>
              <Link
                to="/"
                className="inline-flex items-center gap-2 rounded-lg border border-outline-variant/60 bg-surface-container/70 px-5 py-3 font-headline text-sm font-bold text-on-surface transition-all hover:border-secondary/50 hover:text-secondary"
              >
                Try OLA
                <span className="material-symbols-outlined text-[19px]">
                  north_east
                </span>
              </Link>
            </Reveal>
          </div>

          <Reveal delay={260} className="tech-orbit-wrap mx-auto w-full max-w-md">
            <div className="tech-orbit" aria-hidden="true">
              <div className="tech-orbit-spokes" />
              <div className="tech-orbit-ring tech-orbit-ring-outer" />
              <div className="tech-orbit-ring tech-orbit-ring-inner" />

              <div className="tech-core">
                <span className="font-headline text-3xl font-black tracking-[-0.06em] text-on-surface">
                  OLA
                </span>
                <span className="mt-1 font-headline text-xs font-bold uppercase tracking-[0.28em] text-primary-fixed">
                  core
                </span>
              </div>

              {orbitNodes.map((node) => (
                <div
                  key={node.key}
                  className={`tech-orbit-node tech-orbit-node-${node.key}`}
                >
                  {node.logo ? (
                    <img
                      src={node.logo}
                      alt=""
                      className={`tech-orbit-logo ${node.logoClass ?? ""}`}
                    />
                  ) : (
                    <span className="tech-orbit-mark">{node.mark}</span>
                  )}
                  <span>{node.title}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        <section
          id="mission"
          className="border-t border-outline-variant/25 py-20 lg:py-24"
        >
          <div className="grid gap-10 lg:grid-cols-[0.76fr_1.24fr] lg:gap-16">
            <Reveal delay={80}>
              <p className="font-headline text-xs font-bold uppercase tracking-[0.22em] text-primary-fixed">
                Why I built OLA
              </p>
              <h2 className="mt-3 max-w-md font-headline text-3xl font-bold tracking-[-0.035em] text-on-surface sm:text-4xl">
                A project with a clear mission.
              </h2>
              <div className="mt-7 h-px w-20 bg-linear-to-r from-primary to-secondary" />
              <p className="mt-7 max-w-md text-sm leading-7 text-on-surface-variant">
                The technology matters because it serves the player - not the
                other way around. OLA focuses on clean UI and full transparency
                to provide players with free of charge insights into their LoL games.
              </p>
            </Reveal>

            <div className="tech-mission-copy">
              <Reveal
                as="p"
                delay={170}
                className="font-headline text-2xl font-medium leading-[1.45] tracking-[-0.025em] text-on-surface sm:text-3xl"
              >
                <span className="text-primary-fixed">
                  Open League Analyzer (OLA)
                </span>{" "}
                is my project with a mission to create a flexible web
                application that helps League of Legends players progress.
              </Reveal>

              <div className="mt-9 grid gap-4 sm:grid-cols-2">
                <Reveal delay={280} className="tech-mission-card">
                  <span className="font-headline text-[14px] font-bold uppercase tracking-[0.2em] text-secondary">
                    Where it is today
                  </span>
                  <p className="mt-4 text-sm leading-7 text-on-surface-variant">
                    I have built a user-first, intuitive interface that lets
                    players browse their games and evaluate their performance
                    with the OLA Score.
                  </p>
                </Reveal>

                <Reveal delay={390} className="tech-mission-card">
                  <span className="font-headline text-[14px] font-bold uppercase tracking-[0.2em] text-primary-fixed">
                    Where it is going
                  </span>
                  <p className="mt-4 text-sm leading-7 text-on-surface-variant">
                    My next goal is to enhance the evaluation process and build
                    a robust analytical model that can explain how someone
                    plays and help them improve—something closer to a personal
                    coach.
                  </p>
                </Reveal>
              </div>

              <Reveal
                as="p"
                delay={500}
                className="mt-7 border-l-2 border-secondary/60 pl-5 text-sm italic leading-7 text-on-surface"
              >
                I believe OLA can become a valuable resource for casual players
                who want to improve their game sense and perform more
                consistently.
              </Reveal>
            </div>
          </div>
        </section>

        <section className="border-t border-outline-variant/25 py-20 lg:py-24">
          <Reveal delay={80} className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <p className="font-headline text-xs font-bold uppercase tracking-[0.22em] text-secondary">
                The toolkit
              </p>
              <h2 className="mt-3 font-headline text-3xl font-bold tracking-[-0.035em] text-on-surface sm:text-4xl">
                The stack behind the mission.
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-on-surface-variant">
              Python powers the analysis at OLA&apos;s core; the remaining
              layers collect the data and turn its results into a useful
              experience.
            </p>
          </Reveal>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {stack.map((item, index) => (
              <Reveal
                key={item.title}
                delay={160 + index * 90}
                className={`tech-stack-card tech-stack-card-${item.accent}`}
              >
                <div className="flex items-start justify-between">
                  <span className="tech-stack-icon">
                    <img
                      src={item.logo}
                      alt={item.logoAlt}
                      className={`tech-stack-logo ${item.logoClass ?? ""}`}
                    />
                  </span>
                  <span className="font-headline text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">
                    {item.label}
                  </span>
                </div>
                <h3 className="mt-10 font-headline text-xl font-bold text-on-surface">
                  {item.title}
                </h3>
                <p className="mt-3 min-h-18 text-sm leading-6 text-on-surface-variant">
                  {item.description}
                </p>
                <div className="mt-6 flex flex-wrap gap-2">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-outline-variant/40 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        <section
          id="how-it-works"
          className="scroll-mt-24 border-t border-outline-variant/25 py-20 lg:py-24"
        >
          <Reveal delay={80} className="">
            <p className="font-headline text-xs font-bold uppercase tracking-[0.22em] text-primary-fixed">
              How it works
            </p>
            <h2 className="mt-3 font-headline text-3xl font-bold tracking-[-0.035em] text-on-surface sm:text-4xl">
              From Riot ID to useful insight.
            </h2>
            <p className="mt-4 text-sm leading-7 text-on-surface-variant sm:text-base">
              The experience is progressive: collect only what is needed,
              analyze it in Python, and present the useful insights.
            </p>
          </Reveal>

          <div className="tech-pipeline mt-12 grid gap-6 md:grid-cols-4">
            {pipeline.map((step, index) => (
              <Reveal
                key={step.number}
                delay={170 + index * 110}
                className="tech-pipeline-step"
              >
                <div className="flex items-center justify-between">
                  <span className="font-headline text-xs font-bold tracking-[0.2em] text-outline">
                    {step.number}
                  </span>
                  <span className="material-symbols-outlined text-[22px] text-secondary">
                    {step.icon}
                  </span>
                </div>
                <h3 className="mt-8 font-headline text-lg font-bold text-on-surface">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-on-surface-variant">
                  {step.description}
                </p>
                {index < pipeline.length - 1 && (
                  <span
                    className="tech-pipeline-arrow material-symbols-outlined"
                    aria-hidden="true"
                  >
                    arrow_forward
                  </span>
                )}
              </Reveal>
            ))}
          </div>

          <Reveal
            delay={650}
            className="mt-10 flex flex-col gap-5 rounded-2xl border border-secondary/20 bg-secondary/5 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8"
          >
            <div className="flex items-start gap-4">
              <span className="material-symbols-outlined rounded-xl bg-secondary/15 p-3 text-secondary">
                verified_user
              </span>
              <div>
                <h3 className="font-headline font-bold text-on-surface">
                  Transparent by design
                </h3>
                <p className="mt-1 text-sm leading-6 text-on-surface-variant">
                  The score uses explicit, role-aware weights (not an opaque
                  model) so every result stays inspectable.
                </p>
              </div>
            </div>
            <Link
              to="/"
              className="shrink-0 font-headline text-sm font-bold text-secondary transition-colors hover:text-secondary-fixed"
            >
              Analyze a player →
            </Link>
          </Reveal>
        </section>
      </div>
    </main>
  );
}
