import React, { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import {
  MapPin,
  Layers,
  Crosshair,
  Compass,
  Map as MapIcon,
  Shield,
  Activity,
} from "lucide-react"

const CIRCLES = [
  { name: "Circle I (One Town / Old City)", wards: "Wards 1 - 22", complaints: 0 },
  { name: "Circle II (Governorpet & Gandhi Nagar)", wards: "Wards 23 - 42", complaints: 0 },
  { name: "Circle III (Patamata & Benz Circle)", wards: "Wards 43 - 64", complaints: 0 },
]

export function AdminMapPage() {
  const [activeLayer, setActiveLayer] = useState("all")

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        tag="Geospatial Intelligence"
        title="Ward Boundary & Incident Map"
        description="Spatial distribution, ward boundary layers, and incident cluster density visualization for Vijayawada."
        actions={
          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className="text-xs font-mono border-primary/30 text-primary">
              16.5062° N, 80.6480° E
            </Badge>
            <Badge variant="secondary" className="text-xs">
              EPSG:4326
            </Badge>
          </div>
        }
      />

      {/* Geospatial Architecture Notice Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-lg border border-border/70 bg-surface text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-primary shrink-0" />
          <span>
            <strong className="text-foreground font-medium">Spatial Architecture:</strong> High-precision coordinate persistence ready for PostGIS <code className="font-mono text-[11px] bg-muted px-1 py-0.5 rounded">geometry(Point, 4326)</code> migration.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[11px]">
            64 Municipal Wards
          </Badge>
          <Badge variant="outline" className="text-[11px]">
            3 Administrative Circles
          </Badge>
        </div>
      </div>

      {/* Map Viewport Card */}
      <Card className="shadow-xs overflow-hidden">
        {/* Map Header Controls */}
        <div className="flex flex-wrap items-center justify-between border-b border-border p-3.5 bg-muted/20 gap-2">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium text-foreground">Map Layers:</span>
            <div className="flex items-center gap-1">
              <Button
                variant={activeLayer === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveLayer("all")}
                className="h-7 text-xs px-2.5"
              >
                All Incidents
              </Button>
              <Button
                variant={activeLayer === "clusters" ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveLayer("clusters")}
                className="h-7 text-xs px-2.5"
              >
                Density Clusters
              </Button>
              <Button
                variant={activeLayer === "wards" ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveLayer("wards")}
                className="h-7 text-xs px-2.5"
              >
                Ward Polygons
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Crosshair className="h-3.5 w-3.5 text-primary" />
            <span>Center: Krishna River Basin, Vijayawada</span>
          </div>
        </div>

        {/* Map Canvas Simulated Viewport */}
        <div className="relative h-[440px] w-full bg-surface flex items-center justify-center p-6 border-b border-border">
          {/* Subtle grid pattern for cartographic look */}
          <div
            className="absolute inset-0 opacity-[0.04] dark:opacity-[0.08]"
            style={{
              backgroundImage:
                "radial-gradient(circle, currentColor 1px, transparent 1px)",
              backgroundSize: "24px 24px",
            }}
          />

          {/* Simulated Ward Labels in background */}
          <div className="absolute inset-0 pointer-events-none p-6 flex flex-col justify-between text-[11px] font-mono text-muted-foreground/30 select-none">
            <div className="flex justify-between">
              <span>CIRCLE I &bull; ONE TOWN (16.5200° N)</span>
              <span>GUNADALA RIDGE (80.6700° E)</span>
            </div>
            <div className="flex justify-between">
              <span>PRAKASAM BARRAGE / KRISHNA RIVER</span>
              <span>BENZ CIRCLE &bull; CIRCLE III</span>
            </div>
          </div>

          {/* Central Empty State Card Overlay */}
          <div className="relative z-10 max-w-md bg-card/95 backdrop-blur-xs border border-border/80 rounded-xl p-6 shadow-sm">
            <EmptyState
              icon={MapPin}
              title="Spatial Engine Ready"
              description="Interactive Leaflet / MapLibre visualization with live ward polygon boundaries and complaint cluster pins will render as soon as geotagged reports are submitted."
              badgeText="0 Geotagged Reports"
            />
          </div>
        </div>

        {/* Administrative Circles Breakdown */}
        <div className="grid grid-cols-1 divide-y sm:divide-y-0 sm:divide-x divide-border sm:grid-cols-3 bg-muted/10">
          {CIRCLES.map((circle) => (
            <div key={circle.name} className="p-4 space-y-1 text-xs">
              <div className="font-semibold text-foreground">{circle.name}</div>
              <div className="text-muted-foreground text-[11px]">{circle.wards}</div>
              <div className="text-[11px] text-muted-foreground flex items-center gap-1 pt-1">
                <Activity className="h-3 w-3 text-primary" />
                <span>{circle.complaints} Active Reports</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
