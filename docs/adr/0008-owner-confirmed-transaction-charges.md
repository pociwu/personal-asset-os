---
status: accepted
---

# Treat Owner-confirmed transaction charges as authoritative

Personal Asset OS可依券商費率設定、交易方向及Asset類別自動預估手續費與交易稅，但預估值只用於減少輸入，Owner可依券商對帳資料修改，最終確認值才影響買入成本、賣出淨收入、銀行交割金額及已實現損益。系統必須保留預估值、最終值及修改audit；這比完全自動套用費率多一個確認步驟，但能處理券商折扣、最低手續費、Asset稅率差異及費率變動，避免估算誤差污染正式帳務。
