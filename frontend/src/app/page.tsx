"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ClinicianLayout from "./components/ClinicianLayout";
import { api } from "./api";
import { 
  Plus, 
  Search, 
  ChevronRight, 
  Heart, 
  Droplet,
  User,
  Users,
  Filter,
  Calendar,
  AlertTriangle,
  ClipboardList
} from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const [patients, setPatients] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPatients() {
      try {
        const data = await api.getPatients();
        setPatients(data);
      } catch (err) {
        console.error("Failed to load patients:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPatients();
  }, []);

  const filteredPatients = patients.filter((p) => {
    const fullName = `${p.first_name || ""} ${p.last_name || ""}`.toLowerCase();
    return fullName.includes(searchQuery.toLowerCase()) || 
      p.id.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const getGenderColor = (gender: string) => {
    switch (gender?.toLowerCase()) {
      case "male": return "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/30 border border-blue-200/20";
      case "female": return "text-pink-600 bg-pink-50 dark:text-pink-400 dark:bg-pink-950/30 border border-pink-200/20";
      default: return "text-slate-600 bg-slate-50 dark:text-slate-400 dark:bg-slate-900/30 border border-slate-200/20";
    }
  };

  // Vitals BP warning logic
  const getBPWarning = (sbp?: number, dbp?: number) => {
    if (!sbp || !dbp) return null;
    if (sbp >= 140 || dbp >= 90) return { label: "HTN Stage 2", color: "text-rose-600 bg-rose-50 dark:text-rose-450 dark:bg-rose-950/30" };
    if (sbp >= 130 || dbp >= 80) return { label: "HTN Stage 1", color: "text-amber-600 bg-amber-50 dark:text-amber-450 dark:bg-amber-950/30" };
    return null;
  };

  const calculateAverageAge = () => {
    if (!patients.length) return 0;
    const currentYear = new Date().getFullYear();
    const sum = patients.reduce((acc, p) => {
      const birthYear = new Date(p.date_of_birth).getFullYear();
      return acc + (currentYear - birthYear);
    }, 0);
    return Math.round(sum / patients.length);
  };

  return (
    <ClinicianLayout>
      <div className="space-y-8 animate-fade-in-up">
        {/* Header section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Clinician Console</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Select or create a patient digital twin to calculate composite risk and initiate AI debates.
            </p>
          </div>
          <Link
            href="/patients/new"
            className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm px-5 py-3 transition-all shadow-lg shadow-indigo-600/25 hover:-translate-y-0.5"
          >
            <Plus className="h-5 w-5" />
            Build Patient Twin
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 p-2.5">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Active Twins</p>
                <p className="text-2xl font-bold mt-1 text-slate-800 dark:text-slate-100">{patients.length}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-cyan-50 dark:bg-cyan-950/30 text-cyan-600 dark:text-cyan-400 p-2.5">
                <Calendar className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Average Age</p>
                <p className="text-2xl font-bold mt-1 text-slate-800 dark:text-slate-100">{calculateAverageAge()} y/o</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-rose-50 dark:bg-rose-950/30 text-rose-600 dark:text-rose-450 p-2.5">
                <Heart className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">Risk Alerts</p>
                <p className="text-2xl font-bold mt-1 text-rose-600 dark:text-rose-400">
                  {patients.filter(p => p.systolic_bp >= 140 || p.diastolic_bp >= 90).length} Elevated
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-450 p-2.5">
                <ClipboardList className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">MDT Reports</p>
                <p className="text-2xl font-bold mt-1 text-slate-800 dark:text-slate-100">
                  {patients.length > 0 ? "Ready" : "N/A"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Patients List Section */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden transition-colors duration-300">
          <div className="flex flex-col gap-4 border-b border-slate-200 dark:border-slate-800 p-6 sm:flex-row sm:items-center sm:justify-between bg-slate-50/50 dark:bg-slate-900/50">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Patient Twin Directory</h2>
            
            <div className="relative w-full sm:w-72">
              <Search className="absolute top-3 left-3 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search patient name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 pr-4 pl-9 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 outline-none transition-all focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="animate-pulse text-sm font-semibold text-slate-400">Loading directory...</div>
            </div>
          ) : filteredPatients.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center h-64">
              <User className="h-10 w-10 text-slate-350 dark:text-slate-600" />
              <h3 className="text-base font-bold text-slate-700 dark:text-slate-300 mt-2">No patients found</h3>
              <p className="text-slate-400 dark:text-slate-500 text-xs mt-1 max-w-xs">
                Create a patient digital twin to get started with machine learning risk analysis.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/30 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    <th className="py-4 px-6">Name</th>
                    <th className="py-4 px-6">Age / DOB</th>
                    <th className="py-4 px-6">Gender</th>
                    <th className="py-4 px-6">Blood Type</th>
                    <th className="py-4 px-6">Clinician Vitals</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredPatients.map((patient) => {
                    const age = new Date().getFullYear() - new Date(patient.date_of_birth).getFullYear();
                    const bpAlert = getBPWarning(patient.systolic_bp, patient.diastolic_bp);
                    return (
                      <tr 
                        key={patient.id} 
                        onClick={() => router.push(`/patients/${patient.id}`)}
                        className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 cursor-pointer transition-colors duration-150 group"
                      >
                        <td className="py-4 px-6 font-semibold text-slate-900 dark:text-slate-100">
                          {patient.first_name} {patient.last_name}
                        </td>
                        <td className="py-4 px-6 text-slate-500 dark:text-slate-400">
                          <span className="font-medium text-slate-850 dark:text-slate-250">{age} y/o</span>
                          <span className="block text-xs text-slate-400">{patient.date_of_birth}</span>
                        </td>
                        <td className="py-4 px-6">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${getGenderColor(patient.gender)}`}>
                            {patient.gender}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center gap-1 font-semibold text-slate-600 dark:text-slate-400">
                            <Droplet className="h-4 w-4 text-rose-500 shrink-0" />
                            {patient.blood_type?.toUpperCase() || "unknown"}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          {patient.systolic_bp ? (
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-slate-800 dark:text-slate-200">
                                {patient.systolic_bp}/{patient.diastolic_bp}
                              </span>
                              <span className="text-xs text-slate-400">mmHg</span>
                              {bpAlert && (
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold ${bpAlert.color}`}>
                                  {bpAlert.label}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400">No vitals added</span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <button className="inline-flex items-center justify-center rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            <ChevronRight className="h-5 w-5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </ClinicianLayout>
  );
}
