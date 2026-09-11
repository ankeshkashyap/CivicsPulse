import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { getAdminComplaints, getAdminDepartments } from "@/lib/api"
import {
  ClipboardList,
  Search,
  CheckCircle,
  AlertTriangle,
  Clock,
  Building2,
  TrendingUp,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Filter,
} from "lucide-react"

const STATUS_TABS = [
  { label: "All", value: "ALL" },
  { label: "Submitted", value: "SUBMITTED" },
  { label: "Under Review", value: "UNDER_REVIEW" },
  { label: "Assigned", value: "ASSIGNED" },
  { label: "In Progress", value: "IN_PROGRESS" },
  { label: "Resolved", value: "RESOLVED" },
  { label: "Rejected", value: "REJECTED" },
]

const SEVERITY_OPTIONS = [
  { label: "All Severities", value: "ALL" },
  { label: "Low Severity", value: "LOW" },
  { label: "Medium Severity", value: "MEDIUM" },
  { label: "High Severity", value: "HIGH" },
]

const CATEGORY_OPTIONS = [
  { label: "All Categories", value: "ALL" },
  { label: "Roads & Potholes", value: "ROADS" },
  { label: "Streetlights", value: "STREETLIGHTS" },
  { label: "Garbage & Sanitation", value: "GARBAGE" },
  { label: "Drainage", value: "DRAINAGE" },
  { label: "Water Supply", value: "WATER" },
  { label: "Sewerage", value: "SEWERAGE" },
  { label: "Traffic & Signals", value: "TRAFFIC" },
  { label: "Public Safety", value: "PUBLIC_SAFETY" },
  { label: "Parks & Recreation", value: "PARKS" },
  { label: "Other", value: "OTHER" },
]

const PAGE_SIZE = 20

