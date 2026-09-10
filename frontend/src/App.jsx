import { useState } from "react"
import { Sun, Moon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

function App() {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle("dark")
  }

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
                Foundation
              </Badge>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-6">
        <div className="text-center space-y-3 max-w-md">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary mb-2">
            <span className="text-lg font-bold">CP</span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            CivicPulse Web Foundation
          </h1>
          <p className="text-sm text-muted-foreground">
            Frontend development environment active. Built with React, Vite, JavaScript, Tailwind CSS, and shadcn/ui.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App