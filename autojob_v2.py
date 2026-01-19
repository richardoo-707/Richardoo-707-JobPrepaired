"""
多 Agent 职业规划系统 (v2) - 带质量审核与自我修正

本文件使用 smolagents 构建原生多 Agent 系统，实现 Reflexion 模式。
系统由三个专业化的专家 Agent（分析师、猎头、导师）
和一个负责质量审核的 Manager Agent 组成。

工作流程（带质量审核）：
1. Analyst Agent: 分析简历，基于真实市场数据推荐目标公司
2. Headhunter Agent: 搜索职位描述（优先使用本地缓存）
3. Coach Agent: 分析技能差距，推荐 GitHub 学习资源
4. Manager Agent: 审核每个阶段的质量，不合格则要求重试，最终生成报告
"""

import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, BaseTool

# 导入所有工具函数
from tools.resume_tools import read_resume_tool
from tools.web_tools import search_jd_tool, visit_page_tool
from tools.github_tools import search_github_tool
from tools.market_tools import analyze_market_match_tool
from tools.db_tools import query_local_db_tool, save_to_db_tool
from tools.file_tools import save_report_tool

# ==================== 1. 加载环境变量 ====================
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
api_base = os.getenv("ANTHROPIC_API_BASE")
model_name = os.getenv("ANTHROPIC_MODEL_ID")

# 验证必要的环境变量
if not api_key:
    raise ValueError("错误：未设置 ANTHROPIC_API_KEY 环境变量，请在 .env 文件中配置")
if not model_name:
    raise ValueError("错误：未设置 ANTHROPIC_MODEL_ID 环境变量，请在 .env 文件中配置")

# ==================== 2. 初始化模型 ====================
# 使用 LiteLLMModel 可以兼容 OpenAI 格式、Anthropic 格式或任何中转 API
model = LiteLLMModel(
    model_id=model_name,  # 例如: "anthropic/claude-3-5-sonnet" 或 "openai/qwen-2.5-coder"
    api_key=api_key,
    api_base=api_base  # 如果使用官方 API，这里可能是 None；如果使用中转，这里是中转地址
)

# ==================== 3. 定义 AgentTool 包装类 ====================
class AgentTool(BaseTool):
    """
    将 Agent 包装成 Tool 的适配器类
    
    这个类允许将 CodeAgent 实例作为工具使用，实现 "Agent as Tool" 模式。
    这样 Manager Agent 可以将子 Agent 视为工具来调用。
    """
    
    def __init__(self, agent: CodeAgent, name: str, description: str):
        """
        初始化 AgentTool
        
        Args:
            agent: 要包装的 CodeAgent 实例
            name: 工具名称
            description: 工具描述
        """
        self.agent = agent
        self.name = name
        self.description = description
        # 定义输入参数结构
        self.inputs = {
            "task": {
                "type": "string",
                "description": "任务的具体描述，将传递给 Agent 执行"
            }
        }
        self.output_type = "string"
        # 设置 jinja_pass_arg 属性，用于 Jinja 模板渲染
        self.jinja_pass_arg = True
        super().__init__()
    
    def __call__(self, task: str) -> str:
        """
        执行 Agent 任务（工具调用接口，带超时保护）
        
        Args:
            task: 任务描述字符串
            
        Returns:
            Agent 执行结果的字符串
        """
        try:
            # 调用子 Agent 执行任务
            # 注意：子 Agent 已经设置了 max_steps 限制，避免执行时间过长
            # 添加超时保护（通过 max_steps 限制实现，不额外添加超时以避免复杂性）
            print(f"[{self.name}] 开始执行任务...")
            result = self.agent.run(task)
            print(f"[{self.name}] 任务执行完成")
            return str(result) if result else "任务执行完成，但未返回结果"
        except KeyboardInterrupt:
            # 处理用户中断
            print(f"[{self.name}] 执行被用户中断")
            return f"错误：{self.name} Agent 执行被用户中断"
        except TimeoutError:
            # 处理超时
            print(f"[{self.name}] 执行超时")
            return f"警告：{self.name} Agent 执行超时，请检查网络连接或减少任务复杂度"
        except Exception as e:
            # 捕获所有其他异常并返回错误信息
            error_msg = str(e)
            print(f"[{self.name}] 执行失败: {error_msg}")
            # 返回错误信息，但不中断整个流程
            return f"警告：{self.name} Agent 执行遇到问题 - {error_msg[:200]}（已继续执行）"
    
    def forward(self, task: str) -> str:
        """
        执行 Agent 任务（备用接口）
        
        Args:
            task: 任务描述字符串
            
        Returns:
            Agent 执行结果的字符串
        """
        return self.__call__(task)
    
    def to_code_prompt(self) -> str:
        """
        生成用于 CodeAgent 的代码提示字符串
        
        这个方法用于在 CodeAgent 的 system prompt 中生成工具的函数签名。
        返回格式化的函数定义字符串。
        
        Returns:
            工具的函数签名字符串，用于 CodeAgent 的代码生成提示
        """
        # 生成函数签名，格式：def tool_name(task: str) -> str:
        # 然后添加文档字符串
        prompt = f"def {self.name}(task: str) -> str:\n"
        prompt += f'    """\n'
        prompt += f'    {self.description}\n'
        prompt += f'    \n'
        prompt += f'    Args:\n'
        prompt += f'        task (str): 任务的具体描述，将传递给 Agent 执行\n'
        prompt += f'    \n'
        prompt += f'    Returns:\n'
        prompt += f'        str: Agent 执行结果的字符串\n'
        prompt += f'    """\n'
        prompt += f'    # 调用 {self.name} Agent 执行任务\n'
        prompt += f'    pass'
        return prompt

