import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Analyzer from './pages/Analyzer';
import Results from './pages/Results';
import ArchitecturePage from './pages/ArchitecturePage';
import Dashboard from './pages/Dashboard';
import Debugging from './pages/Debugging';
import Optimization from './pages/Optimization';
import Testing from './pages/Testing';
import Jira from './pages/Jira';
import PullRequests from './pages/PullRequests';
import ReturnSummary from './pages/ReturnSummary';
import FrictionAnalytics from './pages/FrictionAnalytics';
import Settings from './pages/Settings';
import CodeAnalysis from './pages/CodeAnalysis';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/" element={<Landing />} />
        <Route path="/architecture" element={<ArchitecturePage />} />

        {/* Core analysis workspace */}
        <Route path="/analyzer" element={<Analyzer />} />
        <Route path="/results" element={<Results />} />

        {/* Authenticated app */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/debugging" element={<Debugging />} />
        <Route path="/optimization" element={<Optimization />} />
        <Route path="/testing" element={<Testing />} />
        <Route path="/jira" element={<Jira />} />
        <Route path="/pull-requests" element={<PullRequests />} />
        <Route path="/return-summary" element={<ReturnSummary />} />
        <Route path="/friction" element={<FrictionAnalytics />} />
        <Route path="/code-analysis" element={<CodeAnalysis />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}
