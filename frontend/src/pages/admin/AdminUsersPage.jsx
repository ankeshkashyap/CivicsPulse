import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { useAuth } from "@/context/AuthContext"
import {
  Users,
  Search,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  Lock,
  Mail,
  Calendar,
} from "lucide-react"

export function AdminUsersPage() {
  const { user } = useAuth()
  const [roleFilter, setRoleFilter] = useState("All")
  const [searchQuery, setSearchQuery] = useState("")

  const activeUser = user || {
    id: "usr_active_admin",
    email: "admin@civicpulse.org",
    role: "ADMIN",
    full_name: "Municipal Administrator",
    is_verified: true,
    is_active: true,
    created_at: new Date().toISOString(),
  }

  // Filter matching
  const matchesRole = roleFilter === "All" || activeUser.role === roleFilter
  const matchesSearch =
    !searchQuery ||
    activeUser.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (activeUser.full_name && activeUser.full_name.toLowerCase().includes(searchQuery.toLowerCase()))

  const showActiveUser = matchesRole && matchesSearch

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Identity & Access Management"
        title="Municipal IAM & User Directory"
        description="Oversee citizen accounts, administrative privileges, cryptographic OTP authentication history, and municipal role assignments."
        actions={
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-xs border-primary/30 text-primary">
              RBAC Enforced
            </Badge>
            <Badge variant="secondary" className="text-xs">
              Passwordless IAM
            </Badge>
          </div>
        }
      />

      {/* KPI Overview Pills */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Active Users</span>
            <span className="text-lg font-bold text-foreground">1</span>
          </div>
          <Users className="h-4 w-4 text-primary" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Administrators</span>
            <span className="text-lg font-bold text-primary">1</span>
          </div>
          <UserCheck className="h-4 w-4 text-primary" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Verified Citizens</span>
            <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">0</span>
          </div>
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
        </div>
        <div className="rounded-lg border border-border bg-card p-3.5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground block">Auth Method</span>
            <span className="text-xs font-semibold text-foreground">Email OTP</span>
          </div>
          <Lock className="h-4 w-4 text-muted-foreground" />
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          {["All", "CITIZEN", "ADMIN"].map((role) => (
            <button
              key={role}
              type="button"
              onClick={() => setRoleFilter(role)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                roleFilter === role
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {role === "All" ? "All Roles" : role}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by email, name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 text-xs h-8"
          />
        </div>
      </div>

      {/* Users Table / Directory Card */}
      <Card className="shadow-xs overflow-hidden">
        {showActiveUser ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground font-medium">
                  <th className="p-3.5 pl-5">User</th>
                  <th className="p-3.5">Role</th>
                  <th className="p-3.5">Jurisdiction</th>
                  <th className="p-3.5">Verification</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 pr-5 text-right">User ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                <tr className="hover:bg-muted/10 transition-colors">
                  <td className="p-3.5 pl-5">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs">
                        {activeUser.email.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-medium text-foreground">
                          {activeUser.full_name || "Municipal Administrator"}
                        </div>
                        <div className="text-[11px] text-muted-foreground flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {activeUser.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3.5">
                    <Badge variant={activeUser.role === "ADMIN" ? "default" : "secondary"} className="text-[10px]">
                      {activeUser.role}
                    </Badge>
                  </td>
                  <td className="p-3.5 text-muted-foreground">
                    Vijayawada (VMC)
                  </td>
                  <td className="p-3.5">
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Verified
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      Active
                    </span>
                  </td>
                  <td className="p-3.5 pr-5 text-right font-mono text-[11px] text-muted-foreground">
                    {activeUser.id ? String(activeUser.id).slice(0, 8) + "..." : "usr_active"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <CardContent className="p-8">
            <EmptyState
              icon={Users}
              title="No users match search criteria"
              description="Adjust your role filter or search term to view registered municipal accounts."
              badgeText="Directory Filtered"
            />
          </CardContent>
        )}
      </Card>
    </div>
  )
}
