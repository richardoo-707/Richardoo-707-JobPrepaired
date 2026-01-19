# 多 Agent 职业规划系统 - Hugging Face Spaces 部署指南

## 📋 简介

这是一个基于 AI Agent 的智能职业规划系统，可以帮助用户：
- 📊 分析简历背景，推荐务实的目标公司
- 🔍 搜索职位描述（JD），提取薪资和地点信息
- 📚 分析技能差距，推荐 GitHub 学习项目
- 📝 生成完整的职业规划报告

## 🚀 在 Hugging Face Spaces 上部署

### 步骤 1: 创建新的 Space

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 填写信息：
   - **Space name**: 你的空间名称（如 `career-planning-agent`）
   - **SDK**: 选择 `Gradio`
   - **Hardware**: 选择 `CPU basic`（免费）或 `CPU upgrade`（付费，更快）
   - **Visibility**: 选择 `Public` 或 `Private`

### 步骤 2: 上传文件

将以下文件上传到你的 Space：

```
your-space/
├── app.py              # 主应用文件（将 app_hf.py 重命名为 app.py）
├── requirements.txt    # 依赖包列表
├── README.md          # Space 说明（可选）
└── tools/             # 工具目录
    ├── __init__.py
    ├── resume_tools.py
    ├── web_tools.py
    ├── github_tools.py
    ├── market_tools.py
    ├── db_tools.py
    └── file_tools.py
```

**重要**：将 `app_hf.py` 重命名为 `app.py`，因为 HF Spaces 默认查找 `app.py`。

### 步骤 3: 配置 Secrets（环境变量）

1. 在 Space 页面，点击 **Settings** 标签
2. 找到 **Secrets** 部分
3. 添加以下环境变量：

| Key | Value | 说明 |
|-----|-------|------|
| `ANTHROPIC_API_KEY` | 你的 API 密钥 | Anthropic API 密钥（必需） |
| `ANTHROPIC_API_BASE` | API 基础 URL | 如果使用中转 API，填写中转地址（可选） |
| `ANTHROPIC_MODEL_ID` | `anthropic/claude-3-5-sonnet` | 模型 ID（可选，有默认值） |

**或者使用以下替代名称**（代码会自动识别）：
- `HF_API_KEY` 替代 `ANTHROPIC_API_KEY`
- `MODEL_ID` 替代 `ANTHROPIC_MODEL_ID`

### 步骤 4: 等待部署

HF Spaces 会自动：
1. 安装 `requirements.txt` 中的依赖
2. 运行 `app.py`
3. 启动 Gradio 应用

部署完成后，你会看到一个可用的 Web 界面。

## ⚙️ 优化说明

为了适配 Hugging Face Spaces 的免费 CPU 环境，我们对代码进行了以下优化：

### 1. 减少执行步数
- Analyst Agent: `max_steps=8`（原 10）
- Headhunter Agent: `max_steps=10`（原 15）
- Coach Agent: `max_steps=6`（原 8）
- Manager Agent: `max_steps=15`（原 20）

### 2. 简化工作流程
- 推荐公司数量：从 7 家减少到 **3-5 家**
- JD 搜索：只搜索前 **3 家公司**，节省时间
- GitHub 项目推荐：从多个减少到 **3-5 个**

### 3. 优化 Prompt
- 添加了"高效执行"提示，避免重复步骤
- 强调优先使用本地缓存
- 简化了部分指令

### 4. 环境变量适配
- 支持 HF Spaces 的 secrets 机制
- 提供多种环境变量名称支持
- 更好的错误提示

## 📝 本地测试

在部署到 HF Spaces 之前，可以在本地测试：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（创建 .env 文件）
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_API_BASE=your_api_base  # 可选
ANTHROPIC_MODEL_ID=anthropic/claude-3-5-sonnet  # 可选

# 3. 运行应用
python app_hf.py
```

## 🔧 故障排除

### 问题 1: 超时错误

**解决方案**：
- 升级到 `CPU upgrade` 硬件（付费）
- 进一步减少 `max_steps`
- 减少推荐公司数量（在 prompt 中修改）

### 问题 2: API 密钥错误

**解决方案**：
- 检查 Secrets 中是否正确配置了 `ANTHROPIC_API_KEY`
- 确保 API 密钥有效且有足够的额度

### 问题 3: 依赖安装失败

**解决方案**：
- 检查 `requirements.txt` 格式是否正确
- 确保所有依赖包名称正确
- 查看 HF Spaces 的日志输出

### 问题 4: 文件上传失败

**解决方案**：
- 确保上传的是 PDF 格式
- 检查文件大小（建议 < 10MB）
- 查看浏览器控制台错误信息

## 📊 性能优化建议

如果仍然遇到超时问题，可以进一步优化：

1. **减少推荐公司数量**：在 `build_prompt()` 函数中，将 "3-5 家" 改为 "3 家"
2. **只搜索 1-2 家公司**：在 prompt 中修改 "只搜索前 3 家公司" 为 "只搜索前 2 家公司"
3. **减少 GitHub 项目推荐**：将 "3-5 个" 改为 "3 个"
4. **进一步减少 max_steps**：根据实际情况调整

## 📄 许可证

本项目使用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
