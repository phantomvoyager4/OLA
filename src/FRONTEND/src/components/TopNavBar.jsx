import { Link, NavLink } from 'react-router-dom';

export default function TopNavBar() {
  return (
    <nav className="w-full h-16 bg-[#0b0f0f] flex justify-between items-center px-8 fixed top-0 z-50">
      <div className="flex items-center gap-8">
        <Link to="/" className="text-2xl font-bold tracking-tight text-[#53eede] font-['Space_Grotesk']">
          OLA
        </Link>
        <div className="hidden md:flex gap-6 items-center h-full">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? 'text-[#53eede] border-b-2 border-[#53eede] pb-1'
                  : 'text-[#a8acab] hover:text-[#53eede]'
              }`
            }
          >
            Dashboard
          </NavLink>
          {/* Invisible tier list link */}
          <NavLink
            to="/tier-list"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter sr-only transition-colors duration-300 ${
                isActive
                  ? 'text-[#53eede] border-b-2 border-[#53eede] pb-1'
                  : 'text-[#a8acab] hover:text-[#53eede]'
              }`
            }
          >
            Tier list
          </NavLink>
          {/* Invisible prediction link */}
          <NavLink
            to="/prediction"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter sr-only transition-colors duration-300 ${
                isActive
                  ? 'text-[#53eede] border-b-2 border-[#53eede] pb-1'
                  : 'text-[#a8acab] hover:text-[#53eede]'
              }`
            }
          >
            Prediction
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="material-symbols-outlined text-[#a8acab] cursor-pointer hover:text-[#53eede] transition-colors">
          notifications
        </span>
        <span className="material-symbols-outlined text-[#a8acab] cursor-pointer hover:text-[#53eede] transition-colors">
          settings
        </span>
        <button className="bg-primary-container text-on-primary-container hover:shadow-[0_0_10px_rgba(83,238,222,0.4)] transition-all cursor-pointer duration-300 font-headline px-5 py-2 text-sm rounded-md flex items-center justify-center gap-2 active:scale-95">
          Sign In
        </button>
      </div>
    </nav>
  );
}