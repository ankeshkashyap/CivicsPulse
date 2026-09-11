import React from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { LoginForm } from "@/components/auth/LoginForm"
import { ShieldCheck, MapPin, RefreshCw } from "lucide-react"

export function LoginPage() {
  const { user, isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
      </div>
    )
  }

  // If already authenticated, redirect to destination or role-appropriate dashboard
  if (isAuthenticated && user) {
    const from = location.state?.from?.pathname || (user.role === "ADMIN" ? "/admin" : "/dashboard")
    return <Navigate to={from} replace />
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between p-4 sm:p-6">
      {/* Top Banner */}
      <header className="flex items-center justify-between max-w-5xl w-full mx-auto py-2">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-sm">
            CP
          </div>
          <div>
            <span className="font-semibold text-base tracking-tight">CivicPulse</span>
            <span className="text-xs text-muted-foreground ml-2">Vijayawada</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <MapPin className="h-3.5 w-3.5 text-primary" />
          <span>Andhra Pradesh, India</span>
        </div>
      </header>

      {/* Main Card */}
      <main className="flex-1 flex items-center justify-center py-8">
        <LoginForm />
      </main>

      {/* Footer */}
      <footer className="text-center py-4 text-xs text-muted-foreground border-t border-border max-w-5xl w-full mx-auto">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>CivicPulse &bull; Official Municipal Complaint Resolution Platform</span>
          <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            Zero-Password Cryptographic Verification
          </span>
        </div>
      </footer>
    </div>
  )
}
