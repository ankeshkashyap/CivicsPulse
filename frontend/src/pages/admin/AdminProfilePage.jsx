import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import {
  UserCheck,
  ShieldAlert,
  ShieldCheck,
  KeyRound,
  Lock,
  Building,
  LogOut,
  RefreshCw,
  CheckCircle2,
  FileCheck,
} from "lucide-react"

const ADMIN_PRIVILEGES = [
  { name: "Complaint Triage & Review", desc: "Inspect and validate citizen submissions", granted: true },
  { name: "Department Assignment", desc: "Dispatch complaints to PWD, Sanitation, Drainage, Water", granted: true },
  { name: "Lifecycle State Transition", desc: "Move complaints through Under Review -> Assigned -> Resolved", granted: true },
  { name: "Priority Score Overrides", desc: "Adjust urgency ranking based on ground inspection", granted: true },
  { name: "Spatial & Analytics Oversight", desc: "Access ward maps, density clusters, and resolution SLAs", granted: true },
  { name: "Municipal IAM & User Directory", desc: "Inspect citizen profiles and verify municipal operators", granted: true },
]

export function AdminProfilePage() {
  const { user, logout, isLoggingOut } = useAuth()

  if (!user) return null

  const joinedDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "Active Session"

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page Header */}
      <PageHeader
        tag="Administrative Identity"
        title="Administrator Profile & Security"
        description="Municipal operator credentials, administrative authorization privileges, and active session audit metadata."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Administrator Profile Card */}
        <Card className="shadow-xs md:col-span-1">
          <CardContent className="p-6 flex flex-col items-center text-center space-y-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-xl ring-4 ring-primary/20">
              {user.email.slice(0, 2).toUpperCase()}
            </div>
            <div className="space-y-0.5">
              <h3 className="text-sm font-semibold text-foreground">
                {user.full_name || "Municipal Administrator"}
              </h3>
              <p className="text-xs text-muted-foreground break-all">{user.email}</p>
            </div>
            <div className="flex flex-wrap gap-1.5 justify-center pt-1">
              <Badge variant="default" className="text-[11px]">
                {user.role}
              </Badge>
              <Badge variant="outline" className="text-[11px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" />
                VMC Operator
              </Badge>
            </div>
          </CardContent>
          <CardFooter className="p-4 border-t border-border bg-muted/20 justify-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => logout()}
              disabled={isLoggingOut}
              className="text-destructive hover:text-destructive hover:bg-destructive/10 w-full text-xs"
            >
              {isLoggingOut ? (
                <>
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                  Signing out...
                </>
              ) : (
                <>
                  <LogOut className="mr-1.5 h-3.5 w-3.5" />
                  Sign Out of Console
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        {/* Right Column: Privileges & Security Details */}
        <div className="space-y-6 md:col-span-2">
          {/* RBAC Privileges Card */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-primary" />
                Administrative RBAC Privileges
              </CardTitle>
              <CardDescription className="text-xs">
                Authorization scope granted to this municipal administrative account
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-2">
              <div className="grid grid-cols-1 gap-2">
                {ADMIN_PRIVILEGES.map((priv) => (
                  <div
                    key={priv.name}
                    className="flex items-start justify-between p-2.5 rounded-md border border-border/70 bg-surface text-xs"
                  >
                    <div>
                      <div className="font-medium text-foreground flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        {priv.name}
                      </div>
                      <div className="text-[11px] text-muted-foreground pl-5">{priv.desc}</div>
                    </div>
                    <Badge variant="outline" className="text-[10px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shrink-0">
                      Granted
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Session Security Details Card */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-primary" />
                Session Security & Cryptography
              </CardTitle>
              <CardDescription className="text-xs">
                Backend-enforced token safety and zero-password authentication parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-2 text-xs">
              <div className="space-y-2 text-muted-foreground">
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Transport Security:</span>
                  <span className="font-medium text-foreground">HttpOnly, SameSite=Lax Cookie</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Token Specification:</span>
                  <span className="font-medium text-foreground">HMAC-SHA256 JWT (backend-verified)</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Municipal Jurisdiction:</span>
                  <span className="font-medium text-foreground">Vijayawada Municipal Corporation</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Member Since:</span>
                  <span className="font-medium text-foreground">{joinedDate}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span>Administrator ID:</span>
                  <span className="font-mono text-[11px] text-foreground truncate max-w-[200px]">{user.id}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
