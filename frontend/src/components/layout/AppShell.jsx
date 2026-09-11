import * as React from "react"
import { Outlet } from "react-router-dom"
import { Header } from "@/components/navigation/Header"
import { Sidebar } from "@/components/navigation/Sidebar"
import { useAuth } from "@/context/AuthContext"

export function AppShell({ children }) {
  const { user } = useAuth()
  const [mobileOpen, setMobileOpen] = React.useState(false)

  const toggleMobileSidebar = () => {
    setMobileOpen((prev) => !prev)
  }

  const closeMobileSidebar = () => {
    setMobileOpen(false)
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col transition-colors duration-150">
      {/* Top Application Header */}
      <Header onToggleMobileSidebar={toggleMobileSidebar} />

      {/* Main Workspace: Sidebar + Content */}
      <div className="flex flex-1 items-start">
        {/* Role-Appropriate Sidebar */}
        <Sidebar
          role={user?.role || "CITIZEN"}
          mobileOpen={mobileOpen}
          onCloseMobile={closeMobileSidebar}
        />

        {/* Dynamic Main Content Container */}
        <main
          role="main"
          className="flex-1 w-full min-w-0 px-4 py-6 sm:px-6 sm:py-8 lg:px-8 max-w-7xl mx-auto"
        >
          {children || <Outlet />}
        </main>
      </div>

      {/* Municipal Civic System Footer */}
      <footer className="border-t border-border bg-surface py-3 px-6 text-center text-xs text-muted-foreground">
        CivicPulse &bull; Vijayawada Municipal Corporation &bull; Municipal Civic Resolution System
      </footer>
    </div>
  )
}
