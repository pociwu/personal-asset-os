import { FormEvent, useCallback, useEffect, useState } from "react";

type Tab = "gold" | "insurance" | "salary";

interface BankAccount {
  id: string;
  name: string;
  balance: string;
}

interface Summary {
  bank_cash: string;
  gold_value: string | null;
  insurance_cash_value: string;
  total_assets: string;
  alerts: {
    gold_price_stale: boolean;
    gold_valuation_stale_count: number;
    policy_valuation_stale_count: number;
  };
}

interface GoldHolding {
  id: string;
  name: string;
  holding_type: string;
  quantity_grams: string;
  total_cost: string;
  average_cost_per_gram: string;
  market_value: string | null;
  valuation_date: string | null;
  valuation_stale: boolean;
}

interface GoldResponse {
  holdings: GoldHolding[];
  reference_price: string | null;
  reference_price_date: string | null;
  reference_price_stale: boolean;
  reference_price_source: string | null;
}

interface GoldTransaction {
  id: string;
  kind: string;
  occurred_on: string;
  quantity_grams: string;
  gross_amount: string;
  reversed: boolean;
}

interface Policy {
  id: string;
  insurer: string;
  name: string;
  policy_type: string;
  status: string;
  cumulative_premiums: string;
  cumulative_benefits: string;
  cash_value: string;
  valuation_date: string;
  valuation_stale: boolean;
}

interface InsuranceEvent {
  id: string;
  kind: string;
  occurred_on: string;
  amount: string;
  reversed: boolean;
}

interface SalaryRecord {
  id: string;
  employer: string;
  paid_on: string;
  net_amount: string;
  reversed: boolean;
}

interface SalaryTemplate {
  id: string;
  employer: string;
  default_pay_day: number;
  bank_account_id: string;
  earnings: Record<string, string>;
  deductions: Record<string, string>;
}

const today = new Date().toISOString().slice(0, 10);
const emptySummary: Summary = {
  bank_cash: "0.00",
  gold_value: null,
  insurance_cash_value: "0.00",
  total_assets: "0.00",
  alerts: {
    gold_price_stale: false,
    gold_valuation_stale_count: 0,
    policy_valuation_stale_count: 0
  }
};

