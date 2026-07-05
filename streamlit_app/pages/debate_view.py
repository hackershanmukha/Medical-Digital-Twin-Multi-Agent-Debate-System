"""
Clinical Debate Page — Multi-agent AI specialist debate viewer.
"""
import streamlit as st
import time


AGENT_STYLES = {
    "Cardiology":        {"color": "#ef4444", "bg": "#fff5f5", "icon": "❤️"},
    "Endocrinology":     {"color": "#8b5cf6", "bg": "#faf5ff", "icon": "🧬"},
    "General Practice":  {"color": "#3b82f6", "bg": "#eff6ff", "icon": "👨‍⚕️"},
    "Moderator":         {"color": "#f59e0b", "bg": "#fffbeb", "icon": "⚖️"},
    "MDT Consensus":     {"color": "#f59e0b", "bg": "#fffbeb", "icon": "⚖️"},
}


def render():
    st.markdown("# 🗣️ Clinical Debate")
    st.markdown("*Multi-agent AI specialist debate powered by Gemini 2.5 Pro*")

    twin = st.session_state.get("patient_twin")
    risk = st.session_state.get("risk_results")
    debate = st.session_state.get("debate_result")

    if twin is None:
        st.warning("⚠️ Please build a patient profile first.")
        if st.button("👤 Go to Patient Profile"):
            st.session_state.page = "patient"
            st.rerun()
        return

    if risk is None:
        st.warning("⚠️ Please run the Risk Analysis first.")
        if st.button("📊 Go to Risk Analysis"):
            st.session_state.page = "risk"
            st.rerun()
        return

    # ── Control panel ────────────────────────────────────────────────────────
    if debate is None:
        _render_launch_panel(twin, risk)
    else:
        _render_debate_transcript(debate)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-run Debate", use_container_width=True):
                st.session_state.debate_result = None
                st.rerun()
        with col2:
            if st.button("📋 View Consensus Report →", type="primary", use_container_width=True):
                st.session_state.page = "report"
                st.rerun()


def _render_launch_panel(twin, risk):
    comp = risk.get("composite", {})

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a5f, #0d2137);
        border-radius: 16px;
        padding: 2rem;
        color: white;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color:#7dd3fc; margin:0;">Preparing Clinical Debate</h3>
        <p style="color:#94a3b8; margin:0.5rem 0 0;">
            Patient: <strong style="color:white;">{twin.demographics.full_name}</strong> · 
            Composite Risk: <strong style="color:#fbbf24;">{comp.get("risk_percentage", "?"):.1f}%</strong> 
            ({comp.get("risk_category", "?")})
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Agent lineup
    st.markdown("### 👥 Debate Panel")
    cols = st.columns(3)
    agents = [
        ("❤️", "Dr. Elena Vasquez", "Interventional Cardiologist",
         "Cardiovascular risk, lipids, hypertension, ASCVD"),
        ("🧬", "Dr. Priya Sharma", "Endocrinologist",
         "Diabetes, metabolic syndrome, HbA1c targets, GLP-1"),
        ("👨‍⚕️", "Dr. James Okafor", "General Practitioner",
         "Holistic care, multimorbidity, patient adherence"),
    ]
    colors = ["#ef4444", "#8b5cf6", "#3b82f6"]
    for col, (icon, name, title, focus), color in zip(cols, agents, colors):
        with col:
            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 1.25rem;
                border-top: 4px solid {color};
                box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                text-align: center;
            ">
                <div style="font-size:2.5rem;">{icon}</div>
                <div style="font-weight:600; color:#1e293b;">{name}</div>
                <div style="color:{color}; font-size:0.85rem; font-weight:500;">{title}</div>
                <div style="color:#64748b; font-size:0.78rem; margin-top:0.4rem;">{focus}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Debate settings
    with st.expander("⚙️ Debate Settings"):
        rounds = st.slider("Number of Debate Rounds", 1, 3, 3)
        st.info(
            "**Round 1:** Opening arguments (each specialist presents their case)  \n"
            "**Round 2:** Rebuttals (specialists respond to each other)  \n"
            "**Round 3:** Closing statements (final positions)  \n"
            "**Final:** Moderator synthesises consensus report"
        )

    # Launch button
    if st.button("🚀 Launch Clinical Debate", type="primary", use_container_width=True):
        _run_debate(twin, risk, rounds)


