# 农产品价格采集监控平台 API 文档

## 1. 基本信息

| 项目 | 内容 |
| --- | --- |
| 服务名称 | AgriPulse 农产品价格监控平台后端 |
| 默认地址 | `http://127.0.0.1:8080` |
| 当前演示地址 | `http://127.0.0.1:8081` |
| 接口前缀 | `/api` |
| 数据格式 | JSON |
| 认证方式 | `Authorization: Bearer <accessToken>` |

后端根路径可用于确认服务是否在线：

| 方法 | 地址 | 是否需要登录 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/` | 否 | 后端服务状态 |
| `GET` | `/api` | 否 | 后端服务状态 |
| `GET` | `/actuator/health` | 否 | Spring Boot 健康检查 |

## 2. 统一返回格式

成功响应：

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

失败响应：

```json
{
  "success": false,
  "message": "账号或密码不正确",
  "data": null
}
```

常见状态码：

| 状态码 | 含义 |
| --- | --- |
| `200` | 请求成功 |
| `400` | 请求参数错误 |
| `401` | 未登录或 Token 无效 |
| `403` | 权限不足 |
| `404` | 数据不存在 |
| `409` | 数据重复，例如账号已存在 |
| `500` | 服务内部错误 |

## 3. 登录认证

首次启动且 MongoDB 可写时，系统会创建默认管理员：

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `Agri@123456` | `admin` |

### 3.1 用户注册

| 项目 | 内容 |
| --- | --- |
| 方法 | `POST` |
| 地址 | `/api/auth/register` |
| 权限 | 公开 |

请求体：

```json
{
  "account": "zhangsan",
  "password": "Agri@123456",
  "name": "张三",
  "phone": "13800000000",
  "email": "zhangsan@example.com",
  "organization": "农产品价格监测中心"
}
```

响应数据 `data`：

```json
{
  "id": "665c...",
  "account": "zhangsan",
  "name": "张三",
  "phone": "13800000000",
  "email": "zhangsan@example.com",
  "role": "user",
  "organization": "农产品价格监测中心",
  "permissions": ["dashboard:read", "analysis:read", "alerts:read"],
  "active": true,
  "avatarUrl": null,
  "createdAt": "2026-06-01T12:00:00",
  "lastLoginAt": null
}
```

### 3.2 用户登录

| 项目 | 内容 |
| --- | --- |
| 方法 | `POST` |
| 地址 | `/api/auth/login` |
| 权限 | 公开 |

请求体：

```json
{
  "account": "admin",
  "password": "Agri@123456"
}
```

响应数据 `data`：

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "665c...",
    "account": "admin",
    "name": "平台管理员",
    "role": "admin",
    "permissions": ["dashboard:read", "users:write", "settings:write"],
    "active": true
  }
}
```

登录后访问业务接口：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

### 3.3 退出登录

| 项目 | 内容 |
| --- | --- |
| 方法 | `POST` |
| 地址 | `/api/auth/logout` |
| 权限 | 登录用户 |

请求体：

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

### 3.4 刷新 Token

| 项目 | 内容 |
| --- | --- |
| 方法 | `POST` |
| 地址 | `/api/auth/refresh-token` |
| 权限 | 公开 |

请求体：

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

### 3.5 当前用户

| 项目 | 内容 |
| --- | --- |
| 方法 | `GET` |
| 地址 | `/api/auth/me` |
| 权限 | 登录用户 |

### 3.6 修改当前用户密码

| 项目 | 内容 |
| --- | --- |
| 方法 | `PUT` |
| 地址 | `/api/auth/password` |
| 权限 | 登录用户 |

请求体：

```json
{
  "oldPassword": "Agri@123456",
  "newPassword": "Agri@654321"
}
```

### 3.7 忘记密码

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/reset-password` | 根据账号直接重置密码 |
| `POST` | `/api/auth/forgot-password` | 根据账号直接重置密码，兼容找回密码入口 |

请求体：

```json
{
  "account": "admin",
  "newPassword": "Agri@654321"
}
```

说明：当前演示版不再要求短信或邮箱验证码；密码重置成功后会撤销该用户已有 refresh token 会话，需要重新登录。

## 4. 监控大盘接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/dashboard/overview` | 登录用户 | 首页指标：采集量、市场数、产品数、预警数 |
| `GET` | `/api/dashboard/realtime` | 登录用户 | Redis 最新批次、最新价格、实时预警 |
| `GET` | `/api/dashboard/trend` | 登录用户 | 价格趋势折线图数据 |
| `GET` | `/api/dashboard/alerts` | 登录用户 | 首页预警摘要 |

`/api/dashboard/trend` 支持查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `product` | string | 否 | 产品名称，例如 `番茄` |
| `region` | string | 否 | 地区名称，例如 `山东` |

