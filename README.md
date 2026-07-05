# MedTwin AI: Clinical Digital Twin & Multi-Agent Debate System

MedTwin AI is an advanced clinical decision support system designed to build patient digital twins, perform clinical risk predictions, and simulate multi-agent debates between clinical specialists (e.g., General Practitioner, Cardiologist, Endocrinologist) to arrive at a treatment consensus.

This system is built using the **Google Agent Development Kit (ADK)**, **Gemini Models**, **FastAPI**, **Next.js**, and the **Model Context Protocol (MCP)**.

---

## 🚀 Quick Start & Installation

To run this project on a new laptop, you must set up both the **Backend** and the **Frontend** servers.

### 📋 Prerequisites
Make sure you have the following installed:
* **Python 3.10+**
* **Node.js 18+** & **npm**

---

## 🛠️ Step 1: Backend Setup

1. **Clone the repository** (if not already done) and navigate to the project directory:
   ```bash
   cd Medical-Digital-Twin-Multi-Agent-Debate-System
   ```

2. **Create and Activate a Virtual Environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   * Copy the template `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   * Open the `.env` file and insert your **Google API Key**:
     ```env
     GOOGLE_API_KEY=your_actual_gemini_api_key_here
     GOOGLE_MODEL=gemini-2.5-pro
     ```
     > [!IMPORTANT]
     > The backend will not be able to generate debate transcripts or run Gemini models without a valid `GOOGLE_API_KEY`.

5. **Start the FastAPI Backend Server**:
   Launch the API server using Uvicorn:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
   * The API docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
   * **Note**: On startup, SQLite databases will be initialized automatically in the `data/` directory.

---

## 💻 Step 2: Frontend Setup (Next.js)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Configure Environment Variables (Optional)**:
   By default, the frontend requests `http://127.0.0.1:8000/api/v1`. If you run your backend on a different port or host, create a `.env.local` file inside the `frontend/` directory and configure:
   ```env
   NEXT_PUBLIC_API_BASE=http://your-custom-backend-ip:8000/api/v1
   ```

4. **Run the Next.js Development Server**:
   ```bash
   npm run dev
   ```
   * Access the clinician UI dashboard at [http://localhost:3000](http://localhost:3000).

---

## 🔌 Step 3: MCP Servers (Model Context Protocol)

The debate engine uses 3 standalone MCP servers for clinical data retrieval and guidelines validation. They operate in **stdio** mode and are launched dynamically by the backend `MCPClient` on a per-call basis.

To test that all MCP servers and their underlying tools work correctly, run the smoke-test suite from the root directory:
```bash
python start_mcp_servers.py --test
```

---

## 🔍 Troubleshooting "Failed to Get Request" Errors

If the frontend displays errors when loading patient profiles or running debates:

1. **Ensure the Backend Server is running**: Check that the Uvicorn command in Step 1 is active on port `8000`.
2. **Verify your `.env` file exists**: When you clone a repo, `.env` is gitignored. Ensure you have copied `.env.example` to `.env` in the root folder and configured your `GOOGLE_API_KEY`.
3. **CORS / Host Misalignment**: If you run the frontend and backend on different laptops or environments, configure the `NEXT_PUBLIC_API_BASE` in `frontend/.env.local` to point to the backend's IP address.
4. **Database Check**: If the backend starts up but crashes immediately, make sure the default `DATABASE_URL` in `backend/app/core/config.py` is set to SQLite (`sqlite+aiosqlite:///./data/medical_ai.db`), which runs without requiring a PostgreSQL service setup.