def _run_debate(twin, risk, rounds):
    """Run the debate with live progress."""
    from debate.engine import DebateEngine

    total_calls = rounds * 3 + 1  # 3 agents × rounds + moderator
    completed = 0

    status_placeholder = st.empty()
    progress_bar = st.progress(0, text="Initialising debate engine…")

    def update(msg):
        nonlocal completed
        completed += 1
        progress_bar.progress(
            min(1.0, completed / total_calls),
            text=msg,
        )
        status_placeholder.info(f"🔄 {msg}")

    try:
        engine = DebateEngine()

        # Patch with progress callbacks by running manually
        transcript = []

        round_labels = {1: "Opening Arguments", 2: "Rebuttals", 3: "Closing Statements"}
        patient_context = twin.to_summary_dict()
        rag_context = engine._retrieve_guidelines(twin, risk)

        # Round 1: Openings
        if rounds >= 1:
            update("Round 1: Cardiologist opening argument…")
            r1_cardio = engine.cardiologist.generate_opening_argument(patient_context, risk, rag_context)
            r1_cardio["round"] = 1
            transcript.append(r1_cardio)

            update("Round 1: Endocrinologist opening argument…")
            r1_endo = engine.endocrinologist.generate_opening_argument(patient_context, risk, rag_context)
            r1_endo["round"] = 1
            transcript.append(r1_endo)

            update("Round 1: GP opening argument…")
            r1_gp = engine.gp.generate_opening_argument(patient_context, risk, rag_context)
            r1_gp["round"] = 1
            transcript.append(r1_gp)

        # Round 2: Rebuttals
        if rounds >= 2:
            round1_entries = [e for e in transcript if e.get("round") == 1]

            update("Round 2: Cardiologist rebuttal…")
            r2_cardio = engine.cardiologist.generate_rebuttal(patient_context, risk, round1_entries, rag_context)
            r2_cardio["round"] = 2
            transcript.append(r2_cardio)

            update("Round 2: Endocrinologist rebuttal…")
            r2_endo = engine.endocrinologist.generate_rebuttal(patient_context, risk, round1_entries, rag_context)
            r2_endo["round"] = 2
            transcript.append(r2_endo)

            update("Round 2: GP rebuttal…")
            r2_gp = engine.gp.generate_rebuttal(patient_context, risk, round1_entries, rag_context)
            r2_gp["round"] = 2
            transcript.append(r2_gp)

        # Round 3: Closings
        if rounds >= 3:
            update("Round 3: Cardiologist closing statement…")
            r3_cardio = engine.cardiologist.generate_closing(patient_context, transcript)
            r3_cardio["round"] = 3
            transcript.append(r3_cardio)

            update("Round 3: Endocrinologist closing statement…")
            r3_endo = engine.endocrinologist.generate_closing(patient_context, transcript)
            r3_endo["round"] = 3
            transcript.append(r3_endo)

            update("Round 3: GP closing statement…")
            r3_gp = engine.gp.generate_closing(patient_context, transcript)
            r3_gp["round"] = 3
            transcript.append(r3_gp)

        # Moderator consensus
        update("⚖️ Moderator synthesising consensus report…")
        consensus = engine.moderator.generate_consensus_report(
            patient_context, risk, transcript, rag_context
        )
        consensus["round"] = rounds + 1

        progress_bar.progress(1.0, text="✅ Debate complete!")
        status_placeholder.success("✅ Clinical debate completed successfully!")
        time.sleep(0.5)
        progress_bar.empty()
        status_placeholder.empty()

        result = {
            "patient_id": twin.patient_id,
            "rounds_completed": rounds,
            "transcript": transcript,
            "consensus": consensus,
            "final_consensus_report": consensus.get("consensus_report", ""),
            "consensus_score": consensus.get("consensus_score", 0.75),
            "predicted_risk": risk.get("predicted_risk", 0.0),
            "explanation_attributions": risk.get("explanation_attributions", {}),
        }
        st.session_state.debate_result = result
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_placeholder.empty()
        st.error(f"❌ Debate failed: {e}")
        st.exception(e)


def _render_debate_transcript(debate):
    """Render the full debate transcript."""
    transcript = debate.get("transcript", [])
    consensus = debate.get("consensus", {})

    # Summary header
    n_rounds = debate.get("rounds_completed", 3)
    n_agents = len(set(e.get("agent") for e in transcript))
    consensus_score = debate.get("consensus_score", 0)

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #065f46, #064e3b);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
        display: flex;
        gap: 2rem;
        align-items: center;
    ">
        <div>
            <h3 style="color:#6ee7b7; margin:0;">✅ Debate Complete</h3>
            <p style="color:#a7f3d0; margin:0.25rem 0 0;">
                {n_rounds} rounds · {n_agents} specialist agents · 
                Consensus: <strong style="color:#fbbf24;">{int(consensus_score*100)}%</strong>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Group transcript by round
    rounds = {}
    for entry in transcript:
        r = entry.get("round", 1)
        rounds.setdefault(r, []).append(entry)

    round_labels = {
        1: "🎤 Round 1 — Opening Arguments",
        2: "💬 Round 2 — Rebuttals",
        3: "🏁 Round 3 — Closing Statements",
    }

    for round_num in sorted(rounds.keys()):
        st.markdown(f"### {round_labels.get(round_num, f'Round {round_num}')}")
        for entry in rounds[round_num]:
            _render_agent_entry(entry)

    # Moderator consensus
    if consensus:
        st.markdown("### ⚖️ Moderator Consensus Report")
        _render_agent_entry(consensus, is_consensus=True)


def _render_agent_entry(entry: dict, is_consensus: bool = False):
    agent = entry.get("agent", "Unknown")
    style = AGENT_STYLES.get(agent, {"color": "#6b7280", "bg": "#f9fafb", "icon": "🔬"})
    emoji = entry.get("emoji", style["icon"])
    confidence = entry.get("confidence", 70)
    priority = entry.get("priority_action", "")
    argument = entry.get("argument", "")
    round_type = entry.get("round_type", "")

    st.markdown(f"""
    <div style="
        background: {style["bg"]};
        border-radius: 12px;
        border-left: 5px solid {style["color"]};
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    ">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">
            <span style="font-size:1.5rem;">{emoji}</span>
            <div>
                <strong style="color:{style["color"]}; font-size:1rem;">{agent}</strong>
                <span style="color:#64748b; font-size:0.8rem; margin-left:0.5rem;">
                    {round_type.replace("_", " ").title()} · Confidence: {confidence}%
                </span>
            </div>
        </div>
        <div style="color:#1e293b; line-height:1.7; white-space:pre-wrap;">{argument[:2000]}</div>
        {f'<div style="margin-top:0.75rem; padding:0.5rem 0.75rem; background:rgba(0,0,0,0.04); border-radius:8px; font-size:0.85rem;"><strong>Priority Action:</strong> {priority}</div>' if priority and not is_consensus else ""}
    </div>
    """, unsafe_allow_html=True)