响应示例：

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "collectionRecords": 9668,
    "marketCount": 92,
    "productCount": 5,
    "alertCount": 3,
    "cards": [
      { "label": "今日采集记录", "value": 9668, "change": "+实时", "trend": "up" }
    ]
  }
}
```

## 5. 采集任务接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/tasks` | 登录用户 | 任务列表 |
| `POST` | `/api/tasks` | 登录用户 | 新增采集任务 |
| `PUT` | `/api/tasks/{id}` | 登录用户 | 编辑采集任务 |
| `POST` | `/api/tasks/{id}/start` | 登录用户 | 启动任务 |
| `POST` | `/api/tasks/{id}/stop` | 登录用户 | 停止任务 |
| `GET` | `/api/tasks/{id}/logs` | 登录用户 | 查看任务日志 |
| `GET` | `/api/tasks/{id}/status` | 登录用户 | 查看任务状态 |

`GET /api/tasks` 查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 否 | `all`、`running`、`stopped`、`error` |
| `keyword` | string | 否 | 按任务名称或来源搜索 |

新增任务请求体示例：

```json
{
  "id": "xf-001",
  "name": "北京新发地价格采集",
  "source": "新发地批发市场",
  "frequency": "5分钟/次",
  "status": "stopped",
  "successRate": 99.2,
  "backlog": 128
}
```

## 6. 价格分析接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/analysis/overview` | 登录用户 | 总体统计 |
| `GET` | `/api/analysis/product-statistics` | 登录用户 | 按产品统计 |
| `GET` | `/api/analysis/region-statistics` | 登录用户 | 按地区统计 |
| `GET` | `/api/analysis/region-price-difference` | 登录用户 | 地区价格差异 |
| `GET` | `/api/analysis/yearly-trend` | 登录用户 | 年度趋势 |
| `GET` | `/api/analysis/daily-trend` | 登录用户 | 日趋势 |
| `GET` | `/api/analysis/seasonal-price-change` | 登录用户 | 季节性变化 |
| `GET` | `/api/analysis/price-range-analysis` | 登录用户 | 价格区间分析 |
| `GET` | `/api/analysis/volatility` | 登录用户 | 波动规律 |
| `GET` | `/api/analysis/weather-correlation` | 登录用户 | 气象相关性 |
| `GET` | `/api/analysis/spark-sql` | 登录用户 | Spark SQL 分析结果 |
| `GET` | `/api/analysis/top-fluctuations` | 登录用户 | 最大波动记录 |
| `GET` | `/api/analysis/export` | 登录用户 | 导出分析结果 |

产品统计响应 `data` 示例：

```json
[
  {
    "product_name": "番茄",
    "product_category": "蔬菜类",
    "record_count": 620,
    "region_count": 31,
    "market_count": 92,
    "mean_price": 4.28,
    "min_price": 2.1,
    "max_price": 8.9
  }
]
```

## 7. 趋势预测接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/predictions` | 登录用户 | 预测结果列表 |
| `GET` | `/api/predictions/{product}` | 登录用户 | 单品类预测详情 |
| `GET` | `/api/predictions/{product}/factors` | 登录用户 | 影响因子权重 |
| `POST` | `/api/predictions/refresh` | 登录用户 | 手动刷新预测结果 |

预测列表响应 `data` 示例：

```json
[
  {
    "product": "番茄",
    "model": "timeSeries",
    "next7DayAverage": 4.62,
    "confidence": 0.86,
    "riskLevel": "medium",
    "updatedAt": "2026-06-01T12:00:00"
  }
]
```

## 8. 预警中心接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/alerts/rules` | 登录用户 | 预警规则列表 |
| `POST` | `/api/alerts/rules` | 登录用户 | 新增预警规则 |
| `PUT` | `/api/alerts/rules/{id}` | 登录用户 | 修改预警规则 |
| `DELETE` | `/api/alerts/rules/{id}` | 登录用户 | 删除预警规则 |
| `GET` | `/api/alerts/records` | 登录用户 | 预警记录列表 |
| `PUT` | `/api/alerts/records/{id}/ack` | 登录用户 | 确认预警 |
| `PUT` | `/api/alerts/records/{id}/close` | 登录用户 | 关闭预警 |

预警规则请求体示例：

```json
{
  "product_name": "番茄",
  "region": "山东",
  "threshold_percent": 10,
  "enabled": true
}
```

`GET /api/alerts/records` 查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 否 | `all`、`open`、`acknowledged`、`closed` |

## 9. 用户权限接口

