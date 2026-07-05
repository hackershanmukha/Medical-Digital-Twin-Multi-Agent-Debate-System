/**
 * MedTwin AI - Clinician Frontend API Client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/v1";

// Client-side helper for token management
export const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("medtwin_token");
  }
  return null;
};

export const setAuthToken = (token: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("medtwin_token", token);
  }
};

export const clearAuthToken = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("medtwin_token");
  }
};

const getHeaders = (isMultipart = false) => {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

async function handleResponse(response: Response) {
  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail.map((err: any) => err.msg || JSON.stringify(err)).join(", ");
        } else if (typeof errJson.detail === "object") {
          errorDetail = JSON.stringify(errJson.detail);
        } else {
          errorDetail = String(errJson.detail);
        }
      } else {
        errorDetail = JSON.stringify(errJson);
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  // Authentication
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData,
    });
    const data = await handleResponse(res);
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },

  async register(email: string, password: string, role = "clinician") {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ email, password, role }),
    });
    return handleResponse(res);
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Patients (Digital Twins)
  async getPatients() {
    const res = await fetch(`${API_BASE}/patients/`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async getPatient(id: string) {
    const res = await fetch(`${API_BASE}/patients/${id}`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async createPatient(patientData: any) {
    const res = await fetch(`${API_BASE}/patients/`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(patientData),
    });
    return handleResponse(res);
  },

  async updatePatient(id: string, patientData: any) {
    const res = await fetch(`${API_BASE}/patients/${id}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(patientData),
    });
    return handleResponse(res);
  },

  async deletePatient(id: string) {
    const res = await fetch(`${API_BASE}/patients/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Vitals
  async getVitals(patientId: string) {
    const res = await fetch(`${API_BASE}/vitals/${patientId}/history`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async addVitals(patientId: string, vitalsData: any) {
    const res = await fetch(`${API_BASE}/vitals/`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, ...vitalsData }),
    });
    return handleResponse(res);
  },

  // Conditions
  async getConditions(patientId: string) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/conditions`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async addCondition(patientId: string, conditionData: any) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/conditions`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, ...conditionData }),
    });
    return handleResponse(res);
  },

  // Allergies
  async getAllergies(patientId: string) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/allergies`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async addAllergy(patientId: string, allergyData: any) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/allergies`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, ...allergyData }),
    });
    return handleResponse(res);
  },

  // Medications
  async getMedications(patientId: string) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/medications`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async addMedication(patientId: string, medData: any) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/medications`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, ...medData }),
    });
    return handleResponse(res);
  },

  // Labs
  async getLabs(patientId: string) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/labs`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async addLab(patientId: string, labData: any) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/labs`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, ...labData }),
    });
    return handleResponse(res);
  },

  // Debate Engine
  async runDebate(patientId: string, maxRounds = 3) {
    const res = await fetch(`${API_BASE}/debate/run`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ patient_id: patientId, max_rounds: maxRounds }),
    });
    return handleResponse(res);
  },

  async getPatientDebates(patientId: string) {
    const res = await fetch(`${API_BASE}/debate/patient/${patientId}`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },
};
