import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Overview from "./pages/Overview";
import Datasets from "./pages/Datasets";
import AskAI from "./pages/AskAI";
import Insights from "./pages/Insights";
import Dashboards from "./pages/Dashboards";
import DashboardView from "./pages/DashboardView";
import Admin from "./pages/Admin";

function RootRedirect() {
  const { user } = useAuth();
  return user ? <Navigate to="/" replace /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<RootRedirect />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/app" element={<Navigate to="/" replace />} />
            <Route index element={<Overview />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/ask" element={<AskAI />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/dashboards" element={<Dashboards />} />
            <Route path="/dashboards/:id" element={<DashboardView />} />
            <Route path="/admin" element={<Admin />} />
          </Route>
          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
