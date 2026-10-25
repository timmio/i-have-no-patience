# 實際載入前後：進度對照與可追溯證據

**證據收集日：2026-10-25，時區 UTC+08:00。研究線凍結窗口截至 08:38:12。**

## 結論先講

- **不是只有把 Skill 放進資料夾。** 安裝工具留下 5 檔完整性收據，Hermes 的 `skill_view` 實際回傳完整指令；還原路徑展開後，內容與本專案 `SKILL.md` 完全相同。
- **載入後的可驗證交付：** 本機 Budget Guard 的 18 個測試通過；本文、原始測試輸出與去識別化證據隨專案一起提供。
- **同一段期間，既有研究線從 2 次手動觸發，走到 2 次手動 + 13 次內建排程觸發。** 共保存 15 份研究輸出；執行帳本均記錄 `completed`、`delivered`，不再只是「已設定排程」。
- **但不能把這 13 次排程進展全部歸功於 Skill。** 研究線是獨立 session，讀回設定為 `skills: []`、工具僅 `web`；沒有證據證明那些模型上下文也載入本 Skill。研究主題也有重複，15 份輸出不等於 15 個不同的已驗收任務。
- **Native 自治 Worker、不可繞過的模型預算入口仍未獲證明。** 不發布虛構的上線成功、Token 節省率或生產力提升百分比。

## 1. 可比較的前後狀態

| 面向 | 載入前基線 | 載入後／本次發布整理 | 可以下的結論 |
|---|---|---|---|
| Skill 安裝 | 尚無成功安裝／載入收據 | 5 檔逐一 SHA-256 比對一致 | 本機安裝已驗證 |
| Skill 真正載入 | 尚無本 Skill 的成功工具回傳 | `skill_view` 成功、`readiness_status=available`、回傳完整內容 | 主對話確實取得 Skill 指令，不是只宣稱啟用 |
| Budget Guard | 尚未由助手重現套件測試；不代表原測試失敗 | 首次載入後 18/18；發布前重新檢查仍 18/18 | 本機 Guard 行為可測；不是全模型硬預算 |
| 研究線 A | 已有 A-R01、A-R02，2 次手動執行與接續證據 | 同一既有研究線保存 A-R01～A-R15；另外 13 次為 `builtin` 且有 `scheduled_instant` | 定時執行、產生報告與排程器記錄的交付已實際發生 |
| 研究品質／新穎性 | 未獨立評分 | 部分題目重複；未獨立重查每份報告 | 不能把報告數直接當作不同任務完成數 |
| GitHub | 尚未發布 | 本文與證據成為待推送的發布內容；遠端狀態以 GitHub 實際頁面／commit 為準 | 本地檔案、Git commit、遠端可見是不同里程碑 |
| Native 自治編碼 | 未證明運行；安全／簽核阻擋保留 | 本次發布沒有執行受保護回歸，沒有新 Native 運行證據 | 不宣稱 Skill 修好了原生隔離或自治編碼 |
| 模型呼叫硬攔截 | 未整合可信入口 | 仍未證明所有呼叫都經過不可繞過的 Guard | 不宣稱強制控制所有 Token 或帳單 |

**這是一份觀察紀錄，不是對照實驗。** 前後時間、任務、上下文與排程並未控制一致；只能描述發生了什麼，不能證明因果。基線中的兩次研究也早於 Skill 載入，不能拿來充當 Skill 的成果。

## 2. 實際載入的證據鏈

1. **安裝收據：** 歷史安裝工具 exit 0，輸出 `INSTALLED_VERIFIED 5`；本次再讀回 5 個安裝檔，逐一比對本專案原始發行雜湊。
2. **載入收據：** 歷史 `skill_view` 工具事件回傳 `success=true`、`name=i-have-no-patience`、完整 `content`。
3. **內容核對：** Hermes 把 `${HERMES_SKILL_DIR}` 展開為本機路徑。發布證據只將該已知路徑還原為變數；還原後內容與 repo 內原始 `SKILL.md` 完全一致。
4. **範圍限制：** 工具回傳能證明指令被提供給主對話，不能證明模型每輪遵從、其他 session 也載入，或模型呼叫已被強制攔截。