export function App() {
  const [tab, setTab] = useState<Tab>("gold");
  const [banks, setBanks] = useState<BankAccount[]>([]);
  const [summary, setSummary] = useState<Summary>(emptySummary);
  const [gold, setGold] = useState<GoldResponse>({
    holdings: [],
    reference_price: null,
    reference_price_date: null,
    reference_price_stale: false,
    reference_price_source: null
  });
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [salaries, setSalaries] = useState<SalaryRecord[]>([]);
  const [salaryTemplates, setSalaryTemplates] = useState<SalaryTemplate[]>([]);
  const [goldTransactions, setGoldTransactions] = useState<GoldTransaction[]>(
    []
  );
  const [insuranceEvents, setInsuranceEvents] = useState<InsuranceEvent[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    try {
      const [
        nextBanks,
        nextGold,
        nextPolicies,
        nextSalaries,
        nextSalaryTemplates,
        nextGoldTransactions,
        nextInsuranceEvents
      ] = await Promise.all([
        api<BankAccount[]>("/api/v1/bank-accounts"),
        api<GoldResponse>("/api/v1/gold/holdings"),
        api<Policy[]>("/api/v1/insurance/policies"),
        api<SalaryRecord[]>("/api/v1/salary/records"),
        api<SalaryTemplate[]>("/api/v1/salary/templates"),
        api<GoldTransaction[]>("/api/v1/gold/transactions"),
        api<InsuranceEvent[]>("/api/v1/insurance/events")
      ]);
      const nextSummary = await api<Summary>("/api/v1/dashboard/assets-income");
      setBanks(nextBanks);
      setSummary(nextSummary);
      setGold(nextGold);
      setPolicies(nextPolicies);
      setSalaries(nextSalaries);
      setSalaryTemplates(nextSalaryTemplates);
      setGoldTransactions(nextGoldTransactions);
      setInsuranceEvents(nextInsuranceEvents);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "資料載入失敗");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const task = window.setTimeout(() => void reload(), 0);
    return () => window.clearTimeout(task);
  }, [reload]);

  async function submit(path: string, body: object, success: string) {
    try {
      await api(path, { method: "POST", body: JSON.stringify(body) });
      setMessage(success);
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "儲存失敗");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">PRIVATE · OWNER ONLY</p>
          <h1>Personal Asset OS</h1>
        </div>
        <span className="privacy-chip">Tailscale 私人存取</span>
      </header>

      <section className="summary-grid" aria-label="資產摘要">
        <SummaryCard label="資產合計" value={summary.total_assets} primary />
        <SummaryCard label="銀行現金" value={summary.bank_cash} />
        <SummaryCard label="黃金估值" value={summary.gold_value} />
        <SummaryCard
          label="保單現金價值"
          value={summary.insurance_cash_value}
        />
      </section>

      {(summary.alerts.gold_price_stale ||
        summary.alerts.gold_valuation_stale_count > 0 ||
        summary.alerts.policy_valuation_stale_count > 0) && (
        <aside className="alert" role="status">
          有估值資料需要更新；過期資料仍保留在資產合計中。
        </aside>
      )}

      {message && (
        <div className="notice" role="status">
          {message}
          <button type="button" onClick={() => setMessage("")}>
            關閉
          </button>
        </div>
      )}

      <section className="workspace">
        <div className="section-heading">
          <div>
            <p className="section-label">OTHER ASSETS &amp; INCOME</p>
            <h2>其他資產與收入</h2>
          </div>
          <nav className="tabs" aria-label="資產類型">
            {(["gold", "insurance", "salary"] as const).map((item) => (
              <button
                className={tab === item ? "active" : ""}
                key={item}
                onClick={() => setTab(item)}
                type="button"
              >
                {{ gold: "黃金", insurance: "保單", salary: "薪資" }[item]}
              </button>
            ))}
          </nav>
        </div>

        {banks.length === 0 ? (
          <BankSetup onSubmit={submit} />
        ) : loading ? (
          <p className="empty">資料載入中…</p>
        ) : tab === "gold" ? (
          <GoldPanel
            data={gold}
            transactions={goldTransactions}
            banks={banks}
            onSubmit={submit}
          />
        ) : tab === "insurance" ? (
          <InsurancePanel
            policies={policies}
            events={insuranceEvents}
            banks={banks}
            onSubmit={submit}
          />
        ) : (
          <SalaryPanel
            salaries={salaries}
            templates={salaryTemplates}
            banks={banks}
            onSubmit={submit}
          />
        )}
      </section>
    </main>
  );
}

function SummaryCard({
  label,
  value,
  primary = false
}: {
  label: string;
  value: string | null;
  primary?: boolean;
}) {
  return (
    <article className={`summary-card${primary ? " primary" : ""}`}>
      <span>{label}</span>
      <strong>{value === null ? "尚無估值" : formatTwd(value)}</strong>
    </article>
  );
}

function BankSetup({ onSubmit }: PanelProps) {
  return (
    <div className="onboarding">
      <div>
        <h3>先建立銀行帳戶</h3>
        <p>黃金、保單與薪資都會連動銀行現金。期初餘額只需輸入一次。</p>
      </div>
      <form
        onSubmit={(event) => {
          const data = formData(event);
          void onSubmit(
            "/api/v1/bank-accounts",
            { name: data.name, opening_balance: data.opening_balance },
            "銀行帳戶已建立"
          );
        }}
      >
        <Field label="帳戶名稱" name="name" placeholder="例：主要銀行" />
        <Field
          label="期初餘額"
          name="opening_balance"
          type="number"
          step="0.01"
        />
        <Submit>建立帳戶</Submit>
      </form>
    </div>
  );
}

interface PanelProps {
  onSubmit: (path: string, body: object, success: string) => Promise<void>;
}

