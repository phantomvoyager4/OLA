import { Link, NavLink } from "react-router-dom";

export default function TopNavBar() {
  return (
    <nav
      className="w-full h-16 flex justify-between items-center px-8 fixed top-0 z-50"
      style={{ backgroundColor: '#0a0a0a' }}
    >
      <div className="flex items-center gap-8">
        <Link
          to="/"
          className="text-2xl font-bold tracking-tight text-secondary font-['Space_Grotesk']"
        >
          OLA
        </Link>
        <div className="hidden md:flex gap-6 items-center h-full">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/tier-list"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Tier list
          </NavLink>
          <NavLink
            to="/prediction"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Prediction
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-secondary transition-colors">
          notifications
        </span>
        <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-secondary transition-colors">
          settings
        </span>
        <Link to='/login'>
        <button className="bg-primary-container text-on-primary-container hover:shadow-[0_0_10px_rgba(83,238,222,0.4)] transition-all cursor-pointer duration-300 font-headline px-5 py-2 text-sm rounded-md flex items-center justify-center gap-2 active:scale-95">
          Sign In
        </button>
        </Link>
      </div>
    </nav>
  );
}
