import { useEffect, useState } from "react";

type ServiceState = "checking" | "available" | "unavailable";

interface ServiceStatus {
  backend: ServiceState;
  dependencies: ServiceState;
}

const initialStatus: ServiceStatus = {
  backend: "checking",
  dependencies: "checking"
};

const statusLabel: Record<ServiceState, string> = {
  checking: "檢查中",
  available: "正常",
  unavailable: "尚未就緒"
};

export function App() {
  const [status, setStatus] = useState<ServiceStatus>(initialStatus);

  useEffect(() => {
    const controller = new AbortController();

    void checkServices(controller.signal).then((nextStatus) => {
      if (!controller.signal.aborted) {
        setStatus(nextStatus);
      }
    });

    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">PRIVATE · OWNER ONLY</p>
        <h1 id="page-title">Personal Asset OS</h1>
        <p className="intro">
          私人資產管理系統的安全基礎服務已建立。財務功能將在後續階段逐步開放。
        </p>
      </section>

      <section className="status-panel" aria-labelledby="status-title">
        <div>
          <p className="section-label">PHASE 0</p>
          <h2 id="status-title">系統狀態</h2>
        </div>
        <div className="status-grid" aria-live="polite">
          <StatusItem label="Backend" state={status.backend} />
          <StatusItem label="資料服務" state={status.dependencies} />
        </div>
      </section>

      <footer>
        <span>僅限 Tailscale 私人網路</span>
        <span aria-hidden="true">·</span>
        <span>不提供公開存取</span>
      </footer>
    </main>
  );
}

function StatusItem({ label, state }: { label: string; state: ServiceState }) {
  return (
    <div className="status-item">
      <span className={`status-dot status-dot--${state}`} aria-hidden="true" />
      <div>
        <span className="status-name">{label}</span>
        <strong>{statusLabel[state]}</strong>
      </div>
    </div>
  );
}

async function checkServices(signal: AbortSignal): Promise<ServiceStatus> {
  const [backend, dependencies] = await Promise.all([
    checkEndpoint("/api/v1/health", signal),
    checkEndpoint("/api/v1/health/ready", signal)
  ]);

  return { backend, dependencies };
}

async function checkEndpoint(
  path: string,
  signal: AbortSignal
): Promise<ServiceState> {
  try {
    const response = await fetch(path, {
      headers: { Accept: "application/json" },
      signal
    });
    return response.ok ? "available" : "unavailable";
  } catch {
    return "unavailable";
  }
}
