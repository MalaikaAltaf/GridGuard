import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedLayout from './components/ProtectedLayout';
import Login from './pages/Login';
import RiskQueue from './pages/RiskQueue';
import ConsumerDetail from './pages/ConsumerDetail';
import CaseList from './pages/CaseList';
import CaseDetail from './pages/CaseDetail';
import FeederMap from './pages/FeederMap';
import ModelPerformance from './pages/ModelPerformance';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Protected routes — require auth */}
          <Route element={<ProtectedLayout />}>
            <Route path="/risk-queue" element={<RiskQueue />} />
            <Route path="/consumer/:id" element={<ConsumerDetail />} />
            <Route path="/cases" element={<CaseList />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/feeder-map" element={<FeederMap />} />
            <Route path="/analytics" element={<ModelPerformance />} />
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/risk-queue" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
