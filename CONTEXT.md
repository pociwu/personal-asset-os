# Personal Asset OS Domain

Personal Asset OS 是單一 Owner 私人使用的資產管理系統。本文件只定義正式領域語言，不包含實作細節。

## Language

**Owner／系統擁有者**：  
唯一可登入並擁有本 Personal Asset OS 實例的人。  
_Avoid_: User、Member、登入 Account

**Financial Account／金融帳戶**：  
券商、銀行或其他資產及現金的保管位置。證券帳戶可指定一個供未來交易使用的預設交割銀行帳戶。
_Avoid_: 登入帳號、Owner Account

**Settlement Bank Account／交割銀行帳戶**：
目前與證券帳戶連結、預設承接未來股票買入扣款及賣出入款的銀行金融帳戶。
_Avoid_: Brokerage Account、Cash Wallet

**Trade Settlement Bank／交易交割銀行**：
一筆交易確認時實際指定、永久隨交易及待交割款保存的銀行帳戶；不受證券帳戶日後更換預設交割銀行影響。
_Avoid_: Current Settlement Bank、Mutable Account Link

**Cash Balance／現金餘額**：
某銀行金融帳戶依起始餘額及已完成交割的現金事件累積出的帳面餘額，不包含待交割款，也不代表銀行即時同步餘額。
_Avoid_: Available Credit、Bank API Balance

**Cash Event／現金事件**：
起始日後已實際發生、會改變某銀行帳戶現金餘額的非股票交割事實，例如存入、提領、轉帳、利息、銀行費用或其他調整。
_Avoid_: Balance Edit、Pending Settlement

**Backdated Cash Event／補登現金事件**：
在實際發生日之後才輸入、但依原發生日納入現金帳本的帳務起始日後現金事件。
_Avoid_: Current Cash Event、Balance Adjustment

**Cash Transfer／現金轉帳**：
在兩個系統內銀行帳戶間移動同額本金的單一現金事件，由互相關聯的來源流出與目的流入共同表示。
_Avoid_: Independent Withdrawal and Deposit、Bank Transfer Execution

**Cash Outflow Shortfall／現金流出不足**：
一筆提領、轉出、銀行費用或其他流出會使銀行現金為負，或使既有買入待交割應付款失去足額現金的無效狀態。
_Avoid_: Overdraft、Warning Only

**Accounting Start Date／帳務起始日**：
Personal Asset OS開始要求完整交易紀錄的單一開帳日期；更早的資產狀態由期初現金及期初持股摘要承接。
_Avoid_: First Trade Date、Import Date

**Opening Cash Balance／期初現金**：
銀行金融帳戶在帳務起始時點已完成交割的現金餘額，作為後續現金事件的計算基準。
_Avoid_: Deposit Transaction、Pending Settlement

**Opening Holding／期初持股**：
證券帳戶在帳務起始時點持有某項 Asset 的數量及移動平均成本，作為後續交易計算的起點。
_Avoid_: Synthetic Buy、Historical Transaction

**Opening Pending Settlement／期初待交割款**：
帳務起始日前已成交、但在開帳時點尚未完成的買入應付款或賣出應收款；只承接未完成的現金效果，不再次改變期初持股或成本。
_Avoid_: Opening Cash Balance、Synthetic Trade

**Asset／資產標的**：  
由市場與代號共同識別的金融商品，例如 `TWSE + 00919`；不包含 Owner 持有的數量。  
_Avoid_: Holding、Position

**Holding／持股**：  
某個證券帳戶目前持有某項 Asset 的彙總數量與移動平均成本；代表交易累積後的現況。
_Avoid_: Transaction、Order

**Share Quantity／股數**：
台股買賣、期初持股及目前持股使用的整數單位；每筆買賣可為任意正整數股，因此同時涵蓋整張與零股。
_Avoid_: Lot Count、Fractional Share

**Transaction／交易**：  
買入、賣出、費用或稅額等會改變持股、成本或現金餘額的事實。
_Avoid_: Holding Update

**Backdated Transaction／補登交易**：
在實際成交時間之後才輸入、但依原成交順序納入帳務的帳務起始日後交易。
_Avoid_: Current Transaction、Opening Holding Adjustment

**Aggregated Trade／合併成交**：
同一證券帳戶、Asset、方向及成交日的一段連續成交，以總股數、成交總額及最終費稅記為一筆交易；反向交易穿插時不得跨越合併。
_Avoid_: Daily Net Trade、Rounded Average Price Trade

