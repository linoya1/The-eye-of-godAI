import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import SignupPage from './pages/SignupPage';
import LoginPage from './pages/LoginPage';
import InterestQuestionnairePage from './pages/InterestQuestionnairePage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<LandingPage />} />
        <Route path="/signup"     element={<SignupPage />} />
        <Route path="/login"      element={<LoginPage />} />
        <Route path="/onboarding" element={<InterestQuestionnairePage />} />
        <Route path="/dashboard"  element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}
