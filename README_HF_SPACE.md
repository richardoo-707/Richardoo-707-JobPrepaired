---
title: 多 Agent 职业规划系统
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.3.0
app_file: app.py
pinned: false
license: mit
---

# 🤖 多 Agent 职业规划系统

基于 AI Agent 的智能职业规划助手，帮助您分析简历、推荐目标公司、搜索职位描述并生成完整的职业规划报告。

## ✨ 功能特点

- 📊 **简历分析**：基于真实市场数据推荐务实的目标公司
- 🔍 **职位搜索**：自动搜索职位描述（JD），提取薪资和地点信息
- 📚 **技能差距分析**：识别技能差距并推荐 GitHub 学习项目
- 📝 **完整报告**：生成详细的职业规划报告（Markdown 格式）

## 🚀 使用方法

1. **上传简历**：点击"上传简历"按钮，选择您的 PDF 格式简历
2. **开始分析**：点击"开始职业规划"按钮
3. **等待结果**：系统会自动分析（可能需要 2-5 分钟）
4. **查看报告**：生成的报告会显示在右侧，并保存为 `my_career_plan_v2.md`

## ⚙️ 配置要求

在 **Settings -> Secrets** 中配置以下环境变量：

- `ANTHROPIC_API_KEY`：您的 Anthropic API 密钥（必需）
- `ANTHROPIC_API_BASE`：API 基础 URL（可选，如果使用中转 API）
- `ANTHROPIC_MODEL_ID`：模型 ID（可选，默认：`anthropic/claude-3-5-sonnet`）

## 📌 注意事项

- 请确保简历文件为 PDF 格式
- 分析过程可能需要 2-5 分钟，请耐心等待
- 在免费 CPU 环境下，处理时间可能较长
- 系统会自动进行质量审核，确保输出信息的完整性

## 🔧 技术栈

- **smolagents**：多 Agent 框架
- **Gradio**：Web 界面
- **LiteLLM**：LLM 模型接口
- **pypdf**：PDF 处理

## 📄 许可证

MIT License
