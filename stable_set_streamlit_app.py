import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
import base64

# --- Favicon ως base64 ---
favicon_base64 = """
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAABGFBMVEUAAABcXFxVVVXa
2to5OTnW1tZ1dXXq6urx8fHq6urp6enX19fd3d3e3t6SkpKWlpbn5+fb29vOzs7u7u7p
6emLi4vOzs7Y2NjR0dG9vb0eHh7FxcXGxsaioqKOjo5ISEg4ODgxMTH///8zMzMcHBwv
Ly9JSUnY2NjT09NISEjMzMyDg4OGhoaRkZHZ2dnBwcF5eXmAgIB0dHRBQUEZGRnPz8/t
7e2EhIRaWlo7OzvX19dLS0sAAABHR0cNDA1TU1OJioqUlJSgoKAFhYX39/fV1dXU1NRs
bGwpKSksLCwtLS1aWlojIyMcHBz9/f2urq6VlZXJycljY2MkJCRra2vq6uqBgYGZmZnr
6+uioqKLioqUlJSjo6M5OTmVlZVWVlbAwMCwsLCZmZmVlZXDw8PU1NRZWVnHx8eFhYUu
Li45OTmTk5Pa2toWFhZaWlo2NjZKSkq9vb0fHx9AQECkpKS5ubnY2NhISEgqKiopKSlA
QEBycnIiIiIrKysrKys1NTU6OjoNDQ1dXV1cXFxXV1dPT09SUlJSUlKmpqZvE8Z7AAAB
VklEQVQY05WOSxaCMBCFZ+0NClLVh3I0SkpWlbr///W1CgRn3C3gZjHuHB4bOmu6DQpU
6m0CGtQYiq1ZGTphE++5NhnV3XkjCpRKZDKRtczrf1i05JZN1HKN8c10wtLv0WkTnFgh
CzRdYKv0xpmiqlae2mc4xl2w2fAItu1hqA7yGdbkE6zPTGYb96D7PgtF4dcuPAPaqNqz
H7pLHo1MgLK3g4PgJkZhDRkBvRs8TpWeG4rv/f/zwFcCX4EpT3g4vyu1egTwuacC4qg+
pPdrXhf7wF5BOx1bMn+g3KXoR7hzDhx8AN2QiAwCjGZfD2AAAAAElFTkSuQmCC
"""

favicon_html = f"""
<link rel="icon" href="data:image/png;base64,{favicon_base64.strip()}" type="image/png" />
"""

st.set_page_config(page_title="Stable Set Explorer", layout="wide")
st.markdown(favicon_html, unsafe_allow_html=True)

st.title("📦 Stable Set Explorer for Social Choice Theory")
st.write("Upload an Excel or CSV file with voter preferences (each column = one voter).")

uploaded_file = st.file_uploader("📁 Upload your profile file", type=["xls", "xlsx", "csv"])

# ------------------------ Hasse Diagram Function ------------------------
def draw_hasse_diagram(G):
    if not nx.is_directed_acyclic_graph(G):
        return None
    H = nx.transitive_reduction(G)
    pos = nx.spring_layout(H, seed=42)
    fig, ax = plt.subplots()
    nx.draw(H, pos, with_labels=True, node_color="lightgreen", node_size=2000,
            font_size=14, font_weight='bold', arrows=True, ax=ax)
    ax.set_title("Hasse Diagram (Transitive Reduction)", fontsize=14)
    return fig

