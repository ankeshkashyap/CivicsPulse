import * as React from "react"
import { Link, useNavigate } from "react-router-dom"
import {
  Menu,
  Sun,
  Moon,
  LogOut,
  User as UserIcon,
  Shield,
  ShieldCheck,
  RefreshCw,
  ChevronDown,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"

export function Header({ onToggleMobileSidebar }) {
  const { user, logout, isLoggingOut } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const isAdmin = user?.role === "ADMIN"

  const handleLogout = async () => {
    try {
      await logout()
      navigate("/login")
    } catch (err) {
      console.error("Logout failed:", err)
    }
  }

  return (
    <header className="sticky top-0 z-40 h-14 border-b border-border bg-surface/95 backdrop-blur-xs">
      <div className="flex h-full items-center justify-between px-4 sm:px-6">
        {/* Left: Hamburger & Brand */}
        <div className="flex items-center gap-3">
          {/* Mobile Sidebar Toggle Button */}
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring lg:hidden"
            aria-label="Open navigation sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Logo & Brand Name */}
          <Link
            to={isAdmin ? "/admin" : "/dashboard"}
            className="flex items-center gap-2.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs tracking-tight shadow-xs">
              CP
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-base tracking-tight text-foreground">
                CivicPulse
              </span>
              <span className="hidden sm:inline-flex text-[11px] font-normal text-muted-foreground">
                /
              </span>
              <span className="hidden sm:inline-flex text-xs text-muted-foreground font-medium">
                Vijayawada
              </span>
            </div>
          </Link>
        </div>

        {/* Right: Theme Toggle & User Menu */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* User Account Dropdown */}
          {user && (
            <DropdownMenu>
              {({ open, setOpen }) => (
                <>
                  <DropdownMenuTrigger
                    onClick={() => setOpen(!open)}
                    className="flex cursor-pointer items-center gap-2 rounded-md p-1.5 text-left transition-colors hover:bg-muted/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    role="button"
                    aria-expanded={open}
                    aria-label="Open user account menu"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-xs border border-primary/20">
                      {isAdmin ? <Shield className="h-3.5 w-3.5" /> : <UserIcon className="h-3.5 w-3.5" />}
                    </div>
                    <div className="hidden md:flex flex-col text-left leading-tight">
                      <span className="text-xs font-medium text-foreground truncate max-w-[130px]">
                        {user.full_name || user.email.split("@")[0]}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {user.role}
                      </span>
                    </div>
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground hidden sm:block" />
                  </DropdownMenuTrigger>

                  <DropdownMenuContent open={open} align="right" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-0.5">
                        <span className="text-xs font-semibold text-foreground truncate">
                          {user.full_name || "Civic Citizen"}
                        </span>
                        <span className="text-[11px] text-muted-foreground truncate">
                          {user.email}
                        </span>
                        <div className="pt-1 flex items-center gap-1">
                          <Badge variant={isAdmin ? "default" : "secondary"} className="text-[10px] py-0 px-1.5 h-4">
                            {user.role}
                          </Badge>
                          {user.is_verified && (
                            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5 font-medium">
                              <ShieldCheck className="h-3 w-3" />
                              Verified
                            </span>
                          )}
                        </div>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />

                    <DropdownMenuItem
                      onClick={() => {
                        setOpen(false)
                        navigate(isAdmin ? "/admin/profile" : "/profile")
                      }}
                    >
                      <UserIcon className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                      View Profile & Account
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      onClick={() => {
                        toggleTheme()
                      }}
                    >
                      {isDark ? (
                        <Sun className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                      ) : (
                        <Moon className="mr-2 h-3.5 w-3.5 text-muted-foreground" />
                      )}
                      Switch to {isDark ? "Light" : "Dark"} Mode
                    </DropdownMenuItem>

                    <DropdownMenuSeparator />

                    <DropdownMenuItem
                      onClick={() => {
                        setOpen(false)
                        handleLogout()
                      }}
                      disabled={isLoggingOut}
                      className="text-destructive hover:bg-destructive/10 focus:bg-destructive/10 focus:text-destructive"
                    >
                      {isLoggingOut ? (
                        <>
                          <RefreshCw className="mr-2 h-3.5 w-3.5 animate-spin" />
                          Logging out...
                        </>
                      ) : (
                        <>
                          <LogOut className="mr-2 h-3.5 w-3.5" />
                          Log Out
                        </>
                      )}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </>
              )}
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  )
}
