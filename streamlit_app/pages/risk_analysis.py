"""
Risk Analysis Page — ML risk prediction with visual explanations.
"""
import streamlit as st
import time


def render():
    st.markdown("# 📊 Risk Analysis")
    st.markdown("*XGBoost multi-domain risk prediction with SHAP explanations*")

    twin = st.session_state.get("patient_twin")
    if twin is None:
        st.warning("⚠️ Please build a patient profile first.")
        if st.button("👤 Go to Patient Profile"):
            st.session_state.page = "patient"
            st.rerun()
        return

    risk = st.session_state.get("risk_results")

    if risk is None:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(
                f"**Patient:** {twin.demographics.full_name} · Age {twin.age}\n\n"
                "Click **Run Risk Analysis** to generate ML risk predictions."
            )
        with col2:
            if st.button("🔍 Run Risk Analysis", type="primary", use_container_width=True):
                _run_risk_analysis(twin)
    else:
        _render_risk_dashboard(twin, risk)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-run Analysis", use_container_width=True):
                st.session_state.risk_results = None
                st.rerun()
        with col2:
            if st.button("🗣️ Launch Clinical Debate →", type="primary", use_container_width=True):
                st.session_state.page = "debate"
                st.rerun()


def _run_risk_analysis(twin):
    with st.spinner("🤖 Running XGBoost risk models…"):
        progress = st.progress(0, text="Loading models…")
        time.sleep(0.3)

        try:
            from ml.inference import predict_all_risks
            progress.progress(30, text="Training on synthetic data (first run only)…")
            risk = predict_all_risks(twin)
            progress.progress(100, text="Complete!")
            time.sleep(0.3)
            progress.empty()
            st.session_state.risk_results = risk
            st.rerun()
        except Exception as e:
            progress.empty()
            st.error(f"❌ Risk analysis failed: {e}")
            st.exception(e)


