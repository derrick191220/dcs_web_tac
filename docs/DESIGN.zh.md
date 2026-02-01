# 需求与设计文档 - DCS Web‑Tac（企业版）

> **版本**：v1.0（可自我迭代）
> **最后更新**：2026‑02‑01
> **负责人**：小鸥

本文档为**可落地实现**的需求设计文档，包含范围、流程、接口、数据、验收与非功能指标，可直接指导开发。

---

## 1. 愿景与目标
- 构建 Tacview 级别的 DCS World 回放分析平台。
- 提供高质量 3D 回放、HUD 遥测与分析能力。
- 稳定、可复现、可部署（Render）。

## 2. 核心原则
1. **技术卓越**：高性能后端（FastAPI）+ 专业级 3D（Cesium.js）。
2. **友好 UI**：Tailwind CSS，清晰的信息层级。
3. **实用功能**：ACMI 回放、任务浏览、性能指标。
4. **可靠安全**：事务性存储 + 安全后台处理。
5. **航空标准**：兼容 ACMI 2.1/2.2。
6. **文档规范**：API 文档 + 结构化设计。

---

## 3. 用户故事（MVP）
1. **上传真实 ACMI**，并在列表中看到 sortie。
2. **选择飞机**，回放其轨迹。
3. **实时 HUD** 展示高度/速度/G/姿态。
4. **自检健康**（诊断链路）。

---

## 4. 功能范围（V1）
### 4.1 数据导入
- 支持 `.acmi/.zip/.gz/.zip.acmi`
- 后台解析并写入 SQLite
- 不支持的格式需报错

### 4.2 数据浏览
- Sortie 列表（时间倒序）
- 飞机对象列表
- 支持按 `obj_id` 过滤 telemetry

### 4.3 回放
- 显示飞机位置与姿态
- 显示完整航迹
- HUD 基于最近采样更新

### 4.4 诊断
- 本地链路测试（pytest + headless）
- 线上 `doctor.py` 扫描

---

## 5. 交互流程（文字版）
### 5.1 上传流程
1) 点击 **Upload ACMI**
2) 选择文件
3) 前端 `POST /api/upload`
4) 后端后台解析
5) 前端刷新 sortie 列表

### 5.2 回放流程
1) 选择 sortie
2) 加载对象列表
3) 选择飞机
4) 拉取该飞机 telemetry
5) 3D 回放 + HUD

---

## 6. API 契约（V1）
### `GET /api/`
```json
{ "status": "DCS Web‑Tac Online", "version": "0.2.x" }
```

### `GET /api/sorties`
```json
[{"id":1,"mission_name":"...","pilot_name":"...","aircraft_type":"...","start_time":"...","map_name":null}]
```

### `GET /api/sorties/{id}/objects`
```json
[{"id":10,"sortie_id":1,"obj_id":"b1100","name":"F‑16C_50","type":"Air+FixedWing","coalition":"Blue","pilot":"Blade"}]
```

### `GET /api/sorties/{id}/telemetry?obj_id=...`
```json
[{"obj_id":"b1100","time_offset":1.0,"lat":25.0,"lon":54.4,"alt":1000,
  "roll":0.1,"pitch":0.0,"yaw":180.0,"ias":350,"g_force":1.1}]
```

### `POST /api/upload`
```json
{ "message": "Successfully uploaded <filename>" }
```

---

## 7. 数据模型
### 7.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name

### 7.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 7.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

---

## 8. 非功能指标
- **上传大小**：≥100MB
- **解析时间**：100MB < 60s（Render）
- **交互延迟**：<200ms
- **控制台错误**：0 致命错误

---

## 9. 验收标准（V1）
- 上传成功且 sortie 可见
- 飞机列表完整
- 选飞机可回放 + HUD 更新
- 本地+线上无致命报错

---

## 10. 风险与缓解
- **文件大** → 流式解析/批量写入
- **对象缺字段** → fallback 显示 obj_id
- **Cesium 延迟** → 初始化重试

---

## 11. 路线图（Tacview 对齐）
1) 时间轴控制（播放/暂停/倍速）
2) 事件标注（击落/发射/命中）
3) 图表（速度/高度/G）
4) 多机筛选
5) 实时 UDP 采集

---

## 12. QA 与发布
- 严格遵循 `docs/qa.md`（Xiao Ou Loop v2.0）
