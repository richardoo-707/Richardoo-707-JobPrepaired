# 🚀 AutoJob V2: 您的私人 AI 职业规划特种部队

<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Q2eW95bnh6eXJ6eXJ6eXJ6eXJ6eXJ6eXJ6eXJ6eXJ6CZ/xUPGGDNsLvBLG/giphy.gif" width="100" alt="AI Agent Icon">

### "拒绝盲目海投，用 AI 重新定义职业规划。"

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Framework](https://img.shields.io/badge/Agent-smolagents-FFD21E?logo=huggingface&logoColor=black)
![UI](https://img.shields.io/badge/UI-Gradio-FF7C00?logo=gradio&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-blueviolet)
![License](https://img.shields.io/badge/License-Apache%202.0-green)

[⚡️ 快速启动](#-快速启动) | [🧠 核心架构](#-核心架构) | [🕵️ 团队介绍](#-专家团队介绍) | [☁️ 云端部署](#-云端部署)

</div>

---

## 📖 项目背景 (Why AutoJob?)

主播作为要秋招的人深受找JD和不停的看是否符合要求的痛苦，正好最近在学agent相关的内容，于是这个项目诞生了，纯为爱发电。

如果帮到你，那就太好了！

我上传了两个版本V2会比较严谨输出结果较慢，V1比较快，效果也不错，大家如果本地跑不出来可以试试V1。

from 707，以下是readme:

传统的 AI 求职工具往往存在两个极端：要么是只会改简历的"文案机器"，要么是只会推荐 Google/OpenAI 的"做梦机器"。

**AutoJob V2** 是一个基于 **原生多智能体架构 (Native Multi-Agent)** 的求职辅助系统。它不只是一个脚本，而是一支**由 LLM 驱动的虚拟咨询团队**。

### 🔥 核心差异化 (V1 vs V2)

| 特性 | 🤖 传统单体 Agent (V1) | 🚀 AutoJob 多智能体 (V2) |
| :--- | :--- | :--- |
| **思维模式** | 混乱，容易把 Github 搜成 JD | **专注**，通过 Tool 隔离实现专人专事 |
| **数据来源** | 容易产生幻觉 (Hallucination) | **务实**，基于牛客/知乎真实 Offer 数据 |
| **成本效率** | 每次都联网搜，费钱费时 | **智能缓存**，优先查本地库，越用越快 |
| **质量控制** | 给啥吃啥，无法分辨垃圾信息 | **自我反思**，Manager 会打回低质量结果 |

---

## 🧠 核心架构 (Architecture)

系统采用 **"Agent-as-Tool"** 模式，实现了完美的权限隔离与上下文解耦。

```mermaid
graph TD
    User((👤 用户)) -->|上传简历| WebUI[🖥️ Gradio 控制台]
    WebUI --> Manager[👩‍💼 Manager Agent<br/>(总指挥 & 质量审核)]
    
    subgraph "AI 专家团队"
        direction TB
        Manager -- "1. 市场画像" --> Analyst[🕵️‍♂️ Industry Analyst]
        Manager -- "2. 职位搜寻" --> Headhunter[🦅 Job Headhunter]
        Manager -- "3. 差距补强" --> Coach[🎓 Career Coach]
    end

    subgraph "Reflexion Loop (反思闭环)"
        Analyst -->|结果太泛?| Manager
        Headhunter -->|没薪资?| Manager
        Coach -->|建议无效?| Manager
        Manager -- "❌ 打回重做!" --> Analyst & Headhunter & Coach
    end

    Manager -->|✅ 审核通过| Report[📄 Markdown 职业规划书]
```

---

## 🕵️ 专家团队介绍 (Meet the Team)

AutoJob V2 由四位性格迥异的 AI 专家组成，他们各司其职，模拟真实的职业咨询服务：

### 1. 👩‍💼 **Manager Agent (总指挥)**

> *"我是这里的负责人。只要我还在，垃圾报告就别想流出去。"*

- **职责**：任务分发、进度监控、**质量审核**
- **必杀技**：**Reflexion (反思机制)**。如果猎头找不到薪资，或者分析师推荐的公司太离谱，她会直接 Reject 并要求重试，直到结果达标

### 2. 🕵️‍♂️ **Industry Analyst (行业分析师)**

> *"别谈梦想，看数据。你的背景在市场上到底值多少钱？"*

- **职责**：简历画像提取、市场对标
- **核心工具**：`analyze_market_match_tool` (DuckDuckGo 深度搜索)
- **特点**：利用**社会证明 (Social Proof)**，专门去牛客网、知乎挖掘和你背景相似的人都去了哪，只推荐"够得着"的务实公司

### 3. 🦅 **Job Headhunter (猎头专家)**

> *"即使是同样的工作，我也能帮你找到薪资最高的那一个。"*

- **职责**：JD 搜索、薪资提取、地点确认
- **核心工具**：`query_local_db_tool`, `save_to_db_tool`, `search_jd_tool`
- **特点**：**记忆大师**。它维护着一个本地职位数据库 (`jd_database.json`)，优先查库，极速响应。库里没有才会去联网搜索并自动入库

### 4. 🎓 **Career Coach (职业导师)**

> *"Talk is cheap, show me the code."*

- **职责**：Gap Analysis (差距分析)、资源推荐
- **核心工具**：`search_github_tool`
- **特点**：**拒绝废话**。它不会给你"去学 Python"这种泛泛的建议，而是直接甩给你一个 `langchain-ai/langchain` 的 GitHub 仓库链接让你去读源码

---

## 📄 产出预览 (Report Preview)

运行结束后，你将获得一份包含 **职位对比表** 的 Markdown 报告：

| 公司名称 | 职位名称 | Base 地点 | 预估薪资 | 核心要求 (简述) | 匹配度 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **得物 (Poizon)** | 算法工程师 | 上海 | **28k-45k** | 搜广推, C++, TensorFlow | ⭐⭐⭐⭐ |
| **Shopee** | Backend Eng | 新加坡 | **5k-8k SGD** | Go, Distributed Systems | ⭐⭐⭐⭐⭐ |
| **美团** | LLM Engineer | 北京 | **30k-50k** | Transformer, CUDA, RAG | ⭐⭐⭐ |

*(以及详细的技能差距分析和 GitHub 学习路径)*

---

## ⚡ 快速启动 (Quick Start)

### 1. 克隆项目

```bash
git clone https://github.com/your-username/AutoJob-V2.git
cd AutoJob-V2
```

### 2. 安装依赖

建议使用 Conda 创建独立环境：

```bash
conda create -n autojob python=3.10
conda activate autojob
pip install -r requirements.txt
```

### 3. 🔑 配置环境变量 (至关重要！)

本项目不提供任何内置的 API Key。您需要使用自己的 LLM 服务商 Key。

复制示例配置文件：

```bash
cp env.example .env
```

打开 `.env` 文件并填入您的配置：

```ini
# 填写您的 API Key (支持 OpenAI, Anthropic, DeepSeek 等)
ANTHROPIC_API_KEY=sk-xxxxxx

# 填写模型名称 (注意：LiteLLM 要求加上厂商前缀!)
# 如果是用 OpenAI 格式的接口 (如 DeepSeek/Qwen)，请务必加 openai/ 前缀
ANTHROPIC_MODEL_ID=openai/qwen-2.5-coder-32b-instruct

# (可选) 如果使用中转 API，请配置 Base URL
ANTHROPIC_API_BASE=https://api.your-proxy.com/v1
```

### 4. 运行系统

```bash
python app.py
```

浏览器访问 `http://127.0.0.1:7860` 即可开始使用。

---

## ⚠️ 免责声明 & 注意事项

- **Token 消耗**：由于采用了多智能体反思机制 (Reflexion)，一次完整的运行可能会进行 10-30 次 LLM 交互。请确保您的 API Key 额度充足。建议使用 DeepSeek V3 或 Qwen 2.5 等高性价比模型。

- **数据隐私**：本项目支持本地部署，您的简历文件只会在本地/服务器内存中处理，不会上传到任何第三方（除非您使用的 LLM 服务商有特定的数据政策）。

- **结果准确性**：AI 可能会产生幻觉 (Hallucination)，生成的薪资范围和职位信息仅供参考，请以官方 JD 为准。

---

## 🤝 贡献 (Contributing)

欢迎提交 Issue 和 Pull Request！如果你有更好的 Tool Idea (例如自动投递、LinkedIn 爬虫)，欢迎共建。

---

## 📝 版本说明

- **V2 版本**：带质量审核与自我修正 (Reflexion)，输出更严谨但速度较慢
- **V1 版本**：单 Agent 架构，速度快，效果也不错

如果本地运行 V2 遇到问题，可以尝试 V1 版本。

---

## 📄 许可证

本项目采用 Apache 2.0 许可证。

---

<div align="center">

**Made with ❤️ by 707**

如果这个项目帮到了你，给个 ⭐ Star 吧！

</div>
