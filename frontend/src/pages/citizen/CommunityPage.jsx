import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { Users, Search, MapPin, ArrowUpDown } from "lucide-react"

const CATEGORIES = [
  "All Categories",
  "Roads & Potholes",
  "Streetlights",
  "Garbage & Sanitation",
  "Drainage",
  "Water Supply",
  "Public Safety",
]

export function CommunityPage() {
  const [selectedCategory, setSelectedCategory] = useState("All Categories")
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="space-y-6">
      <PageHeader
        tag="Community"
        title="Community Complaints"
        description="Explore civic issues submitted by residents across Vijayawada. Upvote community problems to help administrators prioritize urgent municipal repairs."
      />

      {/* Filter and Category Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-ring ${
                selectedCategory === cat
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search Vijayawada issues..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 text-xs h-8"
          />
        </div>
      </div>

      {/* Community Feed Area */}
      <Card className="shadow-xs">
        <CardContent className="p-6 sm:p-10">
          <EmptyState
            icon={Users}
            title="No community reports published yet"
            description="Verified civic complaints submitted by citizens in Vijayawada will appear in this public feed once reporting opens in Phase 06. Upvoting will allow the community to prioritize urgent repairs."
            badgeText="Vijayawada Municipal Feed"
          />
        </CardContent>
      </Card>
    </div>
  )
}
