import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Building2,
  Trash2,
  Droplets,
  Zap,
  Car,
  Hammer,
  Clock,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react"

const DEPARTMENTS = [
  {
    code: "VMC-PWD",
    name: "Public Works Department",
    category: "Roads, Pavements & Structural Infrastructure",
    description: "Responsible for asphalt pothole repairs, arterial road maintenance, bridge safety, and pedestrian footpath paving.",
    sla: "48 Hours",
    headquarters: "VMC Central Office, Governorpet",
    activeComplaints: 0,
    icon: Hammer,
    status: "Active",
  },
  {
    code: "VMC-SWM",
    name: "Sanitation & Solid Waste",
    category: "Garbage, Sweeping & Waste Disposal",
    description: "Oversees daily residential garbage collection, public bin clearance, commercial market sweeping, and illegal dumping remediation.",
    sla: "24 Hours",
    headquarters: "Public Health Division, Circle II",
    activeComplaints: 0,
    icon: Trash2,
    status: "Active",
  },
  {
    code: "VMC-DRAIN",
    name: "Stormwater Drainage & Sewerage",
    category: "Desilting, Overflow & Drain Safety",
    description: "Maintains primary stormwater channels, desilts secondary open drains, and remediates monsoonal road waterlogging.",
    sla: "24 Hours",
    headquarters: "Engineering Wing, Circle I",
    activeComplaints: 0,
    icon: Droplets,
    status: "Active",
  },
  {
    code: "VMC-WATER",
    name: "Water Supply & Distribution",
    category: "Potable Water, Pipeline Leaks & Valves",
    description: "Operates Krishna river water intake plants, pipeline leak repairs, booster pumps, and drinking water purity testing.",
    sla: "12 Hours (Emergency)",
    headquarters: "Head Water Works, Bhavani Island Road",
    activeComplaints: 0,
    icon: Droplets,
    status: "Active",
  },
  {
    code: "VMC-ELEC",
    name: "Public Lighting & Electrical",
    category: "Streetlights, High-Mast Towers & Cables",
    description: "Repairs non-functional LED streetlights, replaces faulty photocell sensors, and safeguards exposed underground utility cables.",
    sla: "24 Hours",
    headquarters: "Electrical Workshop, Circle III",
    activeComplaints: 0,
    icon: Zap,
    status: "Active",
  },
  {
    code: "VMC-TRAF",
    name: "Urban Mobility & Traffic Engineering",
    category: "Signals, Road Signs & Speed Calming",
    description: "Coordinates with city traffic police for signal timing, junction safety marking, speed-breaker painting, and regulatory signboards.",
    sla: "72 Hours",
    headquarters: "VMC Traffic Cell, MG Road",
    activeComplaints: 0,
    icon: Car,
    status: "Active",
  },
]

export function AdminDepartmentsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Municipal Registry"
        title="Departments & Dispatch Directory"
        description="Vijayawada Municipal Corporation operational departments responsible for complaint resolution, field triage, and SLA enforcement."
        actions={
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-xs border-primary/30 text-primary">
              6 Departments
            </Badge>
            <Badge variant="default" className="text-xs">
              All Operational
            </Badge>
          </div>
        }
      />

      {/* Overview Stat Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg border border-border bg-card p-4 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground block">Active Field Queues</span>
            <span className="text-xl font-bold text-foreground">0 Pending</span>
          </div>
          <Building2 className="h-5 w-5 text-primary" />
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground block">Fastest SLA Benchmark</span>
            <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">12h Water Leak</span>
          </div>
          <Clock className="h-5 w-5 text-emerald-500" />
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground block">Operational Readiness</span>
            <span className="text-xl font-bold text-foreground">100%</span>
          </div>
          <CheckCircle2 className="h-5 w-5 text-primary" />
        </div>
      </div>

      {/* Department Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {DEPARTMENTS.map((dept) => {
          const Icon = dept.icon
          return (
            <Card key={dept.code} className="shadow-xs flex flex-col justify-between">
              <CardHeader className="p-4 pb-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded">
                    {dept.code}
                  </span>
                  <Badge variant="outline" className="text-[10px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                    {dept.status}
                  </Badge>
                </div>
                <CardTitle className="text-sm font-semibold pt-2 flex items-center gap-2">
                  <Icon className="h-4 w-4 text-primary shrink-0" />
                  {dept.name}
                </CardTitle>
                <CardDescription className="text-[11px] font-medium text-foreground/80">
                  {dept.category}
                </CardDescription>
              </CardHeader>

              <CardContent className="p-4 pt-1 space-y-2.5 text-xs">
                <p className="text-muted-foreground text-[11px] leading-relaxed">
                  {dept.description}
                </p>
                <div className="space-y-1 pt-1 border-t border-border/60 text-[11px]">
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span>SLA Benchmark:</span>
                    <span className="font-medium text-foreground">{dept.sla}</span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span>Headquarters:</span>
                    <span className="font-medium text-foreground truncate max-w-[170px]">{dept.headquarters}</span>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="p-4 pt-2 border-t border-border/50 bg-muted/10 flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground">Assigned Workload:</span>
                <span className="font-semibold text-foreground">{dept.activeComplaints} Active Cases</span>
              </CardFooter>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
