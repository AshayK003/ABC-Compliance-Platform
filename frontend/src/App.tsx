import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { DashboardLayout } from './layouts/DashboardLayout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { NotFound } from './pages/NotFound';

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Centres = lazy(() => import('./pages/Centres').then(m => ({ default: m.Centres })));
const Surgeries = lazy(() => import('./pages/Surgeries').then(m => ({ default: m.Surgeries })));
const Inspections = lazy(() => import('./pages/Inspections').then(m => ({ default: m.Inspections })));
const FundTracker = lazy(() => import('./pages/FundTracker').then(m => ({ default: m.FundTracker })));
const Reports = lazy(() => import('./pages/Reports').then(m => ({ default: m.Reports })));
const CommitteePortal = lazy(() => import('./pages/CommitteePortal').then(m => ({ default: m.CommitteePortal })));
const Notifications = lazy(() => import('./pages/Notifications').then(m => ({ default: m.Notifications })));
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const Profile = lazy(() => import('./pages/Profile').then(m => ({ default: m.Profile })));
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));

function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
    </div>
  );
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Suspense fallback={<LoadingFallback />}>
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
                <Route path="*" element={<NotFound />} />
              </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;