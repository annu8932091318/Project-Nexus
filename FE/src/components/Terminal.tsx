import React, { useEffect, useRef } from 'react';
import { LogEntry } from '../types';
import { cn } from '../lib/utils';

interface TerminalProps {
  logs: LogEntry[];
}

export function Terminal({ logs }: TerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="nexus-card h-full flex flex-col font-mono text-sm">
      <div className="bg-nexus-border/50 px-4 py-2 border-bottom border-nexus-border flex items-center justify-between">
        <span className="text-xs uppercase tracking-tighter">Nexus Terminal</span>
        <div className="flex gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-500/50" />
          <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
          <div className="w-2 h-2 rounded-full bg-green-500/50" />
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-nexus-border"
      >
        {logs.length === 0 && (
          <div className="text-nexus-muted italic">Waiting for swarm initialization...</div>
        )}
        {logs.map((log) => (
          <div key={log.id} className="flex gap-3">
            <span className="text-nexus-muted shrink-0">
              [{new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
            </span>
            <span className={cn(
              "font-bold shrink-0",
              log.agentName === 'System' ? "text-nexus-muted" : "text-nexus-accent"
            )}>
              {log.agentName}:
            </span>
            <span className={cn(
              "break-words",
              log.type === 'error' ? "text-red-400" : 
              log.type === 'success' ? "text-nexus-accent" : 
              log.type === 'warning' ? "text-yellow-400" : "text-nexus-ink"
            )}>
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
