# 农产品价格采集监控平台后端

本目录是按 `../后端编写文档.md` 落地的 Spring Boot 3 后端工程，负责给 Vue 前端提供统一 REST API，并从 MongoDB、Redis 读取清洗链路和实时链路结果。

完整接口说明见 [API.md](API.md)。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| Web 框架 | Spring Boot 3.3.x |
| Java 版本 | JDK 17 |
| 构建工具 | Maven |
| 认证 | Spring Security + JWT + BCrypt |
| 主存储 | MongoDB `agri_price` |
| 实时缓存 | Redis `agri:realtime:*` |

## 运行方式

在项目根目录执行：

```bash
cd code/PM/backend
source ../../../servers/env.sh
../../../servers/apache-maven-3.9.6/bin/mvn spring-boot:run
```

如果当前机器已经安装 Maven，也可以直接使用：

```bash
source ../../../servers/env.sh
mvn spring-boot:run
```

默认端口为 `8080`。首次启动且 MongoDB 可写时，会自动创建开发管理员账号：

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `Agri@123456` | 管理员 |

## 常用环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SERVER_PORT` | `8080` | 后端端口 |
| `MONGODB_URI` | `mongodb://127.0.0.1:27017/agri_price` | MongoDB 连接 |
| `REDIS_HOST` | `127.0.0.1` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_DATABASE` | `0` | Redis DB |
| `APP_JWT_SECRET` | 开发默认密钥 | JWT 签名密钥，部署时必须替换 |
| `APP_CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173` | 前端跨域来源 |
| `AGRI_REDIS_KEY_PREFIX` | `agri:realtime` | Scala/Spark 写入 Redis 的 Key 前缀 |

## 接口分组

所有业务接口默认需要请求头：

```text
Authorization: Bearer <accessToken>
```

认证接口：

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/register` | 注册普通用户 |
| `POST` | `/api/auth/login` | 登录并返回 `accessToken`、`refreshToken` |
| `POST` | `/api/auth/logout` | 退出登录并失效 refreshToken |
| `POST` | `/api/auth/refresh-token` | 续签 accessToken |
| `GET` | `/api/auth/me` | 当前用户 |
| `PUT` | `/api/auth/password` | 登录态修改密码 |

业务接口：

| 分组 | 主要地址 |
| --- | --- |
| 监控大盘 | `/api/dashboard/overview`、`/api/dashboard/realtime`、`/api/dashboard/trend`、`/api/dashboard/alerts` |
| 采集任务 | `/api/tasks`、`/api/tasks/{id}/start`、`/api/tasks/{id}/stop`、`/api/tasks/{id}/logs` |
| 价格分析 | `/api/analysis/overview`、`/api/analysis/product-statistics`、`/api/analysis/region-statistics`、`/api/analysis/export` 等 |
| 趋势预测 | `/api/predictions`、`/api/predictions/{product}`、`/api/predictions/{product}/factors` |
| 预警中心 | `/api/alerts/rules`、`/api/alerts/records`、`/api/alerts/records/{id}/ack` |
| 用户权限 | `/api/users`、`/api/roles`、`/api/permissions` |
| 系统配置 | `/api/settings`、`/api/settings/db-status`、`/api/audit-logs` |
| 个人中心 | `/api/profile`、`/api/profile/avatar`、`/api/profile/preferences` |

## 返回格式

接口统一返回：

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

## 数据衔接

后端优先读取真实数据：

- MongoDB：`price_data`、`weather_data`、`task_records`、`alert_rules`、`alert_records`、`prediction_results`、`system_settings`、`audit_logs`。
- Redis：`agri:realtime:last_batch`、`agri:realtime:latest_prices`、`agri:realtime:latest_alerts`、`agri:realtime:metrics`。

如果演示环境暂时没有数据，部分只读接口会返回稳定的演示数据，确保前端可以先联调页面结构。