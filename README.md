# AutoDev (YoRHa Bunker Engine)

[English](./README_EN.md) | 简体中文

![Auto CRUD Copilot Banner](https://github.com/user-attachments/assets/e168ef33-7616-434c-91e6-e2c9eef017c0)

[![NPM Version](https://img.shields.io/npm/v/@yorha2b-lab/autodev.svg?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/@yorha2b-lab/autodev)
[![NPM Downloads](https://img.shields.io/npm/dm/@yorha2b-lab/autodev.svg?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/@yorha2b-lab/autodev)
[![GitHub Stars](https://img.shields.io/github/stars/yorha2b-lab/autodev.svg?style=flat-square&logo=github&logoColor=white)](https://github.com/yorha2b-lab/autodev/stargazers)
[![License](https://img.shields.io/npm/l/@yorha2b-lab/autodev.svg?style=flat-square&logo=gnu&logoColor=white)](https://github.com/yorha2b-lab/autodev/blob/main/LICENSE)
![Total Clones](https://img.shields.io/badge/dynamic/json?query=total_clones&url=https%3A%2F%2Fraw.githubusercontent.com%2Fyorha2b-lab%2Fautodev%2Fgithub-repo-stats%2Fbunker-stats.json&label=Total%20Clones&color=33cc33&style=flat-square&logo=github&logoColor=white)

基于 AI 视觉与语义协议的前端（React + Ant Design）代码构筑与旧系统重构引擎 🚀

![Auto CRUD Copilot 2.0 Demo](https://github.com/user-attachments/assets/287d0db1-d0b0-4290-87da-751ba638655e)

## 🌟 v7.0 地堡架构升级

在 v7.0 时代，AutoDev 进一步升级为 **Mission-Driven 的模块化地堡架构**。

所有任务统一进入 `Mission`，由 **Headquarters** 中的 **Commander** 识别任务需求、匹配最合适的 Unit，并交由 Dispatcher 调度执行。

Unit 不再绑定固定输入目录，而是通过声明自身的 `capabilities` 主动参与任务匹配，让地堡可以根据任务动态组织作战单位。

- 🧠 **任务指挥 (Commander)**：识别任务类型与所需能力，从全部 Units 中选择最合适的执行单位。
- ⚔️ **作战单位 (Units)**：通过能力声明参与任务匹配，负责具体的页面构筑、语义对齐等任务。
- 🕵️ **数字考古 (Scout)**：Puppeteer 无头侦察兵，从旧系统捕获页面并生成重构任务。
- 🗼 **现网防御塔 (Tower)**：代理真实 XHR/Fetch 流量，将现网数据直接送入地堡任务链。
- 🏛️ **议会 (Council)**：解析 OpenAPI / Swagger 文档，提炼枚举与接口语义，为构筑任务提供协议情报。

## ✨ 特性

- 🖼️ **全页构筑 (Page)**：输入完整页面截图，Commander 自动识别构筑需求并调度对应 Unit，生成包含 Table / Form / Tabs 的完整 CRUD 页面及菜单。
- 🧩 **碎片提取 (Part)**：输入局部 UI 截图，自动识别为组件构筑任务，生成可直接使用的 UI 配置代码。
- 🕵️ **数字考古 (Scout)**：通过 Puppeteer 巡检旧系统，浏览器中右键即可捕获当前页面，并将其转换为重构任务。
- 🗼 **现网数据采集 (Tower)**：代理真实 XHR / Fetch 请求，将运行中的后端响应直接送入任务链，无需手工准备 JSON。
- 🔌 **语义对齐 (Reconciler)**：分析后端响应与前端资源定义之间的字段差异，自动修正 `resource.js`。
- 🔧 **智能装配**：自动补全 import、日期格式转换、金额千分位、枚举字典、OSS 上传等实战逻辑。

## 🚀 快速开始

### 安装

```bash
npm install -g @yorha2b-lab/autodev
```

### 环境配置与初始化

在您的目标项目根目录下执行：

```bash
bunker init
```

> **💡 零配置演示模式 (Demo Mode)**
> 项目默认开启 Demo 模式：
> 1. 无需配置 API_KEY，直接运行 `bunker boot`。
> 2. 向 `./bunker/mission` 目录丢入任意图片（系统自动空投标准 `example.json` 构筑包）。
> 3. 若想识别真实代码/截图，请在 `bunker/config.js` 中将 `useDemo` 设为 `false` 并配置 `.env`。

创建 `.env` 文件并配置以下环境变量：

```bash
# AI模型API配置
API_KEY=your_api_key_here
BASE_URL=your_api_base_url_here
```

🚗 **获取API Key直通车**: [阿里云百炼控制台](https://bailian.console.aliyun.com/cn-beijing?tab=doc#/doc/)

## 📖 指挥中心操作指南

启动主监控网络：

```bash
bunker boot
```

启动后，地堡系统将进入全频道联动监听状态：

| 战术操作 | 传感器 / 触发动作 | 作战构筑效果 |
| :--- | :--- | :--- |
| **任务空投**<br>*(智能分流)* | 拖入设计图/截图至<br>`./bunker/mission/` | **司令部（commander）视觉雷达自动研判分流**：<br>• **完整 CRUD 页面** $\rightarrow$ 派出 `striker`（重装打击）：生成全套目录、`index.js`、`resource.js`、Mock 数据并同步 `menus.js`<br>• **局部 UI 碎片/下拉字典** $\rightarrow$ 派出 `raider`（轻装突袭）：终端弹出紫色代码框，即拷即用 |
| **遗迹考古**<br>*(一键克隆)* | 目标老系统浏览器中<br>【鼠标右键】点击任意位置 | 调起 `scout.js` 侦察兵，全屏秒级截屏并自动推导路由命名，空投至 `./bunker/mission/` 触发自动构筑 |
| **全频道通电**<br>*(Swagger 对齐)* | 配置 `apiDoc` 启动地堡 | `council.js` 启动语义雷达与本地 NLP 分词，自动匹配真实接口、请求方式（GET/POST/DELETE）与路径变量，并同步后端 Enum 基因字典 |
| **神之塔嗅探**<br>*(抓包自愈)* | 将业务代理目标指向<br>`http://localhost:42153` | `tower.js` 实时拦截真实网络响应，`reconciler.js` 自动比对并物理覆写修正 `resource.js` 中的字段名 |

## 📁 地堡结构说明

```text
your-project/
├── bunker/                  # 地堡前哨基地与战术传感器
│   ├── .env                 # 神经云连接密钥 (API Key)
│   ├── config.js            # 地堡战略配置文件 (支持热重载)
│   ├── mission/             # 统一作战任务空投舱 (设计图/截图投放点，司令部自动分流)
│   └── .chrome_session/     # 侦察兵 (scout) 浏览器会话与缓存持久化目录
├── mock/                    # 9S 自动执行数据伪装的 Mock 数据包
└── src/
    ├── pages/               # 寄叶部队自动构筑的前端业务页面 (视图与 Schema 解耦)
    └── utils/
        └── menus.js         # 自动同步的战区菜单路由配置

## ⚙️ 配置

在 `bunker/config.js` 中可以配置以下选项：

```javascript
module.exports = {
    // 是否开启 Demo 演示模式
    useDemo: true,
    // 是否自动伪造生成 Mock 数据
    needMock: false,

    // 地堡黑科技开关：
    // 是否开启 42153 战术代理塔 (现网流量劫持与对齐)
    enableAutoAlignment: false,
    // 是否开启 GitHub 克隆数彩蛋
    fetchClone: true,

    // AI 模型配置
    textModel: 'qwen-turbo',
    visionModel: 'qwen3.7-plus',

    // 🕸️ 遗迹与对齐配置 (考古与代理)
    // 1. 旧项目运行 URL (配置后自动启动 Scout 右键考古侦察兵)
    remains: 'http://localhost:8000',
    // 2. 公司 Swagger / OpenAPI JSON 文档地址
    apiDoc: 'http://api.company.com/v2/api-docs',
    // 3. 真实后端代理目标地址 (Tower 转发目标)
    proxyTarget: 'http://backend.company.com',
    // 4. 后端接口成功断言表达式
    responseSuccess: `response?.code === 200`,

    // 前端源码构建目录路径
    pagesDir: 'src/pages',
    componentsDir: 'src/components',
    hooksDir: 'src/hooks',
    utilsDir: 'src/utils',

    // 自定义 Handlebars 模板目录 (留空使用内置模版)
    hbsDir: '',
}
```

## 🤝 贡献与 CLA

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解参与流程。
所有 Pull Request 在合并前需要自动化签署 [CLA 贡献者协议](CLA.md)。

## 📄 许可证

本项目采用 [GNU AGPL v3.0](LICENSE) 许可证。

## 🙏 致谢

感谢以下开源项目为地堡提供核心动力：
- [OpenAI](https://openai.com/) / [Alibaba Qwen](https://tongyi.aliyun.com/) - 强大的 AI 视觉与语言能力
- [Ant Design](https://ant.design/) - 优秀的企业级 UI 组件库
- [Handlebars](https://handlebarsjs.com/) / [Chokidar](https://github.com/paulmillr/chokidar) / [Puppeteer](https://pptr.dev/) - 稳定的构筑与侦察引擎

## 📞 联系方式

如有问题或建议，欢迎提交 [Issue](https://github.com/yorha2b-lab/autodev/issues)。

## 🛠️ 常见问题 (FAQ)

Q: 这个工具收费吗？
A: 工具本身开源免费，但调用的 AI 模型（如 Qwen-VL, GPT-4v）需要配置 API Key。建议使用阿里云通义千问等高性价比模型。

Q: 如何自定义生成的代码风格？
A: 您可以配置 `hbsDir` 指向您自己的 Handlebars 模板目录，打造专属的团队代码构建规范。

---

## ⚖️ Disclaimer

AutoDev is a **fan-made, non-commercial, open-source tool**.

- The themes, names (YoRHa, 2B, 9S, Pod042, etc.), and catchphrases included in this project are inspired by **NieR:Automata**, which is a trademark and copyright of **Square Enix Co., Ltd. / PlatinumGames Inc.**
- This project is not affiliated with, endorsed by, or representative of Square Enix in any way.
- Please support the original masterpiece: [NieR:Automata Official Site](https://nierautomata.square-enix-games.com/).

**Glory to Mankind.** 🤖⚔️