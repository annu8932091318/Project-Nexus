import React from 'react';
import { Task } from '../types';
import { cn } from '../lib/utils';
import { FileText, Layout, Code, ClipboardCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface WorkspaceProps {
  tasks: Task[];
  activeTaskIndex: number;
}

const TASK_ICONS: Record<string, React.ReactNode> = {
  manager: <FileText className="w-4 h-4" />,
  designer: <Layout className="w-4 h-4" />,
  developer: <Code className="w-4 h-4" />,
  qa: <ClipboardCheck className="w-4 h-4" />,
};

export function Workspace({ tasks, activeTaskIndex }: WorkspaceProps) {
  const completedTasks = tasks.filter(t => t.status === 'completed');

  return (
    <div className="nexus-card h-full flex flex-col">
      <div className="bg-nexus-border/50 px-4 py-2 border-bottom border-nexus-border flex items-center gap-4 overflow-x-auto no-scrollbar">
        {tasks.map((task, idx) => (
          <div 
            key={task.id}
            className={cn(
              "flex items-center gap-2 px-3 py-1 text-xs font-mono rounded-t transition-colors whitespace-nowrap",
              idx === activeTaskIndex ? "bg-nexus-bg border-x border-t border-nexus-border text-nexus-accent" : "text-nexus-muted"
            )}
          >
            {TASK_ICONS[task.agentRole]}
            {task.agentRole.toUpperCase()}
          </div>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-6 bg-nexus-bg/50">
        <AnimatePresence mode="wait">
          {tasks[activeTaskIndex]?.output ? (
            <motion.div
              key={tasks[activeTaskIndex].id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="prose prose-invert max-w-none"
            >
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-nexus-border">
                <h3 className="text-xl font-bold flex items-center gap-3">
                  {TASK_ICONS[tasks[activeTaskIndex].agentRole]}
                  {tasks[activeTaskIndex].agentRole.toUpperCase()} OUTPUT
                </h3>
                <span className="text-xs font-mono text-nexus-accent bg-nexus-accent/10 px-2 py-1 rounded">
                  TASK COMPLETED
                </span>
              </div>
              <pre className="text-sm font-mono whitespace-pre-wrap bg-nexus-bg p-4 rounded border border-nexus-border leading-relaxed">
                {tasks[activeTaskIndex].output}
              </pre>
            </motion.div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-nexus-muted space-y-4">
              <div className="w-12 h-12 border-2 border-dashed border-nexus-border rounded-full flex items-center justify-center animate-pulse">
                {TASK_ICONS[tasks[activeTaskIndex]?.agentRole || 'manager']}
              </div>
              <p className="text-sm font-mono">
                {tasks[activeTaskIndex]?.status === 'in-progress' 
                  ? `Agent ${tasks[activeTaskIndex].agentRole} is generating output...`
                  : "Waiting for task initiation..."}
              </p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
