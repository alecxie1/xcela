# Data Model: Deployment Readiness + Chinese-Ready UI (017)

## Brands base directory
| Item | Value |
|---|---|
| Source | env `XCELA_BRANDS_DIR`, default `<repo>/brands` |
| Consumers | `asset_paths.resolve_brand_asset` (scene_author x3, export_layers, persist) |
| Resolution order | absolute-and-exists > brands-relative > repo-relative > named SystemExit |

## Answer-key logo_path (rewritten committed data)
| Key | Old (absolute) | New (brands-relative) |
|---|---|---|
| answer_keys/CJXQ.json | /home/alecx/.../brands/CJXQ/jos cha logo.png | `CJXQ/jos cha logo.png` |
| answer_keys/chajiuxingqiu.json | /home/alecx/.../brands/... | brands-relative equivalent |
| answer_keys/aia.json | /home/alecx/.../brands/aia/assets/AIA-logo.png | `aia/assets/AIA-logo.png` |

`persist.place_logo` writes the brands-relative form for all future onboarding. Absolute
paths in uncommitted legacy keys keep working (resolution order).

## Run listing entry (`GET /runs`, from `run_view.list_runs`)
```json
{
  "id": "run_CJXQ_20260708_151506",
  "brand": "CJXQ",                  // run_meta.json, tolerant null
  "created": "2026-07-08T15:15:06", // parsed from the id's timestamp; dir mtime fallback
  "gate_state": "done",             // gate_state.json state, null for pre-015 dirs
  "image": true,                    // sign_s1/generated.png exists
  "export_state": "done"            // export_state.json state, null if never exported
}
```
Newest-first, limit 50, never raises (tolerant helpers). Root payload: `{"runs": [...]}`.

## Server environment knobs (all optional; defaults = today's behavior)
| Env | Default | Effect |
|---|---|---|
| XCELA_BIND | 127.0.0.1 | bind address (argv port still wins over XCELA_PORT) |
| XCELA_PORT | 8765 | port when no argv port given |
| XCELA_MAX_UPLOAD_MB | 32 | do_POST Content-Length cap -> 413 named |
| XCELA_WORKER_TIMEOUT_S | 1800 | `_spawn_worker` subprocess.run timeout -> named error file |
| XCELA_BRANDS_DIR | `<repo>/brands` | asset resolution base |

## Chinese usage vocabulary (added INSIDE existing tuples; multi-character only)
| Row (existing) | Added keywords |
|---|---|
| MARKETING_USAGE_KEYWORDS | 朋友圈 小红书 社交媒体 公众号 微博 营销 宣传 推广 海报 |
| event row (first) | 手举牌 举牌 应援 打卡 活动现场 |
| wall row | 上墙 墙贴 张贴 |
| formal hard row | 正式文件 公告 通知 |

Semantics inherited: first-match precedence, 014 suppression via MARKETING_USAGE_KEYWORDS
identity, 015 lane options untouched.

## Size normalization map (pre-pass in `resolve_size`; identity on ASCII)
| Input class | Normalized |
|---|---|
| ０-９ (fullwidth digits) | 0-9 |
| × Ｘ ｘ ＊ | x |
| 厘米 公分 | cm |
| 毫米 | mm |
| 英寸 | in |
| fullwidth space (U+3000) | removed |

## ZH display dict (frontend-only; English fallback)
Maps the CLOSED gate vocabulary: assumption dimension names, REGISTER_LANE_OPTIONS labels
("marketing piece" -> 营销物料, "hand-held event prop" -> 手举活动道具, "formal piece" ->
正式物料), render/dial names. Server payloads and submitted values unchanged.

## deploy/ artifacts (committed; secrets NEVER)
| File | Content |
|---|---|
| bootstrap.sh | venv + requirements + dirs + named presence checks for the 2 out-of-band items |
| xcela.service | systemd template: LANG=C.UTF-8, env knobs, Restart=on-failure |
| Caddyfile | reverse_proxy 127.0.0.1:8765, basic_auth + domain placeholders |
| README.md | exact handoff: clone, bootstrap, scp brands/ + ~/.hermes/.env, hash password, enable, restart-after-update, output/ retention |
