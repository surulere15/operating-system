/**
 * OpenClaw MCP Tool Router
 * Inspired by Composio's MCP pattern from open-claude-cowork.
 * 
 * Routes tool calls to MCP-compatible servers, enabling 500+ app integrations
 * without changing OpenClaw's core architecture.
 * 
 * Usage:
 *   import { MCPRouter } from './mcp-router.js';
 *   const router = new MCPRouter();
 *   router.register('composio', { url: '...', headers: {} });
 *   const result = await router.call('composio', 'gmail_send_email', { to: '...', body: '...' });
 */

import { EventEmitter } from 'events';

export class MCPRouter extends EventEmitter {
  constructor() {
    super();
    this.servers = new Map();
    this.tools = new Map(); // toolName -> serverName
  }

  /**
   * Register an MCP server
   * @param {string} name - Server identifier
   * @param {Object} config - Server configuration
   * @param {string} config.url - MCP server URL
   * @param {Object} [config.headers] - Optional auth headers
   * @param {string} [config.type] - 'http' | 'sse' (default: 'http')
   */
  register(name, config) {
    this.servers.set(name, {
      name,
      url: config.url,
      headers: config.headers || {},
      type: config.type || 'http',
      status: 'registered',
    });
    this.emit('server:registered', name);
  }

  /**
   * Discover tools from all registered servers
   */
  async discoverTools() {
    for (const [name, server] of this.servers) {
      try {
        const tools = await this._listTools(server);
        for (const tool of tools) {
          this.tools.set(tool.name, name);
        }
        server.status = 'connected';
        server.toolCount = tools.length;
        this.emit('server:connected', name, tools.length);
      } catch (err) {
        server.status = 'error';
        server.error = err.message;
        this.emit('server:error', name, err);
      }
    }
    return this.getToolManifest();
  }

  /**
   * Get all available tools across servers
   */
  getToolManifest() {
    const manifest = [];
    for (const [toolName, serverName] of this.tools) {
      manifest.push({ tool: toolName, server: serverName });
    }
    return manifest;
  }

  /**
   * Route a tool call to the appropriate MCP server
   * @param {string} toolName - Tool to invoke
   * @param {Object} params - Tool parameters
   * @returns {Promise<Object>} Tool result
   */
  async call(toolName, params = {}) {
    const serverName = this.tools.get(toolName);
    if (!serverName) {
      throw new Error(`Tool '${toolName}' not found. Available: ${[...this.tools.keys()].join(', ')}`);
    }

    const server = this.servers.get(serverName);
    this.emit('tool:call', { tool: toolName, server: serverName, params });

    try {
      const result = await this._invokeTool(server, toolName, params);
      this.emit('tool:result', { tool: toolName, server: serverName, result });
      return result;
    } catch (err) {
      this.emit('tool:error', { tool: toolName, server: serverName, error: err });
      throw err;
    }
  }

  /**
   * Check if a tool is available
   */
  hasTool(toolName) {
    return this.tools.has(toolName);
  }

  /**
   * Get server status
   */
  getStatus() {
    const status = {};
    for (const [name, server] of this.servers) {
      status[name] = {
        status: server.status,
        toolCount: server.toolCount || 0,
        error: server.error || null,
      };
    }
    return status;
  }

  // ── Private methods ──────────────────────────

  async _listTools(server) {
    const response = await fetch(`${server.url}/tools`, {
      headers: {
        'Content-Type': 'application/json',
        ...server.headers,
      },
    });
    if (!response.ok) throw new Error(`Failed to list tools: ${response.status}`);
    const data = await response.json();
    return data.tools || data || [];
  }

  async _invokeTool(server, toolName, params) {
    const response = await fetch(`${server.url}/tools/call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...server.headers,
      },
      body: JSON.stringify({
        name: toolName,
        arguments: params,
      }),
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Tool call failed: ${response.status} - ${err}`);
    }
    return response.json();
  }
}

export default MCPRouter;