function GoldPanel({
  data,
  transactions,
  banks,
  onSubmit
}: PanelProps & {
  data: GoldResponse;
  transactions: GoldTransaction[];
  banks: BankAccount[];
}) {
  const [mode, setMode] = useState<"opening" | "buy" | "sell">("opening");
  return (
    <div className="panel-grid">
      <div className="records">
        <div className="reference-line">
          <span>官方參考買進價</span>
          <strong>
            {data.reference_price
              ? `${formatTwd(data.reference_price)}／公克`
              : "尚未取得"}
          </strong>
          {data.reference_price_date && (
            <small>{data.reference_price_date}</small>
          )}
          {data.reference_price_source && (
            <small>
              {data.reference_price_source.includes("tpex")
                ? "來源：櫃買中心 AU9901 臺銀金"
                : "來源：臺灣銀行黃金存摺"}
            </small>
          )}
        </div>
        {data.holdings.length === 0 ? (
          <p className="empty">尚未建立黃金持有資料。</p>
        ) : (
          data.holdings.map((item) => (
            <article className="record-card" key={item.id}>
              <div>
                <span className="record-type">
                  {item.holding_type === "physical" ? "實體黃金" : "黃金存摺"}
                </span>
                <h3>{item.name}</h3>
                <p>
                  {item.quantity_grams} 公克 · 均價{" "}
                  {formatTwd(item.average_cost_per_gram)}
                </p>
              </div>
              <div className="record-value">
                <strong>
                  {item.market_value ? formatTwd(item.market_value) : "未知"}
                </strong>
                {item.valuation_stale && (
                  <span className="stale">估值過期</span>
                )}
              </div>
            </article>
          ))
        )}
        <History
          title="黃金紀錄"
          items={transactions.map((item) => ({
            id: item.id,
            label: `${item.occurred_on} · ${goldKindLabel(item.kind)}`,
            value: `${item.quantity_grams} 公克 · ${formatTwd(item.gross_amount)}`,
            reversed: item.reversed
          }))}
          onReverse={(id, reason) =>
            onSubmit(
              `/api/v1/gold/transactions/${id}/reverse`,
              { reason },
              "黃金紀錄已沖銷"
            )
          }
        />
      </div>
      <div className="entry-card">
        <Segmented
          value={mode}
          options={["opening", "buy", "sell"]}
          labels={{ opening: "期初", buy: "買入", sell: "賣出" }}
          onChange={setMode}
        />
        {mode === "opening" ? (
          <form
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                "/api/v1/gold/holdings",
                {
                  name: d.name,
                  holding_type: d.holding_type,
                  quantity: d.quantity,
                  unit: d.unit,
                  purity: d.holding_type === "passbook" ? "1" : d.purity,
                  total_cost: d.total_cost,
                  valuation_date: d.valuation_date || null,
                  valuation_price: d.valuation_price || null,
                  valuation_reason: d.valuation_price
                    ? "期初實際回收估值"
                    : null
                },
                "期初黃金已建立"
              );
            }}
          >
            <Field label="名稱" name="name" placeholder="例：黃金存摺" />
            <Select
              label="類型"
              name="holding_type"
              options={{ passbook: "黃金存摺", physical: "實體黃金" }}
            />
            <QuantityFields />
            <Field
              label="純度（0～1）"
              name="purity"
              type="number"
              step="0.0001"
              defaultValue="0.9999"
            />
            <Field label="總成本" name="total_cost" type="number" step="0.01" />
            <Field
              label="估值日期"
              name="valuation_date"
              type="date"
              defaultValue={today}
            />
            <Field
              label="實際回收價／公克（選填）"
              name="valuation_price"
              type="number"
              step="0.01"
              required={false}
            />
            <Submit>確認建立</Submit>
          </form>
        ) : (
          <form
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                "/api/v1/gold/transactions",
                {
                  holding_id: d.holding_id,
                  bank_account_id: d.bank_account_id,
                  kind: mode,
                  occurred_on: d.occurred_on,
                  quantity: d.quantity,
                  unit: d.unit,
                  gross_amount: d.gross_amount,
                  fees: d.fees || "0"
                },
                mode === "buy" ? "黃金買入已入帳" : "黃金賣出已入帳"
              );
            }}
          >
            <Select
              label="黃金項目"
              name="holding_id"
              options={toOptions(data.holdings)}
            />
            <Select
              label="銀行帳戶"
              name="bank_account_id"
              options={toOptions(banks)}
            />
            <Field
              label="交易日期"
              name="occurred_on"
              type="date"
              defaultValue={today}
            />
            <QuantityFields />
            <Field
              label="成交總額"
              name="gross_amount"
              type="number"
              step="0.01"
            />
            <Field
              label="費用"
              name="fees"
              type="number"
              step="0.01"
              defaultValue="0"
            />
            <Submit>
              {mode === "buy" ? "確認買入並扣款" : "確認賣出並入款"}
            </Submit>
          </form>
        )}
      </div>
    </div>
  );
}

