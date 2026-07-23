import { Link } from 'react-router-dom';
import RiotLogo from '../../../../data/static/riot_logo.svg'

export default function SignIn() {
  return (
    <main className="min-h-screen pt-24 pb-12 flex flex-col items-center justify-center relative overflow-hidden bioluminescent-glow">
      {/* Background ambient decorations (purple & green mix) */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Back to Home floating button */}
      <div className="absolute top-24 left-8 md:left-12 z-20">
        <Link to="/" className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-bold tracking-tight">
          <span className="material-symbols-outlined">arrow_back</span>
          Back
        </Link>
      </div>

      {/* Sign In Box */}
      <div className="glass-panel ghost-border rounded-2xl p-8 md:p-10 w-full max-w-md flex flex-col items-center relative z-10 shadow-2xl">
        {/* Logo/Header */}
        <div className="flex flex-col items-center mb-8 w-full text-center">
          <div className='font-body text-xl pb-2'> *Not available yet, coming soon* </div>
          <Link to="/" className="text-4xl font-bold tracking-tight text-secondary font-headline mb-2 hover:scale-105 transition-transform">
            OLA
          </Link>
          <h1 className="text-2xl font-headline font-bold text-on-surface">Welcome Back</h1>
          <p className="text-on-surface-variant text-sm mt-2">Sign in to access your data.</p>
        </div>

        {/* Form */}
        <form className="w-full flex flex-col gap-5" onSubmit={(e) => e.preventDefault()}>
          {/* Email Input */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-bold text-on-surface-variant ml-1 font-headline">Email or Riot ID</label>
            <div className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-4 text-on-surface-variant/50">person</span>
              <input 
                type="text" 
                placeholder="Enter your email or Riot ID"
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg pl-12 pr-4 py-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-on-surface-variant/40"
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center px-1">
              <label className="text-sm font-bold text-on-surface-variant font-headline">Password</label>
              <a href="#" className="text-xs text-primary hover:underline hover:text-primary-dim transition-colors">Forgot password?</a>
            </div>
            <div className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-4 text-on-surface-variant/50">lock</span>
              <input 
                type="password" 
                placeholder="Enter your password"
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg pl-12 pr-4 py-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-on-surface-variant/40"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button 
            type="submit"
            className="w-full mt-4 bg-primary text-on-primary font-headline font-bold text-lg py-3 rounded-lg hover:bg-primary-dim hover:shadow-[0_0_15px_rgba(137,30,199,0.4)] transition-all flex items-center justify-center gap-2 active:scale-95 cursor-pointer"
          >
            <span className="material-symbols-outlined text-xl">login</span>
            Log In
            
          </button>
        </form>

        {/* Divider */}
        <div className="w-full flex items-center gap-4 my-6">
          <div className="h-px bg-outline-variant/30 flex-1"></div>
          <span className="text-xs text-on-surface-variant font-bold uppercase tracking-wider">Or</span>
          <div className="h-px bg-outline-variant/30 flex-1"></div>
        </div>

        {/* Riot Sign-In (Mock) */}
        <button className="w-full bg-[#eb0029] hover:bg-[#c90022] h-14 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-3 transition-colors active:scale-95 cursor-pointer">
          <img src={RiotLogo} />
          <span>Sign in with Riot Account</span>
        </button>

        {/* Sign Up Link */}
        <p className="text-sm text-on-surface-variant mt-8 text-center">
          Don't have an account yet? <Link to="/signup" className="text-secondary font-bold hover:underline hover:text-secondary-dim pl-1">Sign up</Link>
        </p>
      </div>
    </main>
  );
}