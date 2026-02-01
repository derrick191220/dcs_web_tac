# QA / Release Flow (Xiao Ou Loop v2.0)

This project follows a strict end‑to‑end verification pipeline before any GitHub push or production confirmation.

## ✅ Xiao Ou Loop v2.0 (Required)

1) **需求变更确认**
   - 明确需求变更范围与影响面（前端/后端/数据/部署）。
   - 形成简短变更清单（要改什么/影响什么/验证点）。

2) **设计完善（先设计后实现）**
   - 更新/补齐设计文档（中英文双语）。
   - 明确：数据模型、API 契约、UI 交互与性能约束。

3) **代码编写**
   - 按模块完成实现（FastAPI / Cesium / ACMI 解析等）。
   - 保持结构化与可追踪改动。

4) **本地联调（后端 + 前端）**
   - 后端启动并可服务 API。
   - 前端（Vite）能拉取 `/api/sorties` 与 `/api/sorties/:id/telemetry`。

5) **本地无头浏览器诊断（Playwright）**
   - 运行本地诊断脚本，确保无关键错误与崩溃。
   - 若存在错误 → **返回第 3 步继续修复**。

6) **无错误时提交 GitHub**
   - 所有本地验证通过后才允许提交与推送。

7) **扫描 Render 线上控制台**
   - 使用 `doctor.py` 进行线上控制台错误扫描。
   - 若发现错误 → **返回第 3 步继续修复**。

8) **流程写入文档**
   - 任何流程变更必须同步更新本文件。

---

## 常用命令清单

### 后端测试
```bash
python3 -m pytest tests/test_api.py
```

### 前端构建
```bash
cd frontend
npm run build
```

### 线上全链路自检（Render）
```bash
python3 doctor.py
```

---

## 注意事项

- 当前允许 ArcGIS 外部影像（暂时未执行纯离线瓦片替换）。
- `vite.config.js` 的 `outDir` 指向 `../static`，构建时会清空 `static/`，必须确保模型与 Cesium 资源通过 `frontend/public` 或构建产物输出。
