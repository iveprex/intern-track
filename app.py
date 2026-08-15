import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

st.set_page_config(page_title="InternTrack", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

DATA = Path("data/internships.csv")
STATUS = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"]

@st.cache_data
def load_data():
    df = pd.read_csv(DATA)
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    return df

def save_data(df):
    out = df.copy()
    out["deadline"] = pd.to_datetime(out["deadline"]).dt.strftime("%Y-%m-%d")
    out.to_csv(DATA, index=False)

df = load_data()

st.markdown("""
<style>
:root { --muted:#6b7280; }
.block-container {max-width: 1320px; padding-top: 2rem; padding-bottom: 4rem;}
section[data-testid="stSidebar"] {border-right:1px solid rgba(128,128,128,.15);}
h1 {font-size:2.35rem!important; letter-spacing:-.055em; font-weight:700;}
h2 {letter-spacing:-.035em;}
[data-testid="stMetric"] {border:1px solid rgba(128,128,128,.18); border-radius:14px; padding:15px 17px;}
div[data-testid="stDataFrame"] {border-radius:12px; overflow:hidden;}
.brand {font-weight:800; font-size:1.2rem; letter-spacing:-.03em;}
.eyebrow {font-size:.72rem; text-transform:uppercase; letter-spacing:.16em; color:#737373; margin-bottom:.35rem;}
.note {font-size:.88rem; color:#737373;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">INTERNT‍RACK</div>', unsafe_allow_html=True)
    st.caption("Career operations workspace")
    st.divider()

    page = st.radio("Workspace", ["Overview", "Opportunities", "Applications", "Add opportunity", "Insights"])

    st.divider()
    st.caption("Built as a self-initiated CareerTech product.")
    st.caption("Python · Streamlit · Pandas")

if page == "Overview":
    st.markdown('<div class="eyebrow">Career workspace</div>', unsafe_allow_html=True)
    st.title("Internship pipeline")
    st.caption("A focused command centre for discovering, tracking and managing opportunities.")

    total = len(df)
    applied = int(df["status"].isin(["Applied","Assessment","Interview","Offer"]).sum())
    interviews = int((df["status"] == "Interview").sum())
    offers = int((df["status"] == "Offer").sum())

    a,b,c,d = st.columns(4)
    a.metric("Opportunities", total)
    b.metric("Active applications", applied)
    c.metric("Interviews", interviews)
    d.metric("Offers", offers)

    st.divider()
    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("Pipeline")
        pipeline = df["status"].value_counts().reindex(STATUS, fill_value=0)
        st.bar_chart(pipeline, height=300)

    with right:
        st.subheader("Upcoming deadlines")
        upcoming = df[(df["deadline"] >= pd.Timestamp.today().normalize()) & (df["status"] != "Rejected")].sort_values("deadline").head(6).copy()
        if upcoming.empty:
            st.info("No upcoming deadlines.")
        else:
            upcoming["deadline"] = upcoming["deadline"].dt.strftime("%d %b %Y")
            st.dataframe(upcoming[["company","role","deadline","status"]], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Recent opportunities")
    recent = df.sort_values("added_on", ascending=False).head(8).copy()
    st.dataframe(recent[["company","role","location","work_mode","stipend","status"]],
                 use_container_width=True, hide_index=True)

elif page == "Opportunities":
    st.markdown('<div class="eyebrow">Opportunity database</div>', unsafe_allow_html=True)
    st.title("Opportunities")
    st.caption("Search and narrow the roles that fit your profile.")

    q = st.text_input("Search", placeholder="Company, role, skill or keyword")
    c1,c2,c3 = st.columns(3)
    with c1:
        modes = st.multiselect("Work mode", sorted(df["work_mode"].unique()), default=sorted(df["work_mode"].unique()))
    with c2:
        locations = st.multiselect("Location", sorted(df["location"].unique()), default=sorted(df["location"].unique()))
    with c3:
        statuses = st.multiselect("Status", STATUS, default=STATUS)

    view = df[df["work_mode"].isin(modes) & df["location"].isin(locations) & df["status"].isin(statuses)].copy()
    if q:
        mask = view.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False))
        view = view[mask.any(axis=1)]

    st.caption(f"{len(view)} opportunities match the current filters.")
    view["deadline"] = view["deadline"].dt.strftime("%d %b %Y")
    st.dataframe(view[["company","role","location","work_mode","stipend","deadline","status","skills"]],
                 use_container_width=True, hide_index=True)

elif page == "Applications":
    st.markdown('<div class="eyebrow">Application management</div>', unsafe_allow_html=True)
    st.title("Applications")
    st.caption("Keep every active application and next step in one place.")

    active = df[df["status"].isin(["Applied","Assessment","Interview","Offer"])].copy()
    if active.empty:
        st.info("No active applications yet.")
    else:
        for status in ["Applied","Assessment","Interview","Offer"]:
            group = active[active["status"] == status]
            if not group.empty:
                st.subheader(status)
                for idx, row in group.iterrows():
                    with st.container(border=True):
                        c1,c2,c3,c4 = st.columns([2.3,2.4,1.4,1])
                        c1.markdown(f"**{row['role']}**  \n{row['company']}")
                        c2.caption(f"{row['location']} · {row['work_mode']} · {row['stipend']}")
                        c3.caption(f"Deadline\n{row['deadline'].strftime('%d %b %Y')}")
                        new_status = c4.selectbox("Status", STATUS, index=STATUS.index(row["status"]), key=f"status_{idx}")
                        if new_status != row["status"]:
                            df.loc[idx, "status"] = new_status
                            save_data(df)
                            st.rerun()

elif page == "Add opportunity":
    st.markdown('<div class="eyebrow">Opportunity intake</div>', unsafe_allow_html=True)
    st.title("Add opportunity")
    st.caption("Capture the details that matter before an application disappears in a browser tab.")

    with st.form("add_opportunity"):
        c1,c2 = st.columns(2)
        with c1:
            company = st.text_input("Company")
            role = st.text_input("Role")
            location = st.text_input("Location")
            work_mode = st.selectbox("Work mode", ["Remote","Hybrid","On-site"])
        with c2:
            stipend = st.text_input("Stipend / compensation", placeholder="e.g. ₹15,000 / month")
            deadline = st.date_input("Application deadline", value=date.today())
            status = st.selectbox("Current status", STATUS)
            skills = st.text_input("Key skills", placeholder="Python, SQL, React")
        source = st.text_input("Application URL")
        submitted = st.form_submit_button("Add opportunity", type="primary")

    if submitted:
        if not company.strip() or not role.strip():
            st.error("Company and role are required.")
        else:
            new = pd.DataFrame([{
                "company": company.strip(),
                "role": role.strip(),
                "location": location.strip() or "Not specified",
                "work_mode": work_mode,
                "stipend": stipend.strip() or "Not specified",
                "deadline": pd.Timestamp(deadline),
                "status": status,
                "skills": skills.strip(),
                "source": source.strip(),
                "added_on": pd.Timestamp.today().strftime("%Y-%m-%d")
            }])
            df = pd.concat([df,new], ignore_index=True)
            save_data(df)
            st.success("Opportunity added to your pipeline.")
            st.rerun()

elif page == "Insights":
    st.markdown('<div class="eyebrow">Career analytics</div>', unsafe_allow_html=True)
    st.title("Insights")
    st.caption("A lightweight view of how your application pipeline is moving.")

    status_counts = df["status"].value_counts().reindex(STATUS, fill_value=0)
    total = len(df)
    active = status_counts[["Applied","Assessment","Interview","Offer"]].sum()
    interview_rate = (status_counts["Interview"] / active * 100) if active else 0
    offer_rate = (status_counts["Offer"] / active * 100) if active else 0

    a,b,c = st.columns(3)
    a.metric("Active pipeline", int(active))
    b.metric("Interview rate", f"{interview_rate:.1f}%")
    c.metric("Offer rate", f"{offer_rate:.1f}%")

    st.divider()
    left,right = st.columns(2)
    with left:
        st.subheader("Status distribution")
        st.bar_chart(status_counts, height=300)
    with right:
        st.subheader("Work-mode mix")
        st.bar_chart(df["work_mode"].value_counts(), height=300)

    st.divider()
    st.subheader("Skills appearing most often")
    skills = df["skills"].fillna("").str.split(",").explode().str.strip()
    skills = skills[skills != ""].value_counts().head(10)
    st.dataframe(skills.rename("opportunities").to_frame(), use_container_width=True)

st.divider()
st.caption("InternTrack is a self-initiated portfolio project. Sample opportunities are fictional demonstration data.")
