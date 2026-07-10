"""CRM 模块 — 内置客户关系管理系统。

本模块提供完整的自建CRM功能，复用现有 User/Brochure/Tag/Match/Trust/Message/VisitorLog 模型。
联系人可从名片交换记录自动创建，支持销售管道(Pipeline)、活动时间线和笔记。
另含报表分析模块 (CrmAnalyticsService) 提供 Pipeline 分析、转化率和趋势数据。
工作流自动化引擎 (WorkflowEngine) 支持事件触发的规则+动作自动化。

数据流:
    名片交换 → MatchRecord → CrmContact(自动)
     访问记录 → VisitorLog → CrmActivity(时间线)
       消息 → Message → CrmActivity(时间线)
     手动创建 → CrmContact + CrmDeal + CrmNote
     分析模块 → 纯SQL聚合，支持 Dashboard 汇总
     工作流引擎 → 事件触发 → 规则匹配 → 动作执行
"""

from app.crm.crm_models import (
    CrmContact,
    CrmDeal,
    CrmPipelineStage,
    CrmActivity,
    CrmNote,
    CrmWorkflowRule,
    CrmWorkflowLog,
)
from app.crm.email_campaign import EmailCampaign
from app.crm.customer_journey import CustomerJourneyStage
from app.crm.crm_service import CrmService
from app.crm.crm_analytics import CrmAnalyticsService
from app.crm.workflow_engine import WorkflowEngine, test_rule_execution, PRESET_RULES
from app.crm.crm_rbac import (
    CrmRole,
    CRM_PERMISSION_MATRIX,
    CRM_ROLE_DISPLAY,
    CRM_PERMISSION_LABELS,
    get_user_crm_role,
    get_user_crm_permissions,
    has_crm_permission,
    require_permission,
    assign_crm_role,
    ensure_crm_role_definition,
)
from app.crm.crm_router import router

__all__ = [
    "CrmContact",
    "CrmDeal",
    "CrmPipelineStage",
    "CrmActivity",
    "CrmNote",
    "CrmWorkflowRule",
    "CrmWorkflowLog",
    "EmailCampaign",
    "CustomerJourneyStage",
    "CrmService",
    "CrmAnalyticsService",
    "WorkflowEngine",
    "test_rule_execution",
    "PRESET_RULES",
    "CrmRole",
    "CRM_PERMISSION_MATRIX",
    "CRM_ROLE_DISPLAY",
    "CRM_PERMISSION_LABELS",
    "get_user_crm_role",
    "get_user_crm_permissions",
    "has_crm_permission",
    "require_permission",
    "assign_crm_role",
    "ensure_crm_role_definition",
    "router",
]
