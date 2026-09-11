import * as React from "react"
import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  FileText,
  Users,
  Bell,
  User,
  ClipboardList,
  MapPin,
  BarChart3,
  Building2,
  UserCheck,
  Shield,
  X,
  MapPin as CityIcon,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const CITIZEN_LINKS = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "My Complaints", href: "/complaints", icon: FileText },
  { name: "Community", href: "/community", icon: Users },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "Profile", href: "/profile", icon: User },
]

const ADMIN_LINKS = [
  { name: "Dashboard", href: "/admin", icon: LayoutDashboard, end: true },
  { name: "Complaints", href: "/admin/complaints", icon: ClipboardList },
  { name: "City Map", href: "/admin/map", icon: MapPin },
  { name: "Analytics", href: "/admin/analytics", icon: BarChart3 },
  { name: "Departments", href: "/admin/departments", icon: Building2 },
  { name: "Users & IAM", href: "/admin/users", icon: Users },
  { name: "Admin Profile", href: "/admin/profile", icon: UserCheck },
]

export function Sidebar({ role, mobileOpen, onCloseMobile }) {
  const links = role === "ADMIN" ? ADMIN_LINKS : CITIZEN_LINKS
  const isAdmin = role === "ADMIN"

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between bg-surface border-r border-border">
      {/* Top Header & Navigation */}
      <div className="flex flex-col">
        {/* Mobile Close Button & Header */}
        <div className="flex h-14 items-center justify-between px-4 border-b border-border lg:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs">
              CP
            </div>
            <span className="font-semibold text-sm tracking-tight text-foreground">CivicPulse</span>
          </div>
          <button
            type="button"
            onClick={onCloseMobile}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Section Scope Banner */}
        <div className="px-4 py-3.5 border-b border-border/60 bg-muted/20">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium tracking-wider uppercase text-muted-foreground">
              {isAdmin ? "Admin Operations" : "Citizen Portal"}
            </span>
            <Badge variant={isAdmin ? "default" : "secondary"} className="text-[10px] py-0 px-1.5 h-4">
              {role}
            </Badge>
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-foreground/80">
            <CityIcon className="h-3 w-3 text-primary shrink-0" />
            <span className="truncate font-medium">Vijayawada Municipal Corp</span>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="space-y-1 p-3" aria-label="Sidebar navigation">
          {links.map((link) => {
            const Icon = link.icon
            return (
              <NavLink
                key={link.href}
                to={link.href}
                end={link.end}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    isActive
                      ? "bg-primary/10 text-primary font-semibold border-l-3 border-primary"
                      : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{link.name}</span>
              </NavLink>
            )
          })}
        </nav>
      </div>

      {/* Footer Details */}
      <div className="p-3 border-t border-border bg-muted/10">
        <div className="rounded-md border border-border/80 p-2.5 bg-surface text-[11px] text-muted-foreground space-y-1">
          <div className="flex items-center justify-between font-medium text-foreground">
            <span className="flex items-center gap-1">
              <Shield className="h-3 w-3 text-primary" />
              CivicPulse
            </span>
            <span className="text-[10px] text-muted-foreground">v0.3.0</span>
          </div>
          <div className="text-[10px] leading-tight text-muted-foreground/80">
            Verified Civic Infrastructure Platform
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Static Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 h-[calc(100vh-3.5rem)] sticky top-14 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-xs transition-opacity animate-in fade-in"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          {/* Drawer container */}
          <div className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] shadow-xl animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  )
}
