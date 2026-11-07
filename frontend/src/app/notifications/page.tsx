"use client";

import React, { useState } from "react";
import {
  Bell,
  Clock,
  AlertTriangle,
  Sparkles,
  CheckCircle2,
  Trash2,
  ArrowRight
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface NotificationItem {
  id: string;
  type: "deadline" | "proposal" | "capacity" | "system";
  title: string;
  message: string;
  timestamp: string;
  is_read: boolean;
  action_href?: string;
  action_label?: string;
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-1",
    type: "proposal",
    title: "Pending Plan Proposal from Audio Stream",
    message: "2 tasks and 1 commitment extracted from your morning Tanglish voice note are awaiting review.",
    timestamp: "15 mins ago",
    is_read: false,
    action_href: "/",
    action_label: "Review Proposal",
  },
  {
    id: "notif-2",
    type: "deadline",
    title: "Impending Deadline: Client Architecture Demo",
    message: "Commitment scheduled in 2.5 hours. Ensure prototype slides are ready.",
    timestamp: "1 hour ago",
    is_read: false,
    action_href: "/tasks",
    action_label: "View Task",
  },
  {
    id: "notif-3",
    type: "capacity",
    title: "Capacity Deficit Alert (Simulated)",
    message: "Overlapping focus sessions detected at 11:30 AM. Kahn's DAG rescheduling proposal ready.",
    timestamp: "3 hours ago",
    is_read: true,
    action_href: "/planner",
    action_label: "Resolve in Planner",
  },
  {
    id: "notif-4",
    type: "system",
    title: "Gnani AI Prisma v3 Engine Connected",
    message: "Verified streaming STT endpoint https://api.vachana.ai/stt/v3 with zero raw audio retention guarantee.",
    timestamp: "Yesterday",
    is_read: true,
  },
];

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const getTypeIcon = (type: NotificationItem["type"]) => {
    switch (type) {
      case "proposal":
        return <Sparkles className="w-5 h-5 text-cyber-amber-400" />;
      case "deadline":
        return <AlertTriangle className="w-5 h-5 text-rose-400" />;
      case "capacity":
        return <Clock className="w-5 h-5 text-sky-400" />;
      case "system":
      default:
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-sky-500/20">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <span>Notification Center</span>
            {unreadCount > 0 && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyber-amber-500/20 border border-cyber-amber-500/40 text-cyber-amber-300 font-bold">
                {unreadCount} Unread
              </span>
            )}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time alerts for impending deadlines, unreviewed proposals, and capacity warnings.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-xs px-3 py-1.5 rounded-xl bg-canvas-card hover:bg-slate-800 border border-slate-700 text-slate-300 transition"
            >
              Mark all as read
            </button>
          )}
          <button
            onClick={clearAll}
            className="text-xs px-3 py-1.5 rounded-xl bg-canvas-card hover:bg-rose-950/40 border border-slate-700 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 transition flex items-center gap-1"
          >
            <Trash2 className="w-3.5 h-3.5" /> Clear All
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {notifications.length === 0 ? (
          <div className="surface-card p-12 text-center text-slate-400 space-y-3">
            <Bell className="w-12 h-12 text-slate-600 mx-auto" />
            <p className="text-base font-bold text-slate-300">All caught up!</p>
            <p className="text-xs text-slate-500">
              You will receive alerts here when deadlines approach or AI proposals require your approval.
            </p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={cn(
                "surface-card surface-card-hover p-4 sm:p-5 flex items-start justify-between gap-4 transition",
                !n.is_read
                  ? "border-sky-500/40 bg-canvas-card/90"
                  : "border-slate-800/80 bg-canvas-card/40 opacity-75"
              )}
            >
              <div className="flex items-start gap-3.5 flex-1">
                <div className="p-2 rounded-xl bg-canvas-subtle border border-slate-800 flex-shrink-0 mt-0.5">
                  {getTypeIcon(n.type)}
                </div>

                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-white">{n.title}</h3>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-cyber-amber-400 animate-pulse" />
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
                    {n.message}
                  </p>
                  <div className="flex items-center gap-4 pt-2 text-[11px] text-slate-500">
                    <span>{n.timestamp}</span>
                    {n.action_href && (
                      <Link
                        href={n.action_href}
                        className="font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1"
                      >
                        <span>{n.action_label}</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={() => deleteNotification(n.id)}
                className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition flex-shrink-0"
                title="Dismiss"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
