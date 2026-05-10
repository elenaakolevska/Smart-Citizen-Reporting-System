import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { RoleProvider, useRole } from "@/context/RoleContext";
import { AppLayout } from "@/components/AppLayout";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import MyComplaintsPage from "./pages/MyComplaintsPage";
import NewComplaintPage from "./pages/NewComplaintPage";
import ComplaintDetailPage from "./pages/ComplaintDetailPage";
import DashboardPage from "./pages/DashboardPage";
import AssignedComplaintsPage from "./pages/AssignedComplaintsPage";
import ManageComplaintsPage from "./pages/ManageComplaintsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import PublicMapPage from "./pages/PublicMapPage";
import SettingsPage from "./pages/SettingsPage";
import ServerError from "./pages/ServerError";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function AppRoutes() {
  const { role, isLoggedIn, isAuthLoading } = useRole();

  if (isAuthLoading) {
    return <div className="min-h-screen grid place-items-center text-muted-foreground">Loading...</div>;
  }

  if (!isLoggedIn) {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage mode="login" />} />
        <Route path="/register" element={<LoginPage mode="register" />} />
        <Route path="/error" element={<ServerError />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  return (
    <AppLayout>
      <Routes>
        {/* Shared routes for all authenticated users */}
        <Route path="/public-map" element={<PublicMapPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/error" element={<ServerError />} />

        {role === "citizen" && (
          <>
            <Route path="/" element={<HomePage />} />
            <Route path="/my-complaints" element={<MyComplaintsPage />} />
            <Route path="/new-complaint" element={<NewComplaintPage />} />
            <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
          </>
        )}

        {/* Officer/admin land on the dashboard at "/" directly. Avoid <Navigate>
            redirects here — the role briefly resolves from the Supabase JWT
            before the backend call lands, so a redirect can fire under a stale
            JWT claim and strand a citizen on /dashboard with NotFound. */}
        {role === "officer" && (
          <>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/assigned-complaints" element={<AssignedComplaintsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
          </>
        )}

        {role === "admin" && (
          <>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/manage-complaints" element={<ManageComplaintsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
          </>
        )}

        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppLayout>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <RoleProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </RoleProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
