"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ClinicianLayout from "../../components/ClinicianLayout";
import { api } from "../../api";
import { 
  User, 
  Activity, 
  Heart, 
  FlaskConical, 
  AlertCircle, 
  ShieldAlert, 
  MessageSquareHeart, 
  ArrowRight,
  TrendingUp,
  Scale,
  Calendar,
  AlertTriangle,
  Play,
  Loader2
} from "lucide-react";

export default function PatientDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [patient, setPatient] = useState<any>(null);
  const [vitals, setVitals] = useState<any[]>([]);
  const [conditions, setConditions] = useState<any[]>([]);
  const [medications, setMedications] = useState<any[]>([]);
  const [allergies, setAllergies] = useState<any[]>([]);
  const [labs, setLabs] = useState<any[]>([]);
  const [debates, setDebates] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [triggeringDebate, setTriggeringDebate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [pData, vData, cData, mData, aData, lData, dData] = await Promise.all([
          api.getPatient(id),
          api.getVitals(id),
          api.getConditions(id),
          api.getMedications(id),
          api.getAllergies(id),
          api.getLabs(id),
          api.getPatientDebates(id)
        ]);

        setPatient(pData);
        setVitals(vData);
        setConditions(cData);
        setMedications(mData);
        setAllergies(aData);
        setLabs(lData);
        setDebates(dData);
      } catch (err) {
        console.error("Failed to load patient twin:", err);
        setError("Error loading patient digital twin. Verify backend connection.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handleTriggerDebate = async () => {
    setTriggeringDebate(true);
    setError(null);
    try {
      await api.runDebate(id, 3);
      // Reload debates
      const freshDebates = await api.getPatientDebates(id);
      setDebates(freshDebates);
      router.push(`/patients/${id}/debate`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to trigger debate engine.");
      setTriggeringDebate(false);
    }
  };

  if (loading) {
    return (
      <ClinicianLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="animate-pulse text-sm font-semibold text-slate-400">Assembling twin profile...</div>
        </div>
      </ClinicianLayout>
    );
  }

  const age = patient ? new Date().getFullYear() - new Date(patient.date_of_birth).getFullYear() : 0;
  const latestVitals = vitals[0] || {};
  const latestDebate = debates[0];

  // Helper for risk categorisation
  const getRiskCategory = (risk: number) => {
    const pct = risk * 100;
    if (pct < 10) return { label: "Low Risk", color: "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30 border border-emerald-250/20" };
    if (pct < 20) return { label: "Moderate Risk", color: "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30 border border-amber-250/20" };
    if (pct < 30) return { label: "High Risk", color: "text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950/30 border border-rose-250/20" };
    return { label: "Very High Risk", color: "text-pink-600 bg-pink-50 dark:text-pink-400 dark:bg-pink-950/30 border border-pink-250/20" };
  };

  return (
    <ClinicianLayout>
      <div className="space-y-8 animate-fade-in-up">
        {/* Patient Header Panel */}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between border-b border-slate-200 dark:border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 border border-indigo-200/25">
              <User className="h-7 w-7" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
                {patient?.first_name} {patient?.last_name}
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1">
                {age} y/o · {patient?.gender} · Blood Type: {patient?.blood_type?.toUpperCase()}
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            {latestDebate ? (
              <Link
                href={`/patients/${id}/debate`}
                className="flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm px-5 py-3 transition-all shadow-lg shadow-emerald-600/25 hover:-translate-y-0.5"
              >
                <MessageSquareHeart className="h-5 w-5" />
                View MDT Debate
              </Link>
            ) : (
              <button
                onClick={handleTriggerDebate}
                disabled={triggeringDebate}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm px-5 py-3 transition-all disabled:opacity-60 shadow-lg shadow-indigo-600/25 hover:-translate-y-0.5"
              >
                {triggeringDebate ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Triggering Engine...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 fill-current" />
                    Trigger MDT Debate
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-3 rounded-lg bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 p-4 text-sm text-rose-600 dark:text-rose-450">
            <AlertCircle className="h-5 w-5 text-rose-500 shrink-0" />
            <span className="font-semibold">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* DIGITAL TWIN DEMOGRAPHICS & VITALS PANEL */}
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
              <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-6">
                <Activity className="h-5 w-5 text-indigo-500" />
                Clinician Vital Signs
              </h2>
              {latestVitals.systolic_bp ? (
                <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
                  <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-900">
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Blood Pressure</p>
                    <p className="text-xl font-bold mt-1 text-slate-800 dark:text-slate-100">
                      {latestVitals.systolic_bp}/{latestVitals.diastolic_bp}
                    </p>
                    <span className="text-[10px] text-slate-400">mmHg</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-900">
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Heart Rate</p>
                    <p className="text-xl font-bold mt-1 text-slate-800 dark:text-slate-100">{latestVitals.heart_rate}</p>
                    <span className="text-[10px] text-slate-400">bpm</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-900">
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">BMI</p>
                    <p className="text-xl font-bold mt-1 text-slate-800 dark:text-slate-100">
                      {latestVitals.weight_kg && latestVitals.height_cm 
                        ? (latestVitals.weight_kg / Math.pow(latestVitals.height_cm / 100, 2)).toFixed(1)
                        : "N/A"
                      }
                    </p>
                    <span className="text-[10px] text-slate-400">kg/m²</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-900">
                    <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Oxygen Sat.</p>
                    <p className="text-xl font-bold mt-1 text-slate-800 dark:text-slate-100">
                      {latestVitals.oxygen_saturation || "N/A"}
                    </p>
                    <span className="text-[10px] text-slate-400">% SpO₂</span>
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-sm">No vital signs uploaded.</div>
              )}
            </div>

            {/* CLINICAL DATA (CONDITIONS, MEDS, LABS) */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-rose-500" />
                  Conditions & Allergies
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider mb-2">Diagnoses</h4>
                    {conditions.length === 0 ? (
                      <p className="text-sm text-slate-400">No active conditions.</p>
                    ) : (
                      <ul className="space-y-1.5">
                        {conditions.map((c) => (
                          <li key={c.id} className="text-sm font-semibold flex items-center gap-2 text-slate-700 dark:text-slate-350">
                            <span className="h-1.5 w-1.5 rounded-full bg-rose-500"></span>
                            {c.name}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-850">
                    <h4 className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider mb-2">Allergies</h4>
                    {allergies.length === 0 ? (
                      <p className="text-sm text-slate-400">No known allergies.</p>
                    ) : (
                      <ul className="space-y-1.5">
                        {allergies.map((a) => (
                          <li key={a.id} className="text-sm font-semibold flex items-center gap-2 text-slate-700 dark:text-slate-350">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                            {a.allergen} ({a.reaction || "allergen"})
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
                  <FlaskConical className="h-5 w-5 text-indigo-500" />
                  Active Medications & Labs
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider mb-2">Prescriptions</h4>
                    {medications.length === 0 ? (
                      <p className="text-sm text-slate-400">No active medications.</p>
                    ) : (
                      <ul className="space-y-1.5">
                        {medications.map((m) => (
                          <li key={m.id} className="text-sm font-semibold flex items-center gap-2 text-slate-700 dark:text-slate-350">
                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500"></span>
                            {m.name} {m.strength}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-850">
                    <h4 className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider mb-2">Latest Labs</h4>
                    {labs.length === 0 ? (
                      <p className="text-sm text-slate-400">No labs recorded.</p>
                    ) : (
                      <div className="grid grid-cols-2 gap-2">
                        {labs.slice(0, 4).map((l) => (
                          <div key={l.id} className="text-xs bg-slate-50 dark:bg-slate-950 p-2 rounded-lg border border-slate-100 dark:border-slate-900/50">
                            <span className="text-slate-400 block font-medium truncate">{l.test_name}</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{l.value} {l.unit}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RISK CLUSTERING & CALCULATIONS PANEL */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
              <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-indigo-500" />
                XGBoost Risk Score
              </h2>

              {latestDebate ? (
                <div className="space-y-6">
                  {/* Gauge Display */}
                  <div className="flex flex-col items-center">
                    <div className="relative flex items-center justify-center">
                      {/* Simple SVG Ring Gauge */}
                      <svg className="w-36 h-36">
                        <circle
                          cx="72"
                          cy="72"
                          r="60"
                          stroke="#e2e8f0"
                          strokeWidth="10"
                          fill="transparent"
                          className="dark:stroke-slate-800"
                        />
                        <circle
                          cx="72"
                          cy="72"
                          r="60"
                          stroke="#4f46e5"
                          strokeWidth="10"
                          fill="transparent"
                          strokeDasharray="377"
                          strokeDashoffset={377 - (377 * latestDebate.predicted_risk)}
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute text-center">
                        <span className="text-3xl font-extrabold text-slate-800 dark:text-white">
                          {(latestDebate.predicted_risk * 100).toFixed(1)}%
                        </span>
                        <span className="block text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Composite</span>
                      </div>
                    </div>
                    
                    <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mt-4 ${getRiskCategory(latestDebate.predicted_risk).color}`}>
                      {getRiskCategory(latestDebate.predicted_risk).label}
                    </span>
                  </div>

                  {/* SHAP Attributions Bar Chart */}
                  {latestDebate.explanation_attributions && (
                    <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-850">
                      <h3 className="text-xs text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">Top Risk Factors (SHAP)</h3>
                      <div className="space-y-2">
                        {Object.entries(latestDebate.explanation_attributions)
                          .map(([key, val]: [string, any]) => ({ key, val }))
                          .sort((a, b) => Math.abs(b.val) - Math.abs(a.val))
                          .slice(0, 4)
                          .map((attr) => {
                            const absVal = Math.min(1, Math.abs(attr.val) * 8); // Scale for visual representation
                            const isPositive = attr.val >= 0;
                            return (
                              <div key={attr.key} className="space-y-1">
                                <div className="flex justify-between text-xs font-semibold">
                                  <span className="capitalize text-slate-600 dark:text-slate-400">{attr.key.replace(/_/g, " ")}</span>
                                  <span className={isPositive ? "text-rose-500" : "text-emerald-500"}>
                                    {isPositive ? "+" : ""}{attr.val.toFixed(4)}
                                  </span>
                                </div>
                                <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${isPositive ? "bg-rose-500" : "bg-emerald-500"}`}
                                    style={{ width: `${absVal * 100}%` }}
                                  ></div>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  <Link
                    href={`/patients/${id}/debate`}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-100 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 hover:bg-slate-200 dark:hover:bg-slate-800 py-3 text-sm font-bold text-slate-700 dark:text-slate-200 transition-colors"
                  >
                    View MDT Debate Transcript
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              ) : (
                <div className="text-center py-6">
                  <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto" />
                  <p className="text-slate-700 dark:text-slate-300 font-bold mt-2">No Risk Profile Calculated</p>
                  <p className="text-slate-400 dark:text-slate-500 text-xs mt-1 max-w-xs mx-auto">
                    Trigger the clinical debate engine to calculate patient risk scores.
                  </p>
                  <button
                    onClick={handleTriggerDebate}
                    disabled={triggeringDebate}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm py-3 mt-5 transition-all disabled:opacity-60"
                  >
                    {triggeringDebate ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      "Start Debate & Assessment"
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ClinicianLayout>
  );
}
