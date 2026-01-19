"""
Gradio Web 应用 - 多 Agent 职业规划系统 (Hugging Face Spaces 版本)

适配 Hugging Face Spaces 部署，优化执行时间，避免超时。
基于 autojob_v3.py 优化，保持核心逻辑不变。
"""

import os
import gradio as gr
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel

# 导入所有工具函数
from tools.resume_tools import read_resume_tool
from tools.web_tools import search_jd_tool, visit_page_tool
from tools.github_tools import search_github_tool
from tools.market_tools import analyze_market_match_tool
from tools.db_tools import query_local_db_tool, save_to_db_tool
from tools.file_tools import save_report_tool

# ==================== 1. 加载环境变量（适配 HF Spaces）====================
# HF Spaces 使用 secrets 来存储环境变量，通过 os.getenv 直接获取
load_dotenv()  # 仍然尝试加载 .env（本地开发时使用）

# 从环境变量获取配置（HF Spaces 会自动注入 secrets）
api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("HF_API_KEY")
api_base = os.getenv("ANTHROPIC_API_BASE")
model_name = os.getenv("ANTHROPIC_MODEL_ID") or os.getenv("MODEL_ID") or "anthropic/claude-3-5-sonnet"

# 验证必要的环境变量
if not api_key:
    raise ValueError(
        "错误：未设置 API 密钥。\n"
        "在 Hugging Face Spaces 中，请在 Settings -> Secrets 中添加：\n"
        "- ANTHROPIC_API_KEY 或 HF_API_KEY\n"
        "- ANTHROPIC_API_BASE (可选)\n"
        "- ANTHROPIC_MODEL_ID 或 MODEL_ID (可选)"
    )

# ==================== 2. 初始化模型 ====================
model = LiteLLMModel(
    model_id=model_name,
    api_key=api_key,
    api_base=api_base
)

# ==================== 3. 定义专家 Agent（子 Agent）====================
# 优化：减少 max_steps 以加快执行速度

# Analyst Agent: 行业分析师
analyst_agent = CodeAgent(
    tools=[read_resume_tool, analyze_market_match_tool],
    model=model,
    name="industry_analyst",
    description="资深行业分析师。你的职责不是凭空想象，而是基于数据寻找最匹配的求职目标。1. 必须先使用 `read_resume_tool` 分析用户背景，提取关键标签（如学历、专业、亮点）。2. 必须使用 `analyze_market_match_tool` 去牛客/知乎搜索这些标签，看类似背景的人实际拿到了哪些公司的 Offer。3. 拒绝眼高手低，只推荐有真实录取案例的务实公司。",
    max_steps=8  # 优化：减少步数
)

# Headhunter Agent: 猎头专家
headhunter_agent = CodeAgent(
    tools=[query_local_db_tool, save_to_db_tool, search_jd_tool, visit_page_tool],
    model=model,
    name="job_headhunter",
    description="数据驱动的猎头专家。你负责获取职位详情(JD)、薪资和地点。执行逻辑必须严格遵守：1. 【查库】：收到公司名后，**必须第一步**调用 `query_local_db_tool` 检查本地是否有缓存。如果有且匹配，直接返回，跳过后续。2. 【搜网】：如果数据库没有，调用 `search_jd_tool` 和 `visit_page_tool` 去互联网搜索最新的 JD。3. 【入库】：**非常重要！** 如果你是通过联网搜到的新 JD，在返回结果前，**必须**调用 `save_to_db_tool` 将其存入数据库，以便下次复用。4. 提取重点：薪资范围 (Salary)、Base 地点、核心技能要求。",
    max_steps=10  # 优化：减少步数
)

# Coach Agent: 职业导师
coach_agent = CodeAgent(
    tools=[search_github_tool],
    model=model,
    name="career_coach",
    description="技术职业导师。负责分析技能差距 (Gap Analysis) 并推荐学习资源。1. 接收 Analyst 的简历分析和 Headhunter 的 JD 要求。2. 找出用户缺少的关键技能（Hard Skills）。3. 使用 `search_github_tool` 搜索 3 个高质量项目来填补这些差距。4. 推荐时保留项目的英文原名，但用中文解释推荐理由。",
    max_steps=6  # 优化：减少步数
)

