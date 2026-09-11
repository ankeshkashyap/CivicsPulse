import React, { useEffect, useState } from "react"
import { useParams, useNavigate, useLocation, Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ComplaintStatusBadge, ComplaintSeverityBadge } from "@/components/complaints/ComplaintStatusBadge"
import { ComplaintProgressTimeline } from "@/components/complaints/ComplaintProgressTimeline"
import { getComplaint } from "@/lib/api"
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Layers,
  Image as ImageIcon,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Shield,
  Building,
} from "lucide-react"

export function ComplaintDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const [complaint, setComplaint] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)

  // Success message banner if passed via navigation state
  const [successBanner, setSuccessBanner] = useState(location.state?.successMessage || null)

  useEffect(() => {
    let isMounted = true

    async function loadComplaint() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getComplaint(id)
        if (isMounted) {
          setComplaint(data)
          if (data.images && data.images.length > 0) {
            setSelectedImage(data.images[0].image_url)
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err.data?.message || err.message || "Failed to load complaint details.")
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    if (id) {
      loadComplaint()
    }

    return () => {
      isMounted = false
    }
  }, [id])

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-24" />
        </div>
        <Skeleton className="h-10 w-3/4" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="md:col-span-2 h-96 rounded-xl" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </div>
    )
  }

  if (error || !complaint) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mx-auto">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-foreground">Complaint Not Found</h3>
        <p className="text-xs text-muted-foreground">{error || "The requested civic complaint could not be found."}</p>
        <Button variant="outline" size="sm" onClick={() => navigate("/complaints")} className="text-xs">
          Return to My Complaints
        </Button>
      </div>
    )
  }

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
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/complaints"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Complaints
        </Link>
        <span className="text-[11px] font-mono text-muted-foreground">
          REF #{complaint.id.slice(0, 8)}
        </span>
      </div>

      {/* Success Banner */}
      {successBanner && (
        <div className="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 p-4 text-xs text-emerald-800 dark:text-emerald-300 flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-700 dark:text-emerald-400 hover:text-emerald-900 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Complaint Title & Meta Header */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <ComplaintStatusBadge status={complaint.status} />
          <ComplaintSeverityBadge severity={complaint.severity} />
          <Badge variant="outline" className="text-xs font-normal">
            {complaint.category.replace("_", " ")}
          </Badge>
          {complaint.is_owner && (
            <Badge variant="secondary" className="text-[10px]">
              Your Submission
            </Badge>
          )}
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {complaint.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            Reported on {createdDate}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-primary" />
            {complaint.latitude?.toFixed(4)}, {complaint.longitude?.toFixed(4)} ({complaint.location_source})
          </span>
          {complaint.department_name && (
            <span className="inline-flex items-center gap-1.5">
              <Building className="h-3.5 w-3.5" />
              Assigned to {complaint.department_name}
            </span>
          )}
        </div>
      </div>

      {/* Main Grid: Details + Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Description & Evidence Photos (2 cols) */}
        <div className="md:col-span-2 space-y-6">
          {/* Issue Description */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Issue Description
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-1">
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                {complaint.description}
              </p>
            </CardContent>
          </Card>

          {/* Photo Evidence Gallery */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Photo Evidence ({complaint.images?.length || 0})
                </CardTitle>
                <Badge variant="outline" className="text-[10px]">
                  Verified Uploads
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              {complaint.images && complaint.images.length > 0 ? (
                <>
                  {/* Active enlarged preview */}
                  <div className="relative aspect-video rounded-xl overflow-hidden border border-border bg-black/5 dark:bg-black/40">
                    <img
                      src={selectedImage || complaint.images[0].image_url}
                      alt="Selected Evidence"
                      className="h-full w-full object-contain"
                    />
                  </div>

                  {/* Thumbnail Row */}
                  {complaint.images.length > 1 && (
                    <div className="grid grid-cols-3 gap-3">
                      {complaint.images.map((img, idx) => (
                        <button
                          key={img.id || idx}
                          type="button"
                          onClick={() => setSelectedImage(img.image_url)}
                          className={`relative aspect-video rounded-lg overflow-hidden border transition-all ${
                            (selectedImage || complaint.images[0].image_url) === img.image_url
                              ? "border-primary ring-2 ring-primary/20 shadow-xs"
                              : "border-border opacity-70 hover:opacity-100"
                          }`}
                        >
                          <img
                            src={img.image_url}
                            alt={`Evidence thumbnail ${idx + 1}`}
                            className="h-full w-full object-cover"
                          />
                        </button>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="p-6 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                  No photographic evidence attached to this report.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Location Verification Details */}
          <Card className="shadow-xs">
            <CardHeader className="p-5 pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Geographic Verification
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-1 space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-[10px] text-muted-foreground block">Latitude</span>
                  <span className="font-mono font-semibold text-foreground">
                    {complaint.latitude !== null ? complaint.latitude : "N/A"}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-[10px] text-muted-foreground block">Longitude</span>
                  <span className="font-mono font-semibold text-foreground">
                    {complaint.longitude !== null ? complaint.longitude : "N/A"}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60 col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-muted-foreground block">Verification Source</span>
                  <span className="font-semibold text-foreground">
                    {complaint.location_source === "GPS" ? "High-Accuracy GPS" : "Citizen Manual"}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Stored using canonical PostGIS geometry (POINT, SRID 4326) for municipal spatial routing and GIS mapping.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Progress Stepper & Audit Log (1 col) */}
        <div className="space-y-6">
          <ComplaintProgressTimeline
            status={complaint.status}
            updates={complaint.updates || []}
          />
        </div>
      </div>
    </div>
  )
}
export default ComplaintDetailPage
