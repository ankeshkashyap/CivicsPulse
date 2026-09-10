import React from "react"
import { useAuth } from "@/context/AuthContext"
import { RefreshCw, ShieldAlert } from "lucide-react"

export function ProtectedRoute({ children, requiredRole }) {
  const { user, isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
        <span className="text-xs text-muted-foreground">Checking authentication session...</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center space-y-2 max-w-sm mx-auto">
        <ShieldAlert className="h-8 w-8 text-muted-foreground mb-1" />
        <h3 className="text-sm font-semibold">Authentication Required</h3>
        <p className="text-xs text-muted-foreground">
          Please sign in with your email address to access this area.
        </p>
      </div>
    )
  }

  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center space-y-2 max-w-sm mx-auto">
        <ShieldAlert className="h-8 w-8 text-destructive mb-1" />
        <h3 className="text-sm font-semibold text-destructive">Access Restricted</h3>
        <p className="text-xs text-muted-foreground">
          This section requires the {requiredRole} role. Your current role is {user.role}.
        </p>
      </div>
    )
  }

  return children
}