# ==================== 4. 定义专家 Agent（子 Agent）====================

# Analyst Agent: 行业分析师 - 分析简历并基于真实市场数据推荐目标公司
analyst_agent = CodeAgent(
    tools=[read_resume_tool, analyze_market_match_tool],
    model=model,
    name="industry_analyst",
    description="资深行业分析师。你的职责不是凭空想象，而是基于数据寻找最匹配的求职目标。1. 必须先使用 `read_resume_tool` 分析用户背景，提取关键标签（如学历、专业、亮点）。2. 必须使用 `analyze_market_match_tool` 去牛客/知乎搜索这些标签，看类似背景的人实际拿到了哪些公司的 Offer。3. 拒绝眼高手低，只推荐有真实录取案例的务实公司。**重要：请高效执行，避免重复步骤，如果搜索失败或超时，使用已有信息继续。**",
    max_steps=8  # 优化：减少步数，避免卡死
)

# Headhunter Agent: 猎头专家 - 搜索职位描述（带缓存机制）
headhunter_agent = CodeAgent(
    tools=[query_local_db_tool, save_to_db_tool, search_jd_tool, visit_page_tool],
    model=model,
    name="job_headhunter",
    description="数据驱动的猎头专家。你负责获取职位详情(JD)、薪资和地点。执行逻辑必须严格遵守：1. 【查库】：收到公司名后，**必须第一步**调用 `query_local_db_tool` 检查本地是否有缓存。如果有且匹配，直接返回，跳过后续。2. 【搜网】：如果数据库没有，调用 `search_jd_tool` 和 `visit_page_tool` 去互联网搜索最新的 JD。**重要：如果搜索超时或失败，使用市场参考数据继续，不要卡住。**3. 【入库】：如果你是通过联网搜到的新 JD，在返回结果前，调用 `save_to_db_tool` 将其存入数据库。4. 提取重点：薪资范围 (Salary)、Base 地点、核心技能要求。",
    max_steps=12  # 优化：减少步数，避免卡死
)

# Coach Agent: 职业导师 - 分析技能差距并推荐学习资源
coach_agent = CodeAgent(
    tools=[search_github_tool],
    model=model,
    name="career_coach",
    description="技术职业导师。负责分析技能差距 (Gap Analysis) 并推荐学习资源。1. 接收 Analyst 的简历分析和 Headhunter 的 JD 要求。2. 找出用户缺少的关键技能（Hard Skills）。3. 使用 `search_github_tool` 搜索 3 个高质量项目来填补这些差距。**重要：如果搜索失败，使用已知的知名项目推荐，不要卡住。**4. 推荐时保留项目的英文原名，但用中文解释推荐理由。必须推荐具体的 GitHub 仓库链接（格式：owner/repo），不能是泛泛的建议。",
    max_steps=6  # 优化：减少步数，避免卡死
)

# ==================== 5. 将 Agent 包装成 Tool ====================

# 将三个子 Agent 包装成 Tool，供 Manager Agent 使用
analyst_tool = AgentTool(
    agent=analyst_agent,
    name="industry_analyst",
    description="行业分析师工具。基于真实市场数据（牛客网/知乎）分析简历并推荐务实的目标公司。输入：任务描述（包含简历路径和分析要求）。输出：推荐的公司列表（必须基于真实数据，不能是泛泛的大厂）。"
)

