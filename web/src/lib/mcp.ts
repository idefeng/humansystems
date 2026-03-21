/**
 * HumanSystems MCP Connection Wrapper
 * Provides standardized access to the local MCP server on port 8000.
 */

export interface MoodHistoryEntry {
  timestamp: string;
  sentiment: number;
  category: string;
}

export interface LifeStats {
  avg_sentiment: number;
  total_events: number;
  category_dist: Record<string, number>;
  action_items_count: number;
  message?: string;
}

export interface EventRecord {
  timestamp: string;
  category: string;
  content: string;
  sentiment: number;
  action_item: boolean;
}

const BASE_URL = 'http://localhost:8000';

export const mcpClient = {
  /**
   * 获取情绪历史
   */
  async getMoodHistory(days: number = 7): Promise<MoodHistoryEntry[]> {
    const res = await fetch(`${BASE_URL}/mood/history?days=${days}`);
    if (!res.ok) throw new Error('Failed to fetch mood history');
    return res.json();
  },

  /**
   * 获取统计摘要
   */
  async getStatsSummary(): Promise<LifeStats> {
    const res = await fetch(`${BASE_URL}/stats/summary`);
    if (!res.ok) throw new Error('Failed to fetch stats summary');
    return res.json();
  },

  /**
   * 搜索事件
   */
  async searchEvents(query?: string, category?: string, limit: number = 20): Promise<EventRecord[]> {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category) params.append('category', category);
    params.append('limit', limit.toString());
    
    const res = await fetch(`${BASE_URL}/events/search?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to search events');
    return res.json();
  },

  /**
   * 获取系统状态 (包含语音助手在线信息)
   */
  async getStatus(): Promise<{
    status: string;
    assistant_online: boolean;
    recent_history: EventRecord[];
    mood_pulse: { current_index: number; label: string };
  }> {
    const res = await fetch(`${BASE_URL}/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  }
};
