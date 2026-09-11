import React from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import { ThemeProvider } from "@/context/ThemeContext"
import { AuthProvider, useAuth } from "@/context/AuthContext"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { AppShell } from "@/components/layout/AppShell"
import { RefreshCw } from "lucide-react"

// Auth Pages
import { LoginPage } from "@/pages/auth/LoginPage"

// Citizen Pages
import { DashboardPage as CitizenDashboardPage } from "@/pages/citizen/DashboardPage"
import { MyComplaintsPage } from "@/pages/citizen/MyComplaintsPage"
import { NewComplaintPage } from "@/pages/citizen/NewComplaintPage"
import { ComplaintDetailPage } from "@/pages/citizen/ComplaintDetailPage"
import { CommunityPage } from "@/pages/citizen/CommunityPage"
import { NotificationsPage } from "@/pages/citizen/NotificationsPage"
import { ProfilePage as CitizenProfilePage } from "@/pages/citizen/ProfilePage"

// Admin Pages
import { AdminDashboardPage } from "@/pages/admin/AdminDashboardPage"
import { AdminComplaintsPage } from "@/pages/admin/AdminComplaintsPage"
import { AdminComplaintDetailPage } from "@/pages/admin/AdminComplaintDetailPage"
import { AdminMapPage } from "@/pages/admin/AdminMapPage"
import { AdminAnalyticsPage } from "@/pages/admin/AdminAnalyticsPage"
import { AdminDepartmentsPage } from "@/pages/admin/AdminDepartmentsPage"
import { AdminUsersPage } from "@/pages/admin/AdminUsersPage"
import { AdminProfilePage } from "@/pages/admin/AdminProfilePage"

function RootRedirect() {
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-3 bg-background">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground">Verifying civic session...</span>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  return <Navigate to={user.role === "ADMIN" ? "/admin" : "/dashboard"} replace />
}

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Root Redirect */}
          <Route path="/" element={<RootRedirect />} />

          {/* Citizen Protected Routes */}
          <Route
            element={
              <ProtectedRoute requiredRole="CITIZEN">
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<CitizenDashboardPage />} />
            <Route path="/complaints" element={<MyComplaintsPage />} />
            <Route path="/complaints/new" element={<NewComplaintPage />} />
            <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
            <Route path="/community" element={<CommunityPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/profile" element={<CitizenProfilePage />} />
          </Route>

          {/* Admin Protected Routes */}
          <Route
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/complaints" element={<AdminComplaintsPage />} />
            <Route path="/admin/complaints/:id" element={<AdminComplaintDetailPage />} />
            <Route path="/admin/map" element={<AdminMapPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/departments" element={<AdminDepartmentsPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/profile" element={<AdminProfilePage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App