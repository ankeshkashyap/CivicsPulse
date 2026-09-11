import React from "react"
import { PageHeader } from "@/components/ui/page-header"
import { Card, CardContent } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { Bell, CheckCheck } from "lucide-react"

export function NotificationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        tag="Activity"
        title="Notifications"
        description="Audit log alerts, status transitions, and municipal responses for your active civic reports."
      />

      <Card className="shadow-xs">
        <CardContent className="p-6 sm:p-10">
          <EmptyState
            icon={Bell}
            title="All caught up"
            description="You have no unread notifications. When city administrators review, assign, or resolve your submitted reports, real-time alerts and progress notifications will appear here."
            badgeText="0 Unread"
          />
        </CardContent>
      </Card>
    </div>
  )
}
