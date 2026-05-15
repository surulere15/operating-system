/**
 * OpenClaw Agent Modules
 * Enhanced patterns from open-claude-cowork analysis.
 * 
 * Modules:
 *   - MCPRouter:       Route tool calls to MCP-compatible servers
 *   - SessionStore:    Persist agent sessions to disk
 *   - Providers:       Pluggable AI backends (OpenRouter, Ollama)
 *   - OpenClawAgent:   Integrated agent system (ties everything together)
 */

export { MCPRouter } from './mcp-router.js';
export { SessionStore } from './session-store.js';
export { 
  BaseProvider, 
  OpenRouterProvider, 
  OllamaProvider, 
  ProviderRegistry 
} from './provider.js';
export { OpenClawAgent } from './integration.js';
