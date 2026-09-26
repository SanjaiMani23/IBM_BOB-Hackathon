import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Analyzer from './pages/Analyzer';
import Results from './pages/Results';
import ArchitecturePage from './pages/ArchitecturePage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyzer" element={<Analyzer />} />
        <Route path="/results" element={<Results />} />
        <Route path="/architecture" element={<ArchitecturePage />} />
      </Routes>
    </BrowserRouter>
  );
}
