import React, { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { ComplaintProgressTimeline } from "@/components/complaints/ComplaintProgressTimeline"
import {
  getAdminComplaint,
  getAdminDepartments,
  transitionAdminComplaintStatus,
  updateAdminComplaintSeverity,
  assignAdminComplaintDepartment,
  addAdminComplaintRemark,
} from "@/lib/api"
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Building2,
  TrendingUp,
  User,
  Mail,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  FileText,
  Sliders,
  Send,
  MessageSquare,
  Sparkles,
} from "lucide-react"

// Finite State Machine allowed next steps
const VALID_NEXT_STATUSES = {
  SUBMITTED: [
    { value: "UNDER_REVIEW", label: "Mark Under Review" },
  ],
  UNDER_REVIEW: [
    { value: "ASSIGNED", label: "Assign to Department" },
    { value: "REJECTED", label: "Reject Complaint" },
  ],
  ASSIGNED: [
    { value: "IN_PROGRESS", label: "Mark In Progress" },
  ],
  IN_PROGRESS: [
    { value: "RESOLVED", label: "Mark Resolved" },
  ],
  RESOLVED: [],
  REJECTED: [],
}

const SEVERITY_WEIGHTS = {
  LOW: 10,
  MEDIUM: 25,
  HIGH: 50,
}

