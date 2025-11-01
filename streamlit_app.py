
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fuel Ratio Calculator", page_icon="🍌", layout="centered")

@st.cache_data
def load_foods():
    df = pd.read_csv("foods.csv")
    return df

foods = load_foods()

# --- Styles (Agrandir-like bigger type) ---
st.markdown(
    """
    <style>
    :root, html, body, [data-testid="stAppViewContainer"] * {
        font-size: 18px !important;
        line-height: 1.4;
    }
    .title-big { font-size: 28px; font-weight: 700; margin-bottom: 0.2rem; }
    .subtitle { font-size: 18px; opacity: 0.8; margin-bottom: 1rem; }
    .pill { display:inline-block; padding: 6px 10px; border-radius:999px; border:1px solid rgba(0,0,0,0.15); margin-left:8px;}
    .ok { background:#e8f5e9; }
    .warn { background:#fff3e0; }
    .bad { background:#ffebee; }
    .muted { opacity: 0.7; font-size: 16px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title-big">Fuel Ratio Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enter foods + grams to see total carbs and glucose:fructose balance. Perfect for gels and real-food fueling.</div>', unsafe_allow_html=True)

# --- Session state ---
if "food_items" not in st.session_state:
    st.session_state.food_items = []  # {food, grams, carbs_g, sugars_g, glucose_g, fructose_g, note}

# --- Inputs ---
cols = st.columns([3, 2, 1])
with cols[0]:
    food_name = st.selectbox("Food", options=foods["food"].tolist())
with cols[1]:
    grams = st.number_input("Weight (g)", min_value=0, step=5, value=50)
with cols[2]:
    add = st.button("➕ Add")

# --- Compute ---
def compute_entry(row, grams: float):
    carbs_per_100 = float(row["carbs_per_100g"])
    sugars_per_100 = float(row["sugars_per_100g"])
    g_pct = float(row["glucose_pct_sugars"]) / 100.0
    f_pct = float(row["fructose_pct_sugars"]) / 100.0
    note = row.get("notes", "") if isinstance(row, dict) else row["notes"]

    carbs = carbs_per_100 * grams / 100.0
    sugars = sugars_per_100 * grams / 100.0
    starch = max(carbs - sugars, 0.0)  # starch → glucose
    glucose_from_sugar = sugars * g_pct
    fructose_from_sugar = sugars * f_pct
    glucose_total = glucose_from_sugar + starch
    fructose_total = fructose_from_sugar

    return {
        "food": row["food"],
        "grams": grams,
        "carbs_g": round(carbs, 2),
        "sugars_g": round(sugars, 2),
        "glucose_g": round(glucose_total, 2),
        "fructose_g": round(fructose_total, 2),
        "note": note
    }

if add and grams > 0 and food_name:
    row = foods[foods["food"] == food_name].iloc[0]
    entry = compute_entry(row, grams)
    st.session_state.food_items.append(entry)

# --- Items list ---
if len(st.session_state.food_items) == 0:
    st.info("Add a food and weight to get started.")
else:
    remove_idx = None
    for i, item in enumerate(st.session_state.food_items):
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
        col1.markdown(f"**{item['food']}** — {int(item['grams'])} g")
        col2.markdown(f"Carbs: **{item['carbs_g']} g**")
        col3.markdown(f"Glucose: **{item['glucose_g']} g**")
        col4.markdown(f"Fructose: **{item['fructose_g']} g**")
        col5.markdown(f"<span class='muted'>{item['note']}</span>", unsafe_allow_html=True)
        if col6.button("✖", key=f"rm_{i}"):
            remove_idx = i
    if remove_idx is not None:
        st.session_state.food_items.pop(remove_idx)

    total_carbs = sum(x["carbs_g"] for x in st.session_state.food_items)
    total_glu = sum(x["glucose_g"] for x in st.session_state.food_items)
    total_fru = sum(x["fructose_g"] for x in st.session_state.food_items)

    # ratio formatting
    ratio_text = "—"
    pill_class = "warn"
    if total_fru == 0 and total_glu > 0:
        ratio_text = "∞ : 0"
        pill_class = "bad"
    elif total_glu == 0 and total_fru > 0:
        ratio_text = "0 : ∞"
        pill_class = "bad"
    elif total_glu > 0 and total_fru > 0:
        ratio = total_glu / total_fru
        ratio_text = f"{ratio:.2f} : 1"
        if 0.8 <= ratio <= 1.2:
            pill_class = "ok"
        elif 0.6 <= ratio < 0.8 or 1.2 < ratio <= 1.6:
            pill_class = "warn"
        else:
            pill_class = "bad"

    st.markdown("---")
    c1, c2, c3, c4 = st.columns([2,2,2,2])
    c1.metric("Total carbs", f"{total_carbs:.1f} g")
    c2.metric("Glucose (total)", f"{total_glu:.1f} g")
    c3.metric("Fructose (total)", f"{total_fru:.1f} g")
    c4.markdown(f"**G:F ratio** <span class='pill {pill_class}'>{ratio_text}</span>", unsafe_allow_html=True)

    st.markdown(
        "<div class='muted'>Target zone for oxidation ~0.8–1.2 : 1. "
        "Outside this range, pair fructose-heavy foods with glucose sources (e.g., rice syrup) or vice versa.</div>",
        unsafe_allow_html=True
    )

st.markdown("---")
st.caption("Gem Performance • Fuel smarter. Values per 100 g from standard nutrition references.")