export function AdminComplaintsPage() {
  const [activeStatus, setActiveStatus] = useState("ALL")
  const [activeSeverity, setActiveSeverity] = useState("ALL")
  const [activeCategory, setActiveCategory] = useState("ALL")
  const [activeDept, setActiveDept] = useState("ALL")
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")

  const [departments, setDepartments] = useState([])
  const [complaints, setComplaints] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState(null)

  // Load departments for filtering
  useEffect(() => {
    async function loadDepts() {
      try {
        const data = await getAdminDepartments()
        if (Array.isArray(data)) {
          setDepartments(data)
        }
      } catch (err) {
        console.error("Failed to load departments:", err)
      }
    }
    loadDepts()
  }, [])

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Reset page when filters change
  function handleStatusChange(status) {
    setActiveStatus(status)
    setPage(1)
  }

  function handleSeverityChange(severity) {
    setActiveSeverity(severity)
    setPage(1)
  }

  function handleCategoryChange(category) {
    setActiveCategory(category)
    setPage(1)
  }

  function handleDeptChange(deptId) {
    setActiveDept(deptId)
    setPage(1)
  }

  // Fetch complaints
  async function loadComplaints(isManual = false) {
    if (isManual) setIsRefreshing(true)
    else setIsLoading(true)
    setError(null)

    try {
      const offset = (page - 1) * PAGE_SIZE
      const res = await getAdminComplaints({
        search: debouncedSearch.trim() || undefined,
        status: activeStatus !== "ALL" ? activeStatus : undefined,
        severity: activeSeverity !== "ALL" ? activeSeverity : undefined,
        category: activeCategory !== "ALL" ? activeCategory : undefined,
        department_id: activeDept !== "ALL" ? activeDept : undefined,
        limit: PAGE_SIZE,
        offset,
      })

      setComplaints(res.items || [])
      setTotalCount(res.total || 0)
    } catch (err) {
      console.error("Failed to fetch complaints:", err)
      setError(err.message || "Failed to load triage queue")
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadComplaints()
  }, [debouncedSearch, activeStatus, activeSeverity, activeCategory, activeDept, page])

  const totalPages = Math.ceil(totalCount / PAGE_SIZE) || 1

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Triage & Dispatch"
        title="Civic Complaints Management"
        description="Review, prioritize, assign, and oversee the resolution lifecycle for citizen-reported civic issues."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadComplaints(true)}
              disabled={isLoading || isRefreshing}
              className="text-xs h-8 gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </Button>
            <Badge variant="secondary" className="text-xs font-mono">
              {totalCount} Total Cases
            </Badge>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </div>
      )}

      {/* Filter Bar */}
      <div className="space-y-3">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => handleStatusChange(tab.value)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-ring ${
                activeStatus === tab.value
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Secondary Filter Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {/* Category Select */}
            <select
              value={activeCategory}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Filter by category"
            >
              {CATEGORY_OPTIONS.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>

            {/* Severity Select */}
            <select
              value={activeSeverity}
              onChange={(e) => handleSeverityChange(e.target.value)}
              className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Filter by severity"
            >
              {SEVERITY_OPTIONS.map((sev) => (
                <option key={sev.value} value={sev.value}>
                  {sev.label}
                </option>
              ))}
            </select>

            {/* Department Select */}
            <select
              value={activeDept}
              onChange={(e) => handleDeptChange(e.target.value)}
              className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Filter by department"
            >
              <option value="ALL">All Departments</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search ID, title, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-8"
            />
          </div>
        </div>
      </div>

      {/* Main Complaint Table / Queue Area */}
      <Card className="shadow-xs overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full rounded" />
              ))}
            </div>
          ) : complaints.length === 0 ? (
            <div className="p-10">
              <EmptyState
                icon={ClipboardList}
                title={
                  activeStatus === "ALL" && !debouncedSearch
                    ? "No complaints currently in triage"
                    : "No complaints found matching current filters"
                }
                description="Try adjusting your search criteria, severity selection, or status filter to locate relevant citizen reports."
                badgeText="Triage Queue Clear"
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/40 text-muted-foreground font-medium">
                    <th className="py-3 px-4">Priority & ID</th>
                    <th className="py-3 px-4">Title & Category</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Assigned Dept</th>
                    <th className="py-3 px-4">Progress</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {complaints.map((c) => (
                    <tr
                      key={c.id}
                      className="hover:bg-muted/30 transition-colors group"
                    >
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 font-mono font-bold text-primary bg-primary/10 px-2 py-0.5 rounded text-[11px]">
                            <TrendingUp className="h-3 w-3" />
                            {c.priority_score}
                          </span>
                          <span className="font-mono text-[11px] text-muted-foreground">
                            #{c.id.slice(0, 8)}
                          </span>
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">
                          {c.upvote_count} upvotes
                        </div>
                      </td>

                      <td className="py-3 px-4 max-w-xs">
                        <Link
                          to={`/admin/complaints/${c.id}`}
                          className="font-medium text-foreground hover:text-primary transition-colors line-clamp-1 group-hover:underline"
                        >
                          {c.title}
                        </Link>
                        <div className="text-[11px] text-muted-foreground mt-0.5 capitalize">
                          {c.category.toLowerCase().replace(/_/g, " ")}
                        </div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <ComplaintSeverityBadge severity={c.severity} />
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <ComplaintStatusBadge status={c.status} />
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        {c.assigned_department_name ? (
                          <span className="inline-flex items-center gap-1 text-foreground font-medium">
                            <Building2 className="h-3 w-3 text-muted-foreground" />
                            {c.assigned_department_name}
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Unassigned</span>
                        )}
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${c.progress_percentage}%` }}
                            />
                          </div>
                          <span className="text-[11px] text-muted-foreground font-mono">
                            {c.progress_percentage}%
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap text-right">
                        <Link
                          to={`/admin/complaints/${c.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {totalCount > PAGE_SIZE && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20">
              <div className="text-xs text-muted-foreground">
                Showing <span className="font-medium">{(page - 1) * PAGE_SIZE + 1}</span> to{" "}
                <span className="font-medium">
                  {Math.min(page * PAGE_SIZE, totalCount)}
                </span>{" "}
                of <span className="font-medium">{totalCount}</span> complaints
              </div>

              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || isLoading}
                  className="h-8 w-8 p-0"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground px-2">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || isLoading}
                  className="h-8 w-8 p-0"
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

