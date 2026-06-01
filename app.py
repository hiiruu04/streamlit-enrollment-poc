import streamlit as st
import sqlite3
import pandas as pd
import random

# ==========================================
# 1. DATABASE INITIALIZATION & SCHEMA
# ==========================================
db_name = "me_simulation.db"

def init_db():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_code TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            semester INTEGER NOT NULL,
            pillar TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_code TEXT,
            grade_point REAL,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(course_code) REFERENCES courses(course_code)
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        curriculum = [
            ("ME101", "Statics", 1, "Mechanics & Design"),
            ("ME102", "Intro to Thermal Sciences", 1, "Thermo-Fluids"),
            ("ME103", "Engineering Materials", 1, "Manufacturing & Materials"),
            ("ME201", "Dynamics", 2, "Mechanics & Design"),
            ("ME202", "Thermodynamics I", 2, "Thermo-Fluids"),
            ("ME203", "Manufacturing Processes", 2, "Manufacturing & Materials"),
            ("ME301", "Mechanics of Materials", 3, "Mechanics & Design"),
            ("ME302", "Fluid Mechanics I", 3, "Thermo-Fluids"),
            ("ME303", "Material Selection in Design", 3, "Manufacturing & Materials"),
            ("ME401", "Machine Component Design", 4, "Mechanics & Design"),
            ("ME402", "Thermodynamics II", 4, "Thermo-Fluids"),
            ("ME403", "Computer-Aided Manufacturing", 4, "Manufacturing & Materials"),
            ("ME501", "Kinematics & Dynamics", 5, "Mechanics & Design"),
            ("ME502", "Fluid Mechanics II", 5, "Thermo-Fluids"),
            ("ME503", "Advanced Manufacturing", 5, "Manufacturing & Materials"),
            ("ME601", "Finite Element Analysis", 6, "Mechanics & Design"),
            ("ME602", "Heat Transfer", 6, "Thermo-Fluids"),
            ("ME603", "Robotics & Automation", 6, "Manufacturing & Materials"),
            ("ME701", "Mechanical Vibrations", 7, "Mechanics & Design"),
            ("ME702", "Computational Fluid Dynamics", 7, "Thermo-Fluids"),
            ("ME703", "Quality Control & Reliability", 7, "Manufacturing & Materials"),
            ("ME801", "Capstone Design Project", 8, "Mechanics & Design"),
            ("ME802", "Energy Systems Engineering", 8, "Thermo-Fluids"),
            ("ME803", "Industry 4.0 for ME", 8, "Manufacturing & Materials")
        ]
        cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?)", curriculum)
    conn.commit()
    conn.close()

init_db()

def generate_mock_student(name, bias_pillar):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
    student_id = cursor.lastrowid
    cursor.execute("SELECT course_code, pillar FROM courses")
    all_courses = cursor.fetchall()
    
    grades_to_insert = []
    for course_code, pillar in all_courses:
        if pillar == bias_pillar:
            grade = round(random.uniform(3.4, 4.0), 2)
        else:
            grade = round(random.uniform(2.0, 3.4), 2)
        grades_to_insert.append((student_id, course_code, grade))
        
    cursor.executemany("INSERT INTO grades (student_id, course_code, grade_point) VALUES (?, ?, ?)", grades_to_insert)
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(db_name)
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

