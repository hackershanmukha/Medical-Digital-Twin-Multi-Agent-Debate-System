"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ClinicianLayout from "../../../components/ClinicianLayout";
import { api } from "../../../api";
import { 
  ArrowLeft, 
  MessageSquare, 
  Download, 
  FileJson, 
  FileText, 
  CheckCircle, 
  Activity, 
  Scale, 
  TrendingUp,
  Award,
  ChevronDown,
  Sparkles
} from "lucide-react";

const AGENT_META: Record<string, { name: string; title: string; color: string; border: string; bg: string; emoji: string }> = {
  "Cardiology": { 
    name: "Dr. Elena Vasquez", 
    title: "Preventive Cardiologist", 
    color: "text-rose-600 dark:text-rose-400", 
    border: "border-rose-200 dark:border-rose-900/50",
    bg: "bg-rose-50/50 dark:bg-rose-950/20",
    emoji: "❤️"
  },
  "Endocrinology": { 
    name: "Dr. Priya Sharma", 
    title: "Metabolic Specialist", 
    color: "text-violet-600 dark:text-violet-400", 
    border: "border-violet-200 dark:border-violet-900/50",
    bg: "bg-violet-50/50 dark:bg-violet-950/20",
    emoji: "🧬"
  },
  "General Practice": { 
    name: "Dr. James Okafor", 
    title: "Senior Primary Care GP", 
    color: "text-blue-600 dark:text-blue-400", 
    border: "border-blue-200 dark:border-blue-900/50",
    bg: "bg-blue-50/50 dark:bg-blue-950/20",
    emoji: "👨‍⚕️"
  },
  "Moderator": { 
    name: "Dr. Sarah Chen", 
    title: "MDT Chairperson", 
    color: "text-amber-600 dark:text-amber-400", 
    border: "border-amber-250 dark:border-amber-900/50",
    bg: "bg-amber-50/50 dark:bg-amber-950/20",
    emoji: "⚖️"
  },
  "MDT Consensus": { 
    name: "MDT Consensus Report", 
    title: "Integrated Care Protocol", 
    color: "text-emerald-600 dark:text-emerald-400", 
    border: "border-emerald-200 dark:border-emerald-900/50",
    bg: "bg-emerald-50/50 dark:bg-emerald-950/20",
    emoji: "⚖️"
  }
};

