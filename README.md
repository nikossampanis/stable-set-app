
# Stable Set Explorer

This is a Streamlit application for analyzing voting profiles and computing various stable sets from Social Choice Theory.

## 💡 Features
- Upload a `.xls` or `.xlsx` file where **each column is a voter's ranked preferences**
- Computes and explains:
  - Van Deemen Stable Set
  - Extended Stable Set
  - w-Stable Set
  - Duggan Set
  - m - stable Set
- Visualizes the **dominance graph** (Hasse diagram)

## 📂 Example Input

Included: `sample_profile.xlsx`

Each column is a voter. The top row is their 1st preference, the next row is 2nd, and so on.

Example:

| Voter 1 | Voter 2 | Voter 3 |
|---------|---------|---------|
| A       | B       | C       |
| B       | C       | A       |
| C       | A       | B       |

This means:
- Voter 1: A > B > C
- Voter 2: B > C > A
- Voter 3: C > A > B

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run stable_set_streamlit_app.py
```



---

Made with ❤️ for exploring fairness and decision theory in education and research.
