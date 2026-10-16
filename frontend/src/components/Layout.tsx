import { ReactNode, useState } from "react";
import {
  AlertCircle,
  FileText,
  LayoutDashboard,
  Menu,
  Moon,
  Radar,
  RefreshCw,
  Server,
  Sun,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { Button } from "./ui";
import { useApp } from "../lib/store";
import { cn } from "../lib/utils";

const NAVIGATION = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Logs Explorer", href: "/logs", icon: FileText },
  { name: "Incidents", href: "/incidents", icon: AlertCircle },
  { name: "Services", href: "/services", icon: Server },
];

export function Layout({ children }: { children: ReactNode }) {
  const { errors, loading, refresh, setTheme, theme } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);
  const requestError = Object.values(errors).find(Boolean);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-slate-950/70 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border/80 bg-card/95 shadow-2xl backdrop-blur transition-transform md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-border/70 px-5">
          <NavLink to="/dashboard" className="flex items-center gap-3" onClick={() => setMobileOpen(false)}>
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/15 ring-1 ring-primary/30">
              <Radar className="h-5 w-5 text-primary" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-base font-semibold tracking-tight">OpsRadar</span>
              <span className="block text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Local SRE console</span>
            </span>
          </NavLink>
          <button
            type="button"
            aria-label="Close navigation"
            className="rounded-md p-2 text-muted-foreground hover:bg-accent md:hidden"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav aria-label="Primary navigation" className="flex-1 space-y-1 p-3">
          {NAVIGATION.map(({ name, href, icon: Icon }) => (
            <NavLink
              key={href}
              to={href}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive
                    ? "bg-primary/15 text-primary ring-1 ring-inset ring-primary/20"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {name}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border/70 p-3">
          <Button
            type="button"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            variant="ghost"
            className="w-full justify-between"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border/70 bg-background/85 px-4 backdrop-blur md:px-8">
          <button
            type="button"
            aria-label="Open navigation"
            className="rounded-md p-2 text-muted-foreground hover:bg-accent md:hidden"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.55)]" />
            Local environment
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => void refresh()} disabled={loading.dashboard}>
            <RefreshCw className={cn("mr-2 h-3.5 w-3.5", loading.dashboard && "animate-spin")} />
            Refresh data
          </Button>
        </header>

        <main id="main-content" className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 md:p-8">
          {requestError && (
            <div role="alert" className="mb-5 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              Some data could not be loaded. {requestError}
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
