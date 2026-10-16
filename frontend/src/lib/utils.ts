import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const secs = Math.floor((now.getTime() - d.getTime()) / 1000);
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function severityColor(sev: string): string {
  switch (sev) {
    case "CRITICAL": return "text-destructive bg-destructive/10 border-destructive/20";
    case "WARNING": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "INFO": return "text-primary bg-primary/10 border-primary/20";
    default: return "text-muted-foreground";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "healthy": return "text-emerald-400";
    case "warning": return "text-amber-400";
    case "critical": return "text-destructive";
    default: return "text-muted-foreground";
  }
}

export function truncate(str: string, n: number): string {
  if (!str) return "";
  return str.length > n ? str.slice(0, n) + "…" : str;
}
