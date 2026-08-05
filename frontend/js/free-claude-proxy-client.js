/**
 * free-claude-proxy-client.js — AI名片前端调用 free-claude-code-proxy 的客户端工具
 * ===========================================================================
 * 
 * 通过本地的 free-claude-code-proxy SSE 微服务调用 "Claude Code" 能力。
 * 无需 Anthropic API Key，由 proxy 完成 DeepSeek 上游 ↔ Anthropic 格式转换。
 *
 * 用法:
 *   import { freeClaudeProxy } from './free-claude-proxy-client.js';
 *
 *   // 非流式调用
 *   const response = await freeClaudeProxy.chat({
 *     messages: [{ role: 'user', content: 'Hello' }],
 *     max_tokens: 4096,
 *   });
 *
 *   // 流式调用 (SSE)
 *   const stream = await freeClaudeProxy.streamChat({
 *     messages: [{ role: 'user', content: '写一首诗' }],
 *   });
 *   for await (const chunk of stream) {
 *     console.log(chunk);
 *   }
 *
 * 配置: 在环境变量中设置 FREE_CLAUDE_PROXY_URL (默认 http://localhost:5080)
 */

const DEFAULT_PROXY_URL = 'http://localhost:5080';

/**
 * 获取 proxy 服务地址
 * 优先级: 构造函数参数 > 全局变量 > 默认值
 */
function getProxyUrl() {
  if (typeof window !== 'undefined' && window.__FREE_CLAUDE_PROXY_URL__) {
    return window.__FREE_CLAUDE_PROXY_URL__;
  }
  return DEFAULT_PROXY_URL;
}

/**
 * 获取 API Key
 */
function getApiKey() {
  if (typeof window !== 'undefined' && window.__PROXY_API_KEY__) {
    return window.__PROXY_API_KEY__;
  }
  return 'free-claude-key';
}

/**
 * 通过 AI名片后端网关调用 proxy（推荐方式）
 * 走后端 /api/proxy/claude/chat 端点，避免 CORS 问题
 */
async function chatViaGateway(messages, options = {}) {
  const {
    model = 'claude-sonnet-4-20250514',
    maxTokens = 4096,
    temperature = 0.7,
    stream = false,
    system = '',
  } = options;

  const API_BASE = typeof window !== 'undefined'
    ? (window.__API_BASE_URL__ || '')
    : 'http://localhost:8200';

  const payload = {
    model,
    max_tokens: maxTokens,
    messages: messages.map(m => ({ role: m.role, content: m.content })),
    stream,
    temperature,
  };
  if (system) {
    payload.system = [{ type: 'text', text: system }];
  }

  const url = `${API_BASE}/api/proxy/claude/chat`;

  if (stream) {
    // SSE 流式请求
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Proxy gateway error: ${response.status}`);
    }
    return response.body.getReader();
  }

  // 非流式
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Proxy gateway error ${response.status}: ${errText}`);
  }
  return response.json();
}

/**
 * 直接调用 free-claude-code-proxy（用于开发/调试）
 */
async function chatDirect(messages, options = {}) {
  const {
    model = 'claude-sonnet-4-20250514',
    maxTokens = 4096,
    temperature = 0.7,
    stream = false,
    system = '',
  } = options;

  const proxyUrl = getProxyUrl();
  const apiKey = getApiKey();

  const payload = {
    model,
    max_tokens: maxTokens,
    messages: messages.map(m => ({ role: m.role, content: m.content })),
    stream,
    temperature,
  };
  if (system) {
    payload.system = [{ type: 'text', text: system }];
  }

  const url = `${proxyUrl}/v1/messages`;

  if (stream) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Proxy direct error: ${response.status}`);
    }
    return response.body.getReader();
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Proxy direct error ${response.status}: ${errText}`);
  }
  return response.json();
}

/**
 * 健康检查
 */
async function healthCheck() {
  const proxyUrl = getProxyUrl();
  try {
    const response = await fetch(`${proxyUrl}/health`, { signal: AbortSignal.timeout(5000) });
    if (response.ok) {
      const data = await response.json();
      return { healthy: true, data };
    }
    return { healthy: false, status: response.status };
  } catch (err) {
    return { healthy: false, error: err.message };
  }
}

/**
 * 通过 AI名片后端网关进行健康检查
 */
async function healthCheckViaGateway() {
  const API_BASE = typeof window !== 'undefined'
    ? (window.__API_BASE_URL__ || '')
    : 'http://localhost:8200';
  try {
    const response = await fetch(`${API_BASE}/api/v1/providers/free-claude/health`, {
      signal: AbortSignal.timeout(5000),
    });
    return await response.json();
  } catch (err) {
    return { success: false, status: 'unreachable', error: err.message };
  }
}

/**
 * 解析 SSE 流式响应，逐块返回文本内容
 */
async function* parseSSEStream(reader) {
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'content_block_delta' && data.delta?.type === 'text_delta') {
            yield data.delta.text;
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}

// ======================================================================
// 导出统一接口
// ======================================================================

export const freeClaudeProxy = {
  chat: chatViaGateway,
  chatDirect,
  streamChat: (messages, options = {}) => {
    const readerPromise = chatViaGateway(messages, { ...options, stream: true });
    return (async function* () {
      const reader = await readerPromise;
      yield* parseSSEStream(reader);
    })();
  },
  streamChatDirect: (messages, options = {}) => {
    const readerPromise = chatDirect(messages, { ...options, stream: true });
    return (async function* () {
      const reader = await readerPromise;
      yield* parseSSEStream(reader);
    })();
  },
  healthCheck,
  healthCheckViaGateway,
};