export function AdminComplaintDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [complaint, setComplaint] = useState(null)
  const [departments, setDepartments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedPhoto, setSelectedPhoto] = useState(null)

  // Status transition form state
  const [targetStatus, setTargetStatus] = useState("")
  const [statusDeptId, setStatusDeptId] = useState("")
  const [statusRemark, setStatusRemark] = useState("")

  // Severity form state
  const [targetSeverity, setTargetSeverity] = useState("")
  const [severityRemark, setSeverityRemark] = useState("")

  // Department assignment form state
  const [targetDeptId, setTargetDeptId] = useState("")
  const [deptRemark, setDeptRemark] = useState("")

  // Progress remark form state
  const [progressRemark, setProgressRemark] = useState("")

  async function loadData() {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getAdminComplaint(id)
      setComplaint(data)
      setTargetSeverity(data.severity)
      setTargetDeptId(data.assigned_department_id || "")

      if (data.photos && data.photos.length > 0) {
        setSelectedPhoto(data.photos[0].image_url)
      }

      // Load active departments for this city
      const deptList = await getAdminDepartments(data.city_id)
      setDepartments(deptList || [])
    } catch (err) {
      console.error("Failed to load complaint detail:", err)
      setError(err.message || "Failed to load complaint details")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      loadData()
    }
  }, [id])

  function clearMessages() {
    setActionError(null)
    setActionSuccess(null)
  }

  // 1. Handle Status Transition
  async function handleStatusTransition(e) {
    e.preventDefault()
    if (!targetStatus) return
    clearMessages()

    // If transitioning to ASSIGNED and no department is currently assigned, require department selection
    const deptToAssign = statusDeptId || complaint.assigned_department_id
    if (targetStatus === "ASSIGNED" && !deptToAssign) {
      setActionError("A department must be selected when transitioning to ASSIGNED.")
      return
    }

    if (statusRemark && statusRemark.trim().length > 0 && statusRemark.trim().length < 3) {
      setActionError("Remark must be at least 3 characters if provided.")
      return
    }

    setIsSubmitting(true)
    try {
      const updated = await transitionAdminComplaintStatus(complaint.id, {
        status: targetStatus,
        remark: statusRemark.trim() || undefined,
        department_id: targetStatus === "ASSIGNED" ? statusDeptId || undefined : undefined,
      })
      setComplaint(updated)
      setTargetStatus("")
      setStatusDeptId("")
      setStatusRemark("")
      setActionSuccess(`Status successfully transitioned to ${updated.status}.`)
    } catch (err) {
      console.error("Failed status transition:", err)
      setActionError(err.message || "Failed to transition status.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // 2. Handle Severity Update
  async function handleSeverityUpdate(e) {
    e.preventDefault()
    if (!targetSeverity || targetSeverity === complaint.severity) return
    clearMessages()

    if (severityRemark && severityRemark.trim().length > 0 && severityRemark.trim().length < 3) {
      setActionError("Remark must be at least 3 characters if provided.")
      return
    }

    setIsSubmitting(true)
    try {
      const updated = await updateAdminComplaintSeverity(complaint.id, {
        severity: targetSeverity,
        remark: severityRemark.trim() || undefined,
      })
      setComplaint(updated)
      setSeverityRemark("")
      setActionSuccess(`Severity updated to ${updated.severity}. New priority score: ${updated.priority_score}.`)
    } catch (err) {
      console.error("Failed severity update:", err)
      setActionError(err.message || "Failed to update severity.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // 3. Handle Department Assignment / Reassignment / Unassignment
  async function handleDepartmentAssignment(e) {
    e.preventDefault()
    clearMessages()

    const newDeptId = targetDeptId === "UNASSIGN" || !targetDeptId ? null : targetDeptId
    if (newDeptId === complaint.assigned_department_id) {
      return
    }

    if (deptRemark && deptRemark.trim().length > 0 && deptRemark.trim().length < 3) {
      setActionError("Remark must be at least 3 characters if provided.")
      return
    }

    setIsSubmitting(true)
    try {
      const updated = await assignAdminComplaintDepartment(complaint.id, {
        department_id: newDeptId,
        remark: deptRemark.trim() || undefined,
      })
      setComplaint(updated)
      setDeptRemark("")
      setActionSuccess(
        updated.assigned_department_name
          ? `Assigned to ${updated.assigned_department_name}.`
          : "Department assignment removed."
      )
    } catch (err) {
      console.error("Failed department assignment:", err)
      setActionError(err.message || "Failed to assign department.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // 4. Handle Add Progress Remark
  async function handleAddRemark(e) {
    e.preventDefault()
    clearMessages()

    if (!progressRemark.trim() || progressRemark.trim().length < 3) {
      setActionError("Remark must be at least 3 characters.")
      return
    }

    setIsSubmitting(true)
    try {
      const updated = await addAdminComplaintRemark(complaint.id, {
        remark: progressRemark.trim(),
      })
      setComplaint(updated)
      setProgressRemark("")
      setActionSuccess("Official progress remark recorded to audit history.")
    } catch (err) {
      console.error("Failed to add remark:", err)
      setActionError(err.message || "Failed to add remark.")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 pb-12">
        <Skeleton className="h-6 w-36" />
        <Skeleton className="h-10 w-3/4" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="lg:col-span-2 h-96 rounded-xl" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </div>
    )
  }

  if (error || !complaint) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mx-auto">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-foreground">Complaint Not Found</h3>
        <p className="text-xs text-muted-foreground">{error || "The requested civic complaint could not be found."}</p>
        <Button variant="outline" size="sm" onClick={() => navigate("/admin/complaints")} className="text-xs">
          Return to Triage Queue
        </Button>
      </div>
    )
  }

  const allowedNextStatuses = VALID_NEXT_STATUSES[complaint.status] || []
  const isTerminalState = allowedNextStatuses.length === 0

  const createdDate = complaint.created_at
    ? new Date(complaint.created_at).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Recently"

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Top Breadcrumb / Return Link */}
      <div className="flex items-center justify-between">
        <Link
          to="/admin/complaints"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Triage Queue
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground">
            ID: {complaint.id}
          </span>
        </div>
      </div>

      {/* Action Banners */}
      {actionSuccess && (
        <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 p-3.5 text-xs text-emerald-800 dark:text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-xs font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {actionError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3.5 text-xs text-destructive flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{actionError}</span>
          </div>
          <button onClick={() => setActionError(null)} className="text-xs font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Header Bar */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <ComplaintStatusBadge status={complaint.status} />
          <ComplaintSeverityBadge severity={complaint.severity} />
          <span className="inline-flex items-center gap-1 font-mono font-bold text-primary bg-primary/10 px-2.5 py-0.5 rounded text-xs">
            <TrendingUp className="h-3.5 w-3.5" />
            Priority {complaint.priority_score}
          </span>
          <Badge variant="outline" className="text-xs uppercase tracking-wider">
            {complaint.category.replace(/_/g, " ")}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            {complaint.city_name || "Vijayawada"}
          </Badge>
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {complaint.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            Reported on {createdDate}
          </span>
          {complaint.latitude && complaint.longitude && (
            <span className="inline-flex items-center gap-1.5 font-mono">
              <MapPin className="h-3.5 w-3.5 text-primary" />
              {complaint.latitude.toFixed(6)}, {complaint.longitude.toFixed(6)}
            </span>
          )}
          {complaint.assigned_department_name ? (
            <span className="inline-flex items-center gap-1.5 text-foreground font-medium">
              <Building2 className="h-3.5 w-3.5 text-primary" />
              Assigned to {complaint.assigned_department_name}
            </span>
          ) : (
            <span className="text-muted-foreground italic">Unassigned</span>
          )}
        </div>
      </div>

      {/* Main Grid: Details (Left) + Operations / Priority (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Content, Evidence, Reporter, and Audit Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Issue Description */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Citizen Complaint Description
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-2">
              <p className="text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed">
                {complaint.description}
              </p>
            </CardContent>
          </Card>

          {/* Evidence Photos (No raw EXIF) */}
          {complaint.photos && complaint.photos.length > 0 && (
            <Card className="shadow-xs">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="text-sm font-semibold">
                  Evidence Photos ({complaint.photos.length})
                </CardTitle>
                <CardDescription className="text-xs">
                  Photographic documentation submitted with the civic report
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 pt-2 space-y-4">
                {selectedPhoto && (
                  <div className="rounded-lg overflow-hidden border border-border bg-black/5 dark:bg-white/5 flex items-center justify-center max-h-96">
                    <img
                      src={selectedPhoto}
                      alt="Selected evidence"
                      className="max-h-96 w-auto object-contain rounded-lg"
                    />
                  </div>
                )}
                {complaint.photos.length > 1 && (
                  <div className="flex items-center gap-2 overflow-x-auto pb-1">
                    {complaint.photos.map((photo) => (
                      <button
                        key={photo.id}
                        type="button"
                        onClick={() => setSelectedPhoto(photo.image_url)}
                        className={`relative rounded-md overflow-hidden border-2 transition-all shrink-0 ${
                          selectedPhoto === photo.image_url
                            ? "border-primary ring-2 ring-primary/20"
                            : "border-border opacity-70 hover:opacity-100"
                        }`}
                      >
                        <img
                          src={photo.thumbnail_url || photo.image_url}
                          alt="Thumbnail"
                          className="h-16 w-16 object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Citizen Reporter Info & Location */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="shadow-xs">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <User className="h-3.5 w-3.5" />
                  Citizen Information
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-1">
                <div className="text-sm font-medium text-foreground">
                  {complaint.citizen_name || "Verified Citizen"}
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  {complaint.citizen_email || "N/A"}
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-xs">
              <CardHeader className="p-4 pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-primary" />
                  PostGIS Location
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-1 space-y-1">
                <div className="text-xs font-mono text-foreground font-semibold">
                  Lat: {complaint.latitude?.toFixed(6) ?? "N/A"}
                </div>
                <div className="text-xs font-mono text-foreground font-semibold">
                  Lng: {complaint.longitude?.toFixed(6) ?? "N/A"}
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Spatial Reference: EPSG:4326 (PostGIS)
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Structured Audit Trail & Progress Stepper */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 border-b border-border/70">
              <CardTitle className="text-sm font-semibold">
                Lifecycle & Complete Audit Trail
              </CardTitle>
              <CardDescription className="text-xs">
                Immutable chronological log of all state transitions, severity adjustments, and department dispatches
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              <ComplaintProgressTimeline
                status={complaint.status}
                updates={complaint.updates || []}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Col: Operations Panel & Priority Breakdown */}
        <div className="space-y-6">
          {/* Priority Score Breakdown Card */}
          <Card className="shadow-xs bg-card/80">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Priority Score Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-3xl font-extrabold font-mono text-foreground">
                  {complaint.priority_score}
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  Calculated dynamically
                </span>
              </div>

              <div className="space-y-2 text-xs border-t border-border/60 pt-3">
                <div className="flex justify-between items-center text-muted-foreground">
                  <span>Severity Weight ({complaint.severity})</span>
                  <span className="font-mono font-medium text-foreground">
                    +{SEVERITY_WEIGHTS[complaint.severity] || 0} pts
                  </span>
                </div>
                <div className="flex justify-between items-center text-muted-foreground">
                  <span>Community Upvotes</span>
                  <span className="font-mono font-medium text-foreground">
                    +{complaint.upvote_count} pts
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs font-semibold text-foreground border-t border-dashed border-border pt-1.5">
                  <span>Total Priority Score</span>
                  <span className="font-mono text-primary font-bold">
                    {complaint.priority_score}
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Progress Resolution</span>
                  <span className="font-mono font-bold text-foreground">
                    {complaint.progress_percentage}%
                  </span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-300"
                    style={{ width: `${complaint.progress_percentage}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Administration Control Panel */}
          <Card className="shadow-xs border-primary/20">
            <CardHeader className="p-5 border-b border-border/70 bg-primary/5">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Sliders className="h-4 w-4 text-primary" />
                Administrative Operations
              </CardTitle>
              <CardDescription className="text-xs">
                Manage lifecycle state, severity, and department assignment
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-6">
              {/* 1. Lifecycle State Machine Transition */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-foreground flex items-center justify-between">
                  <span>1. Lifecycle Status Transition</span>
                  <span className="text-[10px] font-mono text-muted-foreground">
                    Current: {complaint.status}
                  </span>
                </h4>

                {isTerminalState ? (
                  <div className="p-3 rounded-lg bg-muted text-xs text-muted-foreground">
                    This complaint is in terminal status ({complaint.status}). No further state transitions are permitted.
                  </div>
                ) : (
                  <form onSubmit={handleStatusTransition} className="space-y-3">
                    <select
                      value={targetStatus}
                      onChange={(e) => setTargetStatus(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      aria-label="Target status transition"
                    >
                      <option value="">Select next status step...</option>
                      {allowedNextStatuses.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label} ({opt.value})
                        </option>
                      ))}
                    </select>

                    {/* If transitioning to ASSIGNED, prompt for department selection */}
                    {targetStatus === "ASSIGNED" && (
                      <div className="space-y-1.5 p-3 rounded-lg border border-purple-200 dark:border-purple-900 bg-purple-50/50 dark:bg-purple-950/20">
                        <label className="text-[11px] font-semibold text-purple-900 dark:text-purple-300 block">
                          Assign Department *
                        </label>
                        <select
                          value={statusDeptId || complaint.assigned_department_id || ""}
                          onChange={(e) => setStatusDeptId(e.target.value)}
                          className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                          required
                          aria-label="Department for transition"
                        >
                          <option value="">Choose department...</option>
                          {departments.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <input
                      type="text"
                      placeholder="Audit remark (min 3 chars, optional)..."
                      value={statusRemark}
                      onChange={(e) => setStatusRemark(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    />

                    <Button
                      type="submit"
                      size="sm"
                      disabled={!targetStatus || isSubmitting}
                      className="w-full text-xs h-8"
                    >
                      {isSubmitting ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                      ) : null}
                      Transition Status
                    </Button>
                  </form>
                )}
              </div>

              <div className="border-t border-border/60" />

              {/* 2. Severity Update */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-foreground flex items-center justify-between">
                  <span>2. Adjust Severity Level</span>
                  <span className="text-[10px] font-mono text-muted-foreground">
                    Current: {complaint.severity}
                  </span>
                </h4>

                <form onSubmit={handleSeverityUpdate} className="space-y-3">
                  <select
                    value={targetSeverity}
                    onChange={(e) => setTargetSeverity(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    aria-label="Select new severity"
                  >
                    <option value="LOW">Low (10 pts)</option>
                    <option value="MEDIUM">Medium (25 pts)</option>
                    <option value="HIGH">High (50 pts)</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Reason for severity change..."
                    value={severityRemark}
                    onChange={(e) => setSeverityRemark(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />

                  <Button
                    type="submit"
                    variant="outline"
                    size="sm"
                    disabled={targetSeverity === complaint.severity || isSubmitting}
                    className="w-full text-xs h-8"
                  >
                    {isSubmitting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    ) : null}
                    Update Severity & Recalculate Priority
                  </Button>
                </form>
              </div>

              <div className="border-t border-border/60" />

              {/* 3. Department Assignment / Reassignment */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-foreground flex items-center justify-between">
                  <span>3. Department Dispatch</span>
                  <span className="text-[10px] font-mono text-muted-foreground truncate max-w-[140px]">
                    {complaint.assigned_department_name || "Unassigned"}
                  </span>
                </h4>

                <form onSubmit={handleDepartmentAssignment} className="space-y-3">
                  <select
                    value={targetDeptId}
                    onChange={(e) => setTargetDeptId(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    aria-label="Department dispatch selection"
                  >
                    <option value="">Select department...</option>
                    {complaint.assigned_department_id && (
                      <option value="UNASSIGN">&mdash; Clear / Unassign Department &mdash;</option>
                    )}
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>

                  <input
                    type="text"
                    placeholder="Dispatch note / assignment reason..."
                    value={deptRemark}
                    onChange={(e) => setDeptRemark(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />

                  <Button
                    type="submit"
                    variant="outline"
                    size="sm"
                    disabled={
                      (targetDeptId === (complaint.assigned_department_id || "")) ||
                      (!targetDeptId && !complaint.assigned_department_id) ||
                      isSubmitting
                    }
                    className="w-full text-xs h-8"
                  >
                    {isSubmitting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    ) : null}
                    {targetDeptId === "UNASSIGN" || !targetDeptId
                      ? "Unassign Department"
                      : "Assign / Reassign Department"}
                  </Button>
                </form>
              </div>

              <div className="border-t border-border/60" />

              {/* 4. Add Official Progress Remark */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-foreground">
                  4. Add Progress Remark
                </h4>

                <form onSubmit={handleAddRemark} className="space-y-3">
                  <textarea
                    rows={2}
                    placeholder="Record an official progress note or inspection findings (min 3 chars)..."
                    value={progressRemark}
                    onChange={(e) => setProgressRemark(e.target.value)}
                    className="w-full rounded-md border border-input bg-background p-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                  />

                  <Button
                    type="submit"
                    variant="secondary"
                    size="sm"
                    disabled={!progressRemark.trim() || progressRemark.trim().length < 3 || isSubmitting}
                    className="w-full text-xs h-8 gap-1.5"
                  >
                    {isSubmitting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Send className="h-3.5 w-3.5" />
                    )}
                    Post Official Remark
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
