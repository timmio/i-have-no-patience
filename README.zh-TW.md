# I Have No Patience ⚡

### 別再無腦燒 Token。別再審查審查。把交辦的事真正做完。

**給 Hermes、Claude Code、Codex、OpenCode 等工具型 AI Agent 的開源 Skill，另附可執行的預算紀錄／拒絕工具。**

[English README](README.md) · [真實開發經歷](skills/i-have-no-patience/references/CASE_STUDY.md) · [Token 守門的能力邊界](skills/i-have-no-patience/references/ENFORCEMENT.md)

> **只問一件事：你要的東西，真的在目標環境跑起來了嗎？**
>
> 如果交付物只有 ZIP、測試 PASS、審查收據，答案可能是：沒有。

## 我為什麼做這個 Skill？

這是我這幾週真實踩過的坑。

我組了 Hermes、本地模型、雲端模型、編碼 Agent、技能、排程、Supervisor、各種自動化框架。我只想讓它 **自主找工作 → 執行 → 驗證 → 回報 → 繼續下一件事**。

結果變成：

- 工程交付包堆到 **995、998 個檔案**，每個檔案的 SHA 都正確，還是沒有把自治 Worker 真正跑起來。
- **25/25、12/12** 等測試 PASS；後來連 Windows Runtime 讀取與執行的 **348/348**、寫入與改權限拒絕的 **2,447/2,447** 都有了。
- 我們研究 Ledger、Rollback、SQLite WAL/SHM、Windows Token、ACL、AccessCheck、Job、Desktop、TOCTOU、UAC、人類簽核與控制端。
- 一個問題剛修好，下一輪又多出另一個 Gate。一個拒絕導致整條自動化停住。每次都「STOP → 封裝 → 審查 → 再授權」。
- **驗收愈做愈漂亮，真正的自主編碼執行卻仍沒有上線證據。**

我終於受不了：我花的是自己的時間與寶貴的 Token，不是要幫 AI 生產無窮無盡的報告。

我並不是要求 AI 繞過必要的安全隔離；我要求的是 **不要把一個 Native Worker 的阻斷，拿來當作所有合法研究、規劃、整理與回報都不能繼續的理由**。

於是有了 **I Have No Patience**。

## 這個 Skill 會強制 AI 學會什麼？

| AI 原本常犯的錯 | 這個 Skill 的要求 |
|---|---|
| 長篇計畫、完成不了任務 | 先定義使用者看得見的 DONE，再直接行動 |
| Mock PASS 冒充正式上線 | 嚴格區分程式完成、本地測試、目標主機測試、服務運行 |
| 修一個錯就加一輪審查 | 凍結驗收標準，普通錯誤批次修復 |
| 單點 STOP 造成全部停工 | 僅阻斷有依賴關係的操作，其他既有授權工作繼續 |
| 無限制呼叫模型／重複審查 | Token 預留、呼叫上限、相同請求拒絕、無進展停止 |
| 安全拒絕後換模型硬闖 | 尊重 Safety Stop，不偷換 Provider 或擅自擴權 |

**但 Skill 文字本身無法強制阻止 API 呼叫。** 本專案附了 Python SQLite Budget Guard；必須由可信任的模型路由器在 **每一次呼叫前後** 強制使用，且 Worker 不能直接繞過路由器，才可能有真正的硬性預算控制。

## 實際加入後，進度推進多少？

[完整前後對照與證據](docs/VERIFIED_PROGRESS.zh-TW.md) · [實際載入收據](docs/evidence/skill-load-receipt.json) · [測試原始輸出](docs/evidence/tests-publication-check.txt)

- **真的載入：** 5 個安裝檔 SHA 一致；`skill_view` 回傳完整指令，還原路徑展開後與 repo 原文完全相同。
- **載入後可驗證交付：** Budget Guard 本機 **18/18** 測試通過，發布前再檢查仍通過。
- **同期間研究線進度：** 從 **2 次手動**，推進至 **2 次手動 + 13 次定時**；截至 2026-10-25 08:38，15 份輸出均有執行及排程器交付紀錄。
- **不灌水：** 研究線是另一個 session，設定 `skills: []`，不能宣稱那些執行也載入 Skill；題目有重複，15 份報告不等於 15 個不同的已驗收成果。
- **沒有假裝解鎖：** Native 自治編碼、可信模型入口硬預算、Token 節省率仍未證明。這是觀察證據，不是 Skill 因果效果實驗。

## 三分鐘安裝

Windows PowerShell，在本專案根目錄執行：

```powershell
New-Item -ItemType Directory -Force "$HOME\.hermes\skills\i-have-no-patience" | Out-Null
Copy-Item ".\skills\i-have-no-patience\*" "$HOME\.hermes\skills\i-have-no-patience" -Recurse -Force
hermes skills list
```

Linux / macOS：

```bash
mkdir -p ~/.hermes/skills
cp -R skills/i-have-no-patience ~/.hermes/skills/
hermes skills list
```

Hermes 啟動指令：

```text
/i-have-no-patience

直接完成目前已授權工作，提供目標主機真實執行證據。
不要新增無關 Gate、無限審查、假 PASS 或無意義的 Token 消耗。
保留所有安全 STOP、權限與人工簽核限制。
```

在根目錄跑實際單元測試（需要 Python 3.10+）：

```powershell
python -m unittest discover -s tests -v
```

預算政策範例：單任務 12,000 token、最多六次呼叫、連續兩次沒有新的產出就停止；這是可調整的範例，不是適用所有模型的最佳設定。具體部署與無法保證的部分請看 [ENFORCEMENT](skills/i-have-no-patience/references/ENFORCEMENT.md)。

## 這個專案不做的事

不偷提權、不修改 Production、不跳過正式安全驗收、不偽造人類批准、不用另一個 Provider 規避安全拒絕、不宣稱已有自動化硬預算整合、不把已寫好的 Skill 說成原來 Harness 已部署成功。

**目前實際交付：可安裝的 Skill + 本地可測的預算 Guard；不是已安裝到你家 Windows 主機的 Hermes 強制路由器。**

## 想讓更多人少浪費 Token？

如果你也遇過「Agent 連續五輪都在表示進展，結果根本沒部署」的情況，歡迎 ⭐ Star、分享實際失敗案例、送 PR 與可重現測試。我們衡量的不是產生多少報告，而是**每個真正完成的任務要花多少 Token**。

MIT License · [貢獻指南](CONTRIBUTING.md) · [安全說明](SECURITY.md)
