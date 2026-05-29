# 农产品价格采集监控平台 React Shell

这是企业级 SPA 全局框架原型，技术栈为 React + Tailwind CSS + Lucide Icons + shadcn/ui 风格组件。

## 运行

```powershell
cd frontend-react-shell
npm install
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5180/
```

## 核心结构

| 文件 | 说明 |
| --- | --- |
| src/components/layout/AppShell.jsx | SPA 全局 Shell，负责侧边栏、顶部栏、主内容区和页面切换 |
| src/components/layout/Sidebar.jsx | 深森林绿侧边栏，支持折叠和菜单切换 |
| src/components/layout/Header.jsx | 面包屑、通知中心、市场时间、用户机构信息 |
| src/components/layout/navigation.js | 菜单配置和面包屑配置 |
| src/components/ui/*.jsx | shadcn/ui 风格基础组件 |
| src/index.css | Tailwind 入口、主题变量、全局字体和动效 |

## 已覆盖要求

- 左侧深森林绿 Sidebar：监控大盘、采集任务管理、价格数据分析、AI 趋势预测、价格预警中心、系统配置。
- Sidebar 支持折叠，菜单点击后主内容区无刷新切换。
- Header 包含面包屑、实时系统通知中心、当前市场时间、用户头像及机构名称。
- 主内容区使用 `#f8fafc` 浅灰背景，并加入页面切换动效。
- 视觉采用 1px 描边、轻阴影、Inter 字体栈、Lucide 图标和 shadcn/ui 风格组件。

## 后续接入建议

1. 将 `pages` 配置从 AppShell 中拆到独立路由模块。
2. 用真实 `/api/overview`、`/api/price-trends`、`/api/predictions` 数据替换当前占位内容。
3. 引入 React Router 后，把 `activeKey` 状态切换升级为 URL 路由切换。
4. 接入 ECharts/Chart.js 图表组件，填充监控大盘和价格分析页面。