**Broker Reference／券商參考編號**：
券商在委託、成交或對帳資料中提供、可協助辨識外部交易的選填編號；不同於系統內部交易識別。
_Avoid_: Transaction ID、Owner-Generated Number

**Suspected Duplicate／疑似重複交易**：
沒有可驗證券商參考編號，但關鍵交易內容與既有交易高度相同、需要Owner再次確認的候選交易。
_Avoid_: Confirmed Duplicate、Automatic Rejection

**Transaction Correction／交易更正**：
參照一筆已確認交易、保留其原始內容，並以新的正式內容取代其帳務效果的關聯紀錄。
_Avoid_: Edit Transaction、Delete Transaction

**Correction Conflict／更正衝突**：
套用交易更正並重算後續帳務時，會造成超賣、負持股、交割現金不足或其他領域規則違反的無效結果。
_Avoid_: Correction Warning、Partial Correction

**Transaction Charge／交易費稅**：
券商就一筆股票交易實際收取的手續費、交易稅或其他明列費用；Owner確認的最終金額才屬於正式帳務。
_Avoid_: Charge Estimate、Default Fee Rate

**Charge Estimate／費稅預估**：
系統依交易內容及設定規則提出、供Owner確認或修改的交易費稅建議值，不代表券商實際扣款。
_Avoid_: Transaction Charge、Actual Charge

**Trade Date／成交日**：
股票買入或賣出成交的日期；持股、成本及損益以成交日認列。
_Avoid_: Settlement Date、Created Date

**Trade Sequence／成交順序**：
由成交日、成交時間及必要時由 Owner 指定的同時成交序號所決定的交易先後；用於依序重算可賣數量、移動平均成本及損益。
_Avoid_: Created Order、Input Order

**Settlement Date／交割日**：
股票交易依市場交割日曆完成款項收付的日期；台股買賣採成交日後第二個市場交割日 `T+2`。
_Avoid_: Trade Date、Calendar Day Plus Two

**Market Settlement Calendar／市場交割日曆**：
辨識特定市場哪些日期可辦理交割的正式日曆，包含週末、休市日及臨時停止交割日。
_Avoid_: Gregorian Calendar、Weekdays Only

**Pending Settlement／待交割款**：
股票已成交但尚未到交割日的買入應付款或賣出應收款，不屬於銀行帳戶的已交割現金餘額。
_Avoid_: Cash Balance、Completed Payment

**Settlement-Available Cash／交割可用現金**：
交割銀行帳戶的已交割現金餘額，扣除同帳戶所有尚未付款的買入待交割應付款；賣出待交割應收款在實際交割前不得計入。
_Avoid_: Pending Sale Proceeds、Projected Net Settlement

**Settlement Cash Shortfall／交割現金不足**：
一筆買入交易及既有待交割義務會使指定交割銀行帳戶在交割日無法全額付款的無效狀態；必須先修正相關帳務，不能只以警示接受。
_Avoid_: Negative Cash Balance、Warning Only

**Sellable Quantity／可賣數量**：
同一證券帳戶及 Asset 在指定成交時點已持有且尚未被其他已確認賣出占用的數量，包含同日較早買入的數量；賣出數量不得超過此數量，Holding 不得成為負數。
_Avoid_: Shortable Quantity、Future Buy Quantity

**Moving Average Cost／移動平均成本**：
同一證券帳戶及 Asset 每次買入後，以累積持股成本除以累積數量所得的每股成本；賣出不改變剩餘持股的每股平均成本。
_Avoid_: FIFO Cost、Specific Lot Cost

**Market／市場**：  
Asset 的交易場所；Phase 1 僅包含上市 `TWSE` 與上櫃 `TPEx`。  
_Avoid_: Currency

**Quote／行情**：  
某項 Asset 在特定市場日期、來源與幣別下的價格觀測；第一階段只使用每日正式收盤價，不提供盤中即時行情。
_Avoid_: Holding Value

**Daily Closing Price／每日收盤價**：
TWSE或TPEx就某項Asset及市場日期發布的正式收盤價格，或Owner保留原值後確認的更正價格。
_Avoid_: Intraday Quote、Mock Quote

**Stale Price／過期價格**：
預期市場日期的正式收盤價尚未取得時，暫時沿用的最後成功每日收盤價；必須同時揭露其價格日期及過期狀態。
_Avoid_: Current Price、Zero Price

**Portfolio／投資組合**：  
所有有效金融帳戶中未封存 Holdings 的集合。  
_Avoid_: Account