def _render_risk_dashboard(twin, risk):
    """Render the full risk dashboard with charts."""

    # ── Overall risk gauge ───────────────────────────────────────────────────
    comp = risk.get("composite", {})
    cv = risk.get("cardiovascular", {})
    dm = risk.get("diabetes", {})

    risk_pct = comp.get("risk_percentage", 0)
    risk_cat = comp.get("risk_category", "unknown")

    color_map = {
        "low": "#22c55e", "moderate": "#f59e0b",
        "high": "#ef4444", "very_high": "#9d174d"
    }
    color = color_map.get(risk_cat, "#6b7280")

    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        border-top: 6px solid {color};
        margin-bottom: 1.5rem;
    ">
        <h2 style="color:#1e293b; margin:0;">Composite Risk Score</h2>
        <div style="font-size:4rem; font-weight:700; color:{color}; margin:0.5rem 0;">
            {risk_pct:.1f}%
        </div>
        <div style="
            display:inline-block;
            background:{color}22;
            color:{color};
            padding:0.4rem 1.2rem;
            border-radius:999px;
            font-weight:600;
            font-size:1.1rem;
            text-transform:uppercase;
            letter-spacing:0.1em;
        ">
            {risk_cat.replace('_', ' ')} RISK
        </div>
        <p style="color:#64748b; margin-top:0.75rem; font-size:0.9rem;">
            Patient: {twin.demographics.full_name} · Age {twin.age}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Domain breakdown ─────────────────────────────────────────────────────
    st.markdown("### 🎯 Risk by Domain")
    col1, col2, col3 = st.columns(3)

    with col1:
        _risk_metric_card("❤️ Cardiovascular",
                          cv.get("risk_percentage", 0),
                          cv.get("risk_category", "unknown"),
                          f"ASCVD: {cv.get('ascvd_10yr_risk', 0) * 100:.1f}%" if cv.get("ascvd_10yr_risk") else "ASCVD calculated")

    with col2:
        _risk_metric_card("🧬 Diabetes",
                          dm.get("risk_percentage", 0),
                          dm.get("risk_category", "unknown"),
                          f"FINDRISC: {dm.get('findrisc_score', 'N/A')}/26")

    with col3:
        domain_scores = comp.get("domain_scores", {})
        lifestyle_score = domain_scores.get("lifestyle", 0)
        _risk_metric_card("🏃 Lifestyle Risk",
                          lifestyle_score * 100,
                          "high" if lifestyle_score > 0.5 else "moderate" if lifestyle_score > 0.25 else "low",
                          "Activity, smoking, alcohol, sleep")

    # ── Feature importance / SHAP bar chart ──────────────────────────────────
    st.markdown("### 🔍 Top Risk Factor Contributions (SHAP)")
    top_factors = risk.get("top_risk_factors", [])
    if top_factors:
        try:
            import pandas as pd
            import plotly.graph_objects as go

            df = pd.DataFrame(top_factors).head(10)
            df["feature_label"] = df["feature"].str.replace("_", " ").str.title()
            df = df.sort_values("contribution")

            colors = ["#ef4444" if c > 0 else "#22c55e" for c in df["contribution"]]

            fig = go.Figure(go.Bar(
                x=df["contribution"],
                y=df["feature_label"],
                orientation="h",
                marker_color=colors,
                text=[f"{c:.4f}" for c in df["contribution"]],
                textposition="outside",
            ))
            fig.update_layout(
                title="Feature Contributions to Composite Risk",
                xaxis_title="SHAP Contribution",
                yaxis_title="Feature",
                height=400,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Inter", size=12),
                margin=dict(l=0, r=20, t=40, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            # Fallback if plotly not installed
            for f in top_factors[:8]:
                st.progress(
                    min(1.0, f["contribution"] * 10),
                    text=f"**{f['feature'].replace('_', ' ').title()}**: {f['contribution']:.4f}"
                )

    # ── Domain scores radar ───────────────────────────────────────────────────
    domain_scores = comp.get("domain_scores", {})
    if domain_scores:
        st.markdown("### 🕸️ Risk Domain Profile")
        try:
            import plotly.graph_objects as go

            categories = list(domain_scores.keys())
            values = [domain_scores[c] for c in categories]
            # Close the polygon
            categories_closed = categories + [categories[0]]
            values_closed = values + [values[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                fillcolor="rgba(102,126,234,0.2)",
                line=dict(color="#667eea", width=2),
                name="Risk Profile",
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1]),
                    angularaxis=dict(tickfont=dict(size=12)),
                ),
                showlegend=False,
                height=350,
                paper_bgcolor="white",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for interactive charts: `pip install plotly`")

    # ── Lab abnormalities ─────────────────────────────────────────────────────
    st.markdown("### ⚠️ Abnormal Laboratory Values")
    if twin.latest_labs:
        abnormal = twin.latest_labs.get_abnormal_tests()
        if abnormal:
            cols = st.columns(min(len(abnormal), 4))
            for i, test in enumerate(abnormal[:4]):
                flag_color = "#ef4444" if test.flag in ("H", "HH") else "#3b82f6"
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 1rem;
                        border-left: 4px solid {flag_color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    ">
                        <div style="color:#64748b; font-size:0.8rem;">{test.test_name}</div>
                        <div style="font-size:1.5rem; font-weight:700; color:{flag_color};">
                            {test.value} <span style="font-size:0.8rem;">{test.unit}</span>
                        </div>
                        <div style="color:#94a3b8; font-size:0.75rem;">
                            Ref: {test.reference_range_low or ''}–{test.reference_range_high or ''} {test.unit}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ All laboratory values within normal range.")


def _risk_metric_card(title: str, pct: float, category: str, subtitle: str = ""):
    color_map = {
        "low": "#22c55e", "moderate": "#f59e0b",
        "high": "#ef4444", "very_high": "#9d174d",
        "very_low": "#16a34a",
    }
    color = color_map.get(category, "#6b7280")
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-top: 4px solid {color};
        height: 100%;
    ">
        <div style="font-size:1rem; color:#64748b; font-weight:500;">{title}</div>
        <div style="font-size:2.5rem; font-weight:700; color:{color}; margin:0.4rem 0;">
            {pct:.1f}%
        </div>
        <div style="
            display:inline-block;
            background:{color}22;
            color:{color};
            padding:0.2rem 0.8rem;
            border-radius:999px;
            font-size:0.75rem;
            font-weight:600;
            text-transform:uppercase;
        ">{category.replace('_', ' ')}</div>
        <div style="color:#94a3b8; font-size:0.8rem; margin-top:0.5rem;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
