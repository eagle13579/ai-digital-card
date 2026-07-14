# Coze Loop → AI数智名片 注入方案

> **时间**: 2026-07-14  
> **分析师**: 讹兽_HRBP (Bai Ze Legion, P8)  
> **引擎**: cognitive-evolution-engine  
> **收割源**: Coze Loop (字节跳动开源 AI Agent 全生命周期管理平台)  
> **目标产品**: AI数智名片 (FastAPI + React 19)  

---

## 目录

1. [概述与P0注入总图](#1-概述与p0注入总图)
2. [P0#1: Prompt-as-Code → 名片AI自我介绍/智能生成](#2-p01-prompt-as-code--名片ai自我介绍智能生成)
3. [P0#2: 多LLM适配器 → AI引擎可切换模型](#3-p02-多llm适配器--ai引擎可切换模型)
4. [P0#3: Trace可观测性 → 名片访客交互追踪](#4-p03-trace可观测性--名片访客交互追踪)
5. [P0#4: EDD评估引擎 → AI功能效果量化](#5-p04-edd评估引擎--ai功能效果量化)
6. [P1补充注入](#6-p1补充注入)
7. [P2补充注入](#7-p2补充注入)
8. [注入总路线图（甘特图）](#8-注入总路线图甘特图)
9. [心智模型映射矩阵](#9-心智模型映射矩阵)

---

## 1. 概述与P0注入总图

### 1.1 总览

| 注入编号 | Coze Loop模式源 | 目标产品功能 | 心智模型映射 | 人天 | 优先级 |
|----------|----------------|-------------|-------------|------|--------|
| **P0#1** | P12 Prompt版本管理 + Prompt-as-Code | 名片AI自我介绍/智能生成（小程序+Web） | Prompt-as-Code + Loop Flywheel | 8人天 | **P0** |
| **P0#2** | P2 多LLM适配器 + Pluggable Model Integration | AI引擎多模型可切换（DeepSeek/OpenAI/Claude） | Pluggable Model Integration | 5人天 | **P0** |
| **P0#3** | P3 可观测性追踪管道 + P22 Trace即调试基础设施 | 名片访客交互追踪 + 全链路AI调用记录 | Observability-as-Debugging | 10人天 | **P0** |
| **P0#4** | P11 评估引擎 + EDD | AI功能效果量化（自我介绍质量/推荐准确率） | Eval-Driven Development | 6人天 | **P0** |
| **P1#1** | P4 MQ工厂模式/RocketMQ | 异步名片生成/批量导入 | Loop Flywheel | 3人天 | P1 |
| **P1#2** | P6 ID生成器 | 分布式ID/名片唯一标识 | — | 1人天 | P1 |
| **P1#3** | P16 错误码体系 | 统一错误处理 | — | 2人天 | P1 |
| **P1#4** | P15 配置管理/Viper | 热加载Prompt模板配置 | Prompt-as-Code | 2人天 | P1 |
| **P2#1** | P5 分布式锁 | 并发名片编辑防冲突 | — | 1人天 | P2 |
| **P2#2** | P7 限流器 | API限流（名片生成/访客追踪） | — | 1人天 | P2 |

### 1.2 心智模型→注入映射总图

```
                    ┌─────────────────────────────────┐
                    │    AI Agent全生命周期管理飞轮      │
                    │       (Loop Flywheel)             │
                    │ 开发→调试→评估→观测→优化         │
                    └─────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
   │Prompt即代码   │   │ 评估驱动开发  │   │Trace即调试基础     │
   │(P0#1)        │   │ (P0#4)       │   │设施(P0#3)         │
   │版本管理/回滚  │◄──┤ EDD评估引擎   │──►│全链路Span追踪      │
   │AI自我介绍模板 │   │ 效果量化      │   │访客交互记录        │
   └──────────────┘   └──────────────┘   └──────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ 模型抽象层(可插拔) │
                    │ (P0#2)           │
                    │ 多LLM适配器工厂   │
                    └──────────────────┘
```

---

## 2. P0#1: Prompt-as-Code → 名片AI自我介绍/智能生成

### 2.1 【目标产品】

**小程序端**（微信小程序） + **Web端**（React前端）

- **AI自我介绍生成**: 用户输入基本信息（姓名、职位、行业、个人亮点），AI自动生成多风格自我介绍（正式/亲和/专业/创意）
- **AI智能名片描述**: 根据用户画像生成名片标语、核心价值陈述
- **多版本管理**: 支持保存多个自我介绍版本，一键切换/回滚
- **Prompt模板热更新**: 后端管理后台可动态修改Prompt，不重启服务

### 2.2 【心智模型映射】

| 心智模型 | 映射方式 |
|----------|---------|
| **Prompt-as-Code** | 将Prompt视为一等公民制品，具备版本号、标签(production/beta/test)、回滚能力。当前`writing_assistant.py`硬编码Prompt → 改为从DB/文件加载模板，版本化 |
| **Loop Flywheel** | AI自我介绍生成纳入飞轮：开发(Prompt模板编辑) → 调试(Web Playground预览) → 评测(AB测试不同Version) → 观测(用户点击率) → 优化(迭代Prompt) |

### 2.3 【代码集成路径】

```
写作助手模块重构路径:

backend/app/ai/writing_assistant.py (现状: 硬编码)
    ↓
backend/app/ai/prompt_engine/          (新增: Prompt引擎模块)
├── __init__.py
├── prompt_template.py                  ★ Prompt模板模型 (版本/标签/内容)
├── prompt_repository.py               ★ Prompt仓储 (SQLite CRUD + 版本管理)
├── prompt_renderer.py                 ★ Prompt渲染器 (Jinja2风格变量注入)
├── prompt_hub_service.py              ★ Prompt管理中心 (发布/回滚/灰度)
└── templates/                          (默认模板目录)
    ├── bio_formal.yaml                 (正式风格自我介绍)
    ├── bio_friendly.yaml               (亲和风格自我介绍)
    ├── bio_professional.yaml           (专业风格自我介绍)
    ├── bio_creative.yaml               (创意风格自我介绍)
    ├── company_description.yaml        (公司描述生成)
    └── slogan_generator.yaml           (标语生成)

小程序前端适配:
frontend/src/pages/profile/            (现有)
    ├── ...                              + 新增"AI生成自我介绍"页面
    └── components/PromptStyleSelector  ★ 风格选择器组件

Web前端适配:
frontend/src/pages/dashboard/
    └── components/AIBioGenerator       ★ AI自我介绍生成器组件
```

### 2.4 【具体修改文件】

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/app/ai/writing_assistant.py` | **重构** | 从硬编码Prompt改为调用`PromptRenderer.render(template_key, variables)` |
| `backend/app/ai/prompt_engine/prompt_template.py` | **新增** | `PromptTemplate` dataclass: id, key, version, tags, content, status, created_at |
| `backend/app/ai/prompt_engine/prompt_repository.py` | **新增** | SQLite仓储: save/load/list_versions/rollback/publish |
| `backend/app/ai/prompt_engine/prompt_renderer.py` | **新增** | Jinja2模板渲染引擎: `render(template_content, variables) → str` |
| `backend/app/ai/prompt_engine/prompt_hub_service.py` | **新增** | 管理服务: list_templates/create_version/rollback/promote_to_prod |
| `backend/app/routers/ai.py` | **修改** | + 路由: `POST /api/ai/bio/generate`, `GET /api/ai/bio/templates`, `POST /api/ai/bio/templates/{id}/publish` |
| `backend/app/ai/__init__.py` | **修改** | 注册prompt_engine模块 |
| `frontend/src/pages/profile/` | **修改** | 添加AI生成入口和风格选择 |
| `frontend/src/components/` | **新增** | PromptStyleSelector / AIBioGenerator 组件 |

### 2.5 【具体修改代码片段】

#### writing_assistant.py 重构核心

```python
# 现状 (硬编码):
def generate_bio(self, name, title, company, highlights):
    prompt = f"""你是AI数智名片助手。请为{name}生成一段自我介绍。
职位: {title}
公司: {company}
亮点: {highlights}
风格: 专业正式"""
    return self._call_deepseek(prompt)

# 重构后 (模板驱动):
from .prompt_engine.prompt_renderer import PromptRenderer
from .prompt_engine.prompt_repository import PromptRepository

class WritingAssistant:
    def __init__(self, llm_adapter):
        self.renderer = PromptRenderer()
        self.repo = PromptRepository()
        self.llm = llm_adapter  # 通过P0#2的适配器注入
    
    async def generate_bio(self, name, title, company, highlights, 
                           style="professional", template_version="production"):
        """从模板生成自我介绍"""
        # 1. 获取模板 (版本管理)
        template = await self.repo.get_template("bio", template_version)
        if not template:
            template = await self.repo.get_default("bio")
        
        # 2. 渲染Prompt
        prompt = self.renderer.render(template.content, {
            "name": name, "title": title, 
            "company": company, "highlights": highlights,
            "style": style,
        })
        
        # 3. 调用LLM (通过P0#2的多模型适配器)
        result = await self.llm.generate(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
        )
        
        # 4. 记录调用Trace (通过P0#3的可观测性)
        # span记录在更上层统一处理
        
        return result.content
    
    async def list_styles(self):
        """列出可用风格"""
        return await self.repo.list_templates(category="bio")
```

#### Prompt Template 数据模型

```python
# prompt_engine/prompt_template.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class PromptTemplate:
    """Prompt模板 — Coze Loop Prompt-as-Code模型"""
    id: str = ""
    key: str = ""                    # 模板标识: "bio", "slogan", "company_desc"
    name: str = ""                   # 模板名称
    description: str = ""            # 描述
    version: int = 1                 # 版本号
    tags: list[str] = field(default_factory=list)  # ["production", "beta", "test"]
    content: str = ""                # Jinja2模板内容
    variables_schema: dict = field(default_factory=dict)  # 变量Schema
    status: str = "draft"            # draft/published/archived
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
```

#### 前端Prompt风格选择器组件

```tsx
// PromptStyleSelector.tsx (React 19)
interface StyleOption {
  key: string;
  name: string;
  icon: string;
  description: string;
}

interface Props {
  onSelect: (style: string) => void;
  currentStyle?: string;
}

export function PromptStyleSelector({ onSelect, currentStyle }: Props) {
  const [styles, setStyles] = useState<StyleOption[]>([]);
  
  useEffect(() => {
    fetch('/api/ai/bio/templates')
      .then(r => r.json())
      .then(data => setStyles(data));
  }, []);
  
  return (
    <div className="grid grid-cols-2 gap-3">
      {styles.map(s => (
        <button
          key={s.key}
          onClick={() => onSelect(s.key)}
          className={`p-4 rounded-xl border-2 transition-all
            ${currentStyle === s.key 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-200 hover:border-blue-300'}`}
        >
          <span className="text-2xl">{s.icon}</span>
          <p className="mt-1 font-medium">{s.name}</p>
          <p className="text-xs text-gray-500">{s.description}</p>
        </button>
      ))}
    </div>
  );
}
```

### 2.6 【优先级】P0 — 立即执行

### 2.7 【人天估算】8人天

| 工作项 | 人天 | 角色 |
|--------|------|------|
| PromptEngine数据模型 + 仓储 | 1.5 | 后端 |
| Prompt渲染器 + Jinja2集成 | 1 | 后端 |
| Prompt管理路由 + Version API | 1 | 后端 |
| writing_assistant.py重构 | 1 | 后端 |
| Prompt模板YAML编写(6个模板) | 0.5 | 后端 |
| 前端PromptStyleSelector组件 | 1 | 前端 |
| 前端AIBioGenerator组件 + 页面 | 1.5 | 前端 |
| 小程序端适配 | 0.5 | 前端 |

---

## 3. P0#2: 多LLM适配器 → AI引擎可切换模型

### 3.1 【目标产品】

**AI引擎后端** (`backend/app/ai/`)

- 当前：`ai/gateway/adapters/` 仅有DeepSeek硬编码，FallbackAIGateway/CachedAIGateway耦合DeepSeek API
- 目标：引入Coze Loop ILLM接口 + 工厂模式，支持DeepSeek/OpenAI/Claude一键切换，YAML配置驱动，零代码切换模型

### 3.2 【心智模型映射】

| 心智模型 | 映射方式 |
|----------|---------|
| **Pluggable Model Integration** | 统一ILLM接口 + 适配器工厂 + 注册器模式，当前`DirectAIGateway`深度耦合DeepSeek SDK → 改为通过`FactoryImpl.create_llm()`创建，切换模型改一行YAML |
| **Loop Flywheel** | 多模型支持A/B测试：同一Prompt在不同LLM上的质量对比，直接驱动EDD评估引擎(P0#4) |

### 3.3 【代码集成路径】

```
Coze Loop Go源码 → Python模板 (已有: _code_patterns_llm_adapter.md ~1,440行)
    ↓
backend/app/ai/llm_adapter/              (新增: LLM适配器工厂模块)
├── __init__.py
├── base_adapter.py                      ★ ILLM接口 + Message + Options (复用收割模板)
├── model_config.py                      ★ Model配置 + ProtocolConfig (复用收割模板)
├── adapter_factory.py                   ★ FactoryImpl + AdapterRegistry (复用收割模板)
├── adapters/
│   ├── __init__.py
│   ├── openai_adapter.py                ★ OpenAI适配器 (复用收割模板)
│   ├── deepseek_adapter.py              ★ DeepSeek适配器 (基于OpenAI兼容API)
│   └── claude_adapter.py                ★ Claude适配器 (复用收割模板)
├── model_config.yaml                    ★ 模型配置文件 (可热加载)
└── convertor.py                         ★ 消息转换

gateway层适配:
backend/app/ai/gateway/
├── interfaces.py                        修改: AIGatewayProtocol内部使用ILLM而非直接DeepSeek
└── adapters/
    ├── direct_api_adapter.py            修改: 委托给FactoryImpl.create_llm()
    ├── cached_gateway_adapter.py        不变: 缓存层不变，底层调用替换
    └── fallback_gateway_adapter.py      增强: 支持模型级降级链 (主模型→备用模型)
```

### 3.4 【具体修改文件】

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/app/ai/llm_adapter/base_adapter.py` | **新增** | ILLM抽象接口 + Message/Options/ToolInfo/TokenUsage数据模型 |
| `backend/app/ai/llm_adapter/model_config.py` | **新增** | Model/ProtocolConfig/Protocol/Frame领域模型 |
| `backend/app/ai/llm_adapter/adapter_factory.py` | **新增** | FactoryImpl + AdapterRegistry单例 |
| `backend/app/ai/llm_adapter/adapters/openai_adapter.py` | **新增** | OpenAI适配器（使用openai库） |
| `backend/app/ai/llm_adapter/adapters/deepseek_adapter.py` | **新增** | DeepSeek适配器（继承OpenAIAdapter，覆盖base_url） |
| `backend/app/ai/llm_adapter/adapters/claude_adapter.py` | **新增** | Claude适配器（使用anthropic库） |
| `backend/app/ai/llm_adapter/model_config.yaml` | **新增** | 声明支持的模型列表和连接信息 |
| `backend/app/ai/gateway/interfaces.py` | **修改** | AIGatewayProtocol使用ILLM接口 |
| `backend/app/ai/gateway/adapters/direct_api_adapter.py` | **重构** | 内部使用FactoryImpl创建LLM |
| `backend/app/ai/gateway/adapters/fallback_gateway_adapter.py` | **增强** | 支持模型链路降级 |
| `backend/app/ai/writing_assistant.py` | **修改** | 注入ILLM实例 |
| `backend/app/ai/rag_pipeline.py` | **修改** | 注入ILLM实例 |
| `backend/app/ai/__init__.py` | **修改** | 注册llm_adapter模块 |

### 3.5 【具体修改代码片段】

#### model_config.yaml — 配置即切换

```yaml
# backend/app/ai/llm_adapter/model_config.yaml
# Coze Loop风格: 模型配置驱动，零代码切换

models:
  # 主模型: DeepSeek (当前)
  - id: 1
    name: deepseek-main
    protocol: deepseek
    protocol_config:
      api_key: "${DEEPSEEK_API_KEY}"
      model: "deepseek-chat"
      base_url: "https://api.deepseek.com"
    ability:
      function_call: true
      max_context_tokens: 65536

  # 备用模型: OpenAI (降级用)
  - id: 2
    name: openai-fallback
    protocol: openai
    protocol_config:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4o-mini"
      base_url: "https://api.openai.com/v1"
    ability:
      function_call: true
      max_context_tokens: 128000

  # 本地模型: Ollama (离线/本地部署)
  - id: 3
    name: ollama-local
    protocol: ollama
    protocol_config:
      api_key: ""
      model: "qwen2.5:7b"
      base_url: "http://localhost:11434/v1"
    ability:
      function_call: false
      max_context_tokens: 32768

  # 实验模型: Claude
  - id: 4
    name: claude-experiment
    protocol: claude
    protocol_config:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-sonnet-4-20250514"
    ability:
      function_call: true
      max_context_tokens: 200000

# 场景 → 模型路由 (Coze Loop场景配额模式)
scenarios:
  bio_generation:
    model: deepseek-main
    fallback: openai-fallback
    quota:
      qpm: 60
      tpm: 100000
  
  recommendation:
    model: deepseek-main
    fallback: openai-fallback
  
  rag_query:
    model: deepseek-main
    fallback: ollama-local  # 离线时用本地模型
  
  ab_test_experiment:
    primary: deepseek-main
    secondary: claude-experiment
```

#### DirectAIGateway 重构

```python
# gateway/adapters/direct_api_adapter.py (重构后)
from ai.llm_adapter.adapter_factory import get_factory
from ai.llm_adapter.model_config import Model, ProtocolConfig, Protocol
from ai.llm_adapter.base_adapter import Message

class DirectAIGateway:
    """直接API网关 — 使用LLM适配器工厂"""
    
    def __init__(self, config: dict = None):
        self.factory = get_factory()
        self._default_model = None
        self._load_config(config or {})
    
    def _load_config(self, config: dict):
        """从YAML加载默认模型"""
        # 读取 model_config.yaml
        model_cfg = config.get("model", {})
        self._default_model = Model(
            protocol=Protocol(model_cfg.get("protocol", "deepseek")),
            protocol_config=ProtocolConfig(
                api_key=model_cfg.get("api_key", os.getenv("DEEPSEEK_API_KEY")),
                model=model_cfg.get("model", "deepseek-chat"),
                base_url=model_cfg.get("base_url", "https://api.deepseek.com"),
            ),
        )
    
    async def chat(self, messages: list[dict], **options) -> dict:
        """统一聊天接口 — 通过工厂创建LLM"""
        llm = await self.factory.create_llm(self._default_model)
        
        # 转换消息格式
        domain_messages = [
            Message(role=m["role"], content=m.get("content", ""))
            for m in messages
        ]
        
        result = await llm.generate(messages=domain_messages, **options)
        return {
            "content": result.content,
            "role": result.role,
            "usage": {
                "prompt_tokens": result.response_meta.usage.prompt_tokens,
                "completion_tokens": result.response_meta.usage.completion_tokens,
            } if result.response_meta and result.response_meta.usage else {},
        }
    
    async def chat_with_fallback(self, messages: list[dict], 
                                  scenario: str = "default", **options) -> dict:
        """带降级链的聊天 — 读取scenario配置"""
        scenarios = self._load_scenarios()
        sc_cfg = scenarios.get(scenario, {})
        
        models = [
            sc_cfg.get("model"),
            sc_cfg.get("fallback"),
        ]
        
        last_error = None
        for model_name in models:
            if not model_name:
                continue
            try:
                model_cfg = self._get_model_config(model_name)
                llm = await self.factory.create_llm(model_cfg)
                domain_messages = [
                    Message(role=m["role"], content=m.get("content", ""))
                    for m in messages
                ]
                return await llm.generate(messages=domain_messages, **options)
            except Exception as e:
                last_error = e
                continue
        
        raise last_error or Exception("all models failed")
```

### 3.6 【优先级】P0 — 立即执行

### 3.7 【人天估算】5人天

| 工作项 | 人天 | 角色 |
|--------|------|------|
| ILLM接口 + 数据模型定义（复用模板） | 0.5 | 后端 |
| 适配器工厂 + 注册器（复用模板） | 0.5 | 后端 |
| DeepSeek适配器实现 | 0.5 | 后端 |
| OpenAI适配器实现 | 0.5 | 后端 |
| Claude适配器实现 | 0.5 | 后端 |
| model_config.yaml + 场景路由 | 0.5 | 后端 |
| Gateway层重构（Direct/Cached/Fallback） | 1 | 后端 |
| writing_assistant.py / rag_pipeline.py 注入适配 | 0.5 | 后端 |
| 单元测试 + 集成测试 | 0.5 | 测试 |

---

## 4. P0#3: Trace可观测性 → 名片访客交互追踪

### 4.1 【目标产品】

**后端 + SQLite存储**

- 当前：无任何可观测性埋点，AI调用无日志追踪，访客浏览名片无记录
- 目标：为每个AI调用（自我介绍生成、RAG对话、推荐引擎）创建Span链，记录访客交互轨迹（谁看了名片、触发什么AI能力、耗时、Token消耗、是否满意）

### 4.2 【心智模型映射】

| 心智模型 | 映射方式 |
|----------|---------|
| **Observability-as-Debugging** | 将全链路追踪从"可选项"提升为"基础设施"——每条AI调用自动记录Span，支持按trace_id回溯"用户→AI→输出"全过程 |
| **Loop Flywheel** | 观测数据反哺飞轮：访客交互数据 → EDD评估引擎(P0#4) → Prompt优化(P0#1) → 模型效果提升 |

### 4.3 【代码集成路径】

```
Coze Loop Go源码 → Python模板 (_code_patterns_observability.md ~1,580行)
    ↓

backend/app/ai/observability/            (新增: 可观测性模块)
├── __init__.py
├── span.py                              ★ Span数据模型 (复用Coze Loop模式)
├── tracer.py                            ★ Tracer接口 + Span生命周期管理
├── trace_context.py                     ★ W3C Trace Context传播 (traceparent)
├── span_processor.py                    ★ Span处理链 (过滤/裁剪/清洗)
├── exporter.py                          ★ Span导出器 (SQLite/ClickHouse)
├── trajectory.py                        ★ Trajectory轨迹构建
├── middleware.py                        ★ FastAPI中间件 (自动创建Root Span)
└── query_service.py                     ★ Trace查询服务

访客交互追踪:
backend/app/ai/visitor_tracker/          (新增: 访客追踪模块)
├── __init__.py
├── visitor_span.py                      ★ 访客交互Span类型定义
└── tracking_service.py                  ★ 访客追踪服务

集成点:
├── backend/app/middleware/              FastAPI中间件 (每个请求自动追踪)
├── backend/app/ai/writing_assistant.py  注入Tracer
├── backend/app/ai/rag_pipeline.py       注入Tracer
├── backend/app/ai/recommendation.py     注入Tracer
├── backend/app/ai/gaia_evolution_brain.py 注入Tracer
└── backend/app/routers/                 访客追踪路由
```

### 4.4 【具体修改文件】

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/app/ai/observability/span.py` | **新增** | Span/SpanType/SpanStatus/Annotation/TagValue数据模型（复用Coze Loop） |
| `backend/app/ai/observability/tracer.py` | **新增** | `Tracer`类: start_span/end_span/add_event/inject_context |
| `backend/app/ai/observability/exporter.py` | **新增** | `SQLiteExporter`: Span批量写入SQLite；`ConsoleExporter`: 开发调试 |
| `backend/app/ai/observability/middleware.py` | **新增** | FastAPI中间件: 自动创建RootSpan, 注入traceparent到response header |
| `backend/app/ai/observability/span_processor.py` | **新增** | SpanProcessor链: 裁剪长字段、清洗敏感数据 |
| `backend/app/ai/observability/query_service.py` | **新增** | 按trace_id/span_type/时间范围查询Span |
| `backend/app/ai/visitor_tracker/tracking_service.py` | **新增** | 访客交互追踪: 谁看名片→触发什么AI→结果 |
| `backend/app/middleware/__init__.py` | **修改** | 注册TraceMiddleware |
| `backend/app/middleware/trace_middleware.py` | **新增** | FastAPI中间件（每个请求自动Span） |
| `backend/app/ai/writing_assistant.py` | **修改** | 注入Tracer, 在LLM调用前后创建Span |
| `backend/app/ai/rag_pipeline.py` | **修改** | 注入Tracer, RAG各步骤创建子Span |
| `backend/app/ai/recommendation.py` | **修改** | 注入Tracer |
| `backend/app/routers/analytics.py` | **新增** | 访客分析路由: `GET /api/analytics/visitors`, `GET /api/analytics/traces/{trace_id}` |
| `backend/requirements.txt` | **修改** | + opentelemetry-api (可选) |

### 4.5 【具体修改代码片段】

#### Span核心模型（复用Coze Loop模式）

```python
# observability/span.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid

class SpanType(str, Enum):
    ROOT = "root"
    LLM_CALL = "LLMCall"
    RAG_QUERY = "rag_query"
    VECTOR_SEARCH = "vector_search"
    RECOMMEND = "recommend"
    BIO_GENERATE = "bio_generate"
    VISITOR_VIEW = "visitor_view"
    VISITOR_CLICK = "visitor_click"
    VISITOR_FEEDBACK = "visitor_feedback"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    GATEWAY_CALL = "gateway_call"

class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"

@dataclass
class Span:
    """Core Span — 从Coze Loop LoopSpan提炼"""
    trace_id: str = ""
    span_id: str = ""
    parent_id: str = ""
    name: str = ""
    span_type: str = SpanType.ROOT
    
    start_time_us: int = 0      # 微秒
    end_time_us: int = 0
    duration_us: int = 0
    
    status: str = SpanStatus.OK
    status_code: int = 0        # 0=成功
    error_message: str = ""
    
    # 资源标识
    service: str = "ai-business-card"
    user_id: str = ""
    workspace_id: str = ""
    visitor_id: str = ""
    
    # I/O载荷
    input_data: str = ""        # JSON
    output_data: str = ""       # JSON
    
    # AI指标
    model_provider: str = ""
    model_name: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_first_token_ms: int = 0
    
    # 标签
    tags: dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def new(cls, name: str, span_type: str, trace_id: str = "", 
            parent_id: str = "") -> 'Span':
        now = int(time.time() * 1_000_000)
        return cls(
            span_id=uuid.uuid4().hex[:16],
            trace_id=trace_id or uuid.uuid4().hex[:32],
            parent_id=parent_id,
            name=name,
            span_type=span_type,
            start_time_us=now,
        )
    
    def end(self):
        self.end_time_us = int(time.time() * 1_000_000)
        self.duration_us = self.end_time_us - self.start_time_us
        return self
    
    def set_error(self, message: str):
        self.status = SpanStatus.ERROR
        self.status_code = -1
        self.error_message = message
        return self
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "span_type": self.span_type,
            "start_time_us": self.start_time_us,
            "duration_us": self.duration_us,
            "status": self.status,
            "status_code": self.status_code,
            "service": self.service,
            "user_id": self.user_id,
            "visitor_id": self.visitor_id,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "tags": self.tags,
            "error_message": self.error_message,
        }
```

#### Tracer — Span生命周期管理

```python
# observability/tracer.py
import contextvars
from typing import Optional
from .span import Span, SpanType
from .exporter import SpanExporter

_current_span: contextvars.ContextVar[Optional[Span]] = \
    contextvars.ContextVar('current_span', default=None)

class Tracer:
    """Span创建和管理 — 类似Coze Loop looptracer.Tracer"""
    
    def __init__(self, exporter: SpanExporter, service: str = "ai-business-card"):
        self.exporter = exporter
        self.service = service
    
    def start_span(self, name: str, span_type: str = SpanType.ROOT,
                   parent: Optional[Span] = None,
                   trace_id: str = "") -> Span:
        """创建一个新的Span，成为当前活跃Span"""
        parent_id = ""
        span_trace_id = trace_id
        
        if parent:
            parent_id = parent.span_id
            span_trace_id = parent.trace_id
        else:
            current = _current_span.get()
            if current:
                parent_id = current.span_id
                span_trace_id = current.trace_id
        
        span = Span.new(
            name=name, span_type=span_type,
            trace_id=span_trace_id, parent_id=parent_id,
        )
        span.service = self.service
        
        _current_span.set(span)
        return span
    
    def end_span(self, span: Span):
        """结束Span并导出"""
        span.end()
        self.exporter.export(span)
        
        # 恢复父Span
        _current_span.set(None)  # 实际需要维护栈
    
    def trace(self, name: str, span_type: str = SpanType.ROOT):
        """装饰器/上下文管理器"""
        class _TraceContext:
            def __init__(self, tracer):
                self.tracer = tracer
            async def __aenter__(self):
                self.span = self.tracer.start_span(name, span_type)
                return self.span
            async def __aexit__(self, *args):
                self.tracer.end_span(self.span)
        return _TraceContext(self)

# 全局Tracer单例
_tracer: Optional[Tracer] = None

def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        from .exporter import SQLiteExporter
        _tracer = Tracer(exporter=SQLiteExporter(), service="ai-business-card")
    return _tracer
```

#### FastAPI中间件 — 自动追踪每个请求

```python
# middleware/trace_middleware.py
from fastapi import Request, Response
from ai.observability.tracer import get_tracer
from ai.observability.span import SpanType
import time

async def trace_middleware(request: Request, call_next):
    """为每个HTTP请求创建根Span"""
    tracer = get_tracer()
    
    # 创建根Span
    span = tracer.start_span(
        name=f"{request.method} {request.url.path}",
        span_type=SpanType.ROOT,
        trace_id=request.headers.get("traceparent", ""),
    )
    span.user_id = request.headers.get("x-user-id", "")
    span.visitor_id = request.headers.get("x-visitor-id", "")
    
    try:
        response = await call_next(request)
        # 注入trace上下文到响应头
        response.headers["traceresponse"] = span.trace_id
        return response
    except Exception as e:
        span.set_error(str(e))
        raise
    finally:
        tracer.end_span(span)
```

#### 访客交互追踪 — 核心业务埋点

```python
# visitor_tracker/tracking_service.py
from ai.observability.tracer import get_tracer
from ai.observability.span import SpanType

class VisitorTrackingService:
    """名片访客交互追踪"""
    
    def __init__(self):
        self.tracer = get_tracer()
    
    async def track_view(self, visitor_id: str, card_owner_id: str, 
                         source: str = "direct"):
        """记录访客浏览名片"""
        span = self.tracer.start_span(
            name="visitor_view_card",
            span_type=SpanType.VISITOR_VIEW,
        )
        span.visitor_id = visitor_id
        span.tags = {
            "card_owner_id": card_owner_id,
            "source": source,
        }
        self.tracer.end_span(span)
    
    async def track_ai_call(self, visitor_id: str, card_owner_id: str,
                            ai_feature: str, input_text: str,
                            model_provider: str, model_name: str,
                            input_tokens: int, output_tokens: int,
                            duration_ms: int, success: bool):
        """记录AI功能调用"""
        span = self.tracer.start_span(
            name=f"ai_{ai_feature}",
            span_type=SpanType.LLM_CALL,
        )
        span.visitor_id = visitor_id
        span.model_provider = model_provider
        span.model_name = model_name
        span.input_tokens = input_tokens
        span.output_tokens = output_tokens
        span.input_data = input_text
        span.tags = {
            "card_owner_id": card_owner_id,
            "ai_feature": ai_feature,
            "duration_ms": str(duration_ms),
        }
        if not success:
            span.set_error("AI call failed")
        self.tracer.end_span(span)
```

### 4.6 【优先级】P0 — 立即执行

### 4.7 【人天估算】10人天

| 工作项 | 人天 | 角色 |
|--------|------|------|
| Span数据模型定义（复用Coze Loop模板） | 0.5 | 后端 |
| Tracer实现（Span生命周期管理） | 1 | 后端 |
| SQLiteExporter实现 | 1 | 后端 |
| SpanProcessor链（过滤/裁剪） | 0.5 | 后端 |
| FastAPI TraceMiddleware | 0.5 | 后端 |
| 访客追踪服务（VisitorTrackingService） | 1 | 后端 |
| writing_assistant.py + rag_pipeline.py 埋点 | 1 | 后端 |
| recommendation.py + gaia_brain.py 埋点 | 1 | 后端 |
| Trace查询路由 + 访客分析API | 1.5 | 后端 |
| Trajectory构建 | 0.5 | 后端 |
| 前端访客分析看板 | 1.5 | 前端 |

---

## 5. P0#4: EDD评估引擎 → AI功能效果量化

### 5.1 【目标产品】

**后端 + 管理控制台**

- 当前：无系统化评估，AI功能效果依赖主观感受
- 目标：引入Coze Loop EDD（Eval-Driven Development）模式：
  - 评估集管理（Evaluation Set）：为每个AI功能定义测试Case
  - 自动评估器：准确性、简洁性、合规性、风格匹配度
  - 实验管理：每次Prompt改动作为一个Experiment，自动运行评测并输出前后指标对比
  - 效果看板：可视化展示各AI功能的质量趋势

### 5.2 【心智模型映射】

| 心智模型 | 映射方式 |
|---------|---------|
| **EDD (Eval-Driven Development)** | 将评估从"可有可无"提升为"开发前先定标准"。每个AI功能必须先通过评估基线才能上线 |
| **Loop Flywheel** | 评估数据驱动优化：评估得分 → 定位短板（如自我介绍风格得分低）→ Prompt模板迭代(P0#1) → 再次评估验证 → 得分提升→上线 |

### 5.3 【代码集成路径】

```
Coze Loop modules/evaluation/ 模式:
  EvaluationSet → Evaluator → Experiment
    
backend/app/ai/evaluation/              (新增: 评估引擎)
├── __init__.py
├── eval_set.py                         ★ 评估集管理 (测试用例+期望输出)
├── evaluator.py                        ★ 评估器接口 + 内置评估器
├── evaluators/
│   ├── __init__.py
│   ├── accuracy_evaluator.py           ★ 准确性评估器 (LLM Judge)
│   ├── conciseness_evaluator.py        ★ 简洁性评估器 (长度+冗余度)
│   ├── compliance_evaluator.py         ★ 合规性评估器 (敏感词/隐私)
│   ├── style_match_evaluator.py        ★ 风格匹配度评估器
│   └── relevance_evaluator.py          ★ 相关性评估器
├── experiment.py                       ★ 实验管理 (A/B对比)
├── eval_report.py                      ★ 评估报告生成
└── experiment_runner.py                ★ 实验运行器 (异步执行)

集成点:
├── backend/app/ai/prompt_engine/         P0#1: 每次Prompt发布前自动评估
├── backend/app/ai/llm_adapter/           P0#2: 多模型A/B评估
├── backend/app/ai/observability/         P0#3: 评估结果写入Trace Tags
├── backend/app/routers/evaluation.py    新增: 评估管理路由
├── frontend/src/pages/evaluation/       新增: 评估看板页面
└── backend/app/cron/                    定时运行回归评估
```

### 5.4 【具体修改文件】

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/app/ai/evaluation/eval_set.py` | **新增** | EvaluationSet: id, name, feature, cases[TestCase: input, expected_output, criteria] |
| `backend/app/ai/evaluation/evaluator.py` | **新增** | `Evaluator` ABC: async evaluate(input, actual, expected) → EvalScore |
| `backend/app/ai/evaluation/evaluators/accuracy_evaluator.py` | **新增** | LLM Judge评估：用LLM评判AI输出质量 |
| `backend/app/ai/evaluation/evaluators/conciseness_evaluator.py` | **新增** | 文本长度/信息密度评分 |
| `backend/app/ai/evaluation/evaluators/compliance_evaluator.py` | **新增** | 敏感词/隐私信息检测 |
| `backend/app/ai/evaluation/evaluators/style_match_evaluator.py` | **新增** | 风格一致性评分 |
| `backend/app/ai/evaluation/experiment.py` | **新增** | Experiment: 基线版本vs实验版本，运行评估集，生成对比报告 |
| `backend/app/ai/evaluation/experiment_runner.py` | **新增** | 异步运行实验 |
| `backend/app/ai/evaluation/eval_report.py` | **新增** | Markdown报告生成 |
| `backend/app/routers/evaluation.py` | **新增** | `/api/evaluation/sets`, `/api/evaluation/experiments`, `/api/evaluation/reports` |
| `backend/app/ai/prompt_engine/prompt_hub_service.py` | **修改** | 发布前触发自动评估 |
| `backend/app/ai/__init__.py` | **修改** | 注册evaluation模块 |
| `frontend/src/pages/evaluation/` | **新增** | 评估看板: 评估集管理/实验对比/效果趋势 |

### 5.5 【具体修改代码片段】

#### 评估集数据模型

```python
# evaluation/eval_set.py
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from datetime import datetime

@dataclass
class TestCase:
    """单个测试用例"""
    id: str = ""
    name: str = ""
    input: str = ""              # 输入（Prompt变量）
    expected_output: str = ""    # 期望输出
    criteria: list[str] = field(default_factory=list)  # 评估标准
    tags: list[str] = field(default_factory=list)

@dataclass
class EvaluationSet:
    """评估集 — 类似Coze Loop的EvaluationSet"""
    id: str = ""
    name: str = ""
    description: str = ""
    feature: str = ""            # 目标AI功能: "bio_generation", "rag", "recommendation"
    cases: list[TestCase] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

@dataclass
class EvalScore:
    """单项评估得分"""
    evaluator_name: str = ""
    score: float = 0.0           # 0.0 ~ 1.0
    detail: str = ""
    passed: bool = False

@dataclass
class EvalResult:
    """单Case评估结果"""
    case_id: str = ""
    actual_output: str = ""
    scores: list[EvalScore] = field(default_factory=list)
    
    @property
    def overall_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(s.score for s in self.scores) / len(self.scores)
    
    @property
    def passed(self) -> bool:
        return self.overall_score >= 0.7  # 70% threshold
```

#### 评估器接口 + AI Judge评估器

```python
# evaluation/evaluator.py
import abc

class Evaluator(abc.ABC):
    """评估器接口 — 类似Coze Loop Evaluator"""
    
    @abc.abstractmethod
    async def evaluate(self, input_text: str, actual_output: str,
                       expected_output: str = "", criteria: list[str] = None) -> EvalScore:
        ...

# evaluation/evaluators/accuracy_evaluator.py
class LLMJudgeEvaluator(Evaluator):
    """LLM Judge评估器：用LLM评判AI输出质量"""
    
    def __init__(self, llm_adapter=None):
        from ai.llm_adapter.adapter_factory import get_factory
        self.factory = get_factory()
        self._llm = None
    
    async def _get_judge_llm(self):
        if self._llm is None:
            self._llm = await self.factory.create_llm_by_config(
                protocol=Protocol.DEEPSEEK,
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                model_name="deepseek-chat",
            )
        return self._llm
    
    async def evaluate(self, input_text, actual_output,
                       expected_output="", criteria=None):
        llm = await self._get_judge_llm()
        
        prompt = f"""你是一个AI输出质量评估专家。请对以下AI生成结果进行评分。

【任务】: {input_text}
【AI输出】: {actual_output}
【期望输出】: {expected_output or "无特定期望"}
【评估标准】: {', '.join(criteria) if criteria else '准确性、相关性、完整性'}
【评分规则】: 0-10分，10分为完美。

请分析后给出评分和简短理由。
格式: 分数: X/10
理由: ..."""
        
        result = await llm.generate(
            messages=[Message(role="user", content=prompt)],
            temperature=0.1,
        )
        
        score_text = result.content
        # 提取分数
        import re
        match = re.search(r'分数:\s*(\d+(?:\.\d+)?)\s*/\s*10', score_text)
        score = float(match.group(1)) / 10.0 if match else 0.5
        passed = score >= 0.7
        
        return EvalScore(
            evaluator_name="llm_judge",
            score=score,
            detail=score_text,
            passed=passed,
        )
```

#### 实验对比报告

```python
# evaluation/experiment.py
@dataclass
class Experiment:
    """实验 — 评估基线vs实验版本"""
    id: str = ""
    name: str = ""
    description: str = ""
    feature: str = ""
    
    # 基线配置
    baseline_config: dict = field(default_factory=dict)
    # 实验配置 (如不同的Prompt版本/不同的LLM模型)
    experiment_config: dict = field(default_factory=dict)
    
    eval_set_id: str = ""
    evaluator_names: list[str] = field(default_factory=list)
    
    status: str = "created"  # created/running/completed/failed
    result: Optional['ExperimentResult'] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ExperimentResult:
    """实验结果 — 基线vs实验对比"""
    baseline_results: list[EvalResult] = field(default_factory=list)
    experiment_results: list[EvalResult] = field(default_factory=list)
    
    @property
    def baseline_avg_score(self) -> float:
        scores = [r.overall_score for r in self.baseline_results]
        return sum(scores) / len(scores) if scores else 0.0
    
    @property
    def experiment_avg_score(self) -> float:
        scores = [r.overall_score for r in self.experiment_results]
        return sum(scores) / len(scores) if scores else 0.0
    
    @property
    def improvement(self) -> float:
        """实验相比基线的提升"""
        return self.experiment_avg_score - self.baseline_avg_score
    
    def to_markdown(self) -> str:
        return f"""## 实验报告: {self.name}

### 基线得分: {self.baseline_avg_score:.2f}
### 实验得分: {self.experiment_avg_score:.2f}
### 提升: {self.improvement:+.2f}

| Case | 基线 | 实验 | 变化 |
|------|------|------|------|
{chr(10).join(
    f"| {b.case_id} | {b.overall_score:.2f} | {e.overall_score:.2f} | {e.overall_score - b.overall_score:+.2f} |"
    for b, e in zip(self.baseline_results, self.experiment_results)
)}
"""
```

### 5.6 【优先级】P0 — 立即执行

### 5.7 【人天估算】6人天

| 工作项 | 人天 | 角色 |
|--------|------|------|
| 评估集数据模型 + 仓储 | 1 | 后端 |
| 评估器接口 + 内置评估器x5 | 1.5 | 后端 |
| LLM Judge评估器 | 1 | 后端 |
| 实验管理 + 运行器 | 1 | 后端 |
| 评估路由 + Prompt发布前自动评估集成 | 0.5 | 后端 |
| 评估看板前端页面 | 1 | 前端 |

---

## 6. P1补充注入

### 6.1 P1#1: MQ工厂模式 → 异步名片生成/批量导入

**心智模型**: Loop Flywheel — 事件驱动加速飞轮

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端异步任务（批量生成名片AI自我介绍、批量导入） |
| **Coze Loop模式** | P4 MQ工厂模式（IFactory/IProducer/IConsumer） → RocketMQ抽象层 |
| **集成路径** | `backend/app/ai/mq/` 新增MQ抽象层；当前先使用SQLite+asyncio队列模拟，后续替换为RabbitMQ/Pulsar |
| **具体修改文件** | 新增: `backend/app/ai/mq/interfaces.py`, `backend/app/ai/mq/local_queue.py`; 修改: `writing_assistant.py` 批量生成走队列 |
| **人天** | 3人天 |

### 6.2 P1#2: ID生成器 → 分布式名片唯一标识

**心智模型**: —

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端ID生成（名片ID、访客追踪ID、Span ID） |
| **Coze Loop模式** | P6 ID生成器（Redis + 雪花算法风格） |
| **集成路径** | `backend/app/infra/id_generator.py` 新增Snowflake风格ID生成器 |
| **具体修改文件** | 新增: `backend/app/infra/id_generator.py` (雪花算法, 时间戳+机器ID+序列号) |
| **人天** | 1人天 |

### 6.3 P1#3: 错误码体系 → 统一错误处理

**心智模型**: —

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端API统一错误响应格式 |
| **Coze Loop模式** | P16 错误码体系（`pkg/errorx` + 各模块 `pkg/errno/`） |
| **集成路径** | `backend/app/errors/` 新增分层错误码: 系统级/业务级/外部级 |
| **具体修改文件** | 新增: `backend/app/errors/codes.py`, `backend/app/errors/handler.py`; 修改: 各路由异常处理 |
| **人天** | 2人天 |

### 6.4 P1#4: 配置热加载 → Prompt模板动态生效

**心智模型**: Prompt-as-Code

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端配置管理（Prompt模板、模型配置、评估阈值） |
| **Coze Loop模式** | P15 配置热加载（Viper多源配置） |
| **集成路径** | `backend/app/config/` 新增热加载配置管理器，支持YAML+环境变量+DB三源 |
| **具体修改文件** | 新增: `backend/app/config/hot_reload.py`; 修改: `prompt_engine/` 从热加载配置读取模板路径 |
| **人天** | 2人天 |

---

## 7. P2补充注入

### 7.1 P2#1: 分布式锁 → 并发名片编辑防冲突

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端并发控制（防止多人同时编辑同一名片导致覆盖） |
| **Coze Loop模式** | P5 分布式锁（Redis + 自动续期） |
| **集成路径** | `backend/app/infra/distributed_lock.py` 新增Redis分布式锁（使用aioredis） |
| **人天** | 1人天 |

### 7.2 P2#2: 限流器 → API频率控制

| 维度 | 内容 |
|------|------|
| **目标产品** | 后端API限流（AI名片生成API、访客追踪API、推荐API） |
| **Coze Loop模式** | P7 限流器（Redis滑动窗口） |
| **集成路径** | `backend/app/middleware/rate_limiter.py` 新增FastAPI限流中间件 |
| **人天** | 1人天 |

---

## 8. 注入总路线图（甘特图）

```
          Week 1          Week 2          Week 3          Week 4
P0#1     ████████░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░
Prompt   (8天)

P0#2     █████░░░░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░
Adapter  (5天)

P0#3     ░░░░░░░░░░░░  ██████████░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░
Trace    (10天)

P0#4     ░░░░░░░░░░░░  ░░░░██████░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░
EDD      (6天)

P1#1 MQ  ░░░░░░░░░░░░  ░░░░░░░░░░░░  ███░░░░░░░░░  ░░░░░░░░░░░░
                                  (3天)

P1#2 ID  ░░░░░░░░░░░░  ░░░░░░░░░░░░  █░░░░░░░░░░░  ░░░░░░░░░░░░
                                  (1天)

P1#3 Err ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░██░░░░░░░░  ░░░░░░░░░░░░
                                  (2天)

P1#4 Cfg ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░░░██░░░░░░  ░░░░░░░░░░░░
                                  (2天)

P2#1 Lck ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░  █░░░░░░░░░░░
                                                  (1天)

P2#2 Lim ░░░░░░░░░░░░  ░░░░░░░░░░░░  ░░░░░░░░░░░░  █░░░░░░░░░░░
                                                  (1天)
```

**总人天估算**: P0(29天) + P1(8天) + P2(2天) = **39人天**

**建议并行策略**:
- Week 1: P0#1 (Prompt) + P0#2 (Adapter) 并行 — 两者独立
- Week 2: P0#3 (Trace) + P0#4 (EDD) 并行 — 评估引擎依赖适配器但不冲突
- Week 3: P1补充注入 — 基础设施完善
- Week 4: P2收尾 + 集成测试

---

## 9. 心智模型映射矩阵

| 心智模型 | 注入P0#1 | 注入P0#2 | 注入P0#3 | 注入P0#4 | 注入P1/P2 |
|----------|:--------:|:--------:|:--------:|:--------:|:---------:|
| **Loop Flywheel** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Prompt-as-Code** | ⭐⭐⭐⭐⭐ | — | — | ⭐⭐ | ⭐ (P1#4) |
| **EDD** | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | — |
| **Observability-as-Debugging** | — | — | ⭐⭐⭐⭐⭐ | ⭐⭐ | — |
| **Pluggable Model Integration** | — | ⭐⭐⭐⭐⭐ | — | ⭐⭐ | — |

---

## 附录A. Coze Loop 模式 → 注入文件对照表

| Coze Loop模式编号 | 模式名 | 注入编号 | 目标文件 |
|-------------------|--------|---------|---------|
| P2 | 多LLM适配器 | **P0#2** | `backend/app/ai/llm_adapter/*` |
| P3 | 可观测性追踪管道 | **P0#3** | `backend/app/ai/observability/*` |
| P11 | 评估引擎 | **P0#4** | `backend/app/ai/evaluation/*` |
| P12 | Prompt版本管理 | **P0#1** | `backend/app/ai/prompt_engine/*` |
| P4 | MQ工厂模式 | P1#1 | `backend/app/ai/mq/*` |
| P6 | ID生成器 | P1#2 | `backend/app/infra/id_generator.py` |
| P15 | 配置热加载 | P1#4 | `backend/app/config/hot_reload.py` |
| P16 | 错误码体系 | P1#3 | `backend/app/errors/*` |
| P5 | 分布式锁 | P2#1 | `backend/app/infra/distributed_lock.py` |
| P7 | 限流器 | P2#2 | `backend/app/middleware/rate_limiter.py` |

---

## 附录B. 依赖关系图

```
P0#2 (多LLM适配器) ────┬─── P0#1 (Prompt-as-Code)
                       │         └── 依赖: ILLM接口
                       ├─── P0#3 (Trace可观测性)
                       │         └── 依赖: Tracer
                       └─── P0#4 (EDD评估引擎)
                                 └── 依赖: ILLM + Trace

P0#1 ── P1#4 (配置热加载)
  └── 热加载Prompt模板

P0#3 ── P1#1 (MQ工厂)
  └── 异步Span导出

P0#4 ── P0#1 (Prompt评估)
  └── 发布前自动跑评估集
```

---

> **本方案由 讹兽_HRBP (Bai Ze Legion, P8) 基于Coze Loop全部收割成果综合输出**  
> **收割源文件**: `_harvest_report.md`(22模式) + `_mental_models.md`(5心智模型) + `_code_patterns_llm_adapter.md`(1,440行) + `_code_patterns_observability.md`(1,580行) + `_ai_engine_analysis.md`(10注入点) + `ARCHITECTURE.md`  
> **注入时间**: 2026-07-14
