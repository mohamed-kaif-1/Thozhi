import React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle, BatteryCharging } from "lucide-react";

interface CapacityBarProps {
  totalAvailableMin: number;
  totalScheduledMin: number;
  capacityPercentage: number;
  className?: string;
}

export const CapacityBar: React.FC<CapacityBarProps> = ({
  totalAvailableMin,
  totalScheduledMin,
  capacityPercentage,
  className,
}) => {
  const isOvercapacity = capacityPercentage > 100;
  const isNearCapacity = capacityPercentage >= 85 && capacityPercentage <= 100;

  const barColor = isOvercapacity
    ? "bg-gradient-to-r from-rose-600 to-red-400 shadow-lg shadow-red-500/30"
    : isNearCapacity
    ? "bg-gradient-to-r from-amber-600 to-amber-400 shadow-lg shadow-amber-500/30"
    : "bg-gradient-to-r from-sky-600 to-cyan-400 shadow-lg shadow-sky-500/30";

  const availableHours = (totalAvailableMin / 60).toFixed(1);
  const scheduledHours = (totalScheduledMin / 60).toFixed(1);

  return (
    <div className={cn("surface-card p-5 border border-slate-200/80 dark:border-sky-500/20 shadow-xl", className)}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className={cn(
            "w-7 h-7 rounded-lg flex items-center justify-center border",
            isOvercapacity
              ? "bg-rose-500/20 border-rose-500/40 text-rose-500 dark:text-rose-400"
              : "bg-sky-500/15 border-sky-500/40 text-sky-600 dark:text-sky-400"
          )}>
            {isOvercapacity ? (
              <AlertTriangle className="w-4 h-4" />
            ) : (
              <BatteryCharging className="w-4 h-4" />
            )}
          </div>
          <div>
            <span className="font-bold text-sm text-slate-900 dark:text-white block">
              Daily Focus Capacity
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Deterministic workload allocation
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={cn(
            "text-xs font-bold px-3 py-1 rounded-full border",
            isOvercapacity
              ? "bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/40"
              : isNearCapacity
              ? "bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/40"
              : "bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/40"
          )}>
            {capacityPercentage}% ({scheduledHours}h / {availableHours}h)
          </span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="w-full h-3.5 bg-slate-200/90 dark:bg-slate-900/90 border border-slate-300/60 dark:border-slate-700/60 rounded-full overflow-hidden p-0.5">
        <div
          className={cn("h-full transition-all duration-500 rounded-full", barColor)}
          style={{ width: `${Math.min(capacityPercentage, 100)}%` }}
        />
      </div>

      {isOvercapacity && (
        <div className="mt-3 p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-500/40 text-xs font-medium text-rose-700 dark:text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 flex-shrink-0" />
          <span>Workload exceeds nominal capacity. AI engine recommends deferring lower-priority items.</span>
        </div>
      )}
    </div>
  );
};