管理员接口，需要 `admin` 角色。

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/users` | 管理员 | 用户列表 |
| `POST` | `/api/users` | 管理员 | 新增用户 |
| `PUT` | `/api/users/{id}` | 管理员 | 修改用户 |
| `DELETE` | `/api/users/{id}` | 管理员 | 删除用户 |
| `PUT` | `/api/users/{id}/role` | 管理员 | 修改角色 |
| `PUT` | `/api/users/{id}/status` | 管理员 | 启用或停用用户 |
| `POST` | `/api/users/{id}/reset-password` | 管理员 | 重置密码 |
| `GET` | `/api/roles` | 管理员 | 角色列表 |
| `GET` | `/api/permissions` | 管理员 | 权限标识列表 |

新增或修改用户请求体：

```json
{
  "account": "analyst01",
  "password": "Agri@123456",
  "name": "数据分析员",
  "phone": "13900000000",
  "email": "analyst01@example.com",
  "role": "analyst",
  "organization": "农产品价格监测中心",
  "active": true
}
```

修改角色请求体：

```json
{
  "role": "admin"
}
```

启用或停用请求体：

```json
{
  "active": false
}
```

重置密码请求体：

```json
{
  "password": "Agri@123456"
}
```

### 9.1 用户字段说明

课程文档中的 `user` 表可以和当前 MongoDB `user_accounts` 集合理解为同一业务对象。当前实现字段如下：

| 字段名 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| `id` | string | 是 | 用户 ID，MongoDB 主键 |
| `account` | string | 是 | 登录账号，对应 `username` |
| `passwordHash` | string | 是 | BCrypt 密码摘要，对应加密存储的 `password` |
| `name` | string | 是 | 用户姓名 |
| `role` | string | 是 | 用户角色：`admin`、`analyst`、`user` |
| `phone` | string | 否 | 手机号 |
| `email` | string | 否 | 邮箱 |
| `organization` | string | 否 | 所属机构 |
| `permissions` | array | 否 | 权限标识列表 |
| `active` | boolean | 是 | 是否启用 |
| `avatarUrl` | string | 否 | 头像地址 |
| `createdAt` | datetime | 是 | 创建时间，对应 `create_time` |
| `updatedAt` | datetime | 是 | 更新时间，对应 `update_time` |
| `lastLoginAt` | datetime | 否 | 最近登录时间 |
| `lastLoginIp` | string | 否 | 最近登录 IP |

角色权限说明：

| 角色 | 说明 |
| --- | --- |
| `admin` | 管理员，可管理用户、系统配置、任务、预警和全部业务数据 |
| `analyst` | 数据分析员，可运行任务、导出分析结果和处理预警 |
| `user` | 普通用户，可查看监控、分析、预测和预警结果 |

## 10. 系统配置接口

管理员接口，需要 `admin` 角色。

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/settings` | 管理员 | 获取系统配置 |
| `PUT` | `/api/settings` | 管理员 | 保存系统配置 |
| `GET` | `/api/settings/db-status` | 管理员 | 查看 MongoDB、Redis、Kafka 状态 |
| `GET` | `/api/audit-logs` | 管理员 | 审计日志列表 |

保存系统配置请求体示例：

```json
{
  "apiPrefix": "/api",
  "qualityThreshold": 0.96,
  "alertThresholdPercent": 10,
  "retentionDays": 365,
  "schedulerEnabled": true
}
```

## 11. 个人中心接口

| 方法 | 地址 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/profile` | 登录用户 | 获取个人资料 |
| `PUT` | `/api/profile` | 登录用户 | 保存个人资料 |
| `POST` | `/api/profile/password` | 登录用户 | 修改密码 |
| `POST` | `/api/profile/avatar` | 登录用户 | 上传头像，`multipart/form-data` |
| `PUT` | `/api/profile/preferences` | 登录用户 | 保存通知和监控偏好 |

保存个人资料请求体：

```json
{
  "name": "平台管理员",
  "phone": "13800000000",
  "email": "admin@example.com",
  "organization": "农产品价格监测中心"
}
```

保存偏好请求体：

```json
{
  "theme": "light",
  "alertNotify": true,
  "dailyReport": true,
  "defaultDashboard": "dashboard"
}
```

头像上传字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | 头像文件，最大 5MB |

## 12. 调试示例

登录并访问大盘：

```bash
login=$(curl -s -X POST http://127.0.0.1:8081/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"account":"admin","password":"Agri@123456"}')

token=$(printf '%s' "$login" | jq -r '.data.accessToken')

curl -s http://127.0.0.1:8081/api/dashboard/overview \
  -H "Authorization: Bearer $token" | jq
```

查看服务健康状态：

```bash
curl http://127.0.0.1:8081/actuator/health
```

查看后端根路径状态：

```bash
curl http://127.0.0.1:8081/
```

## 13. 数据来源与持久化

| 数据 | 来源 |
| --- | --- |
| `price_data` | Scala/Spark 清洗后的价格数据 |
| `weather_data` | Scala/Spark 清洗后的气象数据 |
| `task_records` | 后端采集任务管理数据 |
| `task_logs` | 任务操作日志 |
| `alert_rules` | 预警规则 |
| `alert_records` | 预警事件 |
| `user_accounts` | 用户账号、角色、权限和资料 |
| `login_sessions` | refreshToken 会话 |
| `system_settings` | 系统配置 |
| `audit_logs` | 审计日志 |
| `prediction_results` | 趋势预测结果 |

Redis 实时 Key：

| Key | 说明 |
| --- | --- |
| `agri:realtime:last_batch` | 最新批次汇总 |
| `agri:realtime:latest_prices` | 最新价格明细 |
| `agri:realtime:latest_alerts` | 最新预警 |
| `agri:realtime:metrics` | 实时指标 Hash |

当前只读接口会优先读取 MongoDB/Redis；如果演示环境暂无数据，会返回稳定演示数据，方便前端页面先联调。