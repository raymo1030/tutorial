import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

import pricehubble_client as phc
import shap_explainer

st.set_page_config(page_title="AI不動産査定システム", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;600;700&display=swap');

    /* Global */
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
    .block-container { padding-top: 1.5rem; max-width: 1100px; }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #334155 100%);
        padding: 2.2rem 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 1.8rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        color: white; margin: 0 0 0.25rem 0; font-size: 1.75rem;
        font-weight: 700; position: relative;
    }
    .main-header p {
        color: #94a3b8; margin: 0; font-size: 0.88rem;
        font-weight: 300; position: relative; letter-spacing: 0.3px;
    }

    /* Price hero card */
    .price-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 20px;
        padding: 1.8rem 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 40px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }
    .price-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(168,85,247,0.08) 100%);
        pointer-events: none;
    }
    .price-card .label {
        font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px;
        opacity: 0.6; margin-bottom: 0.6rem; font-weight: 500;
        position: relative; z-index: 1;
    }
    .price-card .value {
        font-size: 2.2rem; font-weight: 700; letter-spacing: -0.5px;
        position: relative; z-index: 1;
        background: linear-gradient(135deg, #e2e8f0, #ffffff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .price-card .range {
        font-size: 0.78rem; opacity: 0.5; margin-top: 0.6rem;
        font-weight: 300; position: relative; z-index: 1;
    }

    /* Stat cards */
    .stat-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        transition: box-shadow 0.2s;
    }
    .stat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
    .stat-card .label {
        font-size: 0.7rem; color: #94a3b8; margin-bottom: 0.4rem;
        text-transform: uppercase; letter-spacing: 1px; font-weight: 500;
    }
    .stat-card .value { font-size: 1.15rem; font-weight: 600; color: #1e293b; }

    /* Confidence */
    .conf-good   { color: #059669; }
    .conf-medium { color: #d97706; }
    .conf-poor   { color: #dc2626; }
    .conf-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
    .conf-dot.good   { background: #059669; }
    .conf-dot.medium { background: #d97706; }
    .conf-dot.poor   { background: #dc2626; }

    /* Section header */
    .section-header {
        display: flex; align-items: center; gap: 0.7rem;
        margin: 2.2rem 0 0.8rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .section-header .badge {
        width: 32px; height: 32px; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.95rem; flex-shrink: 0;
    }
    .section-header .badge.blue   { background: #eff6ff; }
    .section-header .badge.violet { background: #f5f3ff; }
    .section-header .badge.emerald { background: #ecfdf5; }
    .section-header h3 {
        margin: 0; font-size: 1rem; font-weight: 600; color: #1e293b;
    }
    .section-header .desc {
        font-size: 0.78rem; color: #94a3b8; font-weight: 400;
        margin-left: auto;
    }

    /* Chart container */
    .chart-container {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 16px;
        padding: 1rem 0.5rem 0.5rem;
        margin-top: 0.5rem;
    }

    /* Contribution bar row */
    .contrib-row {
        display: flex; align-items: center; gap: 0.8rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f8fafc;
        font-size: 0.88rem;
    }
    .contrib-row:last-child { border-bottom: none; }
    .contrib-row .feat-name {
        width: 100px; flex-shrink: 0;
        font-weight: 500; color: #475569;
    }
    .contrib-row .feat-val {
        width: 60px; flex-shrink: 0;
        font-size: 0.8rem; color: #94a3b8; text-align: right;
    }
    .contrib-row .bar-area {
        flex: 1; display: flex; align-items: center; height: 28px; position: relative;
    }
    .contrib-row .bar {
        height: 24px; border-radius: 6px; min-width: 3px;
        display: flex; align-items: center; justify-content: flex-end;
        padding: 0 8px; font-size: 0.75rem; font-weight: 600; color: white;
        transition: width 0.4s ease;
    }
    .contrib-row .bar.pos { background: linear-gradient(90deg, #3b82f6, #6366f1); }
    .contrib-row .bar.neg { background: linear-gradient(90deg, #f87171, #ef4444); }
    .contrib-row .amount {
        width: 130px; flex-shrink: 0; text-align: right;
        font-weight: 600; font-size: 0.85rem;
    }
    .contrib-row .amount.pos { color: #2563eb; }
    .contrib-row .amount.neg { color: #dc2626; }
    .contrib-row .pct {
        width: 55px; flex-shrink: 0; text-align: right;
        font-size: 0.78rem; color: #94a3b8;
    }

    /* Summary strip */
    .summary-strip {
        display: flex; gap: 1rem; margin: 0.8rem 0;
        flex-wrap: wrap;
    }
    .summary-chip {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 0.5rem 1rem;
        font-size: 0.82rem; color: #475569;
        display: flex; align-items: center; gap: 0.4rem;
    }
    .summary-chip strong { color: #1e293b; }

    /* Disclaimer */
    .disclaimer {
        background: #fefce8;
        border: 1px solid #fef08a;
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        font-size: 0.78rem;
        color: #854d0e;
        margin-top: 2rem;
        line-height: 1.6;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafbfc 0%, #f1f5f9 100%);
    }
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #1e293b, #334155);
        color: white; border: none;
        font-weight: 600; font-size: 0.9rem;
        padding: 0.7rem 1rem;
        border-radius: 12px;
        letter-spacing: 0.3px;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(30,41,59,0.3);
    }
    [data-testid="stSidebar"] .stButton button:active {
        transform: translateY(0px);
    }

    /* Welcome state */
    .welcome {
        text-align: center; padding: 5rem 2rem 4rem; color: #94a3b8;
    }
    .welcome-icon {
        font-size: 3.5rem; margin-bottom: 1.2rem;
        filter: grayscale(0.3);
    }
    .welcome h3 { color: #334155; font-weight: 600; margin-bottom: 0.4rem; font-size: 1.2rem; }
    .welcome p  { max-width: 360px; margin: 0 auto; line-height: 1.6; font-size: 0.9rem; }

    /* Hide streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt_price(v, currency):
    """Format price with 万/億 units for JPY."""
    if currency.startswith("円") and v >= 10_000:
        man = v / 10_000
        if man >= 10_000:
            oku = man / 10_000
            remainder = man % 10_000
            if remainder > 0:
                return f"{oku:.0f}億{remainder:,.0f}万{currency}"
            return f"{oku:.0f}億{currency}"
        return f"{man:,.0f}万{currency}"
    return f"{v:,.0f} {currency}"


def fmt_price_short(v, currency):
    """Shorter price format for range display."""
    if currency.startswith("円") and v >= 10_000:
        man = v / 10_000
        if man >= 10_000:
            return f"{man / 10_000:,.1f}億"
        return f"{man:,.0f}万"
    return f"{v:,.0f}"


# ---------------------------------------------------------------------------
# Test properties
# ---------------------------------------------------------------------------
TEST_PROPERTIES = [
    {
        "label": "渋谷区 神宮前 マンション",
        "tag": "🏢 3LDK・75m²・2015年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "150-0001", "city": "渋谷区", "street": "神宮前1-1",
        "livingArea": 75, "buildingYear": 2015, "numberOfRooms": 3, "numberOfBathrooms": 1,
    },
    {
        "label": "港区 六本木 タワマン",
        "tag": "🏢 4LDK・120m²・2018年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "106-0032", "city": "港区", "street": "六本木6-10",
        "livingArea": 120, "buildingYear": 2018, "numberOfRooms": 4, "numberOfBathrooms": 2,
    },
    {
        "label": "世田谷区 成城 戸建",
        "tag": "🏡 5LDK・150m²・2005年築",
        "propertyType": "house", "dealType": "sale", "countryCode": "JP",
        "postCode": "157-0066", "city": "世田谷区", "street": "成城6-1",
        "livingArea": 150, "buildingYear": 2005, "numberOfRooms": 5, "numberOfBathrooms": 2,
    },
    {
        "label": "新宿区 西新宿 ワンルーム",
        "tag": "🏢 1R・25m²・2010年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "160-0023", "city": "新宿区", "street": "西新宿1-1",
        "livingArea": 25, "buildingYear": 2010, "numberOfRooms": 1, "numberOfBathrooms": 1,
    },
    {
        "label": "中央区 銀座 高級マンション",
        "tag": "🏢 3LDK・95m²・2020年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "104-0061", "city": "中央区", "street": "銀座4-1",
        "livingArea": 95, "buildingYear": 2020, "numberOfRooms": 3, "numberOfBathrooms": 2,
    },
    {
        "label": "杉並区 荻窪 築古戸建",
        "tag": "🏡 4LDK・100m²・1985年築",
        "propertyType": "house", "dealType": "sale", "countryCode": "JP",
        "postCode": "167-0051", "city": "杉並区", "street": "荻窪5-1",
        "livingArea": 100, "buildingYear": 1985, "numberOfRooms": 4, "numberOfBathrooms": 1,
    },
    {
        "label": "目黒区 自由が丘 賃貸",
        "tag": "🏢 2LDK・55m²・2012年築",
        "propertyType": "apartment", "dealType": "rent", "countryCode": "JP",
        "postCode": "152-0035", "city": "目黒区", "street": "自由が丘1-1",
        "livingArea": 55, "buildingYear": 2012, "numberOfRooms": 2, "numberOfBathrooms": 1,
    },
    {
        "label": "千代田区 番町 ヴィンテージ",
        "tag": "🏢 3LDK・85m²・1998年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "102-0083", "city": "千代田区", "street": "一番町1-1",
        "livingArea": 85, "buildingYear": 1998, "numberOfRooms": 3, "numberOfBathrooms": 1,
    },
    {
        "label": "大田区 田園調布 邸宅",
        "tag": "🏡 6LDK・200m²・2000年築",
        "propertyType": "house", "dealType": "sale", "countryCode": "JP",
        "postCode": "145-0071", "city": "大田区", "street": "田園調布3-1",
        "livingArea": 200, "buildingYear": 2000, "numberOfRooms": 6, "numberOfBathrooms": 3,
    },
    {
        "label": "豊島区 池袋 コンパクト",
        "tag": "🏢 2K・40m²・2008年築",
        "propertyType": "apartment", "dealType": "sale", "countryCode": "JP",
        "postCode": "171-0022", "city": "豊島区", "street": "南池袋1-1",
        "livingArea": 40, "buildingYear": 2008, "numberOfRooms": 2, "numberOfBathrooms": 1,
    },
]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("#### 物件を選択")

selected_idx = st.sidebar.selectbox(
    "テスト物件",
    range(len(TEST_PROPERTIES)),
    format_func=lambda i: TEST_PROPERTIES[i]["label"],
    label_visibility="collapsed",
)
sel = TEST_PROPERTIES[selected_idx]

property_type = sel["propertyType"]
deal_type = sel["dealType"]
country_code = sel["countryCode"]
location = {"address": {"street": sel["street"], "city": sel["city"], "postCode": sel["postCode"]}}
living_area = sel["livingArea"]
building_year = sel["buildingYear"]
num_rooms = sel["numberOfRooms"]
num_bathrooms = sel["numberOfBathrooms"]

type_icon = "🏢" if property_type == "apartment" else "🏡"
type_label = "マンション" if property_type == "apartment" else "戸建"
deal_label = "売買" if deal_type == "sale" else "賃貸"

st.sidebar.markdown(f"""
<div style="
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0 1rem;
    font-size: 0.82rem;
    line-height: 1.8;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
">
    <div style="font-weight:600; font-size:0.9rem; color:#1e293b; margin-bottom:0.4rem;">
        {type_icon} {sel["label"]}
    </div>
    <div style="color:#64748b;">
        📍 {sel["city"]} {sel["street"]}<br>
        <span style="display:inline-flex; gap:1rem; margin-top:2px;">
            <span>📐 {living_area}m²</span>
            <span>🏗 {building_year}年</span>
        </span><br>
        <span style="display:inline-flex; gap:1rem;">
            <span>🚪 {num_rooms}室</span>
            <span>🚿 {num_bathrooms}</span>
            <span>{'💰' if deal_type == 'sale' else '🔑'} {deal_label}</span>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

run_valuation = st.sidebar.button("査定を実行", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="font-size:0.72rem; color:#94a3b8; text-align:center;">'
    'Powered by PriceHubble API + SHAP</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>AI 不動産査定システム</h1>
    <p>PriceHubble API と SHAP による査定価格の算出・要因分析</p>
</div>
""", unsafe_allow_html=True)

if not run_valuation:
    st.markdown("""
    <div class="welcome">
        <div class="welcome-icon">🏠</div>
        <h3>物件を査定する</h3>
        <p>サイドバーからテスト物件を選択し、<br>「査定を実行」をクリックしてください</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Build property dict
base_property = {
    "location": location,
    "propertyType": {"code": property_type},
    "livingArea": living_area,
    "buildingYear": building_year,
    "numberOfRooms": num_rooms,
    "numberOfBathrooms": num_bathrooms,
}

# ---------------------------------------------------------------------------
# Step 1: Valuation
# ---------------------------------------------------------------------------
with st.spinner("PriceHubble API で査定中…"):
    try:
        valuations = phc.valuate(
            [base_property], country_code=country_code, deal_type=deal_type
        )
    except Exception as e:
        st.error(f"査定APIエラー: {e}")
        st.stop()

if not valuations or not valuations[0]:
    st.error("査定結果が取得できませんでした。入力内容を確認してください。")
    st.stop()

val = valuations[0]

if deal_type == "sale":
    price_key = "salePrice"
    currency_map = {"CH": "CHF", "JP": "円"}
    currency_label = currency_map.get(country_code, "EUR")
else:
    price_key = "rentGross"
    currency_map = {"CH": "CHF/月", "JP": "円/月"}
    currency_label = currency_map.get(country_code, "EUR/月")

price_value = val.get(price_key)
price_range = val.get(f"{price_key}Range", {})
price_lower = price_range.get("lower")
price_upper = price_range.get("upper")
confidence = val.get("confidence", "n/a")

if price_value is None:
    st.error("価格情報が返されませんでした。")
    st.stop()

# ---------------------------------------------------------------------------
# Result section
# ---------------------------------------------------------------------------
st.markdown("""
<div class="section-header">
    <div class="badge blue">📋</div>
    <h3>査定結果</h3>
</div>
""", unsafe_allow_html=True)

col_price, col_stats = st.columns([1.2, 1])

with col_price:
    range_text = ""
    if price_lower and price_upper:
        range_text = f"{fmt_price_short(price_lower, currency_label)} 〜 {fmt_price_short(price_upper, currency_label)}"
    st.markdown(f"""
    <div class="price-card">
        <div class="label">推定価格</div>
        <div class="value">{fmt_price(price_value, currency_label)}</div>
        <div class="range">{range_text}</div>
    </div>
    """, unsafe_allow_html=True)

conf_class = {"good": "good", "medium": "medium", "poor": "poor"}.get(confidence, "")
conf_label = {"good": "高い", "medium": "中程度", "poor": "低い"}.get(confidence, confidence)

with col_stats:
    age = 2026 - building_year
    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.7rem; height:100%;">
        <div class="stat-card">
            <div class="label">信頼度</div>
            <div class="value conf-{conf_class}">
                <span class="conf-dot {conf_class}"></span>{conf_label}
            </div>
        </div>
        <div class="stat-card">
            <div class="label">物件タイプ</div>
            <div class="value">{type_icon} {type_label}</div>
        </div>
        <div class="stat-card">
            <div class="label">面積</div>
            <div class="value">{living_area} m²</div>
        </div>
        <div class="stat-card">
            <div class="label">築年数</div>
            <div class="value">{age}年</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Step 2: SHAP
# ---------------------------------------------------------------------------
st.markdown("""
<div class="section-header">
    <div class="badge violet">🔬</div>
    <h3>価格要因分析</h3>
    <span class="desc">SHAP (Kernel SHAP) による寄与度分解</span>
</div>
""", unsafe_allow_html=True)

with st.spinner("SHAP 解析を実行中…"):
    try:
        result = shap_explainer.explain(
            base_property, country_code=country_code, deal_type=deal_type
        )
    except Exception as e:
        st.error(f"SHAP解析エラー: {e}")
        st.stop()

shap_vals = result["shap_values"]
base_val = float(result["base_value"])
feat_names = result["feature_names"]
feat_values = result["feature_values"]
predicted = result["predicted_value"]

# ---------------------------------------------------------------------------
# Horizontal bar chart — much more readable than waterfall for few features
# ---------------------------------------------------------------------------
sorted_indices = np.argsort(np.abs(shap_vals))[::-1]
sorted_names = [feat_names[i] for i in sorted_indices]
sorted_vals = [shap_vals[i] for i in sorted_indices]
sorted_feat_vals = [feat_values[i] for i in sorted_indices]

max_abs = max(abs(sv) for sv in shap_vals) if len(shap_vals) > 0 else 1

# Build the horizontal bar contribution rows via HTML
rows_html = ""
for name, sv, fv in zip(sorted_names, sorted_vals, sorted_feat_vals):
    pct = (sv / predicted * 100) if predicted != 0 else 0
    bar_width = max(abs(sv) / max_abs * 100, 2)
    bar_class = "pos" if sv >= 0 else "neg"
    amt_class = "pos" if sv >= 0 else "neg"
    sign = "+" if sv >= 0 else ""

    if currency_label.startswith("円"):
        amt_man = sv / 10_000
        amt_display = f"{sign}{amt_man:,.0f}万円"
    else:
        amt_display = f"{sign}{sv:,.0f} {currency_label}"

    rows_html += f"""
    <div class="contrib-row">
        <div class="feat-name">{name}</div>
        <div class="feat-val">{fv:g}</div>
        <div class="bar-area">
            <div class="bar {bar_class}" style="width:{bar_width}%;"></div>
        </div>
        <div class="amount {amt_class}">{amt_display}</div>
        <div class="pct">{pct:+.1f}%</div>
    </div>
    """

# Summary chips
base_display = fmt_price(base_val, currency_label) if base_val else "—"
pred_display = fmt_price(predicted, currency_label) if predicted else "—"
total_positive = sum(sv for sv in shap_vals if sv > 0)
total_negative = sum(sv for sv in shap_vals if sv < 0)

if currency_label.startswith("円"):
    pos_display = f"+{total_positive/10_000:,.0f}万円"
    neg_display = f"{total_negative/10_000:,.0f}万円"
else:
    pos_display = f"+{total_positive:,.0f} {currency_label}"
    neg_display = f"{total_negative:,.0f} {currency_label}"

st.markdown(f"""
<div class="summary-strip">
    <div class="summary-chip">基準価格 <strong>{base_display}</strong></div>
    <div class="summary-chip" style="color:#2563eb;">プラス要因 <strong>{pos_display}</strong></div>
    <div class="summary-chip" style="color:#dc2626;">マイナス要因 <strong>{neg_display}</strong></div>
    <div class="summary-chip" style="border-color:#1e293b;">推定価格 <strong>{pred_display}</strong></div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="chart-container">
    {rows_html}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Waterfall chart (collapsible detail)
# ---------------------------------------------------------------------------
with st.expander("ウォーターフォール図を表示", expanded=False):
    labels = ["基準価格"] + feat_names + ["推定価格"]

    measures = ["absolute"]
    text_vals_wf = []
    if currency_label.startswith("円"):
        text_vals_wf.append(f"{base_val/10_000:,.0f}万")
    else:
        text_vals_wf.append(f"{base_val:,.0f}")

    for sv in shap_vals:
        measures.append("relative")
        sign = "+" if sv >= 0 else ""
        if currency_label.startswith("円"):
            text_vals_wf.append(f"{sign}{sv/10_000:,.0f}万")
        else:
            text_vals_wf.append(f"{sign}{sv:,.0f}")
    measures.append("total")
    if currency_label.startswith("円"):
        text_vals_wf.append(f"{predicted/10_000:,.0f}万")
    else:
        text_vals_wf.append(f"{predicted:,.0f}")

    fig = go.Figure(go.Waterfall(
        orientation="h",
        measure=measures,
        y=labels,
        x=[base_val] + list(shap_vals) + [predicted],
        text=text_vals_wf,
        textposition="outside",
        textfont=dict(size=12, family="Noto Sans JP"),
        connector={"line": {"color": "#e2e8f0", "width": 1}},
        increasing={"marker": {"color": "#3b82f6", "line": {"color": "#2563eb", "width": 1}}},
        decreasing={"marker": {"color": "#f87171", "line": {"color": "#ef4444", "width": 1}}},
        totals={"marker": {"color": "#1e293b", "line": {"color": "#0f172a", "width": 1}}},
    ))

    fig.update_layout(
        xaxis_title=currency_label,
        showlegend=False,
        height=max(280, 60 * len(labels)),
        margin=dict(t=10, b=40, l=10, r=80),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#e2e8f0"),
        yaxis=dict(autorange="reversed"),
        font=dict(family="Noto Sans JP, sans-serif", size=12),
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Disclaimer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="disclaimer">
    <strong>⚠ ご注意</strong> &mdash;
    この内訳は SHAP (Kernel SHAP) による推定説明であり、PriceHubble API 内部の実際のモデル構造を反映するものではありません。
    査定価格は参考値としてご利用ください。
</div>
""", unsafe_allow_html=True)
