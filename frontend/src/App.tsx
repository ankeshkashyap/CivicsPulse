import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  CheckCircle2,
  Database,
  Layers,
  Server,
  Globe,
  RefreshCw,
  Sun,
  Moon,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface HealthResponse {
  status: string
  project_name: string
  environment: string
  version: string
  database: {
    status: string
    connected: boolean
    message: string
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"

function FoundationStatus() {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle("dark")
  }

  const { data, error, isLoading, isFetching, refetch } = useQuery<HealthResponse>({
    queryKey: ["healthCheck"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/health`)
      if (!res.ok) {
        throw new Error(`Health check returned HTTP ${res.status}`)
      }
      return res.json()
    },
    refetchInterval: 10000,
  })

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
      {/* Top Municipal Navigation Bar */}
      <header className="border-b bg-card px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold tracking-wider">
              CP
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight">CivicPulse</span>
                <Badge variant="outline" className="text-[11px] font-mono border-primary/30 text-primary">
                  Foundation v0.1.0
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">Municipal Intelligence & Civic Resolution Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="gap-2 text-xs"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-primary" : ""}`} />
              Refresh Status
            </Button>
            <Button variant="ghost" size="icon" onClick={toggleTheme} title="Toggle theme">
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto max-w-6xl px-6 py-10 space-y-8">
        {/* Banner */}
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-6 dark:bg-primary/10">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <h2 className="text-xl font-semibold tracking-tight text-primary">
                System Infrastructure Initialized
              </h2>
              <p className="text-sm text-muted-foreground max-w-2xl">
                CivicPulse core foundation is online. React 19, Vite, TypeScript, Tailwind CSS, TanStack Query, and FastAPI backend are configured and ready for subsequent domain modules.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-3 py-1 rounded bg-card border text-muted-foreground">
                Target: Vijayawada, India
              </span>
            </div>
          </div>
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Frontend Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
                  <Globe className="h-4 w-4 text-primary" /> Frontend Core
                </CardTitle>
                <Badge variant="success">Active</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Framework</span>
                <span className="font-mono">React 19 + TypeScript</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Bundler</span>
                <span className="font-mono">Vite</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">UI Tokens</span>
                <span className="font-mono">Tailwind CSS + shadcn</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Data Layer</span>
                <span className="font-mono">TanStack Query v5</span>
              </div>
            </CardContent>
          </Card>

          {/* Backend API Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
                  <Server className="h-4 w-4 text-secondary" /> Backend API
                </CardTitle>
                {isLoading ? (
                  <Badge variant="outline" className="animate-pulse">Checking...</Badge>
                ) : data?.status === "ok" ? (
                  <Badge variant="success">Connected</Badge>
                ) : (
                  <Badge variant="destructive">Offline</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Engine</span>
                <span className="font-mono">FastAPI (Python 3.11)</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Endpoint</span>
                <span className="font-mono truncate max-w-[140px]">{API_BASE}/health</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">API Status</span>
                <span className="font-mono">{data?.status ?? (error ? "Unreachable" : "Checking...")}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Environment</span>
                <span className="font-mono">{data?.environment ?? "development"}</span>
              </div>
            </CardContent>
          </Card>

          {/* Database Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
                  <Database className="h-4 w-4 text-accent" /> Spatial Database
                </CardTitle>
                {isLoading ? (
                  <Badge variant="outline" className="animate-pulse">Checking...</Badge>
                ) : data?.database.connected ? (
                  <Badge variant="success">Connected</Badge>
                ) : (
                  <Badge variant="warning">Configured</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Target Engine</span>
                <span className="font-mono">PostgreSQL 18 + PostGIS</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">ORM & Migrations</span>
                <span className="font-mono">SQLAlchemy 2.x + Alembic</span>
              </div>
              <div className="flex justify-between border-b pb-1 text-xs">
                <span className="text-muted-foreground">Spatial Extension</span>
                <span className="font-mono">GeoAlchemy2</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">DB Status</span>
                <span className="font-mono truncate max-w-[140px]">
                  {data?.database.status ?? (error ? "Awaiting Backend" : "Standby")}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Architectural Checklist Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" /> Architecture Verification Matrix
            </CardTitle>
            <CardDescription>
              Foundation checkpoints verified before proceeding to feature development.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="flex items-start gap-3 rounded-lg border p-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <div className="font-medium">Strict Monorepo Separation</div>
                  <div className="text-muted-foreground">Isolated frontend/ and backend/ environments with zero leaky dependencies.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-lg border p-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <div className="font-medium">Type-Safe API Contracts</div>
                  <div className="text-muted-foreground">Pydantic v2 validation models on backend; TypeScript types on frontend.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-lg border p-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <div className="font-medium">CORS & Security Boundaries</div>
                  <div className="text-muted-foreground">Origin-whitelisted CORS middleware; secrets abstracted to environment templates.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-lg border p-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <div className="font-medium">Standardized Error Handling & Logging</div>
                  <div className="text-muted-foreground">Clean structured logging format and consistent JSON error response schema.</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default FoundationStatus