# ==================== 4. 定义 Manager Agent ====================
# 使用单 Agent 模式（更稳定，避免 managed_agents 兼容性问题）
manager_agent = CodeAgent(
    tools=[
        read_resume_tool,
        analyze_market_match_tool,
        query_local_db_tool,
        save_to_db_tool,
        search_jd_tool,
        visit_page_tool,
        search_github_tool,
        save_report_tool
    ],
    model=model,
    name="manager",
    max_steps=15  # 优化：减少总步数，避免超时
)


def build_prompt(resume_path: str) -> str:
    """
    构建执行 prompt（优化版本，减少复杂度）
    
    Args:
        resume_path: 简历文件路径
        
    Returns:
        优化的 prompt 字符串
    """
    prompt = f"""
    我上传了一份简历，路径是 '{resume_path}'。
    请按照以下流程帮我规划求职（**注意：为了节省时间，请高效执行，避免重复步骤**）：
    
    === 阶段 1: 分析简历并推荐公司 ===
    1. 使用 read_resume_tool 读取简历文件 '{resume_path}'，分析我的背景和技能。
    2. 从简历中提取用户标签 (user_tags)，格式如："985 Master CS" 或 "双非本科 非科班 转码"
    3. 使用 analyze_market_match_tool(user_tags) 搜索牛客网和知乎，查找相似背景的人实际拿到 offer 的公司。
    4. 基于搜索结果，推荐 **3-5 家**真实可达成的目标公司（只推荐搜索结果中实际出现的公司）。
    
    === 阶段 2: 获取职位描述 ===
    针对推荐的 3-5 家公司，执行以下步骤：
    
    步骤 2.1: 检查本地缓存
    - 从简历中提取 3-5 个关键词标签（如："Python"、"Java"、"Shanghai"、"AI" 等）
    - 使用 query_local_db_tool(tags) 查询本地数据库
    
    步骤 2.2: 决策
    - **如果本地数据库返回了有用的 JD 信息**：直接使用这些缓存的 JD，跳过在线搜索
    - **如果本地数据库没有返回结果**：
      * 使用 search_jd_tool 搜索这 3-5 家公司的相关职位 JD（**只搜索前 3 家公司，节省时间**）
      * 对于每个找到的 JD URL，使用 visit_page_tool 访问并提取职位描述
    
    步骤 2.3: 缓存新数据
    - 如果进行了在线搜索，使用 save_to_db_tool 将新 JD 保存到数据库
    
    **重要：提取以下关键信息：**
    - 薪资范围: 如 "20k-30k/月"、"面议"（如果是面议，使用"市场参考: XXk-XXk/月"格式）
    - 工作地点: 如 "北京"、"上海"、"Singapore"、"远程"
    - 职位名称: 准确的职位标题
    - 核心要求: 关键技术栈和技能要求
    
    === 阶段 3: 分析技能差距并推荐学习资源 ===
    1. 对比 JD 要求和我的简历技能，分析技能差距。
    2. 对于缺失的技能，使用 search_github_tool 搜索相关的学习项目，推荐 **3-5 个** GitHub 仓库。
    
    === 阶段 4: 生成最终报告 ===
    **语言必须是简体中文**。
    
    1. 编译一份综合摘要报告，包含：
       - **职位对比表**（格式见下方）
       - JD关键要求分析（为每个公司单独分析）
       - 技能差距分析（分为"已具备的核心技能"和"需要提升的技能领域"）
       - 推荐的 GitHub 学习项目（按技术领域分类，包含学习建议）
       - 总结（基于背景评估可达性，提供投递建议）
    
    2. **职位对比表格式**：
       | 公司名称 | 职位名称 | Base (地点) | 预估薪资 | 核心要求 (简述) |
       
       **薪资处理**：
       - 如果 JD 中有薪资范围，直接使用（如 "25k-40k/月"）
       - 如果是"面议"或缺失，使用"市场参考: XXk-XXk/月"格式，**不能留空**
       
       **地点处理**：
       - 必须是具体地点（如 "北京"、"上海"、"远程"）
       - 如果 JD 中没有明确地点，使用"待确认"但尽量从 JD 内容推断
    
    3. 将报告格式化为清晰的 Markdown 文档
    4. 使用 save_report_tool 将内容保存到文件 'my_career_plan_v2.md'
    5. 告诉用户文件已生成
    
    **重要提醒**：
    - 请高效执行，避免不必要的重复步骤
    - 如果本地数据库有缓存，优先使用缓存
    - 只搜索前 3 家公司的 JD，节省时间
    - 确保报告内容完整、格式正确
    """
    return prompt


