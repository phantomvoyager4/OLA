import TopNavBar from './components/TopNavBar';
import Home from './pages/Home';
import TierList from './pages/TierList';
import Match from './pages/Match';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import PlayerProfile from './pages/PlayerProfile';
import RateLimitIndicator from './components/RateLimitIndicator';
import { Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <>
      <TopNavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tier-list" element={<TierList />} />
        <Route path="/player/:region/:riotId" element={<PlayerProfile />} />
        <Route path='/match/:matchId' element={<Match />} />
        <Route path='/login' element={<SignIn />} />
        <Route path='/signup' element={<SignUp />} />
      </Routes>
      <RateLimitIndicator />
    </>
  );
}
