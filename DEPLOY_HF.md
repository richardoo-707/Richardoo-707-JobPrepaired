# Hugging Face Spaces 部署快速指南

## 📦 文件准备

### 必需文件清单

在部署到 HF Spaces 之前，确保以下文件结构：

```
your-space/
├── app.py                    # 主应用（将 app_hf.py 重命名）
├── requirements.txt          # 依赖列表
├── README.md                 # Space 说明（使用 README_HF_SPACE.md 的内容）
└── tools/                    # 工具目录
    ├── __init__.py
    ├── resume_tools.py
    ├── web_tools.py
    ├── github_tools.py
    ├── market_tools.py
    ├── db_tools.py
    └── file_tools.py
```

## 🚀 部署步骤

### 1. 创建 HF Space

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space"
3. 配置：
   - **SDK**: Gradio
   - **Hardware**: CPU basic（免费）或 CPU upgrade（付费，更快）
   - **Visibility**: Public 或 Private

### 2. 上传文件

**方法 A：使用 Git（推荐）**

```bash
# 1. 克隆你的 Space（HF 会提供 Git URL）
git clone https://huggingface.co/spaces/your-username/your-space-name

# 2. 进入目录
cd your-space-name

# 3. 复制文件
cp ../app_hf.py app.py
cp ../requirements.txt .
cp ../README_HF_SPACE.md README.md
cp -r ../tools .

# 4. 提交并推送
git add .
git commit -m "Initial commit"
git push
```

**方法 B：使用 Web 界面上传**

直接在 HF Spaces 的 Web 界面上传文件。

### 3. 配置 Secrets

在 Space 的 **Settings -> Secrets** 中添加：

```
ANTHROPIC_API_KEY = your_api_key_here
ANTHROPIC_API_BASE = your_api_base (可选)
ANTHROPIC_MODEL_ID = anthropic/claude-3-5-sonnet (可选)
```

### 4. 等待部署

HF Spaces 会自动：
- 安装依赖
- 运行应用
- 启动服务

## ⚡ 优化说明

### 与 autojob_v3.py 的主要区别

1. **减少执行步数**
   - Analyst: 8 步（原无限制）
   - Headhunter: 10 步（原无限制）
   - Coach: 6 步（原无限制）
   - Manager: 15 步（原 20 步）

2. **简化工作流程**
   - 推荐公司：3-5 家（原 7 家）
   - JD 搜索：只搜索前 3 家公司（原全部）
   - GitHub 项目：3-5 个（原多个）

3. **环境变量适配**
   - 支持 HF Spaces secrets
   - 多种环境变量名称兼容
   - 更好的错误提示

4. **单 Agent 模式**
   - 使用单 Agent 模式，避免 `managed_agents` 兼容性问题
   - 更稳定，执行更快

## 🔧 如果仍然超时

### 进一步优化选项

1. **减少推荐公司数量**
   
   在 `app_hf.py` 的 `build_prompt()` 函数中：
   ```python
   # 将 "3-5 家" 改为 "3 家"
   4. 基于搜索结果，推荐 **3 家**真实可达成的目标公司
   ```

2. **只搜索 1-2 家公司**
   
   ```python
   # 将 "只搜索前 3 家公司" 改为 "只搜索前 2 家公司"
   * 使用 search_jd_tool 搜索这 3-5 家公司的相关职位 JD（**只搜索前 2 家公司，节省时间**）
   ```

3. **进一步减少 max_steps**
   
   ```python
   analyst_agent = CodeAgent(..., max_steps=6)  # 从 8 改为 6
   headhunter_agent = CodeAgent(..., max_steps=8)  # 从 10 改为 8
   coach_agent = CodeAgent(..., max_steps=5)  # 从 6 改为 5
   manager_agent = CodeAgent(..., max_steps=12)  # 从 15 改为 12
   ```

4. **升级硬件**
   
   在 Space Settings 中升级到 **CPU upgrade**（付费，但更快）

## 📝 测试清单

部署后，请测试：

- [ ] 应用正常启动
- [ ] 可以上传 PDF 文件
- [ ] 可以点击"开始职业规划"按钮
- [ ] 能够生成报告（即使需要较长时间）
- [ ] 报告格式正确
- [ ] 没有错误信息

## 🐛 常见问题

### Q: 应用启动失败

**A**: 检查：
- `app.py` 文件名是否正确
- `requirements.txt` 格式是否正确
- 查看日志中的错误信息

### Q: API 密钥错误

**A**: 检查：
- Secrets 中是否正确配置了 `ANTHROPIC_API_KEY`
- API 密钥是否有效
- 是否有足够的 API 额度

### Q: 超时错误

**A**: 尝试：
- 升级到 CPU upgrade 硬件
- 进一步减少 max_steps
- 减少推荐公司数量

### Q: 文件上传失败

**A**: 检查：
- 文件格式是否为 PDF
- 文件大小是否过大（建议 < 10MB）
- 浏览器控制台是否有错误

## 📞 支持

如有问题，请：
1. 查看 HF Spaces 的日志输出
2. 检查浏览器控制台错误
3. 查看 README_HF.md 获取详细说明