def process_resume(file) -> str:
    """
    处理上传的简历文件（适配 HF Spaces）
    
    Args:
        file: Gradio 文件上传对象
        
    Returns:
        生成的职业规划报告（Markdown 格式）
    """
    # 检查文件是否上传
    if file is None:
        return "❌ **错误**：请先上传简历文件（PDF 格式）"
    
    # 获取文件路径（适配 Gradio 6.3.0 和 HF Spaces）
    file_path = None
    
    if isinstance(file, str):
        file_path = file
    elif hasattr(file, 'name'):
        file_path = file.name
    elif isinstance(file, dict):
        file_path = file.get('name') or file.get('path')
    elif isinstance(file, list) and len(file) > 0:
        first_file = file[0]
        if isinstance(first_file, str):
            file_path = first_file
        elif hasattr(first_file, 'name'):
            file_path = first_file.name
        elif isinstance(first_file, dict):
            file_path = first_file.get('name') or first_file.get('path')
    elif isinstance(file, bytes):
        # 如果是字节流，保存到临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(file)
        temp_file.close()
        file_path = temp_file.name
    else:
        file_path = str(file)
    
    # 验证文件路径
    if not file_path:
        return "❌ **错误**：无法获取文件路径，请重新上传文件"
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return f"❌ **错误**：文件不存在 - {file_path}"
    
    # 检查文件扩展名
    if not file_path.lower().endswith('.pdf'):
        return "❌ **错误**：请上传 PDF 格式的简历文件"
    
    try:
        # 构建 prompt
        prompt = build_prompt(file_path)
        
        # 调用 manager_agent 执行任务
        print(f"🤖 开始处理简历: {file_path}")
        result = manager_agent.run(prompt)
        
        # 返回结果
        if result:
            # 尝试读取生成的报告文件
            report_path = "my_career_plan_v2.md"
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                return report_content
            else:
                # 如果没有生成文件，返回 agent 的执行结果
                return str(result)
        else:
            return "⚠️ **警告**：Agent 执行完成，但未返回结果。请检查控制台输出。"
            
    except KeyboardInterrupt:
        return "❌ **错误**：处理被用户中断"
    except Exception as e:
        error_msg = f"❌ **执行错误**：{str(e)}\n\n**错误类型**：{type(e).__name__}\n\n请检查：\n1. API 密钥是否正确配置\n2. 网络连接是否正常\n3. 文件格式是否正确"
        print(f"错误详情: {error_msg}")
        import traceback
        print(f"完整错误堆栈:\n{traceback.format_exc()}")
        return error_msg


# ==================== 创建 Gradio 界面 ====================
with gr.Blocks(title="多 Agent 职业规划系统", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 多 Agent 职业规划系统
    
    基于 AI Agent 的智能职业规划助手，帮助您：
    - 📊 分析简历背景，推荐务实的目标公司
    - 🔍 搜索职位描述（JD），提取薪资和地点信息
    - 📚 分析技能差距，推荐 GitHub 学习项目
    - 📝 生成完整的职业规划报告
    
    **使用说明**：
    1. 上传您的简历文件（PDF 格式）
    2. 点击"开始职业规划"按钮
    3. 等待系统分析（可能需要 2-5 分钟）
    4. 查看生成的职业规划报告
    
    **注意**：本系统在 Hugging Face Spaces 免费 CPU 环境下运行，处理时间可能较长，请耐心等待。
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="上传简历 (Upload Resume)",
                file_types=[".pdf"],
                type="filepath",
                file_count="single"
            )
            submit_btn = gr.Button(
                "开始职业规划 (Start Planning)",
                variant="primary",
                size="lg"
            )
        
        with gr.Column(scale=2):
            output = gr.Markdown(
                label="职业规划报告",
                value="等待上传简历并开始分析..."
            )
    
    # 绑定事件
    submit_btn.click(
        fn=process_resume,
        inputs=file_input,
        outputs=output,
        api_name="process_resume",
        api_visibility="public"
    )
    
    # 添加说明
    gr.Markdown("""
    ---
    ### 📌 注意事项
    
    - 请确保简历文件为 PDF 格式
    - 分析过程可能需要 2-5 分钟，请耐心等待
    - 生成的报告会保存为 `my_career_plan_v2.md` 文件
    - 系统会自动进行质量审核，确保输出信息的完整性和准确性
    - 在 Hugging Face Spaces 免费环境下，处理时间可能较长
    """)


# ==================== 启动应用 ====================
if __name__ == "__main__":
    # HF Spaces 会自动调用 demo.launch()，但我们也提供本地运行支持
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
