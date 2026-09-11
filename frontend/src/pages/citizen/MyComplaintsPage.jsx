import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { FileText, Search, Filter, PlusCircle } from "lucide-react"

const STATUS_FILTERS = [
  "All",
  "Submitted",
  "Under Review",
  "Assigned",
  "In Progress",
  "Resolved",
]

export function MyComplaintsPage() {
  const [activeFilter, setActiveFilter] = useState("All")
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="space-y-6">
      <PageHeader
        tag="Complaints"
        title="My Complaints"
        description="Comprehensive audit trail and lifecycle tracking for all civic issues you have reported in Vijayawada."
        actions={
          <Button size="sm" className="gap-1.5" disabled>
            <PlusCircle className="h-4 w-4" />
            New Complaint
            <Badge variant="outline" className="ml-1 text-[10px] py-0 px-1 border-primary-foreground/40 text-primary-foreground">
              Phase 06
            </Badge>
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-2">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status}
              onClick={() => setActiveFilter(status)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-ring ${
                activeFilter === status
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by title, ID or ward..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 text-xs h-8"
          />
        </div>
      </div>

      {/* Complaint List Area */}
      <Card className="shadow-xs">
        <CardContent className="p-6 sm:p-10">
          <EmptyState
            icon={FileText}
            title={activeFilter === "All" ? "No civic complaints filed" : `No complaints with status "${activeFilter}"`}
            description="You have not submitted any complaints yet. When you submit a report with location verification, municipal administrators review, assign, and post verified updates here."
            badgeText="0 Records"
          />
        </CardContent>
      </Card>
    </div>
  )
}
