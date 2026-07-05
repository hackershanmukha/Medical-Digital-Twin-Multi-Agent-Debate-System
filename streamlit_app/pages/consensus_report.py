"""
Consensus Report Page — Final MDT consensus with export.
"""
import streamlit as st
from datetime import datetime


def render():
    st.markdown("# 📋 MDT Consensus Report")
    st.markdown("*AI-synthesised multi-disciplinary clinical consensus*")

    twin = st.session_state.get("patient_twin")
    risk = st.session_state.get("risk_results")
    debate = st.session_state.get("debate_result")

    if debate is None:
        st.warning("⚠️ No debate completed. Please run the clinical debate first.")
        if st.button("🗣️ Go to Clinical Debate"):
            st.session_state.page = "debate"
            st.rerun()
        return

    consensus = debate.get("consensus", {})
    report_text = debate.get("final_consensus_report", "")
    consensus_score = debate.get("consensus_score", 0.75)

    # ── Header card ───────────────────────────────────────────────────────────
    patient_name = twin.demographics.full_name if twin else "Patient"
    comp = risk.get("composite", {}) if risk else {}

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e1b4b, #312e81, #4338ca);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(67,56,202,0.3);
    ">
        <div style="display:flex; justify-content:space-between; align-items:start; flex-wrap:wrap; gap:1rem;">
            <div>
                <h2 style="color:#c7d2fe; margin:0; font-size:1.1rem; font-weight:500;">
                    MULTI-DISCIPLINARY TEAM CONSENSUS
                </h2>
                <h1 style="color:white; margin:0.3rem 0; font-size:1.8rem;">
                    {patient_name}
                </h1>
                <p style="color:#a5b4fc; margin:0;">
                    Generated: {datetime.now().strftime("%d %B %Y, %H:%M")} · 
                    Rounds: {debate.get("rounds_completed", 3)} · 
                    Agents: 3 specialists + moderator
                </p>
            </div>
            <div style="text-align:center; background:rgba(255,255,255,0.1); 
                        border-radius:12px; padding:1rem 1.5rem;">
                <div style="font-size:2.5rem; font-weight:700; color:{'#fbbf24' if consensus_score < 0.8 else '#34d399'};">
                    {int(consensus_score * 100)}%
                </div>
                <div style="color:#a5b4fc; font-size:0.85rem;">Consensus Score</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Risk summary ──────────────────────────────────────────────────────────
    if risk:
        st.markdown("### 🎯 Risk Summary")
        col1, col2, col3, col4 = st.columns(4)
        cv = risk.get("cardiovascular", {})
        dm = risk.get("diabetes", {})

        with col1:
            st.metric("Composite Risk", f"{comp.get('risk_percentage', 0):.1f}%",
                      delta=comp.get("risk_category", "").replace("_", " "))
        with col2:
            st.metric("Cardiovascular", f"{cv.get('risk_percentage', 0):.1f}%",
                      delta=cv.get("risk_category", "").replace("_", " "))
        with col3:
            st.metric("Diabetes", f"{dm.get('risk_percentage', 0):.1f}%",
                      delta=dm.get("risk_category", "").replace("_", " "))
        with col4:
            top_factor = risk.get("top_risk_factors", [{}])[0]
            st.metric("Top Risk Factor",
                      top_factor.get("feature", "N/A").replace("_", " ").title(),
                      delta=f"contribution: {top_factor.get('contribution', 0):.3f}")

    # ── Full consensus report ─────────────────────────────────────────────────
    st.markdown("### 📄 Full MDT Consensus Report")
    st.markdown("""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        line-height: 1.8;
    ">
    """, unsafe_allow_html=True)
    st.markdown(report_text)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Debate statistics ─────────────────────────────────────────────────────
    transcript = debate.get("transcript", [])
    if transcript:
        st.markdown("### 📊 Debate Statistics")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Specialist Confidence by Round**")
            for entry in transcript:
                agent = entry.get("agent", "?")
                confidence = entry.get("confidence", 70)
                round_n = entry.get("round", 1)
                icon = {"Cardiology": "❤️", "Endocrinology": "🧬", "General Practice": "👨‍⚕️"}.get(agent, "🔬")
                st.progress(confidence / 100, text=f"{icon} R{round_n} {agent}: {confidence}%")

        with col2:
            try:
                import plotly.graph_objects as go

                agents = list(set(e.get("agent") for e in transcript))
                rounds_data = {}
                for entry in transcript:
                    a = entry.get("agent")
                    r = entry.get("round", 1)
                    rounds_data.setdefault(a, {})[r] = entry.get("confidence", 70)

                fig = go.Figure()
                colors = {"Cardiology": "#ef4444", "Endocrinology": "#8b5cf6", "General Practice": "#3b82f6"}
                for agent, rdata in rounds_data.items():
                    xs = sorted(rdata.keys())
                    ys = [rdata[r] for r in xs]
                    fig.add_trace(go.Scatter(
                        x=xs, y=ys, mode="lines+markers",
                        name=agent,
                        line=dict(color=colors.get(agent, "#6b7280"), width=2),
                        marker=dict(size=8),
                    ))
                fig.update_layout(
                    title="Confidence Trajectory Across Rounds",
                    xaxis_title="Round",
                    yaxis_title="Confidence (%)",
                    yaxis=dict(range=[0, 105]),
                    xaxis=dict(tickvals=[1, 2, 3]),
                    height=300,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(family="Inter", size=11),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 💾 Export Report")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as markdown
        full_report = _format_full_report(twin, risk, debate)
        st.download_button(
            "📄 Download as Markdown",
            data=full_report,
            file_name=f"MDT_Report_{patient_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        # Download transcript as JSON
        import json
        transcript_json = json.dumps({
            "patient": patient_name,
            "generated_at": datetime.now().isoformat(),
            "transcript": transcript,
            "consensus": report_text,
            "risk_scores": risk or {},
        }, indent=2, default=str)
        st.download_button(
            "📊 Download as JSON",
            data=transcript_json,
            file_name=f"debate_transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col3:
        if st.button("🔄 Start New Patient", use_container_width=True):
            st.session_state.patient_twin = None
            st.session_state.risk_results = None
            st.session_state.debate_result = None
            st.session_state.page = "home"
            st.rerun()


def _format_full_report(twin, risk, debate) -> str:
    patient_name = twin.demographics.full_name if twin else "Patient"
    lines = [
        f"# MDT Consensus Report: {patient_name}",
        f"**Generated:** {datetime.now().strftime('%d %B %Y %H:%M')}",
        f"**System:** MedTwin AI Clinical Decision Support",
        "",
        "---",
        "",
        "## Patient Summary",
    ]

    if twin:
        lines += [
            f"- **Name:** {twin.demographics.full_name}",
            f"- **Age:** {twin.age}",
            f"- **Gender:** {twin.demographics.gender.value}",
            f"- **BMI:** {twin.bmi:.1f}" if twin.bmi else "- **BMI:** N/A",
            f"- **Conditions:** {', '.join(twin.get_conditions_summary()) or 'None'}",
            f"- **Medications:** {', '.join(twin.get_medication_names()) or 'None'}",
        ]

    if risk:
        comp = risk.get("composite", {})
        cv = risk.get("cardiovascular", {})
        dm = risk.get("diabetes", {})
        lines += [
            "",
            "## Risk Scores",
            f"- **Composite:** {comp.get('risk_percentage', 0):.1f}% ({comp.get('risk_category', '?')})",
            f"- **Cardiovascular:** {cv.get('risk_percentage', 0):.1f}% ({cv.get('risk_category', '?')})",
            f"- **Diabetes:** {dm.get('risk_percentage', 0):.1f}% ({dm.get('risk_category', '?')})",
        ]

    lines += [
        "",
        "---",
        "",
        "## MDT Consensus Report",
        "",
        debate.get("final_consensus_report", "Not available."),
    ]

    return "\n".join(lines)
