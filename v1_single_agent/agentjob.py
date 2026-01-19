import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel
# 引入我们定义的工具 (确保你已经创建了 tools 文件夹和对应的 .py 文件)
from tools.resume_tools import read_resume_tool
from tools.web_tools import search_jd_tool, visit_page_tool
from tools.github_tools import search_github_tool
from tools.file_tools import save_report_tool
from tools.market_tools import analyze_market_match_tool
from tools.db_tools import query_local_db_tool, save_to_db_tool

# 1. 加载环境变量
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
api_base = os.getenv("ANTHROPIC_API_BASE")
model_name = os.getenv("ANTHROPIC_MODEL_ID")

# 2. 初始化模型 (大脑)
# 使用 LiteLLMModel 可以兼容 OpenAI格式、Anthropic格式 或 任何中转 API
model = LiteLLMModel(
    model_id=model_name,  # 例如: "anthropic/claude-3-5-sonnet" 或 "openai/qwen-2.5-coder"
    api_key=api_key,
    api_base=api_base  # 如果用官方API，这里可能是 None；如果用中转，这里是中转地址
)

# --- 定义主 Agent (Manager) ---
# 将所有工具集中到一个 agent 中，让它自己协调工作
# 注意：当前版本的 smolagents (1.24.0) 不支持 ManagedAgent
# 因此我们使用单一 agent 架构，将所有工具提供给一个 agent
manager_agent = CodeAgent(
    tools=[
        read_resume_tool,           # 读取简历
        search_jd_tool,             # 搜索职位描述
        visit_page_tool,            # 访问网页
        search_github_tool,         # 搜索 GitHub 资源
        save_report_tool,           # 保存报告文件
        analyze_market_match_tool,  # 分析市场匹配度
        query_local_db_tool,        # 查询本地数据库
        save_to_db_tool             # 保存到本地数据库
    ],
    model=model,
    name="career_manager",
    description="A career planning agent that helps with resume analysis, job search, and skill gap analysis."
)

