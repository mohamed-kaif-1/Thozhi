import { redirect } from "next/navigation";

/**
 * Obsolete Memory Management Page
 *
 * Internal AI personalization mechanisms (duration priors, working hours, planning styles)
 * operate autonomously in the background. The user-facing administration interface has been removed.
 * Direct visits are redirected immediately to the main dashboard.
 */
export default function MemoryPage() {
  redirect("/");
}
