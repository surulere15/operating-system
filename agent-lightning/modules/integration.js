/**
 * OpenClaw Agent Integration Layer
 * Wires MCP Router + Session Store + Provider Abstraction into OpenClaw.
 * 
 * This module acts as the glue between our new patterns and OpenClaw's
 * existing skill/tool system.
 * 
 * Usage:
 *   import { OpenClawAgent } from './integration.js';
 *   const agent = new OpenClawAgent();
 *   await agent.init();
 *   const result = await agent.run('Find the latest DeFi exploits');
 */

import { MCPRouter } from './mcp-router.js';
import { SessionStore } from './session-store.js';
import { ProviderRegistry, OpenRouterProvider, OllamaProvider } from './provider.js';
import { readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { homedir } from 'os';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export class OpenClawAgent {
  constructor(config = {}) {
    this.config = {
      workspace: config.workspace || join(homedir(), '.openclaw', 'workspace'),
      sessionsPath: config.sessionsPath || join(homedir(), '.openclaw', 'sessions'),
      defaultProvider: config.defaultProvider || 'openrouter',
      defaultModel: config.defaultModel || 'openai/gpt-4o-mini',
      maxTurns: config.maxTurns || 20,
      ...config,
    };

    this.router = new MCPRouter();
    this.sessions = new SessionStore(this.config.sessionsPath);
    this.providers = new ProviderRegistry();
    this.initialized = false;
  }

  /**
   * Initialize the agent system
   */
  async init() {
    if (this.initialized) return;

    // Load env
    await this._loadEnv();

    // Register providers
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (apiKey) {
      this.providers.register('openrouter', new OpenRouterProvider({ apiKey }));
    }

    const ollamaUrl = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
    this.providers.register('ollama', new OllamaProvider({ baseUrl: ollamaUrl }));

    // Initialize session store
    await this.sessions.init();

    // Initialize providers
    await this.providers.initializeAll();

    // Auto-discover MCP servers from config
    await this._discoverMCPServers();

    this.initialized = true;
    console.log('[OpenClaw] Agent initialized');
    console.log(`[OpenClaw] Providers: ${this.providers.list().join(', ')}`);
    console.log(`[OpenClaw] Tools: ${this.router.getToolManifest().length}`);
  }

  /**
   * Run a single prompt through the agent
   * @param {string} prompt - User message
   * @param {Object} [options]
   * @param {string} [options.provider] - Provider to use
   * @param {string} [options.model] - Model to use
   * @param {string} [options.sessionId] - Session to continue
   * @returns {Promise<Object>} Response with content, toolCalls, sessionId
   */
  async run(prompt, options = {}) {
    await this.init();

    const provider = this.providers.get(options.provider || this.config.defaultProvider);
    const model = options.model || this.config.defaultModel;
    const sessionId = options.sessionId || `session_${Date.now()}`;

    // Load existing session
    const existingSession = await this.sessions.load(sessionId);
    const messages = existingSession?.messages || [];

    // Add system prompt
    if (messages.length === 0) {
      const systemPrompt = await this._loadSystemPrompt();
      messages.push({ role: 'system', content: systemPrompt });
    }

    // Add user message
    messages.push({ role: 'user', content: prompt });

    // Collect response
    let content = '';
    const toolCalls = [];

    try {
      for await (const chunk of provider.stream({
        model,
        messages,
        tools: this._getToolDefinitions(),
      })) {
        if (chunk.type === 'content') {
          content += chunk.content;
          process.stdout.write(chunk.content);
        }
        if (chunk.type === 'tool_calls') {
          toolCalls.push(...chunk.toolCalls);
        }
      }
    } catch (err) {
      console.error('[OpenClaw] Stream error:', err.message);
      content = `Error: ${err.message}`;
    }

    // Add assistant response to messages
    messages.push({ role: 'assistant', content });

    // Execute tool calls if any
    const toolResults = [];
    for (const tc of toolCalls) {
      try {
        const result = await this.router.call(tc.function.name, JSON.parse(tc.function.arguments));
        toolResults.push({ tool_call_id: tc.id, result });
        messages.push({ role: 'tool', content: JSON.stringify(result), tool_call_id: tc.id });
      } catch (err) {
        toolResults.push({ tool_call_id: tc.id, error: err.message });
      }
    }

    // Save session
    await this.sessions.save(sessionId, {
      messages,
      toolCalls: [...(existingSession?.toolCalls || []), ...toolCalls],
      provider: options.provider || this.config.defaultProvider,
      model,
    });

    return {
      content,
      toolCalls,
      toolResults,
      sessionId,
      messageCount: messages.length,
    };
  }

  /**
   * Stream a response with callback
   */
  async *stream(prompt, options = {}) {
    await this.init();

    const provider = this.providers.get(options.provider || this.config.defaultProvider);
    const model = options.model || this.config.defaultModel;
    const sessionId = options.sessionId || `session_${Date.now()}`;

    const existingSession = await this.sessions.load(sessionId);
    const messages = existingSession?.messages || [];

    if (messages.length === 0) {
      const systemPrompt = await this._loadSystemPrompt();
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push({ role: 'user', content: prompt });

    let content = '';

    for await (const chunk of provider.stream({
      model,
      messages,
      tools: this._getToolDefinitions(),
    })) {
      if (chunk.type === 'content') {
        content += chunk.content;
      }
      yield { ...chunk, sessionId };
    }

    messages.push({ role: 'assistant', content });
    await this.sessions.save(sessionId, { messages, model, provider: options.provider });
  }

  /**
   * List all sessions
   */
  async listSessions(options = {}) {
    return this.sessions.list(options);
  }

  /**
   * Get agent status
   */
  async status() {
    await this.init();
    return {
      providers: this.providers.list(),
      tools: this.router.getStatus(),
      sessions: await this.sessions.stats(),
      config: {
        defaultProvider: this.config.defaultProvider,
        defaultModel: this.config.defaultModel,
      },
    };
  }

  /**
   * Register an MCP server
   */
  registerMCPServer(name, config) {
    this.router.register(name, config);
  }

  /**
   * Cleanup resources
   */
  async cleanup() {
    await this.providers.cleanupAll();
  }

  // ── Private ──────────────────────────────────

  async _loadEnv() {
    const envPath = join(homedir(), '.openclaw', '.env');
    try {
      const content = await readFile(envPath, 'utf-8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx > 0) {
          const key = trimmed.slice(0, eqIdx).trim();
          const val = trimmed.slice(eqIdx + 1).trim();
          process.env[key] = process.env[key] || val;
        }
      }
    } catch {
      // .env not found, use existing env vars
    }
  }

  async _loadSystemPrompt() {
    const paths = [
      join(this.config.workspace, 'SOUL.md'),
      join(this.config.workspace, 'AGENTS.md'),
    ];
    for (const p of paths) {
      try {
        return await readFile(p, 'utf-8');
      } catch {}
    }
    return 'You are JOE, a helpful AI agent.';
  }

  _getToolDefinitions() {
    const tools = this.router.getToolManifest();
    if (tools.length === 0) return undefined;
    
    return tools.map(t => ({
      type: 'function',
      function: {
        name: t.tool,
        description: `Tool from ${t.server} server`,
        parameters: { type: 'object', properties: {} },
      },
    }));
  }

  async _discoverMCPServers() {
    // Auto-register Composio if API key exists
    const composioKey = process.env.COMPOSIO_API_KEY;
    if (composioKey) {
      this.router.register('composio', {
        url: 'https://mcp.composio.dev',
        headers: { 'Authorization': `Bearer ${composioKey}` },
      });
    }
  }
}

export default OpenClawAgent;
