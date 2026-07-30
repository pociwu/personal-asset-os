import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { App } from "./App";

test("renders the private Phase 0 system status", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("{}", {
      status: 200,
      headers: { "Content-Type": "application/json" }
    })
  );

  render(<App />);

  expect(
    screen.getByRole("heading", { name: "Personal Asset OS" })
  ).toBeInTheDocument();
  expect(screen.getByText("僅限 Tailscale 私人網路")).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getAllByText("正常")).toHaveLength(2);
  });
});

test("shows an unavailable dependency without hiding backend liveness", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const path = String(input);
    return new Response("{}", {
      status: path.endsWith("/ready") ? 503 : 200
    });
  });

  render(<App />);

  await waitFor(() => {
    expect(screen.getByText("正常")).toBeInTheDocument();
    expect(screen.getByText("尚未就緒")).toBeInTheDocument();
  });
});