headhunter_tool = AgentTool(
    agent=headhunter_agent,
    name="job_headhunter",
    description="职位猎头工具。搜索职位描述(JD)，优先使用本地缓存。输入：任务描述（包含公司列表和搜索要求）。输出：职位详情，必须包含薪资范围和 Base 地点。"
)

coach_tool = AgentTool(
    agent=coach_agent,
    name="career_coach",
    description="职业导师工具。分析技能差距并推荐具体的 GitHub 学习项目。输入：任务描述（包含简历分析和 JD 要求）。输出：技能差距分析和具体的 GitHub 仓库推荐（必须包含仓库链接，不能是泛泛建议）。"
)

# ==================== 6. 定义 Manager Agent（质量审核员）====================
# Manager Agent: 严格的项目经理和质量审核员
# 职责：协调团队并审核他们的工作，不合格则要求重试
manager_agent = CodeAgent(
    tools=[analyst_tool, headhunter_tool, coach_tool, save_report_tool],
    model=model,
    name="manager",
    description="你是一名严格但高效的项目经理和质量审核员。你的职责是协调团队并审核他们的工作。**重要优化原则**：1. 如果结果基本可用（即使有小缺陷），优先接受并继续，而不是反复重试。2. 每个阶段最多重试1次，如果第二次仍然不完美，使用现有结果继续。3. 避免无限重试导致卡死。4. 你负责确保每个阶段的输出都符合基本质量标准，但不要过度追求完美。",
    max_steps=20  # 优化：减少步数，避免卡死（原30步可能导致执行时间过长）
)

