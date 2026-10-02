import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="India Data Job Skills", layout="wide")


@st.cache_data
def load():
    return pd.read_csv("data/postings.csv"), pd.read_csv("data/posting_skills.csv")


postings, ps = load()

ROLE_GROUPS = {
    "All roles": ["analyst", "bi", "data_science", "data_engineering", "other"],
    "Analyst / BI": ["analyst", "bi"],
    "Data science": ["data_science"],
    "Data engineering": ["data_engineering"],
}

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
role = st.sidebar.selectbox("Role group", list(ROLE_GROUPS))
real_cities = sorted(c for c in postings.city.dropna().unique() if c not in ("Other", "Unspecified"))
cities = st.sidebar.multiselect("City", real_cities)
levels = st.sidebar.multiselect("Seniority", ["junior", "mid", "senior"])
hide_soft = st.sidebar.checkbox("Hide soft skills", value=True)

f = postings[postings.role_family.isin(ROLE_GROUPS[role])]
if cities:
    f = f[f.city.isin(cities)]
if levels:
    f = f[f.seniority.isin(levels)]
n = len(f)

st.title("What skills do Indian data jobs ask for?")
st.caption(
    "Sample of Adzuna job postings. This is a sample, not the whole market, and job "
    "descriptions are truncated, so skill counts are understated."
)
if n == 0:
    st.warning("No postings match these filters.")
    st.stop()

s = ps[ps.posting_id.isin(f.id)]
if hide_soft:
    s = s[s.category != "soft_skill"]
salaried = f.salary_mid.dropna()

demand = s.groupby("skill_name").posting_id.nunique().sort_values(ascending=False)
top_skill = demand.index[0] if len(demand) else "n/a"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Postings", f"{n:,}")
c2.metric("Median salary", f"₹{salaried.median() / 1e5:.1f}L" if len(salaried) else "n/a")
c3.metric("Postings with salary", f"{100 * len(salaried) / n:.0f}%")
c4.metric("Top skill", top_skill)

tab1, tab2, tab3, tab4 = st.tabs(["Skill demand", "Skills together", "Cities", "Salary"])

with tab1:
    if demand.empty:
        st.info("No skills detected for these filters.")
    else:
        d = (100 * demand.head(12) / n).round(1).reset_index()
        d.columns = ["skill", "pct"]
        fig = px.bar(d, x="pct", y="skill", orientation="h",
                     title=f"{d.skill[0]} appears in {d.pct[0]:.0f}% of these postings",
                     labels={"pct": "% of postings", "skill": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    m = s[["posting_id", "skill_name"]].drop_duplicates()
    pairs = m.merge(m, on="posting_id")
    pairs = pairs[pairs.skill_name_x < pairs.skill_name_y]
    if pairs.empty:
        st.info("Not enough overlapping skills for these filters.")
    else:
        p = (pairs.groupby(["skill_name_x", "skill_name_y"]).size()
                  .reset_index(name="postings").sort_values("postings", ascending=False).head(15))
        p["pair"] = p.skill_name_x + " + " + p.skill_name_y
        fig = px.bar(p, x="postings", y="pair", orientation="h",
                     title=f"{p.pair.iloc[0]} is the most common pairing",
                     labels={"postings": "Postings mentioning both", "pair": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    by_city = f[~f.city.isin(["Other", "Unspecified"])].city.value_counts().head(10).reset_index()
    by_city.columns = ["city", "postings"]
    if by_city.empty:
        st.info("No city data for these filters.")
    else:
        fig = px.bar(by_city, x="postings", y="city", orientation="h",
                     title=f"{by_city.city[0]} has the most postings in this sample",
                     labels={"postings": "Postings", "city": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        unspec = 100 * (f.city == "Unspecified").mean()
        st.caption(f"{unspec:.0f}% of postings list only 'India' or a state, so they are excluded here.")

with tab4:
    min_n = st.slider("Minimum salaried postings per skill", 5, 50, 20)
    sal = s.merge(f[["id", "salary_mid"]], left_on="posting_id", right_on="id").dropna(subset=["salary_mid"])
    g = sal.groupby("skill_name").salary_mid.agg(n="count", median="median")
    g = g[g.n >= min_n].sort_values("median", ascending=False).reset_index()
    if g.empty:
        st.info("Too few salaried postings per skill. Lower the minimum or widen the filters.")
    else:
        g["median_lakh"] = (g["median"] / 1e5).round(1)
        fig = px.bar(g, x="median_lakh", y="skill_name", orientation="h",
                     title=f"Postings mentioning {g.skill_name[0]} have the highest median salary",
                     labels={"median_lakh": "Median salary (₹ lakh / year)", "skill_name": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Skills overlap heavily, so this shows salaries of postings that mention a skill, "
               "not what the skill itself is worth. Small samples are noisy.")
