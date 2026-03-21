'use client';

import React, { useMemo, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, X } from 'lucide-react';

interface DataPoint {
  timestamp: string;
  sentiment: number;
  category: string;
  content: string;
}

interface MoodPulseChartProps {
  data: DataPoint[];
}

export const MoodPulseChart: React.FC<MoodPulseChartProps> = ({ data }) => {
  const [selectedPoint, setSelectedPoint] = useState<DataPoint | null>(null);

  const avgSentiment = useMemo(() => {
    if (data.length === 0) return 0.5;
    return data.reduce((acc, curr) => acc + curr.sentiment, 0) / data.length;
  }, [data]);

  // 动态颜色逻辑
  const chartConfig = useMemo(() => {
    if (avgSentiment > 0.7) {
      return {
        stroke: '#9ece6a', // Emerald/Green
        fill: 'url(#colorGreen)',
        gradient: ['#9ece6a', 'rgba(158, 206, 106, 0)']
      };
    } else if (avgSentiment < 0.3) {
      return {
        stroke: '#f7768e', // Red/Orange
        fill: 'url(#colorOrange)',
        gradient: ['#f7768e', 'rgba(247, 118, 142, 0)']
      };
    }
    return {
      stroke: '#bb9af7', // Magenta (Normal Tokyo Night)
      fill: 'url(#colorDefault)',
      gradient: ['#bb9af7', 'rgba(187, 154, 247, 0)']
    };
  }, [avgSentiment]);

  const formattedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      timeLabel: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));
  }, [data]);

  return (
    <div className="w-full h-80 relative bg-[#1a1b26] p-4 rounded-xl border border-[#747482]/10">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={formattedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          onClick={(state) => {
            if (state && state.activePayload) {
              setSelectedPoint(state.activePayload[0].payload as DataPoint);
            }
          }}
        >
          <defs>
            <linearGradient id="colorGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#9ece6a" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#9ece6a" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorOrange" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f7768e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f7768e" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorDefault" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#bb9af7" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#bb9af7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#747482" vertical={false} opacity={0.1} />
          <XAxis 
            dataKey="timeLabel" 
            stroke="#aaaab8" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
          />
          <YAxis 
            domain={[0, 1]} 
            stroke="#aaaab8" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            ticks={[0, 0.5, 1]}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#171926', border: '1px solid #74748233', borderRadius: '8px', fontSize: '12px' }}
            itemStyle={{ color: '#eeecfc' }}
            cursor={{ stroke: chartConfig.stroke, strokeWidth: 1 }}
          />
          <Area
            type="monotone"
            dataKey="sentiment"
            stroke={chartConfig.stroke}
            fill={chartConfig.fill}
            strokeWidth={2}
            animationDuration={1500}
            activeDot={{ r: 6, fill: chartConfig.stroke, stroke: '#1a1b26', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Popover Detail */}
      <AnimatePresence>
        {selectedPoint && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 bg-[#24283b] border border-[#7aa2f7]/30 p-4 rounded-lg shadow-2xl z-50 w-72 backdrop-blur-xl"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <div className="bg-[#7aa2f7]/20 p-1 rounded">
                  <Info className="w-3 h-3 text-[#7aa2f7]" />
                </div>
                <span className="text-[10px] font-bold text-[#7aa2f7] uppercase tracking-tighter">
                  {selectedPoint.category}
                </span>
              </div>
              <button 
                onClick={() => setSelectedPoint(null)}
                className="text-[#aaaab8] hover:text-[#f7768e] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm leading-relaxed text-[#c0caf5]">
              {selectedPoint.content}
            </p>
            <div className="mt-3 pt-3 border-t border-[#747482]/10 flex justify-between items-center text-[10px] text-[#565f89]">
              <span>Sentiment Score</span>
              <span className="font-mono text-[#7dcfff]">{selectedPoint.sentiment.toFixed(2)}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
