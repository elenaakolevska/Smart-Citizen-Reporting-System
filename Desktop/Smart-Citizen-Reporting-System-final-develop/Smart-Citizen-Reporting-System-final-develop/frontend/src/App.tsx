import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { RoleProvider, useRole } from "@/context/RoleContext";
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      {/* Shared routes for all authenticated users */}
      <Route path="/public-map" element={<PublicMapPage />} />

      {role === "citizen" && (
        <>
          <Route path="/" element={<HomePage />} />
          <Route path="/my-complaints" element={<MyComplaintsPage />} />
          <Route path="/new-complaint" element={<NewComplaintPage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
        </>
      )}

      {role === "officer" && (
        <>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assigned-complaints" element={<AssignedComplaintsPage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </>
      )}

      {role === "admin" && (
        <>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/manage-complaints" element={<ManageComplaintsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </>
      )}

      <Route path="*" element={<NotFound />} />
    </Routes>
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
