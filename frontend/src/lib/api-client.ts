/**
 * API 客户端 - 统一导出入口
 *
 * 本文件仅为向后兼容的重导出层，所有功能实现在 @/api/client。
 * 新代码请直接使用 import { api } from '@/api/client'。
 *
 * 导出内容：
 *   - api          — 完整的 API 客户端实例（get/post/put/delete/request/saveToken/loadToken/removeToken）
 *   - ApiResponse  — 统一响应类型
 */
export { api } from '../api/client';
export type { ApiResponse } from '../api/client';
