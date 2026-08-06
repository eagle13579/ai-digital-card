"""
customer_importer — Windows RPA 客户数据批量导入管道

通过 Windows RPA 微服务 (:8667) 模拟人工操作，
将 Excel/CSV 客户数据批量导入目标 ERP/CRM 系统。
支持中断恢复（Checkpoint）、进度追踪（JSONL）、多系统适配。
"""

from .import_workflow import ERPWebImport, CRMWebImport, ImportWorkflow
from .rpa_client import RpaClient
from .data_reader import read_customers_from_csv, read_customers_from_excel, read_customers
from .checkpoint import CheckpointManager

__all__ = [
    "ImportWorkflow",
    "ERPWebImport",
    "CRMWebImport",
    "RpaClient",
    "read_customers_from_csv",
    "read_customers_from_excel",
    "read_customers",
    "CheckpointManager",
]