function InsurancePanel({
  policies,
  events,
  banks,
  onSubmit
}: PanelProps & {
  policies: Policy[];
  events: InsuranceEvent[];
  banks: BankAccount[];
}) {
  const [mode, setMode] = useState<
    "opening" | "premium" | "benefit" | "valuation"
  >("opening");
  return (
    <div className="panel-grid">
      <div className="records">
        {policies.length === 0 ? (
          <p className="empty">尚未建立保單。</p>
        ) : (
          policies.map((item) => (
            <article className="record-card" key={item.id}>
              <div>
                <span className="record-type">{item.insurer}</span>
                <h3>{item.name}</h3>
                <p>
                  已繳 {formatTwd(item.cumulative_premiums)} · 已領{" "}
                  {formatTwd(item.cumulative_benefits)}
                </p>
              </div>
              <div className="record-value">
                <strong>{formatTwd(item.cash_value)}</strong>
                {item.valuation_stale && (
                  <span className="stale">估值過期</span>
                )}
              </div>
            </article>
          ))
        )}
        <History
          title="保單紀錄"
          items={events.map((item) => ({
            id: item.id,
            label: `${item.occurred_on} · ${insuranceKindLabel(item.kind)}`,
            value: formatTwd(item.amount),
            reversed: item.reversed
          }))}
          onReverse={(id, reason) =>
            onSubmit(
              `/api/v1/insurance/events/${id}/reverse`,
              { reason },
              "保單紀錄已沖銷"
            )
          }
        />
      </div>
      <div className="entry-card">
        <Segmented
          value={mode}
          options={["opening", "premium", "benefit", "valuation"]}
          labels={{
            opening: "期初",
            premium: "繳費",
            benefit: "給付",
            valuation: "估值"
          }}
          onChange={setMode}
        />
        {mode === "opening" ? (
          <form
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                "/api/v1/insurance/policies",
                {
                  insurer: d.insurer,
                  name: d.name,
                  policy_type: d.policy_type,
                  cumulative_premiums: d.cumulative_premiums || "0",
                  cumulative_benefits: d.cumulative_benefits || "0",
                  cash_value: d.cash_value || "0",
                  valuation_date: d.valuation_date
                },
                "期初保單已建立"
              );
            }}
          >
            <Field label="保險公司" name="insurer" />
            <Field label="保單名稱" name="name" />
            <Field label="保單類型" name="policy_type" placeholder="例：壽險" />
            <Field
              label="累計已繳保費"
              name="cumulative_premiums"
              type="number"
              step="0.01"
              defaultValue="0"
            />
            <Field
              label="累計已領金額"
              name="cumulative_benefits"
              type="number"
              step="0.01"
              defaultValue="0"
            />
            <Field
              label="目前現金價值"
              name="cash_value"
              type="number"
              step="0.01"
              defaultValue="0"
            />
            <Field
              label="估值日期"
              name="valuation_date"
              type="date"
              defaultValue={today}
            />
            <Submit>確認建立</Submit>
          </form>
        ) : (
          <form
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                `/api/v1/insurance/policies/${d.policy_id}/events`,
                {
                  kind: mode,
                  occurred_on: d.occurred_on,
                  amount: mode === "valuation" ? "0" : d.amount,
                  bank_account_id:
                    mode === "valuation" ? null : d.bank_account_id,
                  cash_value_after:
                    mode === "premium" ? null : d.cash_value_after || null,
                  status_after: mode === "benefit" ? d.status_after : null
                },
                "保單紀錄已入帳"
              );
            }}
          >
            <Select
              label="保單"
              name="policy_id"
              options={toOptions(policies)}
            />
            {mode !== "valuation" && (
              <Select
                label="銀行帳戶"
                name="bank_account_id"
                options={toOptions(banks)}
              />
            )}
            <Field
              label="日期"
              name="occurred_on"
              type="date"
              defaultValue={today}
            />
            {mode !== "valuation" && (
              <Field
                label={mode === "premium" ? "保費" : "實收給付"}
                name="amount"
                type="number"
                step="0.01"
              />
            )}
            {mode !== "premium" && (
              <Field
                label="給付後／目前現金價值"
                name="cash_value_after"
                type="number"
                step="0.01"
              />
            )}
            {mode === "benefit" && (
              <Select
                label="保單狀態"
                name="status_after"
                options={{ active: "繼續有效", ended: "保單結束" }}
              />
            )}
            <Submit>確認入帳</Submit>
          </form>
        )}
      </div>
    </div>
  );
}

