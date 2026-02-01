/**
 * Loading skeleton components for ReplicarIA.
 * Provides visual placeholders while data is loading.
 */

import React from "react";
import { cn } from "@/lib/utils";

/**
 * Base skeleton component with pulse animation.
 */
export function Skeleton({ className, ...props }) {
    return (
        <div
            className={cn("animate-pulse rounded-md bg-muted", className)}
            {...props}
        />
    );
}

/**
 * Skeleton for a table row.
 */
export function TableRowSkeleton({ columns = 5 }) {
    return (
        <tr className="border-b">
            {Array.from({ length: columns }).map((_, i) => (
                <td key={i} className="p-4">
                    <Skeleton className="h-4 w-full" />
                </td>
            ))}
        </tr>
    );
}

/**
 * Skeleton for a card.
 */
export function CardSkeleton({ className }) {
    return (
        <div className={cn("rounded-lg border bg-card p-6", className)}>
            <div className="space-y-3">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
            </div>
            <div className="mt-4 flex gap-2">
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-8 w-20" />
            </div>
        </div>
    );
}

/**
 * Skeleton for a list of projects.
 */
export function ProjectListSkeleton({ count = 5 }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-1/3" />
                        <Skeleton className="h-3 w-2/3" />
                    </div>
                    <Skeleton className="h-6 w-16" />
                </div>
            ))}
        </div>
    );
}

/**
 * Skeleton for agent cards.
 */
export function AgentGridSkeleton({ count = 6 }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: count }).map((_, i) => (
                <CardSkeleton key={i} />
            ))}
        </div>
    );
}

/**
 * Skeleton for defense file detail page.
 */
export function DefenseFileDetailSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div className="space-y-2">
                    <Skeleton className="h-8 w-64" />
                    <Skeleton className="h-4 w-40" />
                </div>
                <Skeleton className="h-10 w-32" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="p-4 border rounded-lg">
                        <Skeleton className="h-4 w-20 mb-2" />
                        <Skeleton className="h-8 w-16" />
                    </div>
                ))}
            </div>

            {/* Sections */}
            <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="p-4 border rounded-lg space-y-3">
                        <Skeleton className="h-5 w-1/4" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                    </div>
                ))}
            </div>
        </div>
    );
}

/**
 * Full page loading skeleton.
 */
export function PageSkeleton() {
    return (
        <div className="p-6 space-y-6">
            <Skeleton className="h-8 w-48" />
            <div className="flex gap-4">
                <Skeleton className="h-10 w-32" />
                <Skeleton className="h-10 w-32" />
            </div>
            <ProjectListSkeleton />
        </div>
    );
}
