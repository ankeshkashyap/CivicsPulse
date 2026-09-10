import React, { useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User as UserIcon, Shield, CheckCircle2, LogOut, RefreshCw, Key } from "lucide-react"
import { testCitizenEndpoint, testAdminEndpoint } from "@/lib/api"

export function UserProfileCard() {
  const { user, logout, isLoggingOut } = useAuth()
  const [testResult, setTestResult] = useState(null)
  const [testingEndpoint, setTestingEndpoint] = useState(false)

  if (!user) return null

  const handleTestRoute = async (type) => {
    setTestingEndpoint(true)
    setTestResult(null)
    try {
      const res = type === "admin" ? await testAdminEndpoint() : await testCitizenEndpoint()
      setTestResult({
        success: true,
        message: res.message || "Route access granted successfully.",
      })
    } catch (err) {
      setTestResult({
        success: false,
        message: err.message || `Route access denied (${err.status || 403})`,
      })
    } finally {
      setTestingEndpoint(false)
    }
  }

  const isAdmin = user.role === "ADMIN"

  return (
    <Card className="w-full max-w-lg shadow-md border-border">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold">
              {isAdmin ? <Shield className="h-5 w-5" /> : <UserIcon className="h-5 w-5" />}
            </div>
            <div>
              <CardTitle className="text-base font-semibold">
                {user.full_name || "Civic Citizen"}
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                {user.email}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <Badge variant={isAdmin ? "default" : "secondary"} className="text-xs">
              {user.role}
            </Badge>
            {user.is_verified && (
              <Badge variant="outline" className="text-xs text-emerald-600 border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Verified
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        <div className="rounded-md border p-3 bg-muted/40 space-y-2 text-xs">
          <div className="font-medium text-foreground">Active Session Details:</div>
          <div className="grid grid-cols-2 gap-2 text-muted-foreground">
            <div>Account ID:</div>
            <div className="font-mono truncate">{user.id}</div>
            <div>Account Status:</div>
            <div className="text-emerald-600 font-medium">Active & Verified</div>
            <div>Session Storage:</div>
            <div>Secure HttpOnly Cookie</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-xs font-medium text-foreground flex items-center gap-1">
            <Key className="h-3.5 w-3.5 text-primary" />
            Backend Authorization Check:
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="text-xs flex-1"
              disabled={testingEndpoint}
              onClick={() => handleTestRoute("citizen")}
            >
              Test Citizen Route
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-xs flex-1"
              disabled={testingEndpoint}
              onClick={() => handleTestRoute("admin")}
            >
              Test Admin Route
            </Button>
          </div>

          {testResult && (
            <div
              className={`p-2.5 rounded-md text-xs border ${
                testResult.success
                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30"
                  : "bg-destructive/10 text-destructive border-destructive/30"
              }`}
            >
              <span className="font-semibold">{testResult.success ? "Passed: " : "Access Denied: "}</span>
              {testResult.message}
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex justify-between border-t px-6 py-3 bg-muted/20">
        <span className="text-xs text-muted-foreground">CivicPulse Auth Foundation</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => logout()}
          disabled={isLoggingOut}
          className="text-destructive hover:text-destructive hover:bg-destructive/10 text-xs"
        >
          {isLoggingOut ? (
            <>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              Logging out...
            </>
          ) : (
            <>
              <LogOut className="mr-1.5 h-3.5 w-3.5" />
              Log Out
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
