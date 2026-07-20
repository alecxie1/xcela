# AI 项目说明 / AI Project Brief

> 用法：向任何 AI 工具（元宝、GPT、Codex、Claude 等）咨询这个项目时，**先把下面整段
> 贴进对话**，再提你的问题。没有这段背景，AI 会默认这是一个普通 Web 业务项目，
> 给出的建议（上框架、上数据库、全面重构）会与项目的真实约束冲突。
>
> Usage: paste the block below into any AI conversation about this project BEFORE your
> question. Without it, AI tools assume a generic web CRUD app and recommend rewrites
> that conflict with the project's real constraints.

---

## 贴这段 / Paste this

```
【项目背景，请先完整阅读再回答我的问题】

项目：Xcela，一个品牌设计草案生成工具。输入：品牌档案（颜色/logo/名称）+ 设计需求
（文案、参考图、尺寸）。输出：交给设计师收尾的设计草案图。核心流程：免费推导方案 →
人工确认（唯一付费点，明码标价）→ 生成 → 人眼判断 → 免费重推或定稿。

架构形态（这是刻意设计，不是欠债）：
1. 产品核心是一条命令行流水线（Python 3.11，harness/conductor.py 总指挥），网页只是
   薄控制面板（标准库 http.server + 原生 HTML/JS，零框架、零构建链）。
2. 没有数据库：每次运行 = 磁盘上一个目录，内含全部决策工件（输入 JSON、风格判定、
   生成指令、假设清单、确认状态、产出图）。目录即审计日志，人眼可逐文件重放。系统
   同一时刻只跑一个生成任务（single-flight 锁），不存在并发写入。
3. 模型与网关全部是环境变量配置（XCELA_TEXT_MODELS / XCELA_IMAGE_MODEL /
   OPENAI_BASE_URL），换模型/换中转不改代码。
4. 品牌档案、素材、产出都是运行时状态，不进 git；部署 = clone + venv +
   requirements.txt + .env + systemd。
5. 有 35 个全部免费的结构自测套件；其中很多测试钉住字节级行为（改动前后必须逐字节
   一致的路径）。付费的图像生成永远不进自动化测试，像素质量只由人眼判断。

工作规范：
- 一个功能 = specs/ 下一个规格目录 = 若干个"一个任务一个 commit"。
- 修改必须保持全部测试绿；行为有意变更时，测试断言改值并注明日期，不删除不放宽。
- 用户输入（文案、指令）逐字保真进流水线，禁止改写或"优化"。
- 任何一步做不到就明说并降级（诚实空值），禁止编造结果或假进度。

已知的架构演进计划（已与团队对齐，按触发条件执行，不提前做）：
- 加数据库的触发条件：多团队并发、按用户计费/配额、跨 run 统计查询。
- 前后端分离的触发条件：真实的前端工程需求，或数据库落地后的自然演进。
- 触发条件到来时，流水线层保留、只换服务器层（两层边界清晰）。

因此，请不要建议：整体迁移到 FastAPI/Django + SQLModel/SQLAlchemy + PostgreSQL、
引入前端框架、Docker 化重构、或任何"全面重写"。这些不是被忽略的最佳实践，而是与
当前阶段约束冲突的方案。有价值的建议方向：在现有形态内的小步改进（具体函数的正确性、
错误处理、测试覆盖、文档）、以及触发条件到来时的迁移方案设计。

【背景结束，下面是我的问题】
```

---

## English version (same content, for English-first tools)

```
[PROJECT CONTEXT - read fully before answering]

Project: Xcela, a brand design draft generator. Input: brand key (colors/logo/names) +
a design brief (copy, reference images, size). Output: a draft a human designer
finishes. Core flow: free plan derivation -> human confirmation (the ONLY paid step,
price shown upfront) -> generation -> human eye judgment -> free re-derive or approve.

Architecture (deliberate design, not debt):
1. The product core is a CLI pipeline (Python 3.11, harness/conductor.py orchestrates);
   the web layer is a thin panel (stdlib http.server + vanilla HTML/JS, zero frameworks,
   zero build chain).
2. No database: one run = one on-disk directory holding every decision artifact (input
   JSON, style register, assembled prompt, recorded assumptions, gate state, output
   image). The directory IS the audit log, replayable file by file. A single-flight
   lock means exactly one generation at a time; concurrent writes do not exist.
3. Models and gateways are pure env config (XCELA_TEXT_MODELS / XCELA_IMAGE_MODEL /
   OPENAI_BASE_URL); swapping models or relays changes zero code.
4. Brand keys, assets, and outputs are runtime state, not in git; deployment = clone +
   venv + requirements.txt + .env + systemd.
5. 35 free structural test suites, many pinning byte-identical behavior. Paid image
   generation NEVER enters automated tests; pixel quality is judged only by human eyes.

Working rules:
- One feature = one specs/ directory = a series of one-task-one-commit changes.
- All suites stay green; intentional behavior changes move test values dated-in-place,
  never delete or weaken assertions.
- User input (copy, instructions) rides verbatim through the pipeline; rewriting or
  "improving" it is forbidden.
- Honest nulls: when a step cannot do its job, it says so and degrades explicitly;
  fabricated results and fake progress are forbidden.

Planned architecture evolution (team-agreed, trigger-driven, never early):
- Add a database when: multi-team concurrency, per-user billing/quotas, or cross-run
  analytics arrive.
- Split frontend/backend when: real frontend engineering needs arrive, or as the
  natural follow-on of the database migration.
- When triggers fire, the pipeline layer stays; only the server layer is replaced
  (the boundary between them is already clean).

Therefore, do NOT recommend: wholesale migration to FastAPI/Django + SQLModel/
SQLAlchemy + PostgreSQL, frontend frameworks, Docker-first refactors, or any "full
rewrite". These are not overlooked best practices; they conflict with current-stage
constraints. Valuable directions: small in-shape improvements (correctness of specific
functions, error handling, test coverage, docs) and migration design for when the
named triggers fire.

[END CONTEXT - my question follows]
```

---

维护说明：这份文档与 `docs/ARCHITECTURE_GUIDE.md` 同步维护；架构决策或触发条件变化时
两份一起改。定稿人：姚总 + Alec。