function SalaryPanel({
  salaries,
  templates,
  banks,
  onSubmit
}: PanelProps & {
  salaries: SalaryRecord[];
  templates: SalaryTemplate[];
  banks: BankAccount[];
}) {
  const [mode, setMode] = useState<"record" | "template">("record");
  const [templateId, setTemplateId] = useState(templates[0]?.id ?? "");
  const selected = templates.find((item) => item.id === templateId);
  return (
    <div className="panel-grid">
      <div className="records">
        {salaries.length === 0 ? (
          <p className="empty">尚未登錄薪資。</p>
        ) : (
          salaries.map((item) => (
            <article className="record-card" key={item.id}>
              <div>
                <span className="record-type">{item.paid_on}</span>
                <h3>{item.employer}</h3>
              </div>
              <div className="record-value">
                <strong>{formatTwd(item.net_amount)}</strong>
                {item.reversed ? (
                  <span className="stale">已沖銷</span>
                ) : (
                  <button
                    className="text-button"
                    type="button"
                    onClick={() =>
                      requestReversal(item.id, (id, reason) =>
                        onSubmit(
                          `/api/v1/salary/records/${id}/reverse`,
                          { reason },
                          "薪資紀錄已沖銷"
                        )
                      )
                    }
                  >
                    沖銷
                  </button>
                )}
              </div>
            </article>
          ))
        )}
      </div>
      <div className="entry-card">
        <Segmented
          value={mode}
          options={["record", "template"]}
          labels={{ record: "本月薪資", template: "薪資範本" }}
          onChange={setMode}
        />
        {mode === "record" ? (
          <form
            key={templateId}
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                "/api/v1/salary/records",
                {
                  employer: d.employer,
                  bank_account_id: d.bank_account_id,
                  paid_on: d.paid_on,
                  net_amount: d.net_amount,
                  earnings: detailObject(d, [
                    "base_salary",
                    "overtime",
                    "bonus",
                    "allowance"
                  ]),
                  deductions: detailObject(d, [
                    "labor_insurance",
                    "health_insurance",
                    "income_tax",
                    "other_deduction"
                  ]),
                  template_id: templateId || null
                },
                "薪資已確認入帳"
              );
            }}
          >
            {templates.length > 0 && (
              <label className="field">
                <span>套用範本</span>
                <select
                  value={templateId}
                  onChange={(event) => setTemplateId(event.target.value)}
                >
                  <option value="">不使用範本</option>
                  {templates.map((item) => (
                    <option value={item.id} key={item.id}>
                      {item.employer}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <Field
              label="公司／收入來源"
              name="employer"
              defaultValue={selected?.employer}
            />
            <Select
              label="入帳銀行"
              name="bank_account_id"
              options={toOptions(banks)}
              defaultValue={selected?.bank_account_id}
            />
            <Field
              label="入帳日期"
              name="paid_on"
              type="date"
              defaultValue={today}
            />
            <Field
              label="實領金額"
              name="net_amount"
              type="number"
              step="0.01"
            />
            <SalaryDetails defaults={selected} />
            <Submit>確認薪資入帳</Submit>
          </form>
        ) : (
          <form
            onSubmit={(event) => {
              const d = formData(event);
              void onSubmit(
                "/api/v1/salary/templates",
                {
                  employer: d.employer,
                  default_pay_day: Number(d.default_pay_day),
                  bank_account_id: d.bank_account_id,
                  earnings: detailObject(d, [
                    "base_salary",
                    "overtime",
                    "bonus",
                    "allowance"
                  ]),
                  deductions: detailObject(d, [
                    "labor_insurance",
                    "health_insurance",
                    "income_tax",
                    "other_deduction"
                  ])
                },
                "薪資範本已建立"
              );
            }}
          >
            <Field label="公司／收入來源" name="employer" />
            <Field
              label="預設發薪日"
              name="default_pay_day"
              type="number"
              min="1"
              max="31"
            />
            <Select
              label="預設銀行"
              name="bank_account_id"
              options={toOptions(banks)}
            />
            <SalaryDetails />
            <Submit>建立薪資範本</Submit>
          </form>
        )}
      </div>
    </div>
  );
}

function SalaryDetails({ defaults }: { defaults?: SalaryTemplate }) {
  return (
    <details className="salary-details">
      <summary>薪資與扣除明細（選填）</summary>
      <div className="details-grid">
        <Field
          label="本薪"
          name="base_salary"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.earnings.base_salary}
        />
        <Field
          label="加班費"
          name="overtime"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.earnings.overtime}
        />
        <Field
          label="獎金"
          name="bonus"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.earnings.bonus}
        />
        <Field
          label="津貼"
          name="allowance"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.earnings.allowance}
        />
        <Field
          label="勞保"
          name="labor_insurance"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.deductions.labor_insurance}
        />
        <Field
          label="健保"
          name="health_insurance"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.deductions.health_insurance}
        />
        <Field
          label="所得稅"
          name="income_tax"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.deductions.income_tax}
        />
        <Field
          label="其他扣除"
          name="other_deduction"
          type="number"
          step="0.01"
          required={false}
          defaultValue={defaults?.deductions.other_deduction}
        />
      </div>
    </details>
  );
}

