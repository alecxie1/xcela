# Xcela 架构说明（双语）/ Architecture Guide (bilingual)

> 状态：草稿 v1（2026-07-20，Alec 起草）。请姚总直接修改、补充、批注，我们一起定稿。
> Status: draft v1 (2026-07-20, drafted by Alec). 姚总: please edit directly; we finalize together.
>
> 这份文档回答三个问题：这个系统是什么形状、为什么是这个形状、以及怎么在上面安全地改代码。
> 深度技术细节在 `docs/ARCHITECTURE.md`（英文）；给 AI 工具的项目说明在 `docs/AI_PROJECT_BRIEF.md`。

---

## 1. 系统是什么形状 / What shape is this system

这不是一个"增删改查"的业务系统，它更像一间**暗房/工作台**：

- 用户的一次操作 = 一次 run = 磁盘上的一个目录（`output/run_<品牌>_<时间戳>/`）。
- 目录里是这次运行的**全部证据**：输入的需求（inputs.json）、推导出的风格判定
  （register_profile.json）、组装出的生成指令（final_prompt.txt）、系统替用户做的每一项
  假设（assumptions.json）、确认状态（gate_state.json）、生成的图、导出的图层。
- 任何时候出问题，打开这个目录就能**逐文件重放**整个决策过程。这是产品的核心承诺之一：
  机器的每一步判断都留痕、可审计，最终质量判断永远是人眼。

In one line: **one user action = one run = one on-disk directory of auditable artifacts.**
It is a pipeline with human gates, not a database-backed CRUD service.

## 2. 三个"没有"，为什么 / Three deliberate absences, and why

这三点不是"还没来得及做"，是**当前阶段的刻意选择**。每一点都写明了"什么时候应该改"，
这也是我们和姚总在群里达成的共识：MVP 阶段先验证可行性，验证通过就尽早做架构规范。

### 2.1 为什么现在没有数据库 / Why no database (yet)

- run 目录**就是**数据库：只增不改的工件文件，人眼可读，天然就是审计日志。
- 系统同一时刻只跑一个生成任务（single-flight 锁），没有并发写入，数据库解决的核心问题
  （并发一致性、复杂查询）现在还不存在。
- 产品形态还在快速变（最近四周加了确认门、分层导出、登录、改图模式），每次变动如果都要
  改表结构 + 迁移脚本，迭代速度会明显下降。

**什么时候加数据库（触发条件，到了就做）：**
1. 多个团队并发使用，出现排队瓶颈（single-flight 不够用了）；
2. 需要按用户计费/配额（用量必须可靠地记账）；
3. 需要跨 run 的查询统计（"这个品牌这个月生成了多少张、通过率多少"）。

### 2.2 为什么前后端没有分离 / Why no frontend/backend split (yet)

- 真正的产品是**命令行流水线**（`harness/conductor.py` 一条命令能跑完整个流程，完全不需要
  浏览器）；网页只是它上面的一层薄控制面板：提交表单、轮询工件、渲染结果。
- 网页层全部是标准库 + 原生 HTML/JS，零框架依赖：部署没有 npm/构建链，改一个页面就是改
  一个文件。对现在两三个人的使用规模，这是最低的维护成本。

**什么时候分离（触发条件）：** 出现真正的前端工程需求（实时协作、复杂交互态、专职前端
同学加入），或 2.1 的数据库落地后自然演进为 API 服务 + 前端应用。

### 2.3 为什么模型调用不写死 / Why models are config, not code

这一点已经做完了（020 + 姚总的 yaoyj 分支合并）：所有文本/视觉调用走
`harness/model_client.py` 一个入口，模型和网关全部是环境变量：

```
XCELA_TEXT_MODELS=gpt-5.5          # 文本/视觉模型链
XCELA_IMAGE_MODEL=gpt-image-2      # 生图模型
OPENAI_BASE_URL=<你们的中转地址>    # SDK 原生支持，无需改代码
```

姚总当时整个分支的需求，最终就是 `.env` 里的三行配置。这就是我们希望的协作方式：
**你们的部署差异全部落在配置层，代码层保持一份。**

## 3. 模块地图 / Module map

| 位置 | 干什么 |
|---|---|
| `harness/conductor.py` | 总指挥：读需求、按模式选路线、在人工确认门前停下 |
| `harness/scene_author.py` | 新设计路线的引擎：组装生成指令、调生图模型 |
| `harness/edit_author.py` | 改图路线的引擎（023）：逐字执行修改指令、区域遮罩 |
| `register/` | 风格判定引擎：品牌基因 vs 任务需要，逐维度调和 |
| `harness/format_size.py` | 尺寸解析：cm/px/中文单位 → 合法生成尺寸（保比例） |
| `harness/export_layers.py` | 分层导出（016）：定稿画面拆成逐元素透明图层 |
| `frontend/server.py` | 标准库 HTTP 服务：表单、轮询、登录门、品牌管理 |
| `frontend/*.html` | 四个页面：生成、录入品牌、品牌管理、使用手册 |
| `frontend/auth.py` | 登录核心（021）：users.json 存在才启用，scrypt 白名单 |
| `brand_intake/` | 品牌录入：VI 手册 PDF → 颜色/名称提取 → 人工确认 → 品牌档案 |
| `answer_keys/<品牌>.json` | 品牌档案（运行时状态，不进 git；部署各自维护） |
| `test_*.py`（35 个） | 全部免费的结构自测；付费验证只靠人眼 |

