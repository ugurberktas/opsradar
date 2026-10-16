import * as React from "react";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  FileText,
  AlertCircle,
  Server,
  Menu,
  X,
  ChevronLeft,
  Play,
  Sun,
  Moon,
} from "lucide-react";
import { Button } from "./ui";
import { useApp } from "../lib/store";

const NAV = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Logs", href: "/logs", icon: FileText },
  { name: "Incidents", href: "/incidents", icon: AlertCircle },
  { name: "Services", href: "/services", icon: Server },
];

function classNames(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, setTheme } = useApp();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [current, setCurrent] = useState("/dashboard");

  useEffect(() => {
    setCurrent(window.location.pathname || "/dashboard");
  }, []);

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  return (
    <div className="flex h-screen overflow-hidden">
      <aside
        className={classNames(
          "fixed inset-y-0 left-0 z-20 w-64 border-r border-border bg-card transition-all duration-300",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center gap-2 h-12 px-4">
            <div className="w-7 h-7 rounded bg-primary/20 flex items-center justify-center">
              <Play className="w-4 h-4 text-primary" />
            </div>
            <span className="font-bold text-lg tracking-tight">OpsRadar</span>
          </div>
          <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
            {NAV.map((item) => {
              const Icon = item.icon;
              const active = current === item.href;
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    setCurrent(item.href);
                    window.history.pushState("", "", item.href);
                  }}
                  className={classNames(
                    "flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium transition",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </button>
              );
            })}
          </nav>
          <div className="p-3 space-y-2">
            <Button
              onClick={toggleTheme}
              variant="ghost"
              className="w-full justify-between"
            >
              <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </aside>

      {mobileSidebar && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileSidebar(false)}
        />
      )}

      <div className="flex-1 flex flex-col overflow-hidden relative">
        <div
          className={classNames(
            "absolute left-0 top-0 z-50 transition-all duration-300",
            sidebarOpen ? "ml-64" : "ml-0"
          )}
        >
          <div className="flex items-center justify-between h-12 px-4 border-b border-border bg-background/80 backdrop-blur">
            <button
              onClick={() => setMobileSidebar((p) => !p)}
              className="md:hidden p-2 -ml-1 -mr-1 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-4">
              <span className="text-xs font-mono text-muted-foreground">
                opsradar.local
              </span>
              <button
                onClick={() => setSidebarOpen((p) => !p)}
                className="p-1 -ml-1 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground md:hidden"
              >
                {sidebarOpen ? (
                  <ChevronLeft className="h-5 w-5" />
                ) : (
                  <X className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        <main
          className={classNames(
            "flex-1 overflow-y-auto p-6 md:px-8 transition-all duration-300",
            sidebarOpen ? "ml-64" : "ml-0"
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