**Archived／封存**：  
金融帳戶停止接受新交易、現金事件或預設連結，並退出一般操作畫面，但仍完整保留歷史資料及audit的狀態；不是永久刪除。
_Avoid_: Deleted、Purged

**Market Value／目前市值**：  
Holding 數量乘以最新可用的每日收盤價；從未取得價格時為未知，不得以零計算。
_Avoid_: Cost

**Incomplete Valuation／估值不完整**：
投資組合至少一項有效持股缺少可用價格，因而無法形成完整市值或損益總額的狀態；可計算部分只能稱為已定價小計。
_Avoid_: Zero-Valued Holding、Portfolio Total

**Unrealized Profit or Loss／未實現損益**：  
目前市值減投入成本，不包含已賣出的交易。  
_Avoid_: Realized Profit

**Realized Profit or Loss／已實現損益**：  
賣出淨收入減去依賣出數量及當時移動平均成本計算的轉出成本。
_Avoid_: Unrealized Profit

**Cash Dividend／現金股利**：
Asset發放的現金股利總額；各項實際扣除另行記錄，淨額才存入指定銀行帳戶，且不降低持股的移動平均成本。
_Avoid_: Sale Proceeds、Cost Reduction

**Dividend Deduction Estimate／股利扣除預估**：
依公開股利資料及現行規則計算、供Owner核對的可能扣除金額，不代表私人帳戶實際扣款。
_Avoid_: Actual Deduction、Confirmed Net Dividend

**Net Cash Dividend／現金股利淨額**：
現金股利總額扣除Owner依券商或銀行明細確認的代扣稅、補充保費、匯費及其他實扣後的銀行入帳金額。
_Avoid_: Gross Dividend、Estimated Deposit

**Total Investment Profit or Loss／總投資損益**：
帳務起始日以來的未實現損益、已實現損益及現金股利淨額合計。
_Avoid_: Realized Profit、Market Value

**Gold Holding／黃金持有**：
Owner持有的實體黃金或黃金存摺彙總數量，以公克為共同計算單位並保留原始輸入單位。
_Avoid_: Stock Holding、Gold Price

**Gold Purity／黃金純度**：
實體黃金中可按黃金基準價估值的比例；黃金存摺視為完整公克數，不另套純度折減。
_Avoid_: Recovery Discount、Craftsmanship Fee

**Gold Reference Price／黃金參考價**：
臺灣銀行新臺幣黃金存摺本行買進價，作為每公克可變現價的首選估值基準；臺銀頁面不可用時，採櫃買中心 AU9901 臺銀金買進報價並由每台錢換算為每公克。兩者都不是Owner實際成交保證價，系統必須保存實際來源。
_Avoid_: Purchase Price、Guaranteed Recovery Price

**Gold Valuation Override／黃金估值覆寫**：
Owner依實際回收報價確認、用來取代黃金參考價的每公克估值，必須附估值日期及原因。
_Avoid_: Gold Reference Price、Silent Price Edit

**Insurance Policy／保單**：
Owner持有的保險契約及其保費、給付、現金價值與有效狀態；累計保費本身不等於資產。
_Avoid_: Investment Holding、Premium Asset

**Policy Cash Value／保單現金價值**：
保單在特定估值日期可列入目前資產的Owner確認金額；不是累計保費，也不代表保證給付。
_Avoid_: Total Premium、Policy Profit

**Salary Record／薪資紀錄**：
一次由Owner確認的薪資收入，包含實領金額、入帳銀行及選填的收入與扣除明細。
_Avoid_: Recurring Transfer、Automatic Payroll

**Salary Template／薪資範本**：
供下次薪資草稿重複使用的公司、發薪日、預設銀行及選填明細，不會自行產生正式入帳。
_Avoid_: Confirmed Salary、Scheduled Deposit

**Opening Non-stock Asset／期初非股票資產**：
帳務起始時已持有的黃金或保單摘要，不追溯建立銀行扣款或虛構歷史交易。
_Avoid_: Historical Purchase、Backdated Bank Withdrawal

**Valuation Reminder／估值提醒**：
指出估值資料可能過期但仍保留於資產總額的提示；黃金門檻為30天，保單現金價值門檻為一年。
_Avoid_: Zero Valuation、Automatic Write-down

**Phase Gate／階段閘門**：  
某 Phase 所有必要任務完成後執行的整體驗收。  
_Avoid_: 單一任務測試、Agent自我宣告完成