# ------------------------ Main App Logic ------------------------
if uploaded_file:
    has_header = st.radio("Does your file contain a header row?", ("Yes", "No"))

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=0 if has_header == "Yes" else None)
    else:
        df = pd.read_excel(uploaded_file, header=0 if has_header == "Yes" else None)

    df.columns = [f"Voter {i+1}" for i in range(df.shape[1])]
    st.subheader("📋 Uploaded Preference Profile")
    st.dataframe(df)

    candidates = pd.unique(df.values.ravel())
    candidates = [c for c in candidates if pd.notna(c)]

    def compute_majority_graph(voter_preferences, candidates):
        from collections import defaultdict
        pairwise_counts = defaultdict(int)
        for a, b in combinations(candidates, 2):
            a_wins = sum(df[col].tolist().index(a) < df[col].tolist().index(b) for col in df.columns)
            b_wins = sum(df[col].tolist().index(b) < df[col].tolist().index(a) for col in df.columns)
            if a_wins > len(df.columns) / 2:
                pairwise_counts[(a, b)] = 1
            elif b_wins > len(df.columns) / 2:
                pairwise_counts[(b, a)] = 1
        G = nx.DiGraph()
        G.add_nodes_from(candidates)
        G.add_edges_from(pairwise_counts.keys())
        return G

    def van_deemen(G):
        return {x for x in G.nodes if all(not G.has_edge(y, x) for y in G.nodes if y != x)}

    def extended_stable(G):
        return {x for x in G.nodes if all(
            any(not G.has_edge(y, x) for y in G.nodes if y != z) for z in G.nodes if z != x)}

    def w_stable(G):
        return {x for x in G.nodes if not any(G.has_edge(y, x) for y in G.nodes if y != x)}

    def duggan(G):
        return {x for x in G.nodes if all(not G.has_edge(y, x) for y in G.nodes if y != x)
                and any(G.has_edge(x, y) for y in G.nodes if y != x)}

    def generalized_stable(G):
        result = set()
        for x in G.nodes:
            safe = True
            others = [y for y in G.nodes if y != x]
            for r in range(1, len(others)+1):
                for group in combinations(others, r):
                    if all(G.has_edge(y, x) for y in group):
                        safe = False
                        break
                if not safe:
                    break
            if safe:
                result.add(x)
        return result

    # --- Νέος ορισμός συνάρτησης m_stable ---
    def m_stable(G):
        """
        Υπολογίζει το m-stable set του γράφου G.
        Ένας κόμβος είναι m-stable αν δεν ηττάται από καμία συμμαχία
        που αποτελείται από κόμβους που δεν ηττώνται από αυτόν.
        """
        stable_set = set()
        nodes = set(G.nodes)

        for x in nodes:
            non_defeated_by_x = {y for y in nodes if not G.has_edge(x, y)}
            dominated = False
            for r in range(1, len(non_defeated_by_x) + 1):
                for coalition in combinations(non_defeated_by_x, r):
                    if all(G.has_edge(member, x) for member in coalition):
                        dominated = True
                        break
                if dominated:
                    break
            if not dominated:
                stable_set.add(x)

        return stable_set

    G = compute_majority_graph(df, candidates)

    sets = {
        "Van Deemen Stable Set": van_deemen(G),
        "Extended Stable Set": extended_stable(G),
        "W-Stable Set": w_stable(G),
        "Duggan Set": duggan(G),
        "Generalized Stable Set": generalized_stable(G),
        "M-Stable Set": m_stable(G),  # Νέο σύνολο
    }

    explanations = {
        "Van Deemen Stable Set": "🛡️ No other alternative beats this one.",
        "Extended Stable Set": "🧠 Cannot be beaten by any coalition.",
        "W-Stable Set": "⚖️ Not defeated by any single alternative.",
        "Duggan Set": "🎯 Undefeated and beats at least one opponent.",
        "Generalized Stable Set": "📦 Resistant to all majority coalitions.",
        "M-Stable Set": "🔒 Not collectively dominated by any coalition of candidates it does not defeat."
    }

    for name, result in sets.items():
        st.subheader(name)
        st.caption(explanations.get(name, ""))
        st.write(sorted(result) if result else "∅")

    st.subheader("🔄 Dominance Graph")
    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots()
    nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=2000,
            font_size=14, font_weight='bold', arrows=True, ax=ax)
    st.pyplot(fig)

    st.subheader("🪜 Hasse Diagram (Transitive Reduction)")
    fig2 = draw_hasse_diagram(G)
    if fig2:
        st.pyplot(fig2)
    else:
        st.warning("Cannot display Hasse diagram: the dominance graph is not acyclic (contains cycles).")

    st.subheader("🧠 Condorcet Winner")
    condorcet_winner = None
    for x in candidates:
        if all(G.has_edge(x, y) for y in candidates if y != x):
            condorcet_winner = x
            break
    if condorcet_winner:
        st.success(f"The Condorcet winner is **{condorcet_winner}**.")
    else:
        st.warning("No Condorcet winner exists — Condorcet paradox detected!")

    st.subheader("📊 Borda Count")
    borda_scores = {c: 0 for c in candidates}
    n = len(candidates)
    for col in df.columns:
        ranking = list(df[col].dropna())
        for idx, candidate in enumerate(ranking):
            borda_scores[candidate] += n - idx - 1
    borda_df = pd.DataFrame(sorted(borda_scores.items(), key=lambda x: -x[1]), columns=["Candidate", "Borda Score"])
    st.dataframe(borda_df)

# ------------------------ Footer ------------------------
st.markdown("""
<hr style="border: 1px solid #ccc; margin-top: 3em;">

<div style="
    background-color: #1f2937;
    color: #f3f4f6;
    padding: 14px;
    border-radius: 10px;
    text-align: center;
    font-size: 15px;
    margin-top: 40px;
    line-height: 1.6;">
    Developed with ❤️ by <strong>Nikolaos Sampanis</strong> · 2025<br>
    🧠 Condorcet Analysis · 📊 Borda Count · 📦 Stable Sets Explorer<br>
    <a href="https://github.com/nsampanis/stable-set-app" target="_blank" style="color: #60a5fa; text-decoration: none;">
        🌐 View on GitHub
    </a>
</div>
""", unsafe_allow_html=True)