證據：

- [skill-load-receipt.json](evidence/skill-load-receipt.json)：事件 ID、記錄時間、載入欄位、內容 SHA、5 檔 SHA 與比對結果。
- [skill-loaded.normalized.txt](evidence/skill-loaded.normalized.txt)：實際回傳內容的路徑正規化副本。
- [original-v1.0.0-manifest.json](evidence/original-v1.0.0-manifest.json)：原始交付包的清單，不因新增本文而回寫歷史。

這些是從本機工具紀錄擷取的可稽核投影，**不是第三方簽章或不可偽造的遠端證明**。沒有公開原始 session DB、帳號資料、Token 或本機絕對路徑。部分歷史訊息時間不單調，故保留事件 ID 和原始時間，不以它計算效率。

## 3. 載入後實際跑過的測試

命令：

```bash
python -m unittest discover -s tests -v
```

- 首次載入後的保存輸出：`Ran 18 tests in 0.898s`、`OK`、exit 0。
- 本次發布前的保存輸出：`Ran 18 tests in 1.167s`、`OK`、exit 0。
- 這兩個耗時只記錄實際輸出，**不是效能比較**。
- 覆蓋項目包含 SQLite 重啟讀回、多連線預留、重複請求拒絕、無新產出停止、未知用量保守扣帳、安全 STOP、範圍拒絕等；以測試檔與逐項輸出為準。

原始輸出：

- [首次載入後測試](evidence/tests-first-after-load.txt)
- [發布前檢查](evidence/tests-publication-check.txt)
- [測試事件收據](evidence/test-receipts.json)

**測試的對象是可合作使用的本地 Budget Guard，不是可信模型 Broker、OS 隔離或 Native Worker。**

## 4. 研究線的真實推進，不混淆為 Skill 效果

凍結窗口內，逐筆對照原始輸出檔與本機排程執行帳本：

- 載入前：**2** 筆 `source=direct`，A-R01、A-R02。
- 載入後：新增 **13** 筆 `source=builtin`，A-R03～A-R15，每筆都有排程時刻。
- 合計 **15** 筆 `status=completed`、`delivery_outcome=delivered`，與保存的 15 份輸出一一對應。
- `delivered` 是**排程器記錄**，不是證明人類已閱讀 Telegram。
- 研究報告中的外部文件結論是當時的模型產出，本次未重新研究所有來源，也不是本專案單元測試的驗收對象。

[完整索引與逐筆執行欄位](evidence/research-run-index.json) 包含原始檔 SHA、輸出片段 SHA、時間、來源與交付狀態。`evidence/research/` 只保存報告正文，移除原始 prompt 與本機 routing 資訊。

### 仍存在的空轉跡象

A-R02、A-R06、A-R10、A-R14 都回到「唯讀研究與執行權限分離」；A-R03、A-R07、A-R11、A-R15 也反覆研究 continuity。這證明**排程有持續執行，不證明新穎性或有用成果持續增加**。

本次只收集與發布證據，沒有擅自改動研究線權限、提示詞、模型或既有 STOP。若未來要宣稱 Skill 能改善這種重複，必須先證明該研究 session 真正載入 Skill，再用同一任務集、相同完成標準與實際模型用量做新的對照；不能回頭修改這批紀錄。

## 5. 尚未測得，明確不宣稱

- 每個真正完成任務的 Token、費用或節省比例。
- 因果上的速度提升、減少幾輪審查或整體成功率提升。
- 所有研究輸出都不同、都正確，或都通過外部驗收。
- Native Worker、Handle／Job／TOCTOU／Ledger／人工簽核已因此合格。
- 強制模型路由、Worker 防繞過或跨供應商帳單硬上限已部署。

[comparison-facts.json](evidence/comparison-facts.json) 提供機器可讀的基線、後續狀態與未測量欄位；[RELEASE_MANIFEST.json](../RELEASE_MANIFEST.json) 覆蓋本次發布的內容雜湊。
