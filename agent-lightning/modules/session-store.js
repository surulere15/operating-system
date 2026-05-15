/**
 * OpenClaw Session Persistence
 * Inspired by open-claude-cowork's localStorage pattern.
 * 
 * Saves and restores agent session state to disk, enabling:
 * - Conversation history across restarts
 * - Tool call audit trails
 * - Todo/task state recovery
 * - Multi-session management
 * 
 * Usage:
 *   import { SessionStore } from './session-store.js';
 *   const store = new SessionStore('~/.openclaw/sessions');
 *   await store.save('chat-123', { messages: [...], todos: [...] });
 *   const session = await store.load('chat-123');
 */

import { readFile, writeFile, mkdir, readdir, stat, unlink } from 'fs/promises';
import { join, dirname } from 'path';
import { homedir } from 'os';

export class SessionStore {
  constructor(basePath = null) {
    this.basePath = basePath || join(homedir(), '.openclaw', 'sessions');
    this.cache = new Map();
    this.initialized = false;
  }

  /**
   * Initialize the store (create directory if needed)
   */
  async init() {
    if (this.initialized) return;
    await mkdir(this.basePath, { recursive: true });
    this.initialized = true;
  }

  /**
   * Save a session
   * @param {string} sessionId - Unique session identifier
   * @param {Object} data - Session data to persist
   * @param {Object} [options]
   * @param {boolean} [options.compress] - Gzip large sessions (default: false)
   */
  async save(sessionId, data, options = {}) {
    await this.init();
    
    const sessionData = {
      id: sessionId,
      ...data,
      _meta: {
        savedAt: new Date().toISOString(),
        version: '1.0.0',
        messageCount: data.messages?.length || 0,
        toolCallCount: data.toolCalls?.length || 0,
      },
    };

    const filePath = this._getPath(sessionId);
    const json = JSON.stringify(sessionData, null, 2);
    
    await writeFile(filePath, json, 'utf-8');
    this.cache.set(sessionId, sessionData);
    
    return { path: filePath, size: json.length };
  }

  /**
   * Load a session
   * @param {string} sessionId
   * @returns {Promise<Object|null>} Session data or null if not found
   */
  async load(sessionId) {
    // Check cache first
    if (this.cache.has(sessionId)) {
      return this.cache.get(sessionId);
    }

    try {
      const filePath = this._getPath(sessionId);
      const json = await readFile(filePath, 'utf-8');
      const data = JSON.parse(json);
      this.cache.set(sessionId, data);
      return data;
    } catch (err) {
      if (err.code === 'ENOENT') return null;
      throw err;
    }
  }

  /**
   * List all sessions
   * @param {Object} [options]
   * @param {number} [options.limit] - Max sessions to return
   * @param {string} [options.sort] - 'date' | 'name' (default: 'date')
   * @returns {Promise<Array>} List of session summaries
   */
  async list(options = {}) {
    await this.init();
    
    try {
      const files = await readdir(this.basePath);
      const sessions = [];

      for (const file of files) {
        if (!file.endsWith('.json')) continue;
        
        try {
          const filePath = join(this.basePath, file);
          const stats = await stat(filePath);
          const sessionId = file.replace('.json', '');
          
          sessions.push({
            id: sessionId,
            file: file,
            size: stats.size,
            modified: stats.mtime,
            created: stats.birthtime,
          });
        } catch {
          continue;
        }
      }

      // Sort by modification date (newest first)
      sessions.sort((a, b) => b.modified - a.modified);

      if (options.limit) {
        return sessions.slice(0, options.limit);
      }

      return sessions;
    } catch {
      return [];
    }
  }

  /**
   * Delete a session
   * @param {string} sessionId
   */
  async delete(sessionId) {
    const filePath = this._getPath(sessionId);
    this.cache.delete(sessionId);
    
    try {
      await unlink(filePath);
      return true;
    } catch (err) {
      if (err.code === 'ENOENT') return false;
      throw err;
    }
  }

  /**
   * Append messages to an existing session
   * @param {string} sessionId
   * @param {Array} messages - New messages to append
   */
  async appendMessages(sessionId, messages) {
    const existing = await this.load(sessionId) || { messages: [] };
    existing.messages = [...(existing.messages || []), ...messages];
    return this.save(sessionId, existing);
  }

  /**
   * Get session statistics
   */
  async stats() {
    const sessions = await this.list();
    let totalSize = 0;
    let totalMessages = 0;

    for (const s of sessions) {
      totalSize += s.size;
      const data = await this.load(s.id);
      if (data) {
        totalMessages += data._meta?.messageCount || 0;
      }
    }

    return {
      sessionCount: sessions.length,
      totalSizeBytes: totalSize,
      totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
      totalMessages,
    };
  }

  /**
   * Export sessions to a backup file
   */
  async export(backupPath) {
    const sessions = await this.list();
    const backup = {
      exportedAt: new Date().toISOString(),
      sessionCount: sessions.length,
      sessions: {},
    };

    for (const s of sessions) {
      backup.sessions[s.id] = await this.load(s.id);
    }

    const json = JSON.stringify(backup, null, 2);
    await writeFile(backupPath, json, 'utf-8');
    return { path: backupPath, sessions: sessions.length, size: json.length };
  }

  // ── Private ──────────────────────────────────

  _getPath(sessionId) {
    // Sanitize sessionId for filesystem
    const safeId = sessionId.replace(/[^a-zA-Z0-9_-]/g, '_');
    return join(this.basePath, `${safeId}.json`);
  }
}

export default SessionStore;
