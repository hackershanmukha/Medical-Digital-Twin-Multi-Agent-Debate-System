"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import ClinicianLayout from "../../components/ClinicianLayout";
import { api } from "../../api";
import { 
  User, 
  Heart, 
  FlaskConical, 
  Activity, 
  Loader2, 
  ChevronRight,
  ChevronLeft,
  Check
} from "lucide-react";

export default function NewPatient() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Demographics
  const [firstName, setFirstName] = useState("John");
  const [lastName, setLastName] = useState("Doe");
  const [dob, setDob] = useState("1968-05-12");
  const [gender, setGender] = useState("male");
  const [bloodType, setBloodType] = useState("o_pos");
  const [ethnicity, setEthnicity] = useState("Caucasian");
  const [language, setLanguage] = useState("en");

  // Vitals
  const [systolicBp, setSystolicBp] = useState(135);
  const [diastolicBp, setDiastolicBp] = useState(85);
  const [heartRate, setHeartRate] = useState(76);
  const [heightCm, setHeightCm] = useState(178);
  const [weightKg, setWeightKg] = useState(88);

  // Clinical & Labs
  const [conditions, setConditions] = useState("Essential Hypertension\nPrediabetes");
  const [medications, setMedications] = useState("Metformin 500mg daily");
  const [allergies, setAllergies] = useState("Penicillin");
  const [glucose, setGlucose] = useState(105);
  const [hba1c, setHba1c] = useState(5.9);
  const [cholesterol, setCholesterol] = useState(210);
  const [ldl, setLdl] = useState(130);
  const [hdl, setHdl] = useState(42);
  const [triglycerides, setTriglycerides] = useState(160);

  // Lifestyle
  const [activityLevel, setActivityLevel] = useState("moderate");
  const [smokingStatus, setSmokingStatus] = useState("former");
  const [packYears, setPackYears] = useState(5.0);
  const [alcohol, setAlcohol] = useState("occasional");
  const [sleepHours, setSleepHours] = useState(7.0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // 1. Create Patient
      const patient = await api.createPatient({
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dob,
        gender,
        blood_type: bloodType,
        ethnicity,
        preferred_language: language,
      });

      const pId = patient.id;

      // 2. Add Vitals
      await api.addVitals(pId, {
        systolic_bp: Number(systolicBp),
        diastolic_bp: Number(diastolicBp),
        heart_rate: Number(heartRate),
        height_cm: Number(heightCm),
        weight_kg: Number(weightKg),
      });

      // 3. Add Conditions
      if (conditions.trim()) {
        const condLines = conditions.split("\n");
        for (const c of condLines) {
          if (c.trim()) {
            await api.addCondition(pId, {
              name: c.trim(),
              status: "active",
              severity: "moderate",
            });
          }
        }
      }

      // 4. Add Meds
      if (medications.trim()) {
        const medLines = medications.split("\n");
        for (const m of medLines) {
          if (m.trim()) {
            await api.addMedication(pId, {
              name: m.trim(),
              generic_name: m.trim().split(" ")[0].toLowerCase(),
              strength: m.trim().split(" ")[1] || "unknown",
              frequency: "once_daily",
              is_active: true,
              start_date: new Date().toISOString().split("T")[0],
            });
          }
        }
      }

      // 5. Add Allergies
      if (allergies.trim()) {
        const allergyLines = allergies.split("\n");
        for (const a of allergyLines) {
          if (a.trim()) {
            await api.addAllergy(pId, {
              allergen: a.trim(),
              allergen_type: "drug",
              severity: "moderate",
              reaction: "unknown",
            });
          }
        }
      }

      // 6. Add Labs
      await api.addLab(pId, {
        panel_name: "Metabolic Panel",
        test_name: "Fasting Glucose",
        value: Number(glucose),
        unit: "mg/dL",
        flag: glucose > 100 ? "H" : "N",
        collected_at: new Date().toISOString(),
      });

      await api.addLab(pId, {
        panel_name: "Glycemic Control",
        test_name: "HbA1c",
        value: Number(hba1c),
        unit: "%",
        flag: hba1c > 5.7 ? "H" : "N",
        collected_at: new Date().toISOString(),
      });

      await api.addLab(pId, {
        panel_name: "Lipid Panel",
        test_name: "Total Cholesterol",
        value: Number(cholesterol),
        unit: "mg/dL",
        flag: cholesterol > 200 ? "H" : "N",
        collected_at: new Date().toISOString(),
      });

      await api.addLab(pId, {
        panel_name: "Lipid Panel",
        test_name: "LDL",
        value: Number(ldl),
        unit: "mg/dL",
        flag: ldl > 100 ? "H" : "N",
        collected_at: new Date().toISOString(),
      });

      await api.addLab(pId, {
        panel_name: "Lipid Panel",
        test_name: "HDL",
        value: Number(hdl),
        unit: "mg/dL",
        flag: hdl < 40 ? "L" : "N",
        collected_at: new Date().toISOString(),
      });

      // Redirect to patient detail dashboard
      router.push(`/patients/${pId}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to create patient twin.");
      setLoading(false);
    }
  };

  const nextStep = () => setStep((s) => Math.min(s + 1, 4));
  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  return (
    <ClinicianLayout>
      <div className="max-w-3xl mx-auto space-y-8 animate-fade-in-up">
        {/* Step Indicator */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-5">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Build Patient Digital Twin</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Configure parameters for XGBoost and Clinical Debate engine.</p>
          </div>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={`h-2.5 w-8 rounded-full transition-all duration-300 ${
                  step === i 
                    ? "bg-indigo-600 dark:bg-indigo-500 w-12" 
                    : step > i 
                    ? "bg-indigo-300 dark:bg-indigo-800" 
                    : "bg-slate-200 dark:bg-slate-800"
                }`}
              ></div>
            ))}
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-3 rounded-lg bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 p-4 text-sm text-rose-600 dark:text-rose-400">
            <span className="font-semibold">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* STEP 1: DEMOGRAPHICS */}
          {step === 1 && (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-slate-100 dark:border-slate-850 pb-4">
                <User className="h-5 w-5 text-indigo-500" />
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">1. Demographics</h2>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">First Name</label>
                  <input
                    type="text"
                    required
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Last Name</label>
                  <input
                    type="text"
                    required
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Date of Birth</label>
                  <input
                    type="date"
                    required
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Blood Type</label>
                  <select
                    value={bloodType}
                    onChange={(e) => setBloodType(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  >
                    <option value="o_pos">O Positive</option>
                    <option value="o_neg">O Negative</option>
                    <option value="a_pos">A Positive</option>
                    <option value="a_neg">A Negative</option>
                    <option value="b_pos">B Positive</option>
                    <option value="b_neg">B Negative</option>
                    <option value="ab_pos">AB Positive</option>
                    <option value="ab_neg">AB Negative</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Ethnicity</label>
                  <input
                    type="text"
                    value={ethnicity}
                    onChange={(e) => setEthnicity(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: CLINICAL VITALS */}
          {step === 2 && (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-slate-100 dark:border-slate-850 pb-4">
                <Heart className="h-5 w-5 text-indigo-500" />
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">2. Clinical Vitals</h2>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Systolic BP (mmHg)</label>
                  <input
                    type="number"
                    required
                    value={systolicBp}
                    onChange={(e) => setSystolicBp(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Diastolic BP (mmHg)</label>
                  <input
                    type="number"
                    required
                    value={diastolicBp}
                    onChange={(e) => setDiastolicBp(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Heart Rate (bpm)</label>
                  <input
                    type="number"
                    required
                    value={heartRate}
                    onChange={(e) => setHeartRate(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Height (cm)</label>
                  <input
                    type="number"
                    required
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Weight (kg)</label>
                  <input
                    type="number"
                    required
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: CLINICAL HISTORY & LABS */}
          {step === 3 && (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-slate-100 dark:border-slate-850 pb-4">
                <FlaskConical className="h-5 w-5 text-indigo-500" />
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">3. Labs & Clinical History</h2>
              </div>
              
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 border-b border-slate-100 dark:border-slate-850 pb-6">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Fasting Glucose (mg/dL)</label>
                  <input
                    type="number"
                    required
                    value={glucose}
                    onChange={(e) => setGlucose(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">HbA1c (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={hba1c}
                    onChange={(e) => setHba1c(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Total Cholesterol (mg/dL)</label>
                  <input
                    type="number"
                    required
                    value={cholesterol}
                    onChange={(e) => setCholesterol(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">LDL Cholesterol (mg/dL)</label>
                  <input
                    type="number"
                    required
                    value={ldl}
                    onChange={(e) => setLdl(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">HDL Cholesterol (mg/dL)</label>
                  <input
                    type="number"
                    required
                    value={hdl}
                    onChange={(e) => setHdl(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Triglycerides (mg/dL)</label>
                  <input
                    type="number"
                    required
                    value={triglycerides}
                    onChange={(e) => setTriglycerides(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Active Medical Conditions (One per line)</label>
                  <textarea
                    value={conditions}
                    onChange={(e) => setConditions(e.target.value)}
                    rows={3}
                    placeholder="e.g. Essential Hypertension"
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Active Medications (One per line)</label>
                  <textarea
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    rows={3}
                    placeholder="e.g. Metformin 500mg daily"
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Known Allergies (One per line)</label>
                  <textarea
                    value={allergies}
                    onChange={(e) => setAllergies(e.target.value)}
                    rows={2}
                    placeholder="e.g. Penicillin"
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: LIFESTYLE */}
          {step === 4 && (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-slate-100 dark:border-slate-850 pb-4">
                <Activity className="h-5 w-5 text-indigo-500" />
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">4. Lifestyle Factors</h2>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Physical Activity</label>
                  <select
                    value={activityLevel}
                    onChange={(e) => setActivityLevel(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  >
                    <option value="sedentary">Sedentary (&lt;30m/week)</option>
                    <option value="light">Light Activity</option>
                    <option value="moderate">Moderate Activity</option>
                    <option value="active">High Activity</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Smoking Status</label>
                  <select
                    value={smokingStatus}
                    onChange={(e) => setSmokingStatus(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  >
                    <option value="never">Never Smoked</option>
                    <option value="former">Former Smoker</option>
                    <option value="current">Current Smoker</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Pack-Years (if applicable)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={packYears}
                    onChange={(e) => setPackYears(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Alcohol Intake</label>
                  <select
                    value={alcohol}
                    onChange={(e) => setAlcohol(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  >
                    <option value="none">None</option>
                    <option value="occasional">Occasional</option>
                    <option value="moderate">Moderate</option>
                    <option value="heavy">Heavy</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Average Sleep (Hours/Night)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={sleepHours}
                    onChange={(e) => setSleepHours(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-2.5 px-4 text-sm text-slate-900 dark:text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-800 pt-6">
            <button
              type="button"
              onClick={prevStep}
              disabled={step === 1 || loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all disabled:opacity-40"
            >
              <ChevronLeft className="h-5 w-5" />
              Back
            </button>

            {step < 4 ? (
              <button
                type="button"
                onClick={nextStep}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/10"
              >
                Next
                <ChevronRight className="h-5 w-5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-50 shadow-md shadow-indigo-600/10"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Assembling Digital Twin...
                  </>
                ) : (
                  <>
                    <Check className="h-5 w-5" />
                    Finalise Twin
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </ClinicianLayout>
  );
}
