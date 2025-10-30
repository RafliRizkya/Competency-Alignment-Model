import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import re
import requests

# Page config
st.set_page_config(
    page_title="AI Talent Analytics",
    page_icon="",
    layout="wide"
)

# Database connection
connection_string = st.secrets["DB_CONNECTION_STRING"]
engine = create_engine(connection_string)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .insight-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-left: 4px solid #667eea;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title(" AI Talent Analytics Dashboard")
st.markdown("**Transforming talent data into actionable insights**")

# Centered Job Configuration (no sidebar)
st.header(" Job Configuration")
left, center, right = st.columns([1, 2, 1])
with center:
    roles = [
        "Brand Executive",
        "Data Analyst",
        "Finance Officer",
        "HRBP",
        "Sales Supervisor",
        "Supply Planner",
    ]
    role_name = st.selectbox("Role Name", roles, index=1)

    level = [
        "Entry",
        "Middle",
        "Senior"
    ]
    job_level = st.selectbox("Job Level", level, index = 1)
    role_purpose = st.text_area(
        "Role Purpose", 
        "Analyze business data and generate insights to drive strategic decisions"
    )
    
    st.markdown("---")
    st.subheader(" Benchmark Selection")
    benchmark_ids_input = st.text_input(
        "Benchmark Employee IDs", 
        "312,335,175",
        help="Comma-separated IDs of high-performing employees"
    )
    
    st.markdown("---")
    # == COMPETENCY WEIGHTS REMOVED ==
    # Set static weight values
    weight_execution = 0.3
    weight_strategic = 0.2
    weight_innovation = 0.1
    weight_leadership = 0.1
    weight_motivation = 0.1
    weight_cognitive = 0.1
    weight_demographics = 0.1
    
    # Run Analysis button
    run_analysis = st.button(" Run Analysis", type="primary", use_container_width=True)

