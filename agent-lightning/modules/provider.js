/**
 * OpenClaw Provider Abstraction
 * Inspired by open-claude-cowork's multi-provider pattern.
 * 
 * Pluggable AI provider interface supporting:
 * - Multiple models (Claude, GPT, Gemini, local)
 * - Streaming responses
 * - Session management
 * - Abort support
 * 
 * Usage:
 *   import { ProviderRegistry, OpenRouterProvider } from './provider.js';
 *   const registry = new ProviderRegistry();
 *   registry.register('openrouter', new OpenRouterProvider({ apiKey: '...' }));
 *   const provider = registry.get('openrouter');
 *   for await (const chunk of provider.stream({ model: 'gpt-4o', messages: [...] })) {
 *     process.stdout.write(chunk.content);
 *   }
 */

import { EventEmitter } from 'events';

/**
 * Base provider interface
 */
export class BaseProvider extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = config;
    this.sessions = new Map();
    this.activeRequests = new Map();
  }

  get name() {
    throw new Error('Provider must implement name getter');
  }

  get models() {
    return [];
  }

  async initialize() {}

  /**
   * Stream a completion
   * @param {Object} params
   * @param {string} params.model - Model identifier
   * @param {Array} params.messages - Message array
   * @param {Object} [params.tools] - Tool definitions
   * @param {Object} [params.options] - Additional options
   * @yields {Object} Stream chunks
   */
  async *stream(params) {
    throw new Error('Provider must implement stream method');
  }

  /**
   * Non-streaming completion
   */
  async complete(params) {
    const chunks = [];
    for await (const chunk of this.stream(params)) {
      chunks.push(chunk);
    }
    return chunks;
  }

  abort(requestId) {
    const controller = this.activeRequests.get(requestId);
    if (controller) {
      controller.abort();
      this.activeRequests.delete(requestId);
      return true;
    }
    return false;
  }

  async cleanup() {
    for (const [id, controller] of this.activeRequests) {
      controller.abort();
    }
    this.activeRequests.clear();
    this.sessions.clear();
  }
}


/**
 * OpenRouter provider implementation
 */
export class OpenRouterProvider extends BaseProvider {
  constructor(config = {}) {
    super(config);
    this.apiKey = config.apiKey || process.env.OPENROUTER_API_KEY;
    this.baseUrl = config.baseUrl || 'https://openrouter.ai/api/v1';
  }

  get name() {
    return 'openrouter';
  }

  get models() {
    return [
      { id: 'openai/gpt-4o', name: 'GPT-4o', context: 128000 },
      { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', context: 128000 },
      { id: 'anthropic/claude-sonnet-4', name: 'Claude Sonnet 4', context: 200000 },
      { id: 'anthropic/claude-opus-4', name: 'Claude Opus 4', context: 200000 },
      { id: 'google/gemini-2.5-pro', name: 'Gemini 2.5 Pro', context: 1000000 },
      { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1', context: 64000 },
      { id: 'xiaomi/mimo-v2-pro', name: 'MiMo V2 Pro', context: 32000 },
    ];
  }

  async *stream(params) {
    const { model, messages, tools, options = {} } = params;
    const requestId = `req_${Date.now()}`;
    const controller = new AbortController();
    this.activeRequests.set(requestId, controller);

    const body = {
      model,
      messages,
      stream: true,
      ...(tools && { tools }),
      ...options,
    };

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'HTTP-Referer': 'https://openclaw.ai',
          'X-Title': 'OpenClaw',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`OpenRouter error ${response.status}: ${err}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (data === '[DONE]') {
            yield { type: 'done', requestId };
            return;
          }

          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta;
            if (delta?.content) {
              yield { type: 'content', content: delta.content, requestId };
            }
            if (delta?.tool_calls) {
              yield { type: 'tool_calls', toolCalls: delta.tool_calls, requestId };
            }
          } catch {
            // Skip malformed chunks
          }
        }
      }
    } finally {
      this.activeRequests.delete(requestId);
    }
  }
}


/**
 * Ollama provider for local models
 */
export class OllamaProvider extends BaseProvider {
  constructor(config = {}) {
    super(config);
    this.baseUrl = config.baseUrl || 'http://localhost:11434';
  }

  get name() {
    return 'ollama';
  }

  async *stream(params) {
    const { model, messages, options = {} } = params;
    const requestId = `req_${Date.now()}`;
    const controller = new AbortController();
    this.activeRequests.set(requestId, controller);

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, messages, stream: true, ...options }),
        signal: controller.signal,
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n').filter(l => l.trim());
        buffer = lines.pop() || '';

        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            if (parsed.message?.content) {
              yield { type: 'content', content: parsed.message.content, requestId };
            }
            if (parsed.done) {
              yield { type: 'done', requestId };
              return;
            }
          } catch {}
        }
      }
    } finally {
      this.activeRequests.delete(requestId);
    }
  }
}


/**
 * Provider registry
 */
export class ProviderRegistry {
  constructor() {
    this.providers = new Map();
    this.defaultProvider = null;
  }

  register(name, provider) {
    this.providers.set(name, provider);
    if (!this.defaultProvider) {
      this.defaultProvider = name;
    }
    return this;
  }

  get(name) {
    const provider = this.providers.get(name || this.defaultProvider);
    if (!provider) {
      throw new Error(`Provider '${name}' not found. Available: ${[...this.providers.keys()].join(', ')}`);
    }
    return provider;
  }

  list() {
    return [...this.providers.keys()];
  }

  async initializeAll() {
    for (const [name, provider] of this.providers) {
      await provider.initialize();
    }
  }

  async cleanupAll() {
    for (const [name, provider] of this.providers) {
      await provider.cleanup();
    }
  }
}


export default { BaseProvider, OpenRouterProvider, OllamaProvider, ProviderRegistry };
