import { Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Dashboard } from './pages/Dashboard';
import { Centres } from './pages/Centres';
import { Surgeries } from './pages/Surgeries';
import { Inspections } from './pages/Inspections';
import { FundTracker } from './pages/FundTracker';
import { Reports } from './pages/Reports';
import { CommitteePortal } from './pages/CommitteePortal';
import { Login } from './pages/Login';
import { Notifications } from './pages/Notifications';
import { Settings } from './pages/Settings';
import { Profile } from './pages/Profile';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/centres" element={<Centres />} />
        <Route path="/surgeries" element={<Surgeries />} />
        <Route path="/inspections" element={<Inspections />} />
        <Route path="/funds" element={<FundTracker />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/committee" element={<CommitteePortal />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;