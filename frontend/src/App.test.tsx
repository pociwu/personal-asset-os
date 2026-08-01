import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { App } from "./App";

test("shows the consolidated assets and income workspace", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const path = String(input);
    const payload = path.endsWith("/bank-accounts")
      ? [{ id: "bank-1", name: "主要銀行", balance: "100000.00" }]
      : path.endsWith("/dashboard/assets-income")
        ? {
            bank_cash: "100000.00",
            gold_value: "40000.00",
            insurance_cash_value: "30000.00",
            total_assets: "170000.00",
            alerts: {
              gold_price_stale: false,
              gold_valuation_stale_count: 0,
              policy_valuation_stale_count: 0
            }
          }
        : path.endsWith("/gold/holdings")
          ? {
              holdings: [],
              reference_price: "4000.00",
              reference_price_date: "2026-08-01",
              reference_price_stale: false
            }
          : [];
    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  });

  render(<App />);

  expect(
    screen.getByRole("heading", { name: "Personal Asset OS" })
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: "其他資產與收入" })
  ).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getByText("官方參考買進價")).toBeInTheDocument();
    expect(screen.getByText("$170,000.00")).toBeInTheDocument();
  });
});

test("requires a bank account before linked records", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const path = String(input);
    const payload = path.endsWith("/dashboard/assets-income")
      ? {
          bank_cash: "0.00",
          gold_value: null,
          insurance_cash_value: "0.00",
          total_assets: "0.00",
          alerts: {
            gold_price_stale: false,
            gold_valuation_stale_count: 0,
            policy_valuation_stale_count: 0
          }
        }
      : path.endsWith("/gold/holdings")
        ? {
            holdings: [],
            reference_price: null,
            reference_price_date: null,
            reference_price_stale: false
          }
        : [];
    return new Response(JSON.stringify(payload), { status: 200 });
  });

  render(<App />);

  await waitFor(() => {
    expect(
      screen.getByRole("heading", { name: "先建立銀行帳戶" })
    ).toBeInTheDocument();
  });
});
