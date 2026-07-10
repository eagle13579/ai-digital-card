"""动态字段更新工具 - 来自询赋A05原子吸收"""
from typing import Dict, Any, List, Optional
import sqlite3


def dynamic_update(
    db: Any,
    table: str,
    entity_id: str,
    data: Dict[str, Any],
    id_column: str = "id",
    updated_at_column: str = "updated_at",
    extra_where: Optional[str] = None,
    extra_params: Optional[List] = None,
) -> bool:
    """
    动态构建UPDATE语句，只更新有值的字段
    
    参数:
        db: 数据库连接对象 (支持 .execute() 方法)
        table: 表名
        entity_id: 实体ID值
        data: 要更新的字段字典 {column: value}
        id_column: ID列名，默认 'id'
        updated_at_column: 更新时间列名
        extra_where: 额外的WHERE条件（如 'AND user_id = ?'）
        extra_params: 额外参数
    
    返回:
        True 表示有字段被更新，False 表示无字段可更新
    """
    # 只保留非None的字段
    fields = [k for k, v in data.items() if v is not None]
    
    if not fields:
        return False
    
    set_clause = ", ".join(f"{f} = ?" for f in fields)
    values = [data[f] for f in fields]
    values.append(entity_id)
    
    where = f"{id_column} = ?"
    if extra_where:
        where += f" AND {extra_where}"
        if extra_params:
            values.extend(extra_params)
    
    query = f"UPDATE {table} SET {set_clause}, {updated_at_column} = unixepoch() WHERE {where}"
    
    db.execute(query, values)
    return True


def build_patch_fields(data: Dict[str, Any], allowed_fields: List[str]) -> Dict[str, Any]:
    """
    从请求体中提取允许更新的字段
    
    用法: build_patch_fields(request_body, ['nickname', 'company', 'position'])
    """
    return {k: v for k, v in data.items() if k in allowed_fields and v is not None}


# 异步版本 (用于 aiosqlite)
async def dynamic_update_async(
    db: Any,
    table: str,
    entity_id: str,
    data: Dict[str, Any],
    id_column: str = "id",
    updated_at_column: str = "updated_at",
) -> bool:
    """异步版动态字段更新"""
    fields = [k for k, v in data.items() if v is not None]
    if not fields:
        return False
    set_clause = ", ".join(f"{f} = ?" for f in fields)
    values = [data[f] for f in fields]
    values.append(entity_id)
    query = f"UPDATE {table} SET {set_clause}, {updated_at_column} = unixepoch() WHERE {id_column} = ?"
    await db.execute(query, values)
    return True
