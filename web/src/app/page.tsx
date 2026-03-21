'use client';

import { useEffect, useState } from "react";
import { Activity, Heart, Search, LayoutDashboard, Signal } from "lucide-react";
import { mcpClient, LifeStats, MoodHistoryEntry } from "@/lib/mcp";
import { MoodPulseChart } from "@/components/MoodPulseChart";

export default function Home() {
  const [stats, setStats] = useState<LifeStats | null>(null);
  const [history, setHistory] = useState<MoodHistoryEntry[]>([]);
  const [isAssistantOnline, setIsAssistantOnline] = useState(false);
  const [isProtectionMode, setIsProtectionMode] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, historyData] = await Promise.all([
          mcpClient.getStatsSummary(),
          mcpClient.getMoodHistory(7)
        ]);
        setStats(statsData);
        setHistory(historyData);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // 语音助手在线状态与保护模式轮询 (30秒)
  useEffect(() => {
    async function checkStatus() {
      try {
        const status = await mcpClient.getStatus();
        setIsAssistantOnline(status.assistant_online);
        setIsProtectionMode(status.protection_mode);
      } catch (err) {
        console.error("Status check failed:", err);
      }
    }
    checkStatus();
    const timer = setInterval(checkStatus, 30000);
    return () => clearInterval(timer);
  }, []);

  // 紧急休息模式检测
  const isEmergencyMode = history.some(p => p.fatigue_score > 0.8);

  // 保护/紧急模式下的动态样式
  const theme = {
    accent: isEmergencyMode ? '#ff4d4d' : isProtectionMode ? '#ff9e64' : '#7aa2f7',
    bg: isEmergencyMode ? 'bg-[#3d0c0c]' : isProtectionMode ? 'bg-[#2d2019]' : 'bg-[#1a1b26]',
    text: isEmergencyMode ? 'text-[#ff4d4d]' : isProtectionMode ? 'text-[#ff9e64]' : 'text-[#7aa2f7]',
    border: isEmergencyMode ? 'border-[#ff4d4d]/30' : isProtectionMode ? 'border-[#ff9e64]/20' : 'border-[#7aa2f7]/20',
    animate: isEmergencyMode ? 'duration-[1000ms]' : isProtectionMode ? 'duration-[3000ms]' : 'duration-500',
    pulseSpeed: isEmergencyMode ? 'animate-[pulse_1.5s_ease-in-out_infinite]' : isProtectionMode ? 'animate-[pulse_4s_cubic-bezier(0.4,0,0.6,1)_infinite]' : 'animate-pulse'
  };

  return (
    <div className={`min-h-screen ${theme.bg} text-[#eeecfc] font-mono p-8 transition-colors duration-1000`}>
      <header className="mb-12 flex items-center justify-between border-b border-[#747482]/20 pb-6">
        <div className="flex items-center gap-3">
          <LayoutDashboard className={`${theme.text} w-8 h-8 transition-colors duration-1000`} />
          <h1 className="text-2xl font-bold tracking-tight">
            {isEmergencyMode ? "SYSTEM ALERT: EMERGENCY REST" : isProtectionMode ? "HumanSystems Protocol: Care" : "HumanSystems Core"}
          </h1>
        </div>
        <div className="flex items-center gap-6">
          {/* Voice Assistant Signal */}
          <div className="flex items-center gap-2 transition-all duration-1000">
            <Signal className={`w-4 h-4 ${isAssistantOnline ? (isEmergencyMode ? 'text-[#ff4d4d]' : isProtectionMode ? 'text-[#ff9e64]' : 'text-[#9ece6a]') : 'text-[#565f89]'} transition-colors duration-1000`} />
            <span className={`text-[10px] uppercase font-bold tracking-widest ${isAssistantOnline ? (isEmergencyMode ? 'text-[#ff4d4d]' : isProtectionMode ? 'text-[#ff9e64]' : 'text-[#9ece6a]') : 'text-[#565f89]'}`}>
              Assistant: {isAssistantOnline ? 'Online' : 'Offline'}
            </span>
          </div>
          
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full bg-opacity-10 ${isEmergencyMode ? 'bg-[#ff4d4d]/10 text-[#ff4d4d] border-[#ff4d4d]/20' : isProtectionMode ? 'bg-[#ff9e64]/10 text-[#ff9e64] border-[#ff9e64]/20' : 'bg-[#7aa2f7]/10 text-[#7aa2f7] border-[#7aa2f7]/20'} text-xs border transition-all duration-1000`}>
            <div className={`w-2 h-2 rounded-full ${isEmergencyMode ? 'bg-[#ff4d4d]' : isProtectionMode ? 'bg-[#ff9e64]' : 'bg-[#7aa2f7]'} ${theme.pulseSpeed}`} />
            {isEmergencyMode ? "EMERGENCY REST ACTIVE" : isProtectionMode ? "PROTECTION MODE ACTIVE" : "System Active"}
          </div>
        </div>
      </header>

      <main className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Mood Card */}
          <div className="bg-[#171926] p-6 rounded-lg border border-[#747482]/10 backdrop-blur-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#bb9af7] text-sm font-semibold uppercase tracking-wider">Mood Pulse</h3>
              <Heart className="text-[#f7768e] w-5 h-5" />
            </div>
            <div className="text-4xl font-bold mb-2">
              {loading ? "..." : stats?.avg_sentiment ?? "N/A"}
            </div>
            <p className="text-[#aaaab8] text-xs">Weekly Average Sentiment</p>
          </div>

          {/* Activity Card */}
          <div className="bg-[#171926] p-6 rounded-lg border border-[#747482]/10 backdrop-blur-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#7dcfff] text-sm font-semibold uppercase tracking-wider">Events</h3>
              <Activity className="text-[#9ece6a] w-5 h-5" />
            </div>
            <div className="text-4xl font-bold mb-2">
              {loading ? "..." : stats?.total_events ?? "0"}
            </div>
            <p className="text-[#aaaab8] text-xs">Logged Events (Past 7 Days)</p>
          </div>

          {/* Search Card */}
          <div className={`bg-[#171926] p-6 rounded-lg border ${isProtectionMode ? 'border-[#ff9e64]/10' : 'border-[#747482]/10'} backdrop-blur-2xl transition-colors duration-1000`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className={`${isProtectionMode ? 'text-[#ff9e64]' : 'text-[#7aa2f7]'} text-sm font-semibold uppercase tracking-wider transition-colors duration-1000`}>Quick Actions</h3>
              <Search className={`${theme.text} w-5 h-5 transition-colors duration-1000`} />
            </div>
            <button className={`w-full ${isProtectionMode ? 'bg-[#ff9e64]/20 hover:bg-[#ff9e64]/30 text-[#ff9e64]' : 'bg-[#7aa2f7]/20 hover:bg-[#7aa2f7]/30 text-[#7aa2f7]'} py-2 rounded transition-all duration-1000 text-sm`}>
              Search Archive
            </button>
          </div>
        </div>

        {/* Mood History Chart Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <div className={`w-1 h-4 ${isProtectionMode ? 'bg-[#ff9e64]' : 'bg-[#7aa2f7]'} transition-colors duration-1000`} />
            <h2 className={`text-sm font-bold uppercase tracking-widest ${isProtectionMode ? 'text-[#ff9e64]' : 'text-[#7aa2f7]'} transition-colors duration-1000`}>Mood Fluctuations</h2>
          </div>
          <MoodPulseChart data={history} isProtectionMode={isProtectionMode} />
        </section>

        <section className={`${isProtectionMode ? 'bg-[#3b2b23]' : 'bg-[#0c0d18]'} p-8 rounded-xl border ${isProtectionMode ? 'border-[#ff9e64]/10' : 'border-[#747482]/5'} transition-colors duration-1000`}>
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <div className={`w-1 h-6 ${isProtectionMode ? 'bg-[#ff9e64]' : 'bg-[#bb9af7]'} transition-colors duration-1000`} />
            Infrastructure Overview
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <span className="block text-[#aaaab8] text-[10px] uppercase font-bold mb-1">Architecture</span>
              <span className="text-sm">Next.js 16 (App Router)</span>
            </div>
            <div>
              <span className="block text-[#aaaab8] text-[10px] uppercase font-bold mb-1">Styling</span>
              <span className="text-sm">Tailwind CSS 4.0</span>
            </div>
            <div>
              <span className="block text-[#aaaab8] text-[10px] uppercase font-bold mb-1">Endpoints</span>
              <span className="text-sm">MCP (Port 8000)</span>
            </div>
            <div>
              <span className="block text-[#aaaab8] text-[10px] uppercase font-bold mb-1">Status</span>
              <span className={`text-sm ${isProtectionMode ? 'text-[#ff9e64]' : 'text-[#9ece6a]'} transition-colors duration-1000`}>
                {isProtectionMode ? 'Care Mode Engaged' : 'Ready for Deployment'}
              </span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