export default function PatientDebate({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  
  const [patient, setPatient] = useState<any>(null);
  const [debates, setDebates] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"transcript" | "consensus">("consensus");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [pData, dData] = await Promise.all([
          api.getPatient(id),
          api.getPatientDebates(id)
        ]);
        setPatient(pData);
        setDebates(dData);
      } catch (err) {
        console.error("Failed to load debate history:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <ClinicianLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="animate-pulse text-sm font-semibold text-slate-400">Loading debate transcripts...</div>
        </div>
      </ClinicianLayout>
    );
  }

  const latestDebate = debates[0];
  const transcript = latestDebate?.debate_transcript || [];
  const consensusReport = latestDebate?.final_consensus_report || "";

  // Group transcripts by round
  const rounds: Record<number, any[]> = {};
  transcript.forEach((msg: any) => {
    const r = msg.round || 1;
    if (!rounds[r]) rounds[r] = [];
    rounds[r].push(msg);
  });

  const getRoundLabel = (r: number) => {
    switch (Number(r)) {
      case 1: return "Round 1: Specialty Risk Stratification";
      case 2: return "Round 2: Specialist Rebuttal & Cross-Examination";
      case 3: return "Round 3: Definitive Closing Arguments";
      default: return `Round ${r}`;
    }
  };

  // Export handlers
  const downloadMarkdown = () => {
    if (!latestDebate) return;
    const content = `# MDT Clinical Consensus Report\n\nPatient: ${patient?.first_name} ${patient?.last_name}\nAge/DOB: ${patient?.date_of_birth}\nCVD/Diabetes Composite Risk: ${(latestDebate.predicted_risk * 100).toFixed(1)}%\n\n${consensusReport}`;
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `mdt_consensus_${id}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadJSON = () => {
    if (!latestDebate) return;
    const content = JSON.stringify({
      patient,
      predicted_risk: latestDebate.predicted_risk,
      explanation_attributions: latestDebate.explanation_attributions,
      debate_transcript: transcript,
      final_consensus_report: consensusReport,
      created_at: latestDebate.created_at,
    }, null, 2);
    const blob = new Blob([content], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `mdt_debate_${id}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <ClinicianLayout>
      <div className="space-y-8 animate-fade-in-up">
        {/* Header Navigation */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <Link
              href={`/patients/${id}`}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-all shadow-sm"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">MDT Debate Panel</h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1">
                Consultation Case: <span className="font-semibold text-slate-850 dark:text-slate-200">{patient?.first_name} {patient?.last_name}</span>
              </p>
            </div>
          </div>

          {latestDebate && (
            <div className="flex items-center gap-3">
              <button
                onClick={downloadMarkdown}
                className="flex items-center justify-center gap-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850 text-slate-700 dark:text-slate-350 font-bold text-xs px-4.5 py-2.5 transition-all shadow-sm"
              >
                <FileText className="h-4.5 w-4.5 text-indigo-500" />
                Export Markdown
              </button>
              <button
                onClick={downloadJSON}
                className="flex items-center justify-center gap-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850 text-slate-700 dark:text-slate-350 font-bold text-xs px-4.5 py-2.5 transition-all shadow-sm"
              >
                <FileJson className="h-4.5 w-4.5 text-indigo-500" />
                Export JSON
              </button>
            </div>
          )}
        </div>

        {!latestDebate ? (
          <div className="flex flex-col items-center justify-center p-12 text-center border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 h-96">
            <MessageSquare className="h-12 w-12 text-slate-300 dark:text-slate-650" />
            <h3 className="text-lg font-bold mt-3 text-slate-700 dark:text-slate-300">No debates executed</h3>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 max-w-xs">
              Go back to the patient profile to initiate the multi-agent clinical consultation debate.
            </p>
            <Link
              href={`/patients/${id}`}
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-3 transition-all"
            >
              Go to Profile
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* View Selector Tab */}
            <div className="flex border-b border-slate-250 dark:border-slate-800 gap-6">
              <button
                onClick={() => setActiveTab("consensus")}
                className={`pb-3 text-sm font-bold border-b-2 transition-all ${
                  activeTab === "consensus"
                    ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                    : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                MDT Consensus Report
              </button>
              <button
                onClick={() => setActiveTab("transcript")}
                className={`pb-3 text-sm font-bold border-b-2 transition-all ${
                  activeTab === "transcript"
                    ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                    : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                Debate Transcript ({transcript.length} turns)
              </button>
            </div>

            {/* TAB CONTENT: CONSENSUS */}
            {activeTab === "consensus" && (
              <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 items-start">
                <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 shadow-sm space-y-6 max-h-[800px] overflow-y-auto">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-850 pb-4">
                    <div className="flex items-center gap-2">
                      <Award className="h-6 w-6 text-emerald-500" />
                      <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Chairperson Consensus</h2>
                    </div>
                    <span className="inline-flex px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200/20">
                      Approved Protocol
                    </span>
                  </div>

                  <div className="prose dark:prose-invert prose-indigo max-w-none text-slate-700 dark:text-slate-300 text-sm leading-8 whitespace-pre-wrap">
                    {consensusReport}
                  </div>
                </div>

                <div className="space-y-6">
                  {/* Case Summary */}
                  <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                    <h3 className="text-sm font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-4">Case Summary</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-slate-500">MDT Consensus</span>
                        <span className="text-emerald-600 dark:text-emerald-450">High Agreement</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-slate-500">Composite Risk</span>
                        <span className="text-slate-800 dark:text-white">{(latestDebate.predicted_risk * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-slate-500">Debate Rounds</span>
                        <span className="text-slate-800 dark:text-white">3 Complete</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-semibold">
                        <span className="text-slate-500">Panelists</span>
                        <span className="text-slate-800 dark:text-white">3 Specialists</span>
                      </div>
                    </div>
                  </div>

                  {/* Panelist Profiles */}
                  <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">Debating Panelists</h3>
                    
                    {Object.entries(AGENT_META).slice(0, 3).map(([key, meta]) => (
                      <div key={key} className={`flex items-center gap-3 p-3 rounded-xl border ${meta.border} ${meta.bg}`}>
                        <span className="text-2xl">{meta.emoji}</span>
                        <div>
                          <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{meta.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{meta.title}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: DEBATE TRANSCRIPT */}
            {activeTab === "transcript" && (
              <div className="space-y-8 max-w-4xl mx-auto">
                {Object.entries(rounds).sort((a, b) => Number(a[0]) - Number(b[0])).map(([roundNum, messages]) => (
                  <div key={roundNum} className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-indigo-500 animate-pulse" />
                      <h3 className="text-md font-extrabold text-slate-850 dark:text-slate-200 bg-indigo-50 dark:bg-indigo-950/20 px-3 py-1.5 rounded-lg border border-indigo-200/20">
                        {getRoundLabel(Number(roundNum))}
                      </h3>
                    </div>

                    <div className="space-y-6 pl-4 border-l-2 border-indigo-200 dark:border-indigo-900/50">
                      {messages.map((msg: any, idx: number) => {
                        const specialty = msg.agent || "General";
                        const meta = AGENT_META[specialty] || {
                          name: specialty,
                          title: "Clinical Specialist",
                          color: "text-slate-600 dark:text-slate-400",
                          border: "border-slate-200 dark:border-slate-800",
                          bg: "bg-slate-50/50 dark:bg-slate-900/50",
                          emoji: "🔬"
                        };

                        return (
                          <div 
                            key={idx} 
                            className={`rounded-2xl border ${meta.border} ${meta.bg} p-6 shadow-sm space-y-4 animate-slide-in-left`}
                            style={{ animationDelay: `${idx * 0.1}s` }}
                          >
                            {/* Panelist Header */}
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/40 dark:border-slate-800/40 pb-3">
                              <div className="flex items-center gap-3">
                                <span className="text-2xl">{meta.emoji}</span>
                                <div>
                                  <span className={`text-sm font-bold ${meta.color}`}>{meta.name}</span>
                                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider ml-2.5">
                                    {meta.title}
                                  </span>
                                </div>
                              </div>
                              
                              {msg.confidence !== undefined && (
                                <div className="flex items-center gap-2 bg-white dark:bg-slate-950 px-2.5 py-1 rounded-full border border-slate-200/50 dark:border-slate-850/50 text-xs font-semibold">
                                  <span className="text-slate-400">Confidence:</span>
                                  <span className="text-indigo-600 dark:text-indigo-400">{msg.confidence}%</span>
                                </div>
                              )}
                            </div>

                            {/* Argument Content */}
                            <p className="text-sm leading-8 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                              {msg.argument || msg.content}
                            </p>

                            {/* Priority Action Badge */}
                            {msg.priority_action && (
                              <div className="inline-flex items-center gap-1.5 bg-slate-100 dark:bg-slate-950/50 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 border border-slate-200/30">
                                <span className="font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">Priority Recommendation:</span>
                                {msg.priority_action}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </ClinicianLayout>
  );
}