# --- 7. 启动测试 ---
if __name__ == "__main__":
    # 假设你根目录下放了一个 resume.pdf
    resume_path = "./resume.pdf"

    print("🤖 Agent 开始工作...")
    manager_agent.run(f"""
    我上传了一份简历，路径是 '{resume_path}'。
    请按以下步骤帮我规划求职：
    
    步骤 1: 使用 read_resume_tool 读取简历文件 '{resume_path}'，分析我的背景和技能。
    
    步骤 2 (公司推荐 - 基于真实市场数据):
    步骤 2.1 (用户画像提取): 从简历中提取用户标签 (user_tags)，包括但不限于：
       - 教育背景：985/211/双非、本科/硕士/博士
       - 专业背景：计算机/非计算机/转码
       - 其他标签：海外留学、工作经验等
       - 示例标签格式："985 Master CS" 或 "双非本科 非科班 转码"
    
    步骤 2.2 (市场真实性验证): 使用 analyze_market_match_tool(user_tags) 搜索牛客网和知乎，
      查找具有相似背景标签的候选人实际拿到 offer 的公司。这些搜索结果包含真实的社会证明数据，
      显示哪些公司实际招聘了类似背景的候选人。
    
    步骤 2.3 (公司筛选): 基于步骤 2.2 的搜索结果，推荐 3 家公司。重要规则：
      - **只能推荐在搜索结果中实际出现的公司**
      - **不要编造或假设 FAANG 等大公司，除非它们在搜索结果中明确出现**
      - **优先选择搜索结果中多次提及的公司**
      - **选择"可达成的"公司，即搜索结果中显示有类似背景候选人成功拿到 offer 的公司**
      - 如果搜索结果中没有足够的公司，可以适当扩展搜索，但必须基于真实数据
    
    步骤 3 (JD 搜索与信息提取 - 带缓存机制):
    
    步骤 3.1 (检查本地缓存): 从简历中提取 3-5 个关键词标签（例如："Python"、"Java"、"Shanghai"、"Intern"、"AI" 等），
      这些标签应该包括：技术栈、地点、经验级别等。然后使用 query_local_db_tool(tags) 查询本地数据库，
      检查是否有之前保存的相关 JD 信息。
    
    步骤 3.2 (决策 - 使用缓存或在线搜索):
      - **如果本地数据库返回了有用的 JD 信息**（匹配到相关职位）：
        * 直接使用这些缓存的 JD 信息，跳过在线搜索
        * 这样可以节省 tokens 和时间
        * 继续到步骤 3.3
      - **如果本地数据库没有返回结果，或者返回的 JD 不相关/过时**：
        * 使用 search_jd_tool 搜索这 3 家公司的最近 'AI Engineer' 或相关职位 JD
        * 对于每个找到的 JD URL，使用 visit_page_tool 访问并提取完整的职位描述内容
        * 继续到步骤 3.3
    
    步骤 3.3 (缓存新数据): 如果你在步骤 3.2 中进行了在线搜索并找到了**好的 JD**（包含完整信息、相关性强），
      使用 save_to_db_tool 将这些 JD 保存到本地数据库，供未来使用。保存时需要提供：
      - company: 公司名称
      - role: 职位名称
      - location: 工作地点
      - salary: 薪资信息
      - jd_content: 完整的 JD 内容
      - tags: 关键词标签（从简历和 JD 中提取，如 "Python, AI, Beijing, Junior"）
    
    **重要：在提取 JD 内容时，请特别关注以下关键信息：**
    - **薪资范围 (Compensation/Salary Range)**: 查找明确的薪资信息，如 "20k-30k/月"、"面议"、"Negotiable" 等
    - **工作地点 (Work Location/Base)**: 查找明确的地点信息，如 "Beijing"、"上海"、"Singapore"、"Remote"、"远程" 等
    - **职位名称**: 准确的职位标题
    - **核心要求**: 关键技术栈和技能要求
    
    请确保提取这些信息，它们将在最终报告中用于职位对比表。
    
    步骤 4: 对比 JD 要求和我的简历技能，分析技能差距，告诉我缺什么技能。
    
    步骤 5: 对于缺失的技能，使用 search_github_tool 搜索相关的学习资源和项目，推荐 GitHub 仓库。
    
    步骤 6 (FINAL STEP): 这是最后一步，必须完成以下任务：
    **语言必须是简体中文** (即使 JD 和 GitHub 是英文，也要翻译成中文总结)。z
    
    1. 编译一份综合摘要报告，包含以下内容：
       - **职位对比表**（必须包含，见下方格式要求）
       - 从 JD 中提取的关键要求（详细说明）
       - 我的技能差距分析（我已有的技能 vs. 需要的技能）
       - 推荐的 GitHub 学习项目（项目名称 + 链接）
    
    2. **职位对比表格式要求（必须严格遵守）**：
       表格必须包含以下列：
       `| 公司名称 | 职位名称 | Base (地点) | 预估薪资 | 核心要求 (简述) |`
       
       **薪资处理逻辑（重要）**：
       - 如果 JD 中明确包含薪资范围，直接使用（如 "25k-40k/月"）
       - 如果 JD 显示 "面议"、"Negotiable" 或隐藏薪资信息，必须使用以下方法之一：
         * 参考步骤 2.2 中 `analyze_market_match_tool` 搜索结果中的薪资信息
         * 使用你的内部知识或市场数据，提供 "市场参考" 格式（如 "市场参考: 20k-30k/月"）
       - **绝对不能留空**，必须提供薪资信息（即使是市场参考值）
       
       **地点处理逻辑**：
       - Base Location 必须是具体地点（如 "北京"、"上海"、"Singapore"、"远程"）
       - 不能使用模糊表述（如 "待定"、"TBD"），如果 JD 中没有明确地点，使用 "待确认" 但尽量从 JD 内容推断
       
       **示例表格行**：
       | ByteDance | AI Engineer | 北京 | 25k-40k/月 | Python, PyTorch, K8s |
       | Shopee | Machine Learning Engineer | 新加坡 | 市场参考: 20k-30k/月 | TensorFlow, AWS, Docker |
       | 美团 | AI算法工程师 | 上海 | 面议 (市场参考: 22k-35k/月) | Python, Spark, 推荐系统 |
    
    3. 将这份报告格式化为清晰的 Markdown 文档，确保职位对比表格式正确
    4. 使用 save_report_tool 将内容保存到文件 'my_career_plan.md'
    5. 告诉用户文件已生成
    
    注意：步骤 6 是最终步骤，完成此步骤后任务就结束了。确保报告内容完整、格式良好，职位对比表包含所有必需信息，并且文件已成功保存。
    """)