# ==================== 7. 主执行流程 ====================
if __name__ == "__main__":
    # 简历文件路径（可根据需要修改）
    resume_path = "./resume.pdf"
    
    # 检查简历文件是否存在
    if not os.path.exists(resume_path):
        print(f"⚠️  警告：简历文件 '{resume_path}' 不存在")
        print("请确保简历文件存在于当前目录，或修改 resume_path 变量")
        resume_path = input("请输入简历文件路径（或按 Enter 继续使用默认路径）: ").strip()
        if not resume_path:
            resume_path = "./resume.pdf"
    
    print("🤖 多 Agent 系统启动中（带质量审核机制）...")
    print("=" * 60)
    
    manager_agent.run(f"""
    我上传了简历 '{resume_path}'。请严格按照以下流程执行，并进行质量把控：
    
    ========== 第一阶段：市场定位 (Analyst) ==========
    
    调用 industry_analyst 工具，要求：
    1. 使用 read_resume_tool 读取简历文件 '{resume_path}'，分析用户背景和技能
    2. 从简历中提取用户标签 (user_tags)，包括：
       - 教育背景：985/211/双非、本科/硕士/博士
       - 专业背景：计算机/非计算机/转码
       - 其他标签：海外留学、工作经验等
    3. 使用 analyze_market_match_tool(user_tags) 搜索牛客网和知乎，
       查找具有相似背景标签的候选人实际拿到 offer 的公司
    4. 基于搜索结果，推荐 5 家**真实可达成的**目标公司
    
    【审核点 - 平衡质量和效率】：
    - 如果返回的公司全是 Google/Microsoft/Apple 这种泛泛的大厂且没有具体理由，**可以要求重试1次**
    - 如果推荐的公司少于 5 家，**可以要求重试1次**，但如果重试后仍不足5家，使用现有结果继续（至少3家即可）
    - 必须基于牛客网/知乎的真实数据，但如果搜索失败，可以使用合理的市场知识继续
    
    **重要：每个阶段最多重试1次，避免无限循环导致卡死。如果重试后仍不完美，使用现有结果继续。**
    
    ========== 第二阶段：职位猎取 (Headhunter) ==========
    
    调用 job_headhunter 工具，要求：
    针对第一阶段通过审核的 5 家公司，执行以下步骤：
    
    步骤 2.1 (检查本地缓存):
    - 从简历中提取 3-5 个关键词标签（例如："Python"、"Java"、"Shanghai"、"Intern"、"AI" 等）
    - 使用 query_local_db_tool(tags) 查询本地数据库
    
    步骤 2.2 (决策):
    - 如果本地数据库返回了有用的 JD 信息：直接使用这些缓存的 JD，跳过在线搜索
    - 如果本地数据库没有返回结果，或者返回的 JD 不相关/过时：
      * 使用 search_jd_tool 搜索这 5  家公司的最近与用户相关岗位或相关职位 JD
      * 对于每个找到的 JD URL，使用 visit_page_tool 访问并提取完整的职位描述内容
    
    步骤 2.3 (缓存新数据):
    - 如果进行了在线搜索并找到了好的 JD（包含完整信息、相关性强），
      使用 save_to_db_tool 将这些 JD 保存到本地数据库
    
    【审核点 - 平衡质量和效率】：
    - **薪资检查**：如果薪资是 '面议'、'Negotiable'、'Unknown' 或缺失，**可以要求重试1次**，要求它根据内部知识或市场数据估算一个参考范围（格式：市场参考: XXk-XXk/月）。如果重试后仍缺失，使用"市场参考: 待评估"继续。
    - **地点检查**：如果缺少 Base 地点或地点是 '待定'、'TBD'，**可以要求重试1次**。如果重试后仍缺失，使用"待确认"继续。
    - **岗位检查**：如果岗位和其专业明显不相关（如财经背景却推荐AI岗位），**可以要求重试1次**。但如果岗位基本相关，即使不完全匹配，也接受继续。
    
    **重要：每个阶段最多重试1次，避免无限循环导致卡死。如果重试后仍不完美，使用现有结果继续。**
    
    ========== 第三阶段：技能差距 (Coach) ==========
    
    调用 career_coach 工具，要求：
    1. 对比 JD 要求和简历技能，分析技能差距，告诉我缺什么技能
    2. 对于缺失的技能，使用 search_github_tool 搜索相关的学习资源和项目，推荐 GitHub 仓库
    
    【审核点 - 平衡质量和效率】：
    - 如果推荐的是 '学习 Python'、'学习机器学习' 这种泛泛的建议，**可以要求重试1次**，要求推荐具体的 GitHub 仓库链接。
    - 必须推荐具体的 GitHub 仓库链接，格式为：owner/repo（例如：langchain-ai/langchain）
    - 每个推荐必须包含完整的仓库名称和链接
    - 如果搜索失败，可以使用知名的相关项目（如 tensorflow/tensorflow, pytorch/pytorch）作为备选
    
    **重要：每个阶段最多重试1次，避免无限循环导致卡死。如果重试后仍不完美，使用现有结果继续。**
    
    ========== 第四阶段：最终报告 (Manager) ==========
    
    汇总所有通过审核的高质量数据，执行以下任务：
    
    1. 编译一份**详细且专业**的综合摘要报告，必须包含以下内容（按顺序）：
    
       **1.1 职位对比表**（必须包含，见下方格式要求）
       
       **1.2 JD关键要求分析**（**必须详细，不能简单列表**）
       - 为**每个公司单独**创建一个子章节（格式：### 公司名 - 职位名称）
       - 每个公司的分析必须包含：
         * **核心技术栈**: 列出主要编程语言、框架、工具
         * **系统架构/算法方向**: 分布式系统、微服务、AI算法等（根据职位类型）
         * **性能优化/工程能力**: 缓存策略、数据库优化、系统调优等
         * **业务理解/领域知识**: 特定业务场景、行业知识等
       - 示例格式：
         ```
         ### 腾讯 - 后端开发工程师
         - **核心技术栈**: Java, SpringBoot, MySQL, Redis
         - **分布式系统**: 微服务架构, 高并发处理, 系统稳定性保障
         - **性能优化**: 缓存策略, 数据库优化, 系统调优
         - **工程能力**: 完整的软件开发生命周期经验, 代码质量和可维护性
         ```
       
       **1.3 技能差距分析**（**必须详细，分为两部分**）
       - **第一部分：已具备的核心技能**
         * 必须基于简历内容，详细列出用户已经掌握的技能
         * 包括：编程语言、框架、数据库、工具、实际项目经验等
         * 格式示例：
           ```
           ### 已具备的核心技能
           - **编程语言**: Java (熟练掌握)
           - **框架**: SpringBoot, SpringCloudAlibaba (Nacos, OpenFeign)
           - **数据库**: MySQL (索引优化, 事务), Redis (分布式锁, 缓存策略)
           - **实际项目经验**: 租车政策系统、审批系统、短链接系统
           ```
       
       - **第二部分：需要提升的技能领域**
         * 必须按**公司方向**分类（格式：#### 公司名方向）
         * 每个公司方向列出具体的技能差距和提升建议
         * 格式示例：
           ```
           ### 需要提升的技能领域
           
           #### 腾讯方向
           - **高级分布式系统模式**: CAP理论深入应用, 一致性算法
           - **云平台经验**: 腾讯云/AWS等云服务使用经验
           - **容器化技术**: Docker, Kubernetes基础
           ```
       
       **1.4 推荐GitHub学习项目**（**必须有分类和学习建议**）
       - 必须按**技术领域**分类（如：分布式系统和高并发、AI/机器学习、前端开发等）
       - 每个分类下列出相关的 GitHub 项目
       - 每个项目必须包含：项目名称（链接）、简要说明
       - **必须包含"学习建议"子章节**，提供4-5条具体的学习建议
       - 格式示例：
         ```
         ## 推荐GitHub学习项目
         
         ### 分布式系统和高并发
         - **[项目名](链接)** - 项目说明
         
         ### 学习建议
         1. **优先补足核心差距**: 重点关注...
         2. **动手实践**: 基于推荐的GitHub项目进行二次开发或模仿实现
         3. **参与开源**: 在相关项目中贡献代码，积累实际经验
         4. **准备面试**: 针对目标公司的技术栈进行专项练习
         ```
       
       **1.5 总结**（**必须包含**）
       - 基于用户的背景（学历、专业、经验）进行总结
       - 评估目标公司的可达性
       - 提供优先投递建议和学习路径建议
       - 格式示例：
         ```
         ## 总结
         
         基于您的[背景]和[技能]，[公司列表]都是可达成的目标。您的[经验]已经覆盖了大部分核心要求，主要需要在[具体领域]上进行补充。
         
         建议优先投递[公司1]和[公司2]的[职位类型]岗位，同时准备[公司3]的相关职位。通过针对性的学习和项目实践，您完全有能力获得这些公司的offer。
         ```
    
    2. **职位对比表格式要求（必须严格遵守）**：
       表格必须包含以下列：
       `| 公司名称 | 职位名称 | Base (地点) | 预估薪资 | 核心要求 (简述) |`
       
       **薪资处理逻辑（重要）**：
       - 如果 JD 中明确包含薪资范围，直接使用（如 "25k-40k/月"）
       - 如果 JD 显示 "面议"、"Negotiable" 或隐藏薪资信息，必须使用市场参考格式
       - **绝对不能留空**，必须提供薪资信息（即使是市场参考值）
       
       **地点处理逻辑**：
       - Base Location 必须是具体地点（如 "北京"、"上海"、"Singapore"、"远程"）
       - 不能使用模糊表述（如 "待定"、"TBD"）
       
       **示例表格行**：
       | ByteDance | AI Engineer | 北京 | 25k-40k/月 | Python, PyTorch, K8s |
       | Shopee | Machine Learning Engineer | 新加坡 | 市场参考: 20k-30k/月 | TensorFlow, AWS, Docker |
       | 美团 | AI算法工程师 | 上海 | 面议 (市场参考: 22k-35k/月) | Python, Spark, 推荐系统 |
    
    3. **报告质量要求（非常重要）**：
       - 报告必须**详细且专业**，不能是简单的列表或概述
       - JD关键要求分析必须为每个公司单独分析，不能合并
       - 技能差距分析必须明确区分"已具备"和"需要提升"，并按公司方向分类
       - GitHub项目推荐必须有分类和学习建议
       - 必须包含总结部分
       - 所有内容必须基于简历和JD的实际内容，不能泛泛而谈
    
    4. 将这份报告格式化为清晰的 Markdown 文档，确保格式正确、层次分明
    
    5. **语言必须是简体中文**（即使 JD 和 GitHub 是英文，也要翻译成中文总结）
    
    6. 使用 save_report_tool 将内容保存到文件 'my_career_plan_v2.md'
    
    7. 告诉用户文件已生成
    
    ========== 重要提醒 ==========
    
    作为质量审核员，你必须：
    - 在每个阶段结束后，审核输出质量，但**优先效率，避免卡死**
    - 如果质量不达标，**最多要求重试1次**，说明具体问题
    - 如果重试后仍不完美，**使用现有结果继续**，不要无限重试
    - 最终报告必须包含所有必需信息，格式正确，内容完整
    - **关键原则：宁可接受略有缺陷的结果，也不要因为追求完美而卡死**
    
    现在开始执行，严格按照上述流程和质量标准进行，但始终优先考虑执行效率和稳定性。
    """)