# Main analysis
if run_analysis:
    with st.spinner(" Analyzing talent data..."):
        try:
            # Parse benchmark IDs (support alphanumeric like EMP100026 and numeric)
            raw_tokens = re.findall(r"[A-Za-z]+\d+|\d+", benchmark_ids_input or "")
            benchmark_ids = list(dict.fromkeys(token.strip() for token in raw_tokens if token.strip()))  # deduplicate, preserve order
            
            if not benchmark_ids:
                st.warning(" No valid IDs detected. Using sample: EMP100026, EMP100039")
                benchmark_ids = ["EMP100026", "EMP100039"]
            
            # Generate job vacancy ID
            job_vacancy_id = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Weights configuration
            weights_config = {
                "tgv_weights": {
                    "Execution Excellence": weight_execution,
                    "Strategic Impact": weight_strategic,
                    "Growth & Innovation": weight_innovation,
                    "People Leadership": weight_leadership,
                    "Motivation & Drive": weight_motivation,
                    "Cognitive Complexity": weight_cognitive,
                    "Demographics": weight_demographics
                }
            }
            
            # SQL Query parameters
            params = {
                "job_vacancy_id": job_vacancy_id,
                "role_name": role_name,
                "job_level": job_level,
                "benchmark_ids": benchmark_ids,
                "weights_config": json.dumps(weights_config)
            }
            
            # Execute SQL query (use provided params for benchmark IDs and config)
            query = """
            WITH tb AS (
                SELECT 
                    %(job_vacancy_id)s::TEXT AS job_vacancy_id,
                    %(role_name)s::TEXT AS role_name,
                    %(job_level)s::TEXT AS job_level,
                    %(weights_config)s::JSONB AS weights_config,
                    %(benchmark_ids)s::TEXT[] AS selected_talent_ids
            ),
            employee_enriched AS (
                SELECT 
                    e.employee_id,
                    e.fullname,
                    pos.name as position,
                    dir.name AS directorate,
                    g.name AS grade,
                    edu.name AS education, 
                    pp.disc,
                    MAX(CASE WHEN cy.pillar_code = 'IDS' THEN cy.score END) AS Insight_Decision,
                    MAX(CASE WHEN cy.pillar_code = 'QDD' THEN cy.score END) AS Quality_Delivery,
                    MAX(CASE WHEN cy.pillar_code = 'FTC' THEN cy.score END) AS Forward_Thinking,
                    MAX(CASE WHEN cy.pillar_code = 'STO' THEN cy.score END) AS Team_Orientation,
                    MAX(CASE WHEN cy.pillar_code = 'CSI' THEN cy.score END) AS Commercial_Savvy,
                    MAX(CASE WHEN cy.pillar_code = 'VCU' THEN cy.score END) AS Value_Creation,
                    MAX(CASE WHEN cy.pillar_code = 'GDR' THEN cy.score END) AS Growth_Drive,
                    MAX(CASE WHEN cy.pillar_code = 'CEX' THEN cy.score END) AS Curiosity,
                    MAX(CASE WHEN cy.pillar_code = 'LIE' THEN cy.score END) AS Lead_Inspire,
                    MAX(CASE WHEN cy.pillar_code = 'SEA' THEN cy.score END) AS Social_Empathy,
                    MAX(pp.pauli) AS Pauli_Score,
                    MAX(pp.iq) AS IQ_Score,
                    MAX(pp.gtq) AS GTQ_Score,
                    MAX(pp.tiki) AS TIKI_Score,
                    MAX(CASE WHEN ps.scale_code = 'Papi_P' THEN ps.score END) AS Papi_P,
                    MAX(CASE WHEN ps.scale_code = 'Papi_W' THEN ps.score END) AS Papi_W
                FROM employees e
                LEFT JOIN dim_directorates dir ON e.directorate_id = dir.directorate_id
                LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
                LEFT JOIN dim_education edu ON e.education_id = edu.education_id
                LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
                LEFT JOIN profiles_psych pp ON e.employee_id = pp.employee_id
                LEFT JOIN competencies_yearly cy ON e.employee_id = cy.employee_id AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
                LEFT JOIN papi_scores ps ON e.employee_id = ps.employee_id
                GROUP BY e.employee_id, e.fullname, pos.name, dir.name, g.name, edu.name, pp.disc
            ),
            talent_structure AS (
                SELECT 1 AS tv_order, 'Execution Excellence' AS tgv_name, 'Quality Delivery' AS tv_name, 'Quality_Delivery' AS column_name, 'numeric' AS data_type, 'higher_is_better' AS scoring_direction
                UNION ALL SELECT 2, 'Execution Excellence', 'Forward Thinking', 'Forward_Thinking', 'numeric', 'higher_is_better'
                UNION ALL SELECT 3, 'Execution Excellence', 'Team Orientation', 'Team_Orientation', 'numeric', 'higher_is_better'
                UNION ALL SELECT 4, 'Strategic Impact', 'Commercial Savvy', 'Commercial_Savvy', 'numeric', 'higher_is_better'
                UNION ALL SELECT 5, 'Strategic Impact', 'Value Creation', 'Value_Creation', 'numeric', 'higher_is_better'
                UNION ALL SELECT 6, 'Growth & Innovation', 'Growth Drive', 'Growth_Drive', 'numeric', 'higher_is_better'
                UNION ALL SELECT 7, 'Growth & Innovation', 'Curiosity', 'Curiosity', 'numeric', 'higher_is_better'
                UNION ALL SELECT 8, 'People Leadership', 'Lead & Inspire', 'Lead_Inspire', 'numeric', 'higher_is_better'
                UNION ALL SELECT 9, 'People Leadership', 'Social Empathy', 'Social_Empathy', 'numeric', 'higher_is_better'
                UNION ALL SELECT 10, 'Motivation & Drive', 'Pauli Score', 'Pauli_Score', 'numeric', 'higher_is_better'
                UNION ALL SELECT 11, 'Cognitive Complexity', 'IQ Score', 'IQ_Score', 'numeric', 'higher_is_better'
                UNION ALL SELECT 12, 'Cognitive Complexity', 'GTQ Score', 'GTQ_Score', 'numeric', 'higher_is_better'
                UNION ALL SELECT 13, 'Cognitive Complexity', 'TIKI Score', 'TIKI_Score', 'numeric', 'higher_is_better'
                UNION ALL SELECT 14, 'Demographics', 'Education Level', 'education', 'categorical', 'exact_match'
                UNION ALL SELECT 15, 'Demographics', 'DISC Profile', 'disc', 'categorical', 'exact_match'
                UNION ALL SELECT 16, 'PAPI Alignment', 'Papi_P', 'Papi_P', 'numeric', 'higher_is_better'
                UNION ALL SELECT 17, 'PAPI Alignment', 'Papi_W', 'Papi_W', 'numeric', 'higher_is_better'
            ),
            baseline_scores AS (
                SELECT tb.job_vacancy_id, tb.role_name, tb.job_level, ts.tgv_name, ts.tv_name, ts.column_name, ts.data_type, ts.scoring_direction, tb.weights_config,
                    CASE 
                        WHEN ts.data_type = 'categorical' THEN MODE() WITHIN GROUP (ORDER BY CASE ts.column_name 
                            WHEN 'education' THEN edu.name 
                            WHEN 'disc' THEN pp.disc 
                        END)
                        ELSE PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                            CASE ts.column_name
                                WHEN 'Quality_Delivery' THEN cy.score::NUMERIC 
                                WHEN 'Forward_Thinking' THEN cy.score::NUMERIC
                                WHEN 'Team_Orientation' THEN cy.score::NUMERIC 
                                WHEN 'Commercial_Savvy' THEN cy.score::NUMERIC
                                WHEN 'Value_Creation' THEN cy.score::NUMERIC 
                                WHEN 'Growth_Drive' THEN cy.score::NUMERIC
                                WHEN 'Curiosity' THEN cy.score::NUMERIC 
                                WHEN 'Lead_Inspire' THEN cy.score::NUMERIC 
                                WHEN 'Social_Empathy' THEN cy.score::NUMERIC
                                WHEN 'Pauli_Score' THEN pp.pauli::NUMERIC
                                WHEN 'IQ_Score' THEN pp.iq::NUMERIC
                                WHEN 'GTQ_Score' THEN pp.gtq::NUMERIC
                                WHEN 'TIKI_Score' THEN pp.tiki::NUMERIC
                                WHEN 'Papi_P' THEN ps.score::NUMERIC
                                WHEN 'Papi_W' THEN ps.score::NUMERIC
                            END
                        )::TEXT
                    END AS baseline_score
                FROM tb
                CROSS JOIN talent_structure ts
                INNER JOIN UNNEST(tb.selected_talent_ids) AS benchmark_employee_id ON TRUE
                INNER JOIN employees e ON e.employee_id = benchmark_employee_id
                LEFT JOIN dim_education edu ON e.education_id = edu.education_id
                LEFT JOIN profiles_psych pp ON e.employee_id = pp.employee_id
                LEFT JOIN competencies_yearly cy ON e.employee_id = cy.employee_id AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
                LEFT JOIN papi_scores ps ON e.employee_id = ps.employee_id
                GROUP BY tb.job_vacancy_id, tb.role_name, tb.job_level, ts.tgv_name, ts.tv_name, ts.column_name, ts.data_type, ts.scoring_direction, tb.weights_config
                HAVING CASE 
                    WHEN ts.data_type = 'categorical' THEN 
                        MODE() WITHIN GROUP (ORDER BY CASE ts.column_name WHEN 'education' THEN edu.name WHEN 'disc' THEN pp.disc END) IS NOT NULL
                    ELSE 
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                            CASE ts.column_name
                                WHEN 'Quality_Delivery' THEN cy.score::NUMERIC 
                                WHEN 'Forward_Thinking' THEN cy.score::NUMERIC
                                WHEN 'Team_Orientation' THEN cy.score::NUMERIC 
                                WHEN 'Commercial_Savvy' THEN cy.score::NUMERIC
                                WHEN 'Value_Creation' THEN cy.score::NUMERIC 
                                WHEN 'Growth_Drive' THEN cy.score::NUMERIC
                                WHEN 'Curiosity' THEN cy.score::NUMERIC 
                                WHEN 'Lead_Inspire' THEN cy.score::NUMERIC 
                                WHEN 'Social_Empathy' THEN cy.score::NUMERIC
                                WHEN 'Pauli_Score' THEN pp.pauli::NUMERIC
                                WHEN 'IQ_Score' THEN pp.iq::NUMERIC
                                WHEN 'GTQ_Score' THEN pp.gtq::NUMERIC
                                WHEN 'TIKI_Score' THEN pp.tiki::NUMERIC
                                WHEN 'Papi_P' THEN ps.score::NUMERIC
                                WHEN 'Papi_W' THEN ps.score::NUMERIC
                            END
                        )::TEXT IS NOT NULL
                END
            ),
            tv_match_rates AS (
                SELECT e.employee_id, e.directorate, e.grade, e.position,
                    bs.job_vacancy_id, bs.job_level, bs.tgv_name, bs.tv_name, bs.baseline_score, bs.role_name, bs.weights_config,
                    CASE bs.column_name
                        WHEN 'Quality_Delivery' THEN e.Quality_Delivery::TEXT
                        WHEN 'Forward_Thinking' THEN e.Forward_Thinking::TEXT 
                        WHEN 'Team_Orientation' THEN e.Team_Orientation::TEXT
                        WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy::TEXT 
                        WHEN 'Value_Creation' THEN e.Value_Creation::TEXT
                        WHEN 'Growth_Drive' THEN e.Growth_Drive::TEXT 
                        WHEN 'Curiosity' THEN e.Curiosity::TEXT
                        WHEN 'Lead_Inspire' THEN e.Lead_Inspire::TEXT 
                        WHEN 'Social_Empathy' THEN e.Social_Empathy::TEXT 
                        WHEN 'Pauli_Score' THEN e.Pauli_Score::TEXT
                        WHEN 'IQ_Score' THEN e.IQ_Score::TEXT
                        WHEN 'GTQ_Score' THEN e.GTQ_Score::TEXT
                        WHEN 'TIKI_Score' THEN e.TIKI_Score::TEXT
                        WHEN 'Papi_P' THEN e.Papi_P::TEXT
                        WHEN 'Papi_W' THEN e.Papi_W::TEXT
                        WHEN 'education' THEN e.education 
                        WHEN 'disc' THEN e.disc
                    END AS user_score,
                    CASE 
                        WHEN bs.data_type = 'categorical' THEN
                            CASE 
                                WHEN bs.tv_name = 'Education Level' THEN
                                    CASE 
                                        WHEN (CASE e.education WHEN 'D3' THEN 3 WHEN 'S1' THEN 4 WHEN 'S2' THEN 5 ELSE 0 END) >= 
                                            (CASE bs.baseline_score WHEN 'D3' THEN 3 WHEN 'S1' THEN 4 WHEN 'S2' THEN 5 ELSE 0 END)
                                        THEN 100.00 
                                        ELSE 0.00 
                                    END
                                WHEN (CASE bs.column_name WHEN 'education' THEN e.education WHEN 'disc' THEN e.disc END) IS NULL THEN NULL
                                WHEN (CASE bs.column_name WHEN 'education' THEN e.education WHEN 'disc' THEN e.disc END) = bs.baseline_score THEN 100.00 
                                ELSE 0.00 
                            END
                        WHEN bs.scoring_direction = 'higher_is_better' THEN
                            CASE 
                                WHEN bs.baseline_score IS NULL OR bs.baseline_score::NUMERIC = 0 THEN NULL
                                WHEN (CASE bs.column_name 
                                    WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                                    WHEN 'Forward_Thinking' THEN e.Forward_Thinking 
                                    WHEN 'Team_Orientation' THEN e.Team_Orientation 
                                    WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy 
                                    WHEN 'Value_Creation' THEN e.Value_Creation 
                                    WHEN 'Growth_Drive' THEN e.Growth_Drive 
                                    WHEN 'Curiosity' THEN e.Curiosity 
                                    WHEN 'Lead_Inspire' THEN e.Lead_Inspire 
                                    WHEN 'Social_Empathy' THEN e.Social_Empathy 
                                    WHEN 'Pauli_Score' THEN e.Pauli_Score
                                    WHEN 'IQ_Score' THEN e.IQ_Score
                                    WHEN 'GTQ_Score' THEN e.GTQ_Score
                                    WHEN 'TIKI_Score' THEN e.TIKI_Score
                                    WHEN 'Papi_P' THEN e.Papi_P 
                                    WHEN 'Papi_W' THEN e.Papi_W
                                END)::NUMERIC IS NULL THEN NULL
                                ELSE LEAST(((CASE bs.column_name 
                                    WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                                    WHEN 'Forward_Thinking' THEN e.Forward_Thinking 
                                    WHEN 'Team_Orientation' THEN e.Team_Orientation 
                                    WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy 
                                    WHEN 'Value_Creation' THEN e.Value_Creation 
                                    WHEN 'Growth_Drive' THEN e.Growth_Drive 
                                    WHEN 'Curiosity' THEN e.Curiosity 
                                    WHEN 'Lead_Inspire' THEN e.Lead_Inspire 
                                    WHEN 'Social_Empathy' THEN e.Social_Empathy 
                                    WHEN 'Pauli_Score' THEN e.Pauli_Score
                                    WHEN 'IQ_Score' THEN e.IQ_Score
                                    WHEN 'GTQ_Score' THEN e.GTQ_Score
                                    WHEN 'TIKI_Score' THEN e.TIKI_Score
                                    WHEN 'Papi_P' THEN e.Papi_P 
                                    WHEN 'Papi_W' THEN e.Papi_W
                                END)::NUMERIC / bs.baseline_score::NUMERIC) * 100, 100.00) 
                            END
                        ELSE NULL
                    END AS tv_match_rate
                FROM employee_enriched e 
                INNER JOIN baseline_scores bs 
                    ON LOWER(bs.role_name) = LOWER(e.position)
            ),
            tgv_match_rates AS (
                SELECT employee_id, job_vacancy_id, tgv_name, weights_config,
                    ROUND(AVG(tv_match_rate), 2) AS tgv_match_rate
                FROM tv_match_rates
                WHERE tv_match_rate IS NOT NULL
                GROUP BY employee_id, job_vacancy_id, tgv_name, weights_config
            ),
            final_match_rates AS (
                SELECT tgv.employee_id, tgv.job_vacancy_id,
                    ROUND(
                        CASE 
                            WHEN tgv.weights_config ? 'tgv_weights' THEN
                                SUM(tgv.tgv_match_rate * COALESCE(
                                    (tgv.weights_config->'tgv_weights'->>tgv.tgv_name)::NUMERIC, 0
                                )) / NULLIF(
                                    SUM(COALESCE((tgv.weights_config->'tgv_weights'->>tgv.tgv_name)::NUMERIC, 0)), 0
                                )
                            ELSE 
                                AVG(tgv.tgv_match_rate) 
                        END, 2
                    ) AS final_match_rate
                FROM tgv_match_rates tgv
                GROUP BY tgv.employee_id, tgv.job_vacancy_id, tgv.weights_config
            )
            SELECT
                tv.employee_id,
                tv.directorate,
                tv.role_name AS role,
                tv.grade,
                tv.tgv_name,
                tv.tv_name,
                tv.baseline_score,
                tv.user_score,
                ROUND(tv.tv_match_rate, 2) AS tv_match_rate,
                tgv.tgv_match_rate,
                fm.final_match_rate
            FROM tv_match_rates tv
            INNER JOIN tgv_match_rates tgv 
                ON tv.employee_id = tgv.employee_id 
                AND tv.job_vacancy_id = tgv.job_vacancy_id 
                AND tv.tgv_name = tgv.tgv_name
            INNER JOIN final_match_rates fm 
                ON tv.employee_id = fm.employee_id 
                AND tv.job_vacancy_id = fm.job_vacancy_id
            WHERE tv.tv_match_rate IS NOT NULL
            ORDER BY fm.final_match_rate DESC, tv.tgv_name, tv.tv_name;
            """
            
            # Execute query
            df = pd.read_sql(query, engine, params=params)
            
            if df.empty:
                st.error(" No data returned from query. Please check benchmark IDs and role/level combination.")
                st.stop()
            
            # Store results in session state
            st.session_state.df = df
            st.session_state.benchmark_ids = benchmark_ids
            st.session_state.role_name = role_name
            st.session_state.job_level = job_level
            st.session_state.role_purpose = role_purpose
            
            st.success(" Analysis completed successfully!")
            
        except Exception as e:
            st.error(f" Error: {str(e)}")
            st.stop()

