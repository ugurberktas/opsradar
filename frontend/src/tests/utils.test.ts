import { describe, it, expect } from "vitest";
import { formatRelativeTime, severityColor, statusColor, truncate } from "../lib/utils";

describe("formatRelativeTime", () => {
  it("returns 'just now' for sub-minute", () => {
    const now = new Date().toISOString();
    expect(formatRelativeTime(now)).toBe("just now");
  });
});

describe("severityColor", () => {
  it("maps CRITICAL to destructive", () => {
    expect(severityColor("CRITICAL")).toContain("text-destructive");
  });
  it("maps WARNING to amber", () => {
    expect(severityColor("WARNING")).toContain("text-amber-400");
  });
  it("maps INFO to primary", () => {
    expect(severityColor("INFO")).toContain("text-primary");
  });
});

describe("statusColor", () => {
  it("maps healthy to emerald", () => {
    expect(statusColor("healthy")).toContain("text-emerald-400");
  });
});

describe("truncate", () => {
  it("truncates long strings", () => {
    expect(truncate("abcdefghij", 5)).toBe("abcde…");
  });
  it("returns short strings unchanged", () => {
    expect(truncate("hi", 10)).toBe("hi");
  });
});
