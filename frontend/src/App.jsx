import React, { useState } from "react"
import { Sun, Moon, RefreshCw, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AuthProvider, useAuth } from "@/context/AuthContext"
import { LoginForm } from "@/components/auth/LoginForm"
import { UserProfileCard } from "@/components/auth/UserProfileCard"

function MainContent({ toggleTheme, isDark }) {
  const { user, isLoading, isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col transition-colors duration-150">
      <header className="border-b bg-card px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-semibold text-sm">
              CP
            </div>
            <div>
              <span className="font-semibold text-base tracking-tight">CivicPulse</span>
              <Badge variant="outline" className="ml-2 text-xs border-primary/30 text-primary">
                Phase 04: Auth & IAM
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAuthenticated && (
              <span className="text-xs text-muted-foreground mr-1 hidden sm:inline-flex items-center gap-1">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                {user.email}
              </span>
            )}
            <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-6 bg-muted/10">
        {isLoading ? (
          <div className="text-center space-y-3">
            <RefreshCw className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-xs text-muted-foreground">Checking authentication state...</p>
          </div>
        ) : isAuthenticated ? (
          <UserProfileCard />
        ) : (
          <LoginForm />
        )}
      </main>

      <footer className="border-t py-3 px-6 bg-card text-center text-xs text-muted-foreground">
        CivicPulse Vijayawada &bull; Passwordless Email-OTP & HttpOnly Session Transport &bull; Pure React (JS/JSX)
      </footer>
    </div>
  )
}

function App() {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle("dark")
  }

  return (
    <AuthProvider>
      <MainContent toggleTheme={toggleTheme} isDark={isDark} />
    </AuthProvider>
  )
}

export default App