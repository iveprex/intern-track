import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Aman Finance", page_icon="📊", layout="wide")

DATA_PATH = Path("data/transactions.csv")
CATEGORIES = ["Food", "Transport", "Education", "Shopping", "Bills", "Entertainment", "Health", "Other"]

def load_data():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=["date", "type", "category", "amount", "description"])
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df

def save_data(df):
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    DATA_PATH.parent.mkdir(exist_ok=True)
    out.to_csv(DATA_PATH, index=False)

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1250px;}
h1 {font-size: 2.2rem !important; letter-spacing: -0.04em;}
.metric-card {padding: 18px 20px; border: 1px solid rgba(128,128,128,.20);
border-radius: 14px; background: rgba(128,128,128,.06);}
.small-muted {color: #777; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

df = load_data()

with st.sidebar:
    st.markdown("## AMAN FINANCE")
    st.caption("Personal financial analytics")
    page = st.radio("Workspace", ["Dashboard", "Transactions", "Add transaction", "Data"])

    st.divider()
    st.caption("Self-initiated portfolio project")
    st.caption("Python • Streamlit • Pandas")

if page == "Dashboard":
    st.title("Financial Overview")
    st.caption("A clear view of income, spending and savings.")

    if df.empty:
        st.info("No transactions yet. Add a few transactions from the sidebar to populate your dashboard.")
        st.stop()

    month_options = sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    selected_month = st.selectbox("Reporting month", ["All time"] + month_options)

    view = df if selected_month == "All time" else df[df["date"].dt.to_period("M").astype(str) == selected_month]

    income = view.loc[view["type"] == "income", "amount"].sum()
    expenses = view.loc[view["type"] == "expense", "amount"].sum()
    savings = income - expenses
    rate = (savings / income * 100) if income else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income", f"₹{income:,.0f}")
    c2.metric("Expenses", f"₹{expenses:,.0f}")
    c3.metric("Net savings", f"₹{savings:,.0f}")
    c4.metric("Savings rate", f"{rate:.1f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Cash flow")
        flow = view.groupby(["date", "type"])["amount"].sum().unstack(fill_value=0)
        for col in ["income", "expense"]:
            if col not in flow.columns:
                flow[col] = 0
        st.line_chart(flow[["income", "expense"]], height=300)

    with right:
        st.subheader("Spending by category")
        category = view[view["type"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
        if category.empty:
            st.caption("No expense data for this period.")
        else:
            st.bar_chart(category, height=300)

    st.divider()
    st.subheader("Recent activity")
    recent = view.sort_values("date", ascending=False).head(8).copy()
    recent["date"] = recent["date"].dt.strftime("%d %b %Y")
    recent["amount"] = recent["amount"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(recent[["date", "type", "category", "amount", "description"]],
                 use_container_width=True, hide_index=True)

elif page == "Transactions":
    st.title("Transactions")
    st.caption("Review and manage recorded financial activity.")

    if df.empty:
        st.info("No transactions available.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.multiselect("Type", ["income", "expense"], default=["income", "expense"])
    with col2:
        category_filter = st.multiselect("Category", sorted(df["category"].dropna().unique()), default=sorted(df["category"].dropna().unique()))

    filtered = df[df["type"].isin(type_filter) & df["category"].isin(category_filter)].copy()
    filtered["date"] = filtered["date"].dt.strftime("%d %b %Y")
    filtered["amount"] = filtered["amount"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(filtered.sort_values("date", ascending=False),
                 use_container_width=True, hide_index=True)

elif page == "Add transaction":
    st.title("Add transaction")
    st.caption("Record a new income or expense.")

    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            tx_date = st.date_input("Date", value=date.today())
            tx_type = st.selectbox("Type", ["income", "expense"])
            category = st.selectbox("Category", ["Salary", "Freelance", "Investment"] + CATEGORIES)
        with col2:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            description = st.text_input("Description", placeholder="e.g. Monthly salary")
        submitted = st.form_submit_button("Save transaction", type="primary")

    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            new_row = pd.DataFrame([{
                "date": pd.Timestamp(tx_date),
                "type": tx_type,
                "category": category,
                "amount": amount,
                "description": description.strip()
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("Transaction saved successfully.")
            st.rerun()

elif page == "Data":
    st.title("Data")
    st.caption("Import, inspect and export the underlying dataset.")

    uploaded = st.file_uploader("Import CSV", type=["csv"])
    if uploaded:
        imported = pd.read_csv(uploaded)
        required = {"date", "type", "category", "amount", "description"}
        if required.issubset(imported.columns):
            save_data(imported)
            st.success("Dataset imported.")
            st.rerun()
        else:
            st.error("CSV must contain: date, type, category, amount, description.")

    st.download_button(
        "Download current CSV",
        data=df.to_csv(index=False),
        file_name="transactions.csv",
        mime="text/csv",
        disabled=df.empty
    )

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
