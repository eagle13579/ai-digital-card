# API 路由映射问题记录

> 创建时间: 根据任务发现自动记录
> 相关文件: `api.js`, `mockService.js`

## 问题: AI 模块路由不匹配

### 后端实际路由（据任务描述）
- `POST /api/ai/assist/write`
- `POST /api/ai/assist/generate`（推测，遵循 assist 前缀模式）

### 前端当前路由（`api.js` 第143-150行）
```javascript
const aiApi = {
  write(data) {
    return post('/api/ai/write', data)       // ← 应为 /api/ai/assist/write
  },
  generate(data) {
    return post('/api/ai/generate', data)     // ← 应为 /api/ai/assist/generate
  },
}
```

### 调用方（`mockService.js`）

| mockService.js 方法 | 行号 | 调用对象 | 传递参数 |
|---------------------|------|----------|----------|
| `aiChat(question)`  | 244  | `aiApi.write()` | `{ prompt: question }` |
| `aiGenerate(type, input)` | 257 | `aiApi.generate()` | `{ type, input }` |

### 修正方案（待执行）

将 `api.js` 中的路由路径修改：

| 当前路径 | 修正后路径 |
|----------|------------|
| `/api/ai/write` | `/api/ai/assist/write` |
| `/api/ai/generate` | `/api/ai/assist/generate` |

### 其他模块路由（已验证，无需修改）

| 模块 | 路径前缀 | 状态 |
|------|----------|------|
| miniappApi | `/api/v1/miniapp/*` | ✅ 正确 |
| authApi | `/api/auth/*` | ✅ 正确 |
| userApi | `/api/users/*` | ✅ 正确 |
| brochureApi | `/api/brochures/*` | ✅ 正确 |
| tagApi | `/api/tags/*` | ✅ 正确 |
| matchApi | `/api/match/*` | ✅ 正确 |
| trustApi | `/api/trust/*` | ✅ 正确 |
| visitorApi | `/api/visitors/*` | ✅ 正确 |
