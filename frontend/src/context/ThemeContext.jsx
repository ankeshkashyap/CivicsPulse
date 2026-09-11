import React, { createContext, useContext, useEffect, useState } from "react"

const ThemeContext = createContext({
  theme: "light",
  isDark: false,
  toggleTheme: () => {},
  setTheme: () => {},
})

const THEME_STORAGE_KEY = "civicpulse_theme"

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(THEME_STORAGE_KEY)
      if (stored === "dark" || stored === "light") {
        return stored
      }
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark"
      }
    }
    return "light"
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === "dark") {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch {
      // Storage unavailable or disabled
    }
  }, [theme])

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"))
  }

  const setTheme = (newTheme) => {
    if (newTheme === "dark" || newTheme === "light") {
      setThemeState(newTheme)
    }
  }

  const isDark = theme === "dark"

  return (
    <ThemeContext.Provider value={{ theme, isDark, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}
