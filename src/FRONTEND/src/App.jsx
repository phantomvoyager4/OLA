import TopNavBar from './components/TopNavBar';
import Home from './pages/Home';
import TierList from './pages/TierList';
import { Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <>
      <TopNavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tier-list" element={<TierList />} />
      </Routes>
    </>
  );
}