# Display results if available
if 'df' in st.session_state:
    df = st.session_state.df
    benchmark_ids = st.session_state.benchmark_ids
    role_name = st.session_state.role_name
    job_level = st.session_state.job_level
    role_purpose = st.session_state.role_purpose
    
    # === SECTION 1: AI-Generated Job Profile ===
    st.header(f"AI-Generated Job Profile ({role_name} - {job_level} Level)")

    # AI-generated job profile (requirements, description, key competencies)
    def generate_job_profile(role: str, level: str, purpose: str) -> str:
        try:
            sys_prompt = (
                "You are an expert HR job architect. Write a concise, role-ready job profile with three sections: "
                "Job Requirements (bullet list, 6-10 bullets), Job Description, and Key Competencies (bullet list, 5-8 bullets). "
                "Be specific and actionable. Avoid placeholders. "
                "Output the result ONLY, in the requested format, and DO NOT include any reasoning, process, or meta-commentary. Just output the job profile content as specified."
            )
            user_block = (
                f"Role: {role}\nLevel: {level}\nPurpose: {purpose}\n"
                "Output format EXACTLY:\n\n"
                "Job Requirements:\n- ...\n\n"
                "Job Description:\n<one short paragraph>\n\n"
                "Key Competencies:\n- ...\n"
            )
            headers1 = {
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY_1']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost",
                "X-Title": "AI Talent Analytics Dashboard",
            }
            body = {
                "model": "tngtech/deepseek-r1t2-chimera:free",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_block}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers1, json=body, timeout=30)
            status1 = resp.status_code
            try:
                data1 = resp.json()
            except Exception:
                data1 = {}
            content1 = data1.get("choices", [{}])[0].get("message", {}).get("content", "") if status1 == 200 else ""
            if status1 == 200 and content1:
                return content1.strip()  # Success on first model
            # If gagal atau konten kosong, lanjut coba model kedua (minimax)
            headers2 = {
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY_2']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost",
                "X-Title": "AI Talent Analytics Dashboard",
            }
            body["model"] = "minimax/minimax-m2:free"
            resp2 = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers2, json=body, timeout=30)
            status2 = resp2.status_code
            try:
                data2 = resp2.json()
            except Exception:
                data2 = {}
            content2 = data2.get("choices", [{}])[0].get("message", {}).get("content", "") if status2 == 200 else ""
            # PATCH: Fallback to reasoning if content blank for minimax
            if status2 == 200 and not content2:
                # Coba ambil reasoning_details atau reasoning
                msg2 = data2.get("choices", [{}])[0].get("message", {})
                reasoning = msg2.get("reasoning", "")
                if not reasoning:
                    # Cek reasoning_details jika reasoning kosong
                    reasoning_details = msg2.get("reasoning_details", [])
                    if reasoning_details and isinstance(reasoning_details, list):
                        reasoning = reasoning_details[0].get("text", "")
                if reasoning:
                    return reasoning.strip()
            if status2 == 200 and content2:
                return content2.strip()  # Success with model2
            # If gagal semua, tampilkan error detail dari kedua attempt (untuk helpdesk/diagnosis)
            return f"AI error: (1st model: {status1} - {str(data1)}) (2nd model: {status2} - {str(data2)})"
        except Exception as ex:
            return f"AI error: {ex}"

    ai_profile_text = generate_job_profile(role_name, job_level, role_purpose)
    if ai_profile_text and ai_profile_text.strip() != "":
        st.markdown(ai_profile_text)
    else:
        st.warning("Profil AI tidak dapat dihasilkan untuk role ini. Silakan coba peran/level/purpose yang berbeda atau gunakan istilah yang lebih umum.")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        ### {role_name} - {job_level} Level
        
        **Purpose:**  
        {role_purpose}
        
        **Core Competencies Required:**
        """)
        
        # Extract baseline scores for key competencies
        baseline_df = df[['tv_name', 'baseline_score']].drop_duplicates()
        
        competency_groups = {
            'Execution Excellence': ['Quality Delivery', 'Forward Thinking', 'Team Orientation'],
            'Strategic Impact': ['Commercial Savvy', 'Value Creation'],
            'Growth & Innovation': ['Growth Drive', 'Curiosity'],
            'People Leadership': ['Lead & Inspire', 'Social Empathy']
        }
        
        for group, competencies in competency_groups.items():
            st.markdown(f"**{group}:**")
            for comp in competencies:
                baseline = baseline_df[baseline_df['tv_name'] == comp]['baseline_score'].values
                if len(baseline) > 0:
                    st.markdown(f"- {comp}: Baseline score {baseline[0]}")
    
    # Removed Key Requirements box per request
    
    st.markdown("---")
    
    # === SECTION 2: Talent Pool Overview ===
    st.header(" Talent Pool Overview")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_candidates = df['employee_id'].nunique()
    avg_match = df.groupby('employee_id')['final_match_rate'].first().mean()
    top_match = df.groupby('employee_id')['final_match_rate'].first().max()
    qualified = (df.groupby('employee_id')['final_match_rate'].first() >= 70).sum()
    
    with col1:
        st.metric("Total Candidates", total_candidates)
    with col2:
        st.metric("Average Match Rate", f"{avg_match:.1f}%")
    with col3:
        st.metric("Top Match Rate", f"{top_match:.1f}%")
    with col4:
        st.metric("Qualified (≥70%)", qualified)
    
    # === SECTION 3: Top Talent Ranking ===
    st.header(" Top Talent Ranking")
    
    # Prepare ranking dataframe
    ranking_df = df.groupby('employee_id').agg({
        'final_match_rate': 'first',
        'directorate': 'first',
        'role': 'first',
        'grade': 'first'
    }).reset_index().sort_values('final_match_rate', ascending=False)
    
    # Add rank
    ranking_df['rank'] = range(1, len(ranking_df) + 1)
    
    # Identify benchmark employees
    ranking_df['is_benchmark'] = ranking_df['employee_id'].isin(benchmark_ids)
    
    # Display top 20
    st.dataframe(
        ranking_df.head(20)[['rank', 'employee_id', 'directorate', 'final_match_rate', 'is_benchmark']].style.format({
            'final_match_rate': '{:.1f}%'
        }).background_gradient(subset=['final_match_rate'], cmap='RdYlGn'),
        use_container_width=True
    )
    
    # Summary Insights (Top 3): explain why top employees rank highest
    st.subheader(" Summary Insights (Top 3)")
    try:
        top_n = 3
        top_ids = ranking_df.head(top_n)['employee_id'].tolist()
        insights_blocks = []
        for emp_id in top_ids:
            emp_df = df[df['employee_id'] == emp_id]
            emp_tgv = emp_df.groupby('tgv_name')['tgv_match_rate'].first().sort_values(ascending=False)
            top_tgvs = emp_tgv.head(2)
            overall = ranking_df.loc[ranking_df['employee_id'] == emp_id, 'final_match_rate'].iloc[0]
            reasons = ", ".join([f"{name} ({score:.0f}%)" for name, score in top_tgvs.items()]) if len(top_tgvs) > 0 else "—"
            insights_blocks.append(f"Employee {emp_id}: overall {overall:.0f}% driven by {reasons}")
        if insights_blocks:
            st.markdown(f"""
            <div class='insight-box' style='background-color:#000; color:#fff;'>
            <strong>These employees lead due to strong alignment on key competency groups:</strong><br/>
            {'<br/>'.join(insights_blocks)}
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass
    
    # === SECTION 4: Match Rate Distribution ===
    st.header(" Match Rate Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram
        fig_hist = px.histogram(
            ranking_df,
            x='final_match_rate',
            nbins=20,
            title='Distribution of Final Match Rates',
            labels={'final_match_rate': 'Match Rate (%)', 'count': 'Number of Candidates'},
            color_discrete_sequence=['#667eea']
        )
        fig_hist.add_vline(x=avg_match, line_dash="dash", line_color="red", 
                          annotation_text=f"Avg: {avg_match:.1f}%")
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Box plot by directorate
        fig_box = px.box(
            ranking_df,
            x='directorate',
            y='final_match_rate',
            title='Match Rate by Directorate',
            labels={'final_match_rate': 'Match Rate (%)', 'directorate': 'Directorate'},
            color='directorate'
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # === SECTION 5: Competency Group Analysis ===
    st.header(" Competency Group Performance")
    
    # Average TGV scores
    tgv_df = df.groupby(['employee_id', 'tgv_name']).agg({
        'tgv_match_rate': 'first'
    }).reset_index()
    
    avg_tgv = tgv_df.groupby('tgv_name')['tgv_match_rate'].mean().reset_index()
    avg_tgv = avg_tgv.sort_values('tgv_match_rate', ascending=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_tgv = px.bar(
            avg_tgv,
            x='tgv_match_rate',
            y='tgv_name',
            orientation='h',
            title='Average Match Rate by Competency Group',
            labels={'tgv_match_rate': 'Average Match Rate (%)', 'tgv_name': 'Competency Group'},
            color='tgv_match_rate',
            color_continuous_scale='RdYlGn'
        )
        fig_tgv.update_layout(showlegend=False)
        st.plotly_chart(fig_tgv, use_container_width=True)
    
    with col2:
        pass
    
    # === SECTION 6: Individual Candidate Deep Dive ===
    st.header(" Individual Candidate Analysis")
    
    # Candidate selector
    top_candidates = ranking_df.head(10)['employee_id'].tolist()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_candidate = st.selectbox(
            "Select candidate to analyze",
            options=ranking_df['employee_id'].tolist(),
            format_func=lambda x: f"Employee {x} - {ranking_df[ranking_df['employee_id']==x]['final_match_rate'].values[0]:.1f}% match"
        )
    with col2:
        compare_benchmark = st.checkbox("Compare with benchmark average")
    with col3:
        show_gaps = st.checkbox("Highlight gaps only", value=True)
    
    # Get candidate data
    candidate_df = df[df['employee_id'] == selected_candidate].copy()
    candidate_match = candidate_df['final_match_rate'].iloc[0]
    
    # Candidate overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Match Rate", f"{candidate_match:.1f}%")
    with col2:
        rank = ranking_df[ranking_df['employee_id'] == selected_candidate]['rank'].values[0]
        st.metric("Rank", f"#{rank}")
    with col3:
        percentile = (1 - (rank / len(ranking_df))) * 100
        st.metric("Percentile", f"{percentile:.0f}th")
    
    # Radar chart
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Prepare radar data
        candidate_tgv = candidate_df.groupby('tgv_name')['tgv_match_rate'].first().reset_index()
        
        if compare_benchmark:
            # Get benchmark average
            benchmark_df = df[df['employee_id'].isin(benchmark_ids)]
            benchmark_tgv = benchmark_df.groupby('tgv_name')['tgv_match_rate'].mean().reset_index()
            benchmark_tgv.columns = ['tgv_name', 'benchmark_rate']
            
            radar_data = candidate_tgv.merge(benchmark_tgv, on='tgv_name')
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_data['tgv_match_rate'],
                theta=radar_data['tgv_name'],
                fill='toself',
                name=f'Employee {selected_candidate}',
                line_color='#667eea'
            ))
            
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_data['benchmark_rate'],
                theta=radar_data['tgv_name'],
                fill='toself',
                name='Benchmark Average',
                line_color='#f093fb',
                line_dash='dash'
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title=f"Competency Profile: Employee {selected_candidate} vs Benchmark",
                showlegend=True
            )
        else:
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=candidate_tgv['tgv_match_rate'],
                theta=candidate_tgv['tgv_name'],
                fill='toself',
                name=f'Employee {selected_candidate}',
                line_color='#667eea'
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title=f"Competency Profile: Employee {selected_candidate}",
                showlegend=False
            )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        st.markdown("###  TGV Scores")
        for _, row in candidate_tgv.iterrows():
            score = row['tgv_match_rate']
            tgv = row['tgv_name']
            
            # Color coding
            if score >= 80:
                color = "🟢"
            elif score >= 60:
                color = "🟡"
            else:
                color = "🔴"
            
            st.markdown(f"{color} **{tgv}**: {score:.1f}%")
    
    # Detailed competency breakdown
    st.subheader(" Detailed Competency Breakdown")
    
    # Prepare detailed view - always show semua TV & TGV
    detail_df_all = candidate_df[['tv_name', 'tgv_name', 'baseline_score', 'user_score', 'tv_match_rate']].copy()
    detail_df_all['gap'] = detail_df_all['tv_match_rate'].apply(lambda x: 100 - x)
    detail_df_all = detail_df_all.sort_values('tv_match_rate')
    
    # Improved color coding dengan warna font yang kontras (putih/hitam)
    def color_code_match(val):
        if val >= 80:
            return 'background-color: #d4edda; color: #000;'
        elif val >= 60:
            return 'background-color: #fff3cd; color: #000;'
        else:
            return 'background-color: #f8d7da; color: #000;'
    
    styled_detail = detail_df_all.style.applymap(
        color_code_match, 
        subset=['tv_match_rate']
    ).format({
        'tv_match_rate': '{:.1f}%',
        'gap': '{:.1f}%'
    })
    
    # Tampilkan tabel dengan semua tv & tgv dan heatmap readable
    st.dataframe(styled_detail, use_container_width=True)
    
    # === SECTION 7: Strengths & Development Candidate ===
    st.header(" Strengths & Development Candidate")
    
    # Use unfiltered detail for section 7
    section7_detail = candidate_df[['tv_name', 'tgv_name', 'baseline_score', 'user_score', 'tv_match_rate']].copy()
    section7_detail['gap'] = section7_detail['tv_match_rate'].apply(lambda x: 100 - x)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("###  Strengths")
        strengths = section7_detail[section7_detail['tv_match_rate'] >= 80].sort_values('tv_match_rate', ascending=False)
        for idx, row in strengths.iterrows():
            st.markdown(f"""
        <div class='insight-box' style='background-color:#000; color:#fff; border-left-color: green;'>
        <strong>{row['tv_name']} ({row['tgv_name']})</strong><br/>
        <span style='color: #0f0; font-weight: bold;'>Match Rate: {row['tv_match_rate']:.1f}%</span><br/>
        <span style='color:#fff;'>Candidate Score: {row['user_score']} | Baseline: {row['baseline_score']}</span>
        </div>
        """, unsafe_allow_html=True)
        if strengths.empty:
            st.caption("No strengths at ≥ 80% match.")
    
    with col2:
        st.markdown("###  Development Areas")
        gaps = section7_detail[section7_detail['tv_match_rate'] < 50].sort_values('tv_match_rate')
        for idx, row in gaps.iterrows():
            st.markdown(f"""
        <div class='insight-box' style='background-color:#000; color:#fff; border-left-color: orange;'>
        <strong>{row['tv_name']} ({row['tgv_name']})</strong><br/>
        <span style='color: #ffa500; font-weight: bold;'>Match Rate: {row['tv_match_rate']:.1f}%</span><br/>
        <span style='color:#fff;'>Candidate Score: {row['user_score']} | Baseline: {row['baseline_score']}</span><br/>
        <span style='color:#fff;'>Gap: <strong>{row['gap']:.1f}%</strong></span>
        </div>
        """, unsafe_allow_html=True)
        if gaps.empty:
            st.caption("No development areas below 50% match.")
    
    # AI Recommendations
    st.markdown("###  AI-Generated Recommendations")
    
    # Generate recommendations based on gaps
    recommendations = []
    
    if candidate_match >= 80:
        recommendations.append("**Excellent fit** - This candidate exceeds expectations across most competencies")
        recommendations.append("**Recommendation**: Fast-track for interview and consider for immediate placement")
    elif candidate_match >= 70:
        recommendations.append("**Good fit** - This candidate meets most requirements with minor gaps")
        recommendations.append("**Recommendation**: Proceed with interview, discuss development plan for gap areas")
    elif candidate_match >= 60:
        recommendations.append("**Moderate fit** - This candidate has potential but needs development in key areas")
        recommendations.append("**Recommendation**: Consider with structured onboarding and training program")
    else:
        recommendations.append("**Below threshold** - Significant gaps in critical competencies")
        recommendations.append("**Recommendation**: May require extensive training or better suited for different role")
    
    # Add specific competency recommendations
    weak_tgvs = candidate_tgv[candidate_tgv['tgv_match_rate'] < 70]
    if len(weak_tgvs) > 0:
        recommendations.append(f"\n**Focus development on**: {', '.join(weak_tgvs['tgv_name'].tolist())}")
    
    for rec in recommendations:
        st.markdown(rec)
    
    # === SECTION 8: Benchmark Comparison ===
    st.header(" Benchmark vs Candidate Pool Comparison")
    
    # Prepare benchmark data
    benchmark_employees = df[df['employee_id'].isin(benchmark_ids)]['employee_id'].unique()
    other_employees = df[~df['employee_id'].isin(benchmark_ids)]['employee_id'].unique()
    
    benchmark_scores = df[df['employee_id'].isin(benchmark_employees)].groupby('tgv_name')['tgv_match_rate'].mean()
    other_scores = df[df['employee_id'].isin(other_employees)].groupby('tgv_name')['tgv_match_rate'].mean()
    
    comparison_df = pd.DataFrame({
        'Competency': benchmark_scores.index,
        'Benchmark Average': benchmark_scores.values,
        'Candidate Pool Average': other_scores.values
    })
    comparison_df['Gap'] = comparison_df['Benchmark Average'] - comparison_df['Candidate Pool Average']
    
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        name='Benchmark Employees',
        x=comparison_df['Competency'],
        y=comparison_df['Benchmark Average'],
        marker_color='#667eea'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Candidate Pool',
        x=comparison_df['Competency'],
        y=comparison_df['Candidate Pool Average'],
        marker_color='#f093fb'
    ))
    
    fig_comparison.update_layout(
        title='Benchmark vs Candidate Pool Comparison',
        xaxis_title='Competency Group',
        yaxis_title='Average Match Rate (%)',
        barmode='group',
        height=500
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Gap analysis table
    st.subheader(" Competency Gaps")
    
    comparison_styled = comparison_df.style.format({
        'Benchmark Average': '{:.1f}%',
        'Candidate Pool Average': '{:.1f}%',
        'Gap': '{:.1f}%'
    }).background_gradient(subset=['Gap'], cmap='RdYlGn')
    
    st.dataframe(comparison_styled, use_container_width=True)
    
    # === SECTION 9: Diversity Analysis ===
    st.header(" Talent Pool Diversity Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Directorate distribution
        directorate_dist = ranking_df['directorate'].value_counts()
        fig_dir = px.pie(
            values=directorate_dist.values,
            names=directorate_dist.index,
            title='Distribution by Directorate',
            hole=0.4
        )
        st.plotly_chart(fig_dir, use_container_width=True)
    
    with col2:
        # Education distribution from detailed data
        edu_data = df[['employee_id', 'tv_name', 'user_score']].copy()
        edu_data = edu_data[edu_data['tv_name'] == 'Education Level'].drop_duplicates()
        
        if len(edu_data) > 0:
            edu_dist = edu_data['user_score'].value_counts()
            fig_edu = px.pie(
                values=edu_dist.values,
                names=edu_dist.index,
                title='Distribution by Education Level',
                hole=0.4
            )
            st.plotly_chart(fig_edu, use_container_width=True)
    
    # Final summary
    st.markdown("---")
    st.markdown("###  Executive Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        high_performers = (ranking_df['final_match_rate'] >= 80).sum()
        st.markdown(f"""
        <div class='insight-box' style='background-color:#000; color:#fff; border-left-color: green;'>
        <h3 style='color: #fff;'>{high_performers}</h3>
        <p style='color:#fff;'>High Performers<br/>(≥80% match)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        moderate_performers = ((ranking_df['final_match_rate'] >= 60) & (ranking_df['final_match_rate'] < 80)).sum()
        st.markdown(f"""
        <div class='insight-box' style='background-color:#000; color:#fff; border-left-color: orange;'>
        <h3 style='color: #fff;'>{moderate_performers}</h3>
        <p style='color:#fff;'>Moderate Performers<br/>(60-79% match)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        development_needed = (ranking_df['final_match_rate'] < 60).sum()
        st.markdown(f"""
        <div class='insight-box' style='background-color:#000; color:#fff; border-left-color: red;'>
        <h3 style='color: #fff;'>{development_needed}</h3>
        <p style='color:#fff;'>Development Needed<br/>(<60% match)</p>
        </div>
        """, unsafe_allow_html=True)
