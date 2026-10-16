/**
 * Regression test for the request/render loop bug.
 *
 * The original implementation had two mount-triggered refreshes (provider and
 * dashboard), and development StrictMode replays mount effects. This suite
 * renders the real dashboard in StrictMode and verifies one bounded fetch.
 *
 * This test asserts the fetch methods are invoked a bounded number of times
 * (once on initial mount via AppProvider's own effect) and do not spiral into
 * a loop.
 */

import { describe, it, expect, vi, beforeEach, afterEach, afterAll } from "vitest";
import { StrictMode } from "react";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";

// vi.mock is hoisted above imports, so mocks must be created inline here.
vi.mock("../lib/api", () => ({
  apiService: {
    services: vi.fn(),
    dashboard: vi.fn(),
    incidents: vi.fn(),
    logs: vi.fn(),
  },
}));
vi.mock("../components/Charts/ErrorTrend", () => ({ ErrorTrend: () => <div /> }));
vi.mock("../components/Charts/SeverityDonut", () => ({ SeverityDonut: () => <div /> }));
vi.mock("../components/Charts/ServiceHealth", () => ({ ServiceHealth: () => <div /> }));

import { apiService } from "../lib/api";
import { AppProvider } from "../lib/store";
import { Dashboard } from "../pages/Dashboard";
import App from "../App";

const mockServices = vi.mocked(apiService.services);
const mockDashboard = vi.mocked(apiService.dashboard);
const mockIncidents = vi.mocked(apiService.incidents);
const mockLogs = vi.mocked(apiService.logs);

// Probe only renders; it does NOT call refresh. All fetching is driven by
// AppProvider's own mount effect, mirroring Dashboard's real usage.
function Probe() {
  return <div data-testid="probe">probe</div>;
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, "", "/dashboard");
  mockServices.mockResolvedValue({ data: [] } as any);
  mockDashboard.mockResolvedValue({ data: {
    total_services: 0,
    healthy_services: 0,
    warning_services: 0,
    critical_services: 0,
    active_incidents: 0,
    incidents_by_severity: {},
    incidents_by_status: {},
    recent_events: [],
    error_trend: [],
    service_health: [],
  } } as any);
  mockIncidents.mockResolvedValue({ data: [] } as any);
  mockLogs.mockResolvedValue({ data: [] } as any);
});

afterEach(() => {
  cleanup();
});

afterAll(() => {
  vi.restoreAllMocks();
});

describe("AppProvider request loop regression", () => {
  it("calls each fetch method exactly once on mount (no render loop)", async () => {
    render(
      <StrictMode>
        <AppProvider>
          <Dashboard />
        </AppProvider>
      </StrictMode>
    );

    // Wait for the initial fetch cycle to settle.
    await waitFor(() => screen.getByRole("heading", { name: "Dashboard" }));

    // Small delay to catch any runaway re-renders that would fire more calls.
    await new Promise((r) => setTimeout(r, 250));

    expect(mockServices).toHaveBeenCalledTimes(1);
    expect(mockDashboard).toHaveBeenCalledTimes(1);
    expect(mockIncidents).toHaveBeenCalledTimes(1);
    expect(mockLogs).toHaveBeenCalledTimes(1);
  });

  it("does not re-fetch when state updates from a successful fetch", async () => {
    mockServices.mockResolvedValue({
      data: [{ id: 1, name: "svc", environment: "production", status: "healthy", last_heartbeat: null, log_count: 0, incident_count: 0 }],
    } as any);
    mockDashboard.mockResolvedValue({
      data: {
        total_services: 1,
        healthy_services: 1,
        warning_services: 0,
        critical_services: 0,
        active_incidents: 0,
        incidents_by_severity: {},
        incidents_by_status: {},
        recent_events: [],
        error_trend: [],
        service_health: [],
      },
    } as any);
    mockIncidents.mockResolvedValue({ data: [] } as any);
    mockLogs.mockResolvedValue({ data: [] } as any);

    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    );

    await waitFor(() => screen.getByTestId("probe"));
    await new Promise((r) => setTimeout(r, 250));

    // State updates from the fetch must NOT trigger additional fetches.
    expect(mockServices).toHaveBeenCalledTimes(1);
    expect(mockDashboard).toHaveBeenCalledTimes(1);
    expect(mockIncidents).toHaveBeenCalledTimes(1);
    expect(mockLogs).toHaveBeenCalledTimes(1);
  });
});

describe("application navigation", () => {
  it("uses router navigation without reloading the page", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: "Dashboard" });

    fireEvent.click(screen.getByRole("link", { name: "Logs Explorer" }));

    await screen.findByRole("heading", { name: "Logs Explorer" });
    expect(window.location.pathname).toBe("/logs");
    expect(mockDashboard).toHaveBeenCalledTimes(1);
  });
});
