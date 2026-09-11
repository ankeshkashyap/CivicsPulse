import React, { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { createComplaint } from "@/lib/api"
import {
  MapPin,
  Camera,
  UploadCloud,
  X,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ArrowLeft,
  Flame,
  Droplets,
  Lightbulb,
  Trash2,
  Shield,
  Car,
  Compass,
  Trees,
  HelpCircle,
  Waves,
} from "lucide-react"

const CATEGORIES = [
  { key: "ROADS", label: "Roads & Potholes", icon: Car, desc: "Damaged roads, potholes, broken sidewalks" },
  { key: "STREETLIGHTS", label: "Streetlights", icon: Lightbulb, desc: "Non-functional lights, flickering, damaged poles" },
  { key: "GARBAGE", label: "Garbage & Sanitation", icon: Trash2, desc: "Overflowing bins, uncollected waste, illegal dumping" },
  { key: "DRAINAGE", label: "Drainage", icon: Droplets, desc: "Clogged drains, stagnant storm water, open drains" },
  { key: "WATER", label: "Water Supply", icon: Droplets, desc: "Pipeline leaks, water shortage, contaminated water" },
  { key: "SEWERAGE", label: "Sewerage", icon: Waves, desc: "Sewage overflow, manhole blockage, pipe burst" },
  { key: "TRAFFIC", label: "Traffic & Signals", icon: Compass, desc: "Broken traffic signals, intersection hazards, missing signage" },
  { key: "PUBLIC_SAFETY", label: "Public Safety", icon: Shield, desc: "Hazardous conditions, fallen trees, wire risks" },
  { key: "PARKS", label: "Parks & Recreation", icon: Trees, desc: "Damaged play equipment, overgrown vegetation, broken benches" },
  { key: "OTHER", label: "Other Civic Issues", icon: HelpCircle, desc: "General municipal concerns not categorized above" },
]

const SEVERITIES = [
  { key: "LOW", label: "Low", desc: "Minor civic inconvenience (Weight: 10)", color: "text-slate-600 dark:text-slate-400" },
  { key: "MEDIUM", label: "Medium", desc: "Standard municipal priority (Weight: 25)", color: "text-blue-600 dark:text-blue-400" },
  { key: "HIGH", label: "High", desc: "Hazardous or severe disruption (Weight: 50)", color: "text-amber-600 dark:text-amber-400" },
]

export function NewComplaintPage() {
  const navigate = useNavigate()

  // Form State
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("ROADS")
  const [severity, setSeverity] = useState("MEDIUM")

  // Geolocation State
  const [latitude, setLatitude] = useState("")
  const [longitude, setLongitude] = useState("")
  const [locationSource, setLocationSource] = useState("MANUAL")
  const [isDetectingLocation, setIsDetectingLocation] = useState(false)
  const [locationError, setLocationError] = useState(null)
  const [locationSuccess, setLocationSuccess] = useState(false)

  // Images State (1 to 3 files)
  const [images, setImages] = useState([])
  const [previews, setPreviews] = useState([])

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorBanner, setErrorBanner] = useState(null)

  // Detect GPS via browser Geolocation API
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setLocationError("Geolocation is not supported by your browser.")
      return
    }

    setIsDetectingLocation(true)
    setLocationError(null)
    setLocationSuccess(false)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6)
        const lon = position.coords.longitude.toFixed(6)
        setLatitude(lat)
        setLongitude(lon)
        setLocationSource("GPS")
        setIsDetectingLocation(false)
        setLocationSuccess(true)
      },
      (error) => {
        setIsDetectingLocation(false)
        let msg = "Failed to detect location."
        if (error.code === 1) msg = "Location permission was denied. Please allow access or enter coordinates manually."
        else if (error.code === 2) msg = "Position unavailable. Please enter coordinates manually."
        else if (error.code === 3) msg = "Location request timed out. Please enter coordinates manually."
        setLocationError(msg)
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 0,
      }
    )
  }

  // Handle Image File Selection
  const handleImageChange = (e) => {
    const selectedFiles = Array.from(e.target.files || [])
    if (selectedFiles.length === 0) return

    const totalAllowed = 3 - images.length
    if (totalAllowed <= 0) {
      setErrorBanner("You may only attach up to 3 evidence images.")
      return
    }

    const validNewFiles = []
    const newPreviews = []

    for (const file of selectedFiles.slice(0, totalAllowed)) {
      if (file.size > 5 * 1024 * 1024) {
        setErrorBanner(`Image "${file.name}" exceeds the 5MB maximum limit.`)
        continue
      }
      validNewFiles.push(file)
      newPreviews.push(URL.createObjectURL(file))
    }

    setImages((prev) => [...prev, ...validNewFiles])
    setPreviews((prev) => [...prev, ...newPreviews])
    setErrorBanner(null)
  }

  const handleRemoveImage = (index) => {
    URL.revokeObjectURL(previews[index])
    setImages((prev) => prev.filter((_, i) => i !== index))
    setPreviews((prev) => prev.filter((_, i) => i !== index))
  }

  // Form Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorBanner(null)

    // Client-side validations
    if (title.trim().length < 5) {
      setErrorBanner("Complaint title must be at least 5 characters.")
      return
    }
    if (description.trim().length < 10 || description.trim().length > 5000) {
      setErrorBanner("Complaint description must be between 10 and 5000 characters.")
      return
    }
    const latNum = parseFloat(latitude)
    const lonNum = parseFloat(longitude)
    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setErrorBanner("Valid latitude (-90 to 90) is required.")
      return
    }
    if (isNaN(lonNum) || lonNum < -180 || lonNum > 180) {
      setErrorBanner("Valid longitude (-180 to 180) is required.")
      return
    }
    if (images.length === 0) {
      setErrorBanner("At least one photo evidence image is required to submit a complaint.")
      return
    }
    if (images.length > 3) {
      setErrorBanner("A maximum of 3 images can be attached.")
      return
    }

    // Build FormData
    const formData = new FormData()
    formData.append("title", title.trim())
    formData.append("description", description.trim())
    formData.append("category", category)
    formData.append("severity", severity)
    formData.append("latitude", latNum.toString())
    formData.append("longitude", lonNum.toString())
    formData.append("location_source", locationSource)

    for (const file of images) {
      formData.append("images", file)
    }

    setIsSubmitting(true)
    try {
      const createdComplaint = await createComplaint(formData)
      navigate(`/complaints/${createdComplaint.id}`, {
        state: { successMessage: "Civic complaint submitted successfully! Municipal administrators have been notified." },
      })
    } catch (err) {
      const msg = err.data?.message || err.message || "Failed to submit complaint. Please check your inputs and try again."
      setErrorBanner(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Back Link & Header */}
      <div>
        <Link
          to="/complaints"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground mb-3 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to My Complaints
        </Link>
        <PageHeader
          tag="Citizen Report"
          title="File a New Civic Complaint"
          description="Report infrastructure issues, sanitation hazards, or municipal defects directly to Vijayawada authorities."
        />
      </div>

      {errorBanner && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive flex items-start gap-2.5">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold">Submission Error</span>
            <p className="leading-relaxed">{errorBanner}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 1. Category Selection */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 pb-3">
            <CardTitle className="text-sm font-semibold">1. Select Issue Category</CardTitle>
            <CardDescription className="text-xs">
              Choose the municipal department category that best describes the issue.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon
                const isSelected = category === cat.key
                return (
                  <button
                    type="button"
                    key={cat.key}
                    onClick={() => setCategory(cat.key)}
                    className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-primary bg-primary/5 ring-2 ring-primary/20 shadow-xs"
                        : "border-border hover:border-border/80 hover:bg-muted/40"
                    }`}
                  >
                    <div className={`p-2 rounded-lg mb-2 ${isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="text-xs font-semibold text-foreground">{cat.label}</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2 leading-tight">
                      {cat.desc}
                    </span>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* 2. Issue Details (Title, Description, Severity) */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 pb-3">
            <CardTitle className="text-sm font-semibold">2. Issue Details</CardTitle>
            <CardDescription className="text-xs">
              Provide clear and detailed information to help municipal teams assess the report.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-0 space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>Issue Title *</span>
                <span className="text-[10px] text-muted-foreground font-normal">
                  {title.length}/200 characters (min 5)
                </span>
              </label>
              <Input
                placeholder="e.g. Deep pothole near Benz Circle flyover"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                required
                className="text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>Detailed Description *</span>
                <span className="text-[10px] text-muted-foreground font-normal">
                  {description.length}/5000 characters (min 10)
                </span>
              </label>
              <textarea
                placeholder="Describe the exact issue, landmarks, hazard level, and any impact on pedestrians or traffic..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={5000}
                rows={4}
                required
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div className="space-y-2 pt-1">
              <label className="text-xs font-semibold text-foreground">
                Urgency & Severity Level *
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {SEVERITIES.map((sev) => {
                  const isSelected = severity === sev.key
                  return (
                    <button
                      type="button"
                      key={sev.key}
                      onClick={() => setSeverity(sev.key)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        isSelected
                          ? "border-primary bg-primary/5 ring-2 ring-primary/20 shadow-xs"
                          : "border-border hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${sev.color}`}>{sev.label}</span>
                        {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
                      </div>
                      <p className="text-[10px] text-muted-foreground leading-snug">{sev.desc}</p>
                    </button>
                  )
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3. Location Verification */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold">3. Location Verification</CardTitle>
                <CardDescription className="text-xs">
                  Accurate geographic coordinates are mapped via PostGIS geometry for municipal field dispatch.
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-[10px]">
                {locationSource === "GPS" ? "Verified via GPS" : "Manual Coordinates"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 pt-0 space-y-4">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleDetectLocation}
                disabled={isDetectingLocation}
                className="gap-2 text-xs h-9"
              >
                {isDetectingLocation ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <MapPin className="h-3.5 w-3.5 text-primary" />
                )}
                {isDetectingLocation ? "Detecting High-Accuracy GPS..." : "Auto-Detect My GPS Location"}
              </Button>
              <span className="text-[11px] text-muted-foreground hidden sm:inline">
                or enter coordinates manually below
              </span>
            </div>

            {locationSuccess && (
              <div className="flex items-center gap-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 px-3 py-2 text-xs text-emerald-800 dark:text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span>GPS coordinates detected successfully with high accuracy.</span>
              </div>
            )}

            {locationError && (
              <div className="flex items-center gap-2 rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2 text-xs text-destructive">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span>{locationError}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-foreground">Latitude (-90 to 90) *</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 16.506174"
                  value={latitude}
                  onChange={(e) => {
                    setLatitude(e.target.value)
                    setLocationSource("MANUAL")
                  }}
                  required
                  className="text-xs h-8"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-foreground">Longitude (-180 to 180) *</label>
                <Input
                  type="number"
                  step="any"
                  placeholder="e.g. 80.648015"
                  value={longitude}
                  onChange={(e) => {
                    setLongitude(e.target.value)
                    setLocationSource("MANUAL")
                  }}
                  required
                  className="text-xs h-8"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4. Photo Evidence (1 - 3 Images) */}
        <Card className="shadow-xs">
          <CardHeader className="p-5 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold">4. Photo Evidence (1 - 3 Images)</CardTitle>
                <CardDescription className="text-xs">
                  Upload up to 3 photos of the issue (JPEG, PNG, WebP up to 5MB each). EXIF coordinates will be extracted if available.
                </CardDescription>
              </div>
              <Badge variant={images.length > 0 ? "secondary" : "outline"} className="text-[10px]">
                {images.length}/3 Uploaded
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 pt-0 space-y-4">
            {/* Upload Dropzone */}
            {images.length < 3 && (
              <label className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-border/80 rounded-xl cursor-pointer hover:border-primary/60 hover:bg-muted/30 transition-all">
                <div className="p-3 rounded-full bg-primary/10 text-primary mb-2">
                  <UploadCloud className="h-5 w-5" />
                </div>
                <span className="text-xs font-semibold text-foreground">
                  Click to browse photos or drag and drop
                </span>
                <span className="text-[11px] text-muted-foreground mt-0.5">
                  JPEG, PNG, WebP (Max 5MB each)
                </span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleImageChange}
                  className="hidden"
                />
              </label>
            )}

            {/* Previews */}
            {previews.length > 0 && (
              <div className="grid grid-cols-3 gap-3">
                {previews.map((previewUrl, idx) => (
                  <div
                    key={idx}
                    className="group relative aspect-video rounded-lg overflow-hidden border border-border bg-muted/30 shadow-xs"
                  >
                    <img
                      src={previewUrl}
                      alt={`Evidence ${idx + 1}`}
                      className="h-full w-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(idx)}
                      className="absolute top-1.5 right-1.5 p-1 rounded-full bg-background/80 text-foreground hover:bg-destructive hover:text-destructive-foreground transition-colors shadow-xs"
                      title="Remove image"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                    <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-black/60 text-[9px] font-medium text-white">
                      Photo {idx + 1}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/complaints")}
            disabled={isSubmitting}
            className="text-xs"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="text-xs gap-2 min-w-36"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Submitting Report...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                Submit Civic Complaint
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
export default NewComplaintPage
