import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { User, ShieldCheck, Mail, MapPin, Calendar, LogOut, RefreshCw, KeyRound } from "lucide-react"

export function ProfilePage() {
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
      <PageHeader
        tag="Account"
        title="Citizen Profile"
        description="Your verified civic identity, authentication session, and municipal service jurisdiction."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Profile Snapshot */}
        <Card className="shadow-xs md:col-span-1">
          <CardContent className="p-6 flex flex-col items-center text-center space-y-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xl border-2 border-primary/20">
              {user.email.slice(0, 2).toUpperCase()}
            </div>
            <div className="space-y-0.5">
              <h3 className="text-sm font-semibold text-foreground">
                {user.full_name || "Civic Citizen"}
              </h3>
              <p className="text-xs text-muted-foreground break-all">{user.email}</p>
            </div>
            <div className="flex flex-wrap gap-1.5 justify-center pt-1">
              <Badge variant="secondary" className="text-[11px]">
                {user.role}
              </Badge>
              {user.is_verified && (
                <Badge variant="outline" className="text-[11px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  Verified
                </Badge>
              )}
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
                  Sign Out
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        {/* Right Column: Detailed Jurisdictional & Security Info */}
        <div className="space-y-6 md:col-span-2">
          {/* Municipal Jurisdiction Card */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" />
                Municipal Jurisdiction
              </CardTitle>
              <CardDescription className="text-xs">
                Your civic reports are routed to the corresponding municipal administrative zones
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-md bg-muted/30 border border-border/60">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Demonstration City:</span>
                  <span className="font-medium text-foreground">Vijayawada</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Corporation:</span>
                  <span className="font-medium text-foreground">VMC (Vijayawada Municipal Corp)</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">State / Country:</span>
                  <span className="font-medium text-foreground">Andhra Pradesh, India</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Account Created:</span>
                  <span className="font-medium text-foreground">{joinedDate}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Security & Authentication Protocol Card */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-primary" />
                Authentication Security
              </CardTitle>
              <CardDescription className="text-xs">
                Zero-password architecture protected by cryptographic OTP and HttpOnly sessions
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-2 text-xs">
              <div className="space-y-2 text-muted-foreground">
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Authentication Method:</span>
                  <span className="font-medium text-foreground">Passwordless Email-OTP (Argon2id)</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Session Storage:</span>
                  <span className="font-medium text-foreground">HttpOnly, SameSite=Lax Cookie</span>
                </div>
                <div className="flex items-center justify-between border-b border-border/50 py-1.5">
                  <span>Account Status:</span>
                  <span className="font-medium text-emerald-600 dark:text-emerald-400">Active & Verified</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span>User Identifier:</span>
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
