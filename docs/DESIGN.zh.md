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

**参考基线**：Tacview **1.9.5**（当前版本）与 **1.9.6 Beta 1**（最新 Beta），来源于 Tacview 官方文档索引（更新于 2023‑07‑14）。

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
### 4.1 数据导入（含进度）
- 支持 `.acmi/.zip/.gz/.zip.acmi`
- 生成解析 Job（queued/running/done/failed）
- 进度：已处理字节/总字节，ETA（尽力）
- 完成提示：前端提示 + 刷新 sortie
- 不支持格式要明确报错

### 4.2 数据浏览（Tacview 类似能力）
- Sortie 列表（任务/时间/飞行员/机型/地图）
- 飞机列表 + 过滤（类型/阵营/飞行员/名称）
- 快速搜索（呼号/飞行员）
- 遥测支持窗口查询与降采样

### 4.3 回放（Tacview 类似能力）
- 时间轴控制：播放/暂停/拖动/倍速（0.5x–8x）
- 视角：跟随/自由/俯视
- HUD：高度/速度/G/姿态
- 航迹：全程/最近尾迹切换

### 4.4 回放准确性保障
- 单位/坐标校验（WGS‑84、米、节、度）
- 时间基准：ReferenceTime + time_offset 秒
- 姿态合理性检查（航向连续、俯仰/滚转范围）
- 可选抽样对比（渲染点 vs 原始遥测）

## 4.5 三维模型姿态驱动机制
- 每条遥测包含 **经纬度/高度 + yaw/pitch/roll（度）**
- Cesium 驱动链路：
  1) `SampledPositionProperty`（位置）
  2) `SampledProperty(Quaternion)`（姿态）
  3) `Transforms.headingPitchRollQuaternion` 生成四元数
- 模型随时间轴自动插值更新（无需手动插值）

## 4.6 之前姿态不准的原因
- ACMI 角度语义理解有误（NED/ENU 假设错误）
- 模型正向轴未校准（需要 yaw offset）
- 缺少可视化参考轴与验证流程

## 4.7 后续确保准确的改进
- 固化角度语义与转换规则（写入文档与代码）
- 模型轴校准参数（yawOffset/pitchSign/rollSign）
- 可视化姿态参考轴 + 数值 HUD 对照
- 自动检测姿态异常（逐帧差异阈值）
- 参考场景回归测试（直飞/爬升/滚转）

### 4.5 诊断
- 本地链路测试（pytest + headless）
- 线上 `doctor.py` 扫描 + 最新解析状态

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

## 6. 前端 UX/UI 设计（V1）
### 6.1 布局
- **顶部栏**：项目名、当前飞机、上传按钮、解析状态指示。
- **左侧栏**：Sortie 列表 + 过滤 + 飞机选择。
- **中间**：Cesium 3D 视图 + 时间轴控制。
- **右侧栏**：HUD 卡片（高度/速度/G/姿态）+ 小图（可选）。

### 6.2 关键组件
- **Upload ACMI 弹窗**：文件选择、进度条、状态（queued/running/done/failed）。
- **Sortie 列表**：任务名、时间、飞行员、机型、地图。
- **飞机选择器**：下拉 + 搜索（飞行员/呼号）。
- **时间轴**：播放/暂停、倍速（0.5x–8x）、拖动条、当前时间。
- **视角切换**：跟随/自由/俯视。
- **HUD**：高度、IAS、G、滚转/俯仰/航向、经纬度。

### 6.3 交互规则
- 上传 → 创建 job → 显示进度提示 → 完成后刷新 sortie。
- 选择 sortie 加载飞机列表；选飞机加载遥测。
- 拖动时间轴同步更新 HUD 和模型姿态。
- 空状态（无 sorties/无飞机/无遥测）。

### 6.4 视觉风格
- 深色航空主题，高对比。
- 数字仪表用紧凑字体。
- 颜色：蓝（友军）、红（敌军）、黄（当前轨迹）。

## 7. 工程标准与合规
- **ACMI 2.1/2.2**：字段解析、时间语义、对象元数据、坐标处理遵循 Tacview ACMI 规范。
- **坐标标准**：WGS‑84 经纬度（度），高度 MSL（米）。
- **姿态标准**：roll/pitch/yaw 单位为度（右手系），转换为 Cesium HPR。
- **单位标准**：IAS 节，Altitude 米，Time 秒。
- **数据完整性**：不静默丢数据，异常字段置 0 并记录告警。
- **可追溯性**：每次解析产生 job 记录（状态/耗时/错误）。

## 7. API 契约（V1）
### 错误返回（全局）
```json
{ "error": "string", "details": {"field": "reason"} }
```

### `GET /api/`
```json
{ "status": "DCS Web‑Tac Online", "version": "0.2.x" }
```

### `GET /api/sorties`
```json
[{"id":1,"mission_name":"...","pilot_name":"...","aircraft_type":"...","start_time":"...","map_name":null,
  "parse_status":"done"}]
```

### `GET /api/sorties/{id}/objects`
```json
[{"id":10,"sortie_id":1,"obj_id":"b1100","name":"F‑16C_50","type":"Air+FixedWing","coalition":"Blue","pilot":"Blade"}]
```

### `GET /api/sorties/{id}/telemetry`
**参数**：`obj_id`, `start`, `end`, `downsample`, `limit`
```json
[{"obj_id":"b1100","time_offset":1.0,"lat":25.0,"lon":54.4,"alt":1000,
  "roll":0.1,"pitch":0.0,"yaw":180.0,"ias":350,"g_force":1.1}]
```

### `POST /api/upload`
```json
{ "message": "Successfully uploaded <filename>", "job_id": "abc123" }
```

### `GET /api/jobs/{id}`
```json
{ "id":"abc123", "sortie_id":1, "status":"running", "progress_pct":42, "error":null }
```

### `GET /api/jobs/{id}/events`
```json
[{"ts":1700000000,"level":"info","message":"Parsing ACMI chunk 12/60"}]
```

---

## 8. 数据模型
### 8.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name, parse_status

### 8.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 8.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

### 8.4 Parse Jobs
- id, sortie_id, status, progress_pct, error, created_at, updated_at

---

## 9. 技术栈与权威性
- **Cesium.js**：行业标准 3D 地球/航迹引擎（航空/地理场景广泛使用）
- **FastAPI**：高性能现代 API 框架（Python 生态标准）
- **ACMI（Tacview）**：飞行回放领域事实标准
- **诊断**：pytest + Playwright + doctor.py

## 10. 技术难点与解决措施
1. **遥测数据量巨大** → 窗口查询 + 降采样 + 索引
2. **大文件解析** → 后台任务 + 进度跟踪 + 分块解析
3. **Cesium 性能** → 采样降密 + 懒加载渲染
4. **时间/单位准确性** → 严格转换 + 校验
5. **多机筛选** → 对象索引 + 服务端过滤
6. **Render 冷启动** → 初始化容错 + 重试

## 11. 非功能指标
- **上传大小**：≥100MB
- **解析时间**：100MB < 60s（Render）
- **交互延迟**：<200ms
- **控制台错误**：0 致命错误
- **遥测查询**：支持窗口查询与降采样
- **索引**：telemetry(sortie_id,obj_id,time_offset), objects(sortie_id)
- **安全**：上传大小限制、类型白名单、可选 token 鉴权

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

## 13. 文档自审清单（质量）
- ✅ 引用 Tacview 官方文档（版本基线已记录）
- ✅ API 契约包含错误与参数
- ✅ 单位/时间语义明确
- ✅ 性能目标与索引明确
- ✅ 验收标准可测试
