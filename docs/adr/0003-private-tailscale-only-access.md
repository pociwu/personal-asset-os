# Expose the system only through Tailscale

正式 Web不開放 OCI公網 Port，而由主機上的 Tailscale Serve提供 HTTPS並轉送至本機 Nginx；應用層仍保留 Owner登入。此設計以新裝置必須加入 tailnet的成本，換取顯著較小的公網攻擊面及較簡單的憑證管理。
