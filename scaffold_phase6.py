import os

files = {
    "frontend/src/lib/api.ts": """export interface AgentState {
  agent: string;
  status: 'idle' | 'analyzing' | 'reflecting' | 'validating' | 'done';
  currentSegment: string;
  confidence: number;
}

export const fetchReport = async (corpusId: string) => {
  const res = await fetch(`http://localhost:8000/api/v1/reports/${corpusId}`);
  if (!res.ok) throw new Error("Failed to fetch report");
  return res.json();
};

export const startAnalysis = async (corpusId: string) => {
  const res = await fetch(`http://localhost:8000/api/v1/analyze/${corpusId}`, { method: "POST" });
  return res.json();
};
""",

    "frontend/src/components/dashboard/AgentMonitor.tsx": """'use client';
import { useEffect, useState } from 'react';

interface AgentEvent {
  agent_id: string;
  action: string;
  segment_id: string;
  confidence: number;
}

export default function AgentMonitor() {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    // Mocking websocket connection
    const ws = new WebSocket('ws://localhost:8000/ws/agents');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents((prev) => [data, ...prev].slice(0, 50));
    };
    return () => ws.close();
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        Live Cognitive Trace
      </h3>
      <div className="space-y-3 h-64 overflow-y-auto font-mono text-sm">
        {events.length === 0 ? (
          <p className="text-gray-400">Waiting for agent activity...</p>
        ) : (
          events.map((ev, i) => (
            <div key={i} className="flex justify-between border-b pb-2">
              <span className="font-semibold text-blue-600">[{ev.agent_id}]</span>
              <span className="text-gray-600 truncate px-2">{ev.action}</span>
              <span className={`font-bold ${ev.confidence > 0.8 ? 'text-green-600' : 'text-orange-500'}`}>
                {ev.confidence.toFixed(2)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
""",

    "frontend/src/components/dashboard/EvidenceExplorer.tsx": """'use client';

export default function EvidenceExplorer() {
  // Hardcoded mock for scaffold
  const segment = "I think we should probably reconsider this proposal.";
  const quote = "probably reconsider";
  const theory = "Politeness Theory (Hedging)";
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-bold mb-4">Evidence Explorer</h3>
      <div className="p-4 bg-gray-50 rounded border mb-4 text-gray-800">
        "I think we should <mark className="bg-yellow-200 font-semibold">{quote}</mark> this proposal."
      </div>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="p-3 bg-blue-50 text-blue-800 rounded">
          <strong>Theory Applied:</strong> {theory}
        </div>
        <div className="p-3 bg-green-50 text-green-800 rounded">
          <strong>Reliability Score:</strong> 0.94
        </div>
        <div className="p-3 bg-orange-50 text-orange-800 rounded col-span-2">
          <strong>Ambiguity:</strong> Low - Explicit epistemic hedge indicating face-saving strategy.
        </div>
      </div>
    </div>
  );
}
""",

    "frontend/src/components/dashboard/ReliabilityMetrics.tsx": """'use client';

export default function ReliabilityMetrics() {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-bold mb-4">Scientific Reliability</h3>
      
      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-1 text-sm font-medium">
            <span>Evidence Strength</span>
            <span>92%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '92%' }}></div>
          </div>
        </div>
        
        <div>
          <div className="flex justify-between mb-1 text-sm font-medium">
            <span>Theoretical Defensibility</span>
            <span>88%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-indigo-600 h-2 rounded-full" style={{ width: '88%' }}></div>
          </div>
        </div>
        
        <div>
          <div className="flex justify-between mb-1 text-sm font-medium">
            <span>Hallucination Penalty</span>
            <span className="text-green-600">0%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-green-500 h-2 rounded-full" style={{ width: '100%' }}></div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 p-4 bg-gray-900 text-white rounded text-center">
        <div className="text-xs uppercase tracking-wider text-gray-400">Overall Score</div>
        <div className="text-3xl font-bold">0.90</div>
        <div className="text-sm text-green-400 mt-1">Academically Defensible</div>
      </div>
    </div>
  );
}
""",

    "frontend/src/app/dashboard/layout.tsx": """export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center sticky top-0 z-10">
        <h1 className="text-xl font-bold text-slate-800">PMDD Research Platform</h1>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-slate-100 text-slate-700 rounded-md text-sm font-medium hover:bg-slate-200 transition">Corpus Index</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition shadow-sm">Export Report</button>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-8 px-6">
        {children}
      </main>
    </div>
  );
}
""",

    "frontend/src/app/dashboard/page.tsx": """import AgentMonitor from '@/components/dashboard/AgentMonitor';
import EvidenceExplorer from '@/components/dashboard/EvidenceExplorer';
import ReliabilityMetrics from '@/components/dashboard/ReliabilityMetrics';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <AgentMonitor />
          <EvidenceExplorer />
        </div>
        <div className="space-y-6">
          <ReliabilityMetrics />
          
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold mb-4">Visualization Subsystem</h3>
            <div className="aspect-video bg-slate-100 rounded border border-dashed border-slate-300 flex items-center justify-center text-slate-400">
              [Plotly Heatmap Container]
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
""",

    "backend/api/routes/websocket.py": """from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

router = APIRouter()

@router.websocket("/agents")
async def agent_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        # Mock streaming agent trace data to the frontend
        for i in range(10):
            await asyncio.sleep(2)
            await websocket.send_text(json.dumps({
                "agent_id": "A2_Pragmatic",
                "action": f"Analyzing segment {i} using Speech Act Theory",
                "segment_id": f"seg-{i}",
                "confidence": 0.95 - (i * 0.02)
            }))
    except WebSocketDisconnect:
        pass
""",

    "backend/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.routes import router as api_router
from backend.api.routes.websocket import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PMDD Agentic Linguistic Analyzer API"
)

# Crucial for Next.js to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix="/ws")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
"""
}

def scaffold_phase6():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("Phase 6 Interactive Dashboard scaffolding complete.")

if __name__ == "__main__":
    scaffold_phase6()
