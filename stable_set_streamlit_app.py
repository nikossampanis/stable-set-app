import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

st.set_page_config(page_title="Stable Set Explorer", layout="wide")

st.title("Stable Set Explorer for Social Choice")
st.write("Upload a preference profile file (.xls, .xlsx, or .csv). Each column should represent a voter's ranked preferences (top to bottom).")

uploaded_file = st.file_uploader("Upload your file", type=["xls", "xlsx", "csv"])

# === Συνάρτηση για Hasse Diagram ===
def draw_hasse_diagram(G):
    """
    Given a directed graph G (representing a dominance relation),
    return a matplotlib figure showing the Hasse diagram (transitive reduction).
    """
    H = nx.transitive_reduction(G)
    pos = nx.spring_layout(H, seed=42)
    fig, ax = plt.subplots()
    nx.draw(H, pos, with_labels=True, node_color="lightgreen", node_size=2000, 
            font_size=14, font_weight='bold', arrows=True, ax=ax)
    ax.set_title("Hasse Diagram (Transitive Reduction of Dominance Graph)", fontsize=14)
    return fig

if uploaded_file:
    st.markdown("### 🧩 File Settings")
    has_header = st.radio("Does your file contain a header row (e.g. 'Voter 1', 'Voter 2')?", ("Yes", "No"))

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=0 if has_header == "Yes" else None)
    else:
        df = pd.read_excel(uploaded_file, header=0 if has_header == "Yes" else None)

    df.columns = [f"Voter {i+1}" for i in range(df.shape[1])]
    st.dataframe(df)

    candidates = pd.unique(df.values.ravel())
    candidates = [c for c in candidates if pd.notna(c)]

    # === Συναρτήσεις Υπολογισμών ===

    def compute_majority_graph(voter_preferences, candidates):
        from collections import defaultdict
        pairwise_counts = defaultdict(int)
        for i in range(len(candidates)):
            for j in range(len(candidates)):
                if i == j:
                    continue
                a, b = candidates[i], candidates[j]
                wins = 0
                for col in voter_preferences.columns:
                    ranks = list(voter_preferences[col].dropna())
                    if ranks.index(a) < ranks.index(b):
                        wins += 1
                if wins > len(voter_preferences.columns) / 2:
                    pairwise_counts[(a, b)] = 1
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
            for r in range(1, len(others) + 1):
                for group in combinations(others, r):
                    if all(G.has_edge(y, x) for y in group):
                        safe = False
                        break
                if not safe:
                    break
            if safe:
                result.add(x)
        return result

    # === Υπολογισμός Γράφου και Συνόλων ===

    G = compute_majority_graph(df, candidates)

    sets = {
        "Generalized Stable Set": generalized_stable(G),
        "Van Deemen Stable Set": van_deemen(G),
        "Extended Stable Set": extended_stable(G),
        "W-Stable Set": w_stable(G),
        "Duggan Set": duggan(G),
    }

    explanations = {
        "Van Deemen Stable Set": "A candidate that is undefeated by any other individual candidate.",
        "Extended Stable Set": "A candidate that cannot be defeated by any coalition when evaluated pairwise.",
        "W-Stable Set": "A candidate not defeated by any single alternative (weak stability).",
        "Duggan Set": "A candidate undefeated and defeating at least one other candidate.",
        "Generalized Stable Set": "A candidate not defeated by any coalition of opponents."
    }

    for name, result in sets.items():
        st.subheader(name)
        st.caption(explanations.get(name, ""))
        st.write(sorted(result) if result else "∅")

    # === Γράφος Κυριαρχίας ===
    st.subheader("Majority (Dominance) Graph")
    pos = nx.spring_layout(G, seed=42)
    fig1, ax1 = plt.subplots()
    nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=2000,
            font_size=16, font_weight='bold', ax=ax1, arrows=True)
    st.pyplot(fig1)

    # === Hasse Diagram ===
    st.subheader("Hasse Diagram (Transitive Reduction)")
    fig2 = draw_hasse_diagram(G)
    st.pyplot(fig2)

    # === Condorcet Winner ===
    st.subheader("🧠 Condorcet Winner")
    condorcet_winner = None
    for x in candidates:
        if all(G.has_edge(x, y) for y in candidates if y != x):
            condorcet_winner = x
            break

    if condorcet_winner:
        st.success(f"The Condorcet winner is **{condorcet_winner}**: beats all others in pairwise comparisons.")
    else:
        st.warning("No Condorcet winner exists — this is a Condorcet paradox! (cyclic majority preferences)")

    # === Borda Count ===
    st.subheader("📊 Borda Count")
    borda_scores = {c: 0 for c in candidates}
    n = len(candidates)
    for col in df.columns:
        ranking = list(df[col].dropna())
        for idx, candidate in enumerate(ranking):
            borda_scores[candidate] += n - idx - 1

    borda_df = pd.DataFrame(sorted(borda_scores.items(), key=lambda x: -x[1]), columns=["Candidate", "Borda Score"])
    st.dataframe(borda_df)

    st.markdown("---")
    st.markdown("**Each set provides a unique lens on collective rationality and social choice stability.**")