## 4. 一次运行的生命周期 / Anatomy of a run

```
表单提交（多部分上传：需求 JSON + 参考图/原图 + 产品图）
  → inputs.json 落盘（逐字保真，永不改写用户的话）
  → 免费推导：风格判定 + 生成指令 + 假设清单（零花费）
  → 015 确认门：用户看到全部假设和指令，可免费修改重推
  → 确认（唯一的花钱动作，幂等：重复点击不重复扣费）
  → 生成 → 人眼判断 → 满意定稿 / 写修改意见免费重推
  → 可选：分层导出（单独确认，单独标价）
```

设计上的两条铁律 / Two iron rules:
1. **确认之前零花费**，且每一分钱花之前都明码标价在按钮上。
2. **诚实的空值**：任何一步做不到，就明说做不到并降级，绝不编造结果
   （没有假进度条，没有模型自评的"通过"）。

## 5. 怎么在上面安全地改代码 / How to change it safely

1. **测试就是契约。** 35 个自测套件全部免费可跑（`.venv/bin/python test_<名字>.py`）。
   很多测试钉住的是**字节级行为**（例如"没有 users.json 时服务器响应和加登录前逐字节
   一致"）。改代码前先跑相关套件，改完必须全绿。
2. **一个任务一个提交。** 每个功能有 `specs/<编号>-<名字>/` 目录（spec/plan/tasks），
   每个 task 对应一个 commit。看 git log 就能看懂每一步为什么。
3. **钉子可以搬家，不能拔掉。** 行为有意变更时，把旧测试值改成新值并注明日期，
   绝不删除或放宽断言。
4. **付费调用永远不进自动化测试。** 生图的对错只有人眼能判，测试只管结构。
5. **涉及你们部署和使用的功能，动手之前方案先发姚总。**（群里的约定，写进文档作数。）

## 6. 部署即配置 / Deployment is configuration

```
git clone → python3.11 -m venv → pip install -r requirements.txt
→ 配 .env（模型、网关、密钥；全部变量见 .env.example）
→ frontend/server.py 起服务（deploy/ 里有 systemd + 反代模板）
```

- 品牌档案（answer_keys/）、素材（brands/）、产出（output/）都是**运行时状态**，
  不进 git：拉代码永远不会动你们的数据。
- 登录默认关闭；在服务器上用 `frontend/auth.py add <用户名>` 创建第一个用户即开启
  （详见 `docs/KEVIN_AUTH_GUIDE.md`）。

## 7. 约定与下一步 / Working agreement & next steps

- 这份文档由 Alec 起草、**姚总定稿**：哪里不对、哪里缺、哪里应该更严格，请直接改。
- 2.1/2.2 的触发条件是我们双方对"什么时候做架构升级"的共同判断依据；触发条件到了,
  升级方案我们一起设计（服务器层换成 FastAPI + 数据库时，流水线层可以原样保留，
  这两层的边界今天就是清晰的）。
- 给 AI 工具用的项目说明在 `docs/AI_PROJECT_BRIEF.md`：以后用元宝/GPT 分析这个项目，
  先把那份文档贴进对话，AI 的建议会准确得多。

---

## English summary (for reference)

**Shape.** A CLI pipeline with human gates, wrapped by a thin stdlib web panel. One user
action = one run = one on-disk directory of auditable artifacts (inputs, derived register,
assembled prompt, recorded assumptions, gate state, image, layers). The audit trail IS the
product promise: every machine judgment is inspectable; final quality judgment is human.

**Deliberate absences.** No database: run dirs are append-only, human-readable state; a
single-flight lock means no concurrent writers; the product shape is still moving weekly.
Triggers to add one: multi-team concurrency, per-user billing/quotas, cross-run analytics.
No FE/BE split: the CLI is the product; the web layer is a form + artifact poller in
vanilla HTML/JS with zero build chain. Trigger: real frontend engineering needs, or the
DB migration above. Models/gateways are already pure config (`model_client.py`,
`XCELA_TEXT_MODELS`, `OPENAI_BASE_URL`): Kevin's entire gpt-5.5 deployment diff is three
.env lines.

**Safety rails.** 35 free structural test suites, many pinning byte-identical behavior;
one spec → one task → one commit; pins move dated-in-place, never deleted; paid calls
never enter automated tests (the human eye is the only judge of pixels); features
touching the partner deployment get a written proposal to 姚总 before code.

**Agreement.** Drafted by Alec, finalized by 姚总. When the named triggers fire, we design
the upgrade together; the pipeline layer survives a server-layer rewrite because the
boundary between them is already clean.
