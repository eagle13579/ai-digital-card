# F03 — BFS 社交图谱路径查找

## 心智模型（Mental Model）

在信任网络中，任意两个用户之间可能存在一条"好友链"。询赋使用 **BFS（广度优先搜索）** 在已批准的好友关系图中查找最短路径，实现类似 LinkedIn "X度人脉" 的能力。

核心约束：**最大搜索深度为 3 度人脉**（4层BFS队列），既保证搜索结果有用，又控制计算开销。

```
用户A → [好友列表] → [好友的好友] → [好友的好友的好友] → 目标用户B
  1度         2度              3度
```

## Architecture Decision Records

### ADR-007: 使用 BFS 而非 Dijkstra/Floyd

| 项目 | 决策 |
|------|------|
| 上下文 | 图是无权图（所有连接权重相等），只需最短路径 |
| 决策 | 使用标准 BFS 算法，队列中存储 (节点ID, 路径数组) |
| 理由 | BFS 在无权图上天然找到最短路径；实现简单；SQLite 每次动态查询邻居 |
| 后果 | 每次调用都查询数据库，未做缓存；频繁调用性能可能下降 |

### ADR-008: 最大搜索深度限制为 3 度人脉（4层BFS）

| 项目 | 决策 |
|------|------|
| 上下文 | 商务社交中超过3度的信任价值递减严重 |
| 决策 | BFS队列最大深度为4（path.length > 4 时 skip） |
| 理由 | 3度人脉是商务社交的黄金分割点；控制查询量级 |
| 后果 | 返回 `{distance: -1}` 表示未找到，前端显示"暂无触达路径" |

### ADR-009: 每次 BFS 查询数据库加载邻居

| 项目 | 决策 |
|------|------|
| 上下文 | 图数据存储在关系型数据库 SQLite 中 |
| 决策 | 每层 BFS 执行 `SELECT contact_id FROM connections WHERE user_id = ? AND status = 'approved'` |
| 理由 | 不需要图数据库；SQLite 在千级节点下性能可接受 |
| 后果 | 大量并发查询可能成为瓶颈，可考虑 Redis 缓存图谱 |

## 核心代码提取

```typescript
static findPath(userId: string, targetUserId: string): any {
  if (userId === targetUserId) return { distance: 0, path: [userId] };

  const visited = new Set<string>();
  const queue: { id: string; path: string[] }[] = [{ id: userId, path: [userId] }];
  visited.add(userId);

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (current.path.length > 4) continue; // 最大3度人脉

    const connections = db.prepare(
      'SELECT contact_id FROM connections WHERE user_id = ? AND status = ?'
    ).all(current.id, 'approved') as { contact_id: string }[];

    for (const conn of connections) {
      if (conn.contact_id === targetUserId) {
        return { distance: current.path.length, path: [...current.path, targetUserId] };
      }
      if (!visited.has(conn.contact_id)) {
        visited.add(conn.contact_id);
        queue.push({ id: conn.contact_id, path: [...current.path, conn.contact_id] });
      }
    }
  }

  return { distance: -1, path: [], message: '未找到可触达路径' };
}
```

## 建联系统全流程

```
发起方请求建联
  → POST /api/connections/request
    → 校验不能与自己建联
    → 检查是否已存在关系（已批准/已发送）
    → INSERT 正向记录 (userId→contactId, status='pending')
    → INSERT 反向记录 (contactId→userId, status='pending')
    → 返回 { id, status: 'pending' }

接收方审核
  → PUT /api/connections/:id/review { approved: true/false }
    → 校验请求存在且属于当前用户
    → UPDATE 正向记录 status = 'approved'/'rejected'
    → UPDATE 反向记录 status = 'approved'/'rejected'
    → 返回 { status }
```

## API 路由清单

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/connections/request | 发起建联请求 |
| PUT | /api/connections/:id/review | 审核建联请求 |
| GET | /api/connections | 我的好友列表 |
| GET | /api/connections/pending | 待审核请求列表 |
| GET | /api/connections/path/:targetUserId | BFS触达路径 |

## 数据库 Schema 映射

```sql
CREATE TABLE connections (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  contact_id TEXT REFERENCES users(id),
  source TEXT DEFAULT 'platform',
  status TEXT CHECK(status IN ('pending', 'approved', 'rejected')),
  strength REAL DEFAULT 0,        -- 关系强度，可扩展
  created_at DEFAULT unixepoch(),
  updated_at DEFAULT unixepoch()
);
```

## 吸收建议

| 询赋实现 | AI数智名片适配方案 |
|----------|-------------------|
| SQL + BFS | 可改用 Redis Set 或 Neo4j 图数据库，性能更好 |
| 3度人脉限制 | 可按需调整为 2度/4度 + 前端展示"N度人脉"标签 |
| 双向记录 | 必须保留（见 F05） |
| 建联请求+审核 | 微信小程序内使用订阅消息通知对方 |

## 可复用程度

- **BFS算法逻辑**: 100% 可复用（语言无关）
- **建联请求/审核**: 90% 可复用
- **图查询性能**: 在 <1万用户规模下 SQLite 足够

## 性能评估

| 用户规模 | BFS查询次数 | 预计耗时 |
|---------|------------|---------|
| 100 | <100 | <5ms |
| 1,000 | <1,000 | <20ms |
| 10,000 | <10,000 | <200ms |
| 100,000 | 建议迁移至图数据库 | >2s |
