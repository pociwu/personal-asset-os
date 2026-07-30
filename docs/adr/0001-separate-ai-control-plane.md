# Separate the AI control plane from the product runtime

AI-PM、Codex及其他 Agent與 Personal Asset OS 可以位於同一台 OCI 主機，但不進入產品 Compose，也不共享正式 secrets、Docker socket或資料庫權限。這使控制面故障不會停止產品，並避免負責管理部署的 Agent同時成為被管理 Compose的一部分。