def get_student_metrics(student_id):
    conn = sqlite3.connect(db_name)
    query = f'''
        SELECT g.course_code, c.course_name, c.semester, c.pillar, g.grade_point
        FROM grades g
        JOIN courses c ON g.course_code = c.course_code
        WHERE g.student_id = {student_id}
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==========================================
# 2. STREAMLIT UI & PERSONA ROUTING
# ==========================================
st.set_page_config(page_title="MechEng Talent Analytics", layout="wide")

# Persistent Demo Controls in Sidebar
st.sidebar.title("🎮 Demo Control Panel")
persona = st.sidebar.selectbox(
    "Switch User View Persona:",
    [
        "1. Corporate Recruiter Portal", 
        "2. Student & Parent Dashboard", 
        "3. University Administrator",
        "4. Government Scholarship Agency"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Quick Data Injector")
quick_name = st.sidebar.text_input("Simulate New Student Name", value="Jane Doe")
quick_bias = st.sidebar.selectbox("Assign Core Aptitude", ["Mechanics & Design", "Thermo-Fluids", "Manufacturing & Materials"])

if st.sidebar.button("Inject Student Data & Refresh"):
    generate_mock_student(quick_name, quick_bias)
    st.sidebar.success(f"Injected {quick_name} successfully!")
    st.rerun()

students_df = get_all_students()

# ------------------------------------------
# PERSONA 1: CORPORATE RECRUITER
# ------------------------------------------
if persona == "1. Corporate Recruiter Portal":
    st.title("🏢 Corporate Talent Acquisition Engine")
    st.caption("Targeted engineering talent recruitment based on deep curricular competency mapping.")
    
    if students_df.empty:
        st.info("Use the 'Quick Data Injector' in the sidebar to add simulation profiles first.")
    else:
        target_pillar = st.selectbox(
            "Filter Pipelines by Niche Technical Mastery:",
            ["Mechanics & Design", "Thermo-Fluids", "Manufacturing & Materials"]
        )
        
        conn = sqlite3.connect(db_name)
        rank_query = f'''
            SELECT s.name as [Candidate Name], AVG(g.grade_point) as [Specialty GPA]
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            JOIN courses c ON g.course_code = c.course_code
            WHERE c.pillar = '{target_pillar}'
            GROUP BY s.student_id
            ORDER BY [Specialty GPA] DESC
        '''
        leaderboard_df = pd.read_sql_query(rank_query, conn)
        conn.close()
        
        st.subheader(f"Top Vetted Candidates for: {target_pillar}")
        st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔍 Deep-Dive Candidate Assessment")
        selected_candidate = st.selectbox("Select Candidate for Full Competency Breakdown", students_df['name'].tolist())
        c_id = students_df[students_df['name'] == selected_candidate]['student_id'].values[0]
        
        metrics_df = get_student_metrics(c_id)
        pillar_averages = metrics_df.groupby('pillar')['grade_point'].mean()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Cumulative GPA", f"{metrics_df['grade_point'].mean():.2f}")
        c2.metric(f"{target_pillar} Competency", f"{pillar_averages.get(target_pillar, 0.0):.2f}")
        c3.metric("Recruiter Verdict", "Highly Recommended" if pillar_averages.get(target_pillar, 0.0) >= 3.4 else "Standard Profile")

# ------------------------------------------
# PERSONA 2: STUDENT & PARENT PORTAL
# ------------------------------------------
elif persona == "2. Student & Parent Dashboard":
    st.title("🎓 Student Academic Growth & Career Compass")
    st.caption("Understand your core performance pillars and map out your post-graduation options.")
    
    if students_df.empty:
        st.info("Use the 'Quick Data Injector' in the sidebar to add simulation profiles first.")
    else:
        selected_student = st.selectbox("Select Your Profile:", students_df['name'].tolist())
        s_id = students_df[students_df['name'] == selected_student]['student_id'].values[0]
        
        metrics_df = get_student_metrics(s_id)
        pillar_analysis = metrics_df.groupby('pillar')['grade_point'].mean().reset_index()
        top_pillar = pillar_analysis.loc[pillar_analysis['grade_point'].idxmax()]['pillar']
        
        st.subheader("Your Technical Strength Profile")
        st.bar_chart(pillar_analysis.set_index('pillar'), y="grade_point", color="#2ca02c")
        
        st.subheader("🚀 Career Pathway Recommendations")
        if top_pillar == "Mechanics & Design":
            st.success("**Primary Pathway: Structural & Machine Systems Design.** Excellent fit for CAD/CAE Design, Automotive Chassis development, and Structural Analysis roles.")
        elif top_pillar == "Thermo-Fluids":
            st.success("**Primary Pathway: Energy Systems & Thermal Engineering.** Recommended industries include Renewable Energy Plant Operations, HVAC System Architecture, and Computational Fluid Dynamics (CFD) optimization.")
        elif top_pillar == "Manufacturing & Materials":
            st.success("**Primary Pathway: Advanced Manufacturing & Industry 4.0.** Highly suited for Automation/Robotics track, Plant Operations Management, or Supply Chain Quality Engineering.")

# ------------------------------------------
# PERSONA 3: UNIVERSITY ADMINISTRATOR
# ------------------------------------------
elif persona == "3. University Administrator":
    st.title("🏫 Academic Department Management Console")
    st.caption("Strategic institutional tools for tracking curriculum quality and program health metrics.")
    
    conn = sqlite3.connect(db_name)
    dept_query = '''
        SELECT c.pillar, AVG(g.grade_point) as [Average Grade]
        FROM grades g
        JOIN courses c ON g.course_code = c.course_code
        GROUP BY c.pillar
    '''
    dept_df = pd.read_sql_query(dept_query, conn)
    conn.close()
    
    st.subheader("Department-Wide Competency Benchmark")
    st.dataframe(dept_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("📉 Curriculum Intervention & Quality Triggers")
    low_performing_pillars = dept_df[dept_df['Average Grade'] < 2.80]
    if low_performing_pillars.empty:
        st.success("All technical pillars meet standard baseline benchmarks. Academic performance tracking is healthy.")
    else:
        for _, row in low_performing_pillars.iterrows():
            st.error(f"⚠️ Action Required: **{row['pillar']}** is performing below standard thresholds at **{row['Average Grade']:.2f}** GPA.")

# ------------------------------------------
# PERSONA 4: GOVERNMENT SCHOLARSHIP AGENCY
# ------------------------------------------
elif persona == "4. Government Scholarship Agency":
    st.title("🏛️ State Scholarship Vetting & Strategic Talent Portal")
    st.caption("Optimize public funding allocation for postgraduate programs by identifying high-viability researchers.")
    
    if students_df.empty:
        st.info("Use the 'Quick Data Injector' in the sidebar to add simulation profiles first.")
    else:
        st.subheader("💡 Strategic National Research Alignment")
        national_priority = st.selectbox(
            "Select State Strategic Initiative Focus Area:",
            [
                "Renewable Energy & Climate Adaptation (Requires Thermo-Fluids)",
                "Advanced Infrastructure & Micro-Grid Structures (Requires Mechanics & Design)",
                "National Automation & Strategic Smart Manufacturing (Requires Manufacturing & Materials)"
            ]
        )
        
        # Map the national priority back to the technical pillar
        pillar_map = {
            "Renewable Energy & Climate Adaptation (Requires Thermo-Fluids)": "Thermo-Fluids",
            "Advanced Infrastructure & Micro-Grid Structures (Requires Mechanics & Design)": "Mechanics & Design",
            "National Automation & Strategic Smart Manufacturing (Requires Manufacturing & Materials)": "Manufacturing & Materials"
        }
        selected_pillar = pillar_map[national_priority]
        
        st.write(f"### Screened Applicants Ranked by Funding Viability for **{selected_pillar}**")
        
        # Calculate a custom Funding Score: 70% Specific Pillar Mastery + 30% Global Performance
        conn = sqlite3.connect(db_name)
        funding_query = f'''
            SELECT 
                s.name as [Applicant Name],
                ROUND(AVG(CASE WHEN c.pillar = '{selected_pillar}' THEN g.grade_point END), 2) as [Target Pillar GPA],
                ROUND(AVG(g.grade_point), 2) as [Overall GPA]
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            JOIN courses c ON g.course_code = c.course_code
            GROUP BY s.student_id
            ORDER BY [Target Pillar GPA] DESC, [Overall GPA] DESC
        '''
        agency_df = pd.read_sql_query(funding_query, conn)
        conn.close()
        
        # Calculate a mock viability metric for presentation flair
        if not agency_df.empty:
            agency_df['Funding Viability Index'] = agency_df.apply(
                lambda row: f"{int((row['Target Pillar GPA'] * 0.7 + row['Overall GPA'] * 0.3) / 4.0 * 100)}%", axis=1
            )
        
        st.dataframe(agency_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📋 Agency Grant Allocation Verdict")
        top_candidate = agency_df.iloc[0]['Applicant Name'] if not agency_df.empty else "N/A"
        st.info(f"🏆 **Top Strategic Recommendation:** Based on algorithmic assessment, **{top_candidate}** represents the highest-return investment for postgraduate public sponsorship in this national sector due to zero performance volatility in foundational prerequisites.")