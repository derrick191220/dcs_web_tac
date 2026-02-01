# 设计文档 - DCS Web‑Tac（企业版）

## 1. 愿景与目标
- 构建 Tacview 级别的 DCS World 回放分析平台。
- 提供高质量 3D 回放、HUD 遥测和分析工具。
- 稳定可复现、可部署（Render）。

## 2. 核心原则
1. **技术卓越**：高性能异步后端（FastAPI）+ 专业级 3D 可视化（Cesium.js）。
2. **友好 UI**：Tailwind CSS 统一风格，数据与交互深度融合。
3. **实用功能**：ACMI 回放、任务浏览、飞行性能指标。
4. **可靠安全**：SQLite 事务性存储 + 后台任务处理。
5. **航空标准**：兼容 ACMI 2.1/2.2 与 DCS 约定。
6. **文档规范**：API 文档 + 结构化设计文档。

## 3. MVP 范围
- 上传 ACMI（.acmi/.zip/.gz/.zip.acmi）
- 解析 ACMI 并写入 SQLite
- Sortie 列表与飞机对象列表
- 选飞机回放 + HUD
- 健康检查与诊断

## 4. 数据模型
### 4.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name

### 4.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 4.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

## 5. 后端 API（v0）
- `GET /api/` → health
- `GET /api/sorties`
- `GET /api/sorties/{id}/objects`
- `GET /api/sorties/{id}/telemetry?obj_id=...`
- `POST /api/upload`

## 6. 前端交互
- 左侧：任务列表 + 飞机选择
- 中间：Cesium 3D 地球与航迹
- 右侧：HUD（高度/速度/G/姿态）
- 上传按钮（ACMI）

## 7. 渲染与回放
- Cesium `SampledPositionProperty` 平滑插值
- 模型姿态使用 ACMI yaw/pitch/roll（度）
- 航迹为全程尾迹

## 8. 性能约束
- 大型 ACMI：流式解析、批量入库
- 前端：按需采样/分段渲染，避免卡顿

## 9. 路线图（对齐 Tacview）
- 多机筛选（类型/阵营/飞行员）
- 时间轴控制（播放/暂停/倍速）
- 事件标注（击落/发射/命中）
- 图表（速度/高度/G）
- 实时 UDP 采集

## 10. QA 与发布
- 严格遵循 `docs/qa.md`（Xiao Ou Loop v2.0）
