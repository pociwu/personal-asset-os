# Personal Asset OS Domain

Personal Asset OS 是單一 Owner 私人使用的資產管理系統。本文件只定義正式領域語言，不包含實作細節。

## Language

**Owner／系統擁有者**：  
唯一可登入並擁有本 Personal Asset OS 實例的人。  
_Avoid_: User、Member、登入 Account

**Financial Account／金融帳戶**：  
券商、銀行或其他資產保管位置；Phase 1 主要指證券帳戶。  
_Avoid_: 登入帳號、Owner Account

**Asset／資產標的**：  
由市場與代號共同識別的金融商品，例如 `TWSE + 00919`；不包含 Owner 持有的數量。  
_Avoid_: Holding、Position

**Holding／持股**：  
某個金融帳戶目前持有某項 Asset 的彙總數量與平均成本；代表現況而非交易事件。  
_Avoid_: Transaction、Order

**Transaction／交易**：  
買入、賣出、費用或稅額等會改變持股或現金的事件。Phase 1 修改 Holding 不構成 Transaction。  
_Avoid_: Holding Update

**Market／市場**：  
Asset 的交易場所；Phase 1 僅包含上市 `TWSE` 與上櫃 `TPEx`。  
_Avoid_: Currency

**Quote／行情**：  
某項 Asset 在特定時間、來源與幣別下的價格觀測；Phase 1 只有 Mock Quote。  
_Avoid_: Holding Value

**Portfolio／投資組合**：  
所有有效金融帳戶中未封存 Holdings 的集合。  
_Avoid_: Account

**Archived／封存**：  
不再出現在一般操作畫面，但仍保留資料與 audit紀錄的狀態；不是永久刪除。  
_Avoid_: Deleted、Purged

**Market Value／目前市值**：  
Holding 數量乘以最新可用 Quote。Phase 1 的目前市值必須標示為 Mock。  
_Avoid_: Cost

**Unrealized Profit or Loss／未實現損益**：  
目前市值減投入成本，不包含已賣出的交易。  
_Avoid_: Realized Profit

**Realized Profit or Loss／已實現損益**：  
由已發生的賣出交易產生的損益；必須由 Phase 4 交易帳本計算。  
_Avoid_: Unrealized Profit

**Phase Gate／階段閘門**：  
某 Phase 所有必要任務完成後執行的整體驗收。  
_Avoid_: 單一任務測試、Agent自我宣告完成
