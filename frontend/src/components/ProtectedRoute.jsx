import React from "react"
import { Navigate, useLocation, Link, Outlet } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { RefreshCw, ShieldAlert, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ProtectedRoute({ children, requiredRole }) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground">Verifying municipal session...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center space-y-3 max-w-md mx-auto my-12">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-1">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">Administrative Privileges Required</h2>
        <p className="text-xs text-muted-foreground leading-relaxed">
          The requested section requires administrative authorization. Your active account ({user.email}) has the <span className="font-semibold text-foreground">{user.role}</span> role.
        </p>
        <div className="pt-2">
          <Button asChild variant="outline" size="sm">
            <Link to="/dashboard">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
              Return to Citizen Dashboard
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return children || <Outlet />
}