function History({
  title,
  items,
  onReverse
}: {
  title: string;
  items: { id: string; label: string; value: string; reversed: boolean }[];
  onReverse: (id: string, reason: string) => Promise<void>;
}) {
  if (items.length === 0) return null;
  return (
    <section className="history">
      <h3>{title}</h3>
      {items.map((item) => (
        <div className="history-row" key={item.id}>
          <div>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
          {item.reversed ? (
            <span className="stale">已沖銷</span>
          ) : (
            <button
              className="text-button"
              type="button"
              onClick={() => requestReversal(item.id, onReverse)}
            >
              沖銷
            </button>
          )}
        </div>
      ))}
    </section>
  );
}

function requestReversal(
  id: string,
  onReverse: (id: string, reason: string) => Promise<void>
) {
  const reason = window.prompt("請輸入沖銷原因");
  if (reason?.trim()) void onReverse(id, reason.trim());
}

function goldKindLabel(kind: string) {
  return { opening: "期初", buy: "買入", sell: "賣出" }[kind] ?? kind;
}

function insuranceKindLabel(kind: string) {
  return (
    {
      opening: "期初",
      premium: "繳費",
      benefit: "給付",
      valuation: "估值"
    }[kind] ?? kind
  );
}

function QuantityFields() {
  return (
    <div className="field-row">
      <Field label="數量" name="quantity" type="number" step="0.00000001" />
      <Select
        label="單位"
        name="unit"
        options={{ gram: "公克", mace: "台錢", tael: "台兩" }}
      />
    </div>
  );
}

function Field({
  label,
  name,
  required = true,
  ...props
}: {
  label: string;
  name: string;
  required?: boolean;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="field">
      <span>{label}</span>
      <input name={name} required={required} {...props} />
    </label>
  );
}
function Select({
  label,
  name,
  options,
  defaultValue
}: {
  label: string;
  name: string;
  options: Record<string, string>;
  defaultValue?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select name={name} required defaultValue={defaultValue}>
        {Object.entries(options).map(([value, text]) => (
          <option value={value} key={value}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}
function Submit({ children }: { children: React.ReactNode }) {
  return (
    <button className="submit" type="submit">
      {children}
    </button>
  );
}

function Segmented<T extends string>({
  value,
  options,
  labels,
  onChange
}: {
  value: T;
  options: readonly T[];
  labels: Record<T, string>;
  onChange: (value: T) => void;
}) {
  return (
    <div className="segmented">
      {options.map((item) => (
        <button
          type="button"
          className={value === item ? "active" : ""}
          onClick={() => onChange(item)}
          key={item}
        >
          {labels[item]}
        </button>
      ))}
    </div>
  );
}

function formData(event: FormEvent<HTMLFormElement>): Record<string, string> {
  event.preventDefault();
  return Object.fromEntries(
    new FormData(event.currentTarget).entries()
  ) as Record<string, string>;
}
function detailObject(data: Record<string, string>, keys: string[]) {
  return Object.fromEntries(
    keys.filter((key) => data[key]).map((key) => [key, data[key]])
  );
}
function toOptions(
  items: { id: string; name?: string; employer?: string }[]
): Record<string, string> {
  return Object.fromEntries(
    items.map((item) => [item.id, item.name ?? item.employer ?? item.id])
  );
}
function formatTwd(value: string) {
  return new Intl.NumberFormat("zh-TW", {
    style: "currency",
    currency: "TWD",
    maximumFractionDigits: 2
  }).format(Number(value));
}

async function api<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    ...init
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: { message?: string };
    } | null;
    throw new Error(
      payload?.detail?.message ?? `操作失敗（${response.status}）`
    );
  }
  return (await response.json()) as T;
}
