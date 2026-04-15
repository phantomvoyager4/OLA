import TopNavBar from './components/TopNavBar';
import Home from './pages/Home';
import TierList from './pages/TierList';
import PlayerProfile from './pages/PlayerProfile';
import { Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <>
      <TopNavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tier-list" element={<TierList />} />
        <Route path="/player/:region/:riotId" element={<PlayerProfile />} />
      </Routes>
    </>
  );
}
