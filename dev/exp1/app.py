import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

import pricehubble_client as phc
import shap_explainer

st.set_page_config(page_title="AI不動産査定システム", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar — property input
# ---------------------------------------------------------------------------
st.sidebar.header("物件情報入力")

country_code = st.sidebar.selectbox("国コード", ["CH", "DE", "AT", "FR", "JP", "NL", "BE", "CZ", "SK"])
deal_type = st.sidebar.selectbox("取引タイプ", ["sale", "rent"], format_func=lambda x: "売買" if x == "sale" else "賃貸")
property_type = st.sidebar.selectbox("物件タイプ", ["apartment", "house"])

st.sidebar.subheader("住所 / 座標")
use_coordinates = st.sidebar.checkbox("座標で入力する")
if use_coordinates:
    lat = st.sidebar.number_input("緯度", value=47.3769, format="%.6f")
    lng = st.sidebar.number_input("経度", value=8.5417, format="%.6f")
    location = {"coordinates": {"latitude": lat, "longitude": lng}}
else:
    street = st.sidebar.text_input("通り名", "Limmatstrasse 1")
    city = st.sidebar.text_input("市区町村", "Zürich")
    zip_code = st.sidebar.text_input("郵便番号", "8005")
    location = {"address": {"street": street, "city": city, "zipCode": zip_code}}

st.sidebar.subheader("物件詳細")
living_area = st.sidebar.number_input("面積 (m²)", min_value=10, max_value=1000, value=80)
building_year = st.sidebar.number_input("築年", min_value=1800, max_value=2026, value=2000)
num_rooms = st.sidebar.number_input("部屋数", min_value=1.0, max_value=20.0, value=3.0, step=0.5)
num_bathrooms = st.sidebar.number_input("バスルーム数", min_value=1, max_value=10, value=1)

run_valuation = st.sidebar.button("査定実行", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("🏠 AI不動産査定システム")
st.caption("PriceHubble API + SHAP による不動産バリュエーション & 説明")

if not run_valuation:
    st.info("左のサイドバーから物件情報を入力し、「査定実行」をクリックしてください。")
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

# ---- Step 1: Valuation --------------------------------------------------
with st.spinner("PriceHubble APIで査定中…"):
    try:
        valuations = phc.valuate([base_property], country_code=country_code, deal_type=deal_type)
    except Exception as e:
        st.error(f"査定APIエラー: {e}")
        st.stop()

if not valuations or not valuations[0]:
    st.error("査定結果が取得できませんでした。入力内容を確認してください。")
    st.stop()

val = valuations[0]

if deal_type == "sale":
    price_key = "salePrice"
    currency_label = "CHF" if country_code == "CH" else "EUR"
else:
    price_key = "rentGross"
    currency_label = "CHF/月" if country_code == "CH" else "EUR/月"

price_data = val.get(price_key, {})
price_value = price_data.get("value")
price_lower = price_data.get("lowerBound")
price_upper = price_data.get("upperBound")
confidence = val.get("confidence", "n/a")

if price_value is None:
    st.error("価格情報が返されませんでした。")
    st.stop()

# ---- Result card ---------------------------------------------------------
st.subheader("① 査定結果")

confidence_colors = {"good": "🟢", "medium": "🟡", "poor": "🔴"}
conf_icon = confidence_colors.get(confidence, "⚪")

col1, col2, col3 = st.columns(3)
col1.metric("推定価格", f"{price_value:,.0f} {currency_label}")
col2.metric("価格範囲", f"{price_lower:,.0f} 〜 {price_upper:,.0f}" if price_lower and price_upper else "—")
col3.metric("信頼度", f"{conf_icon} {confidence}")

st.divider()

# ---- Step 2: SHAP explanation --------------------------------------------
st.subheader("② SHAP 査定内訳")

with st.spinner("SHAP解析を実行中… (API呼び出しが多いため少々お待ちください)"):
    try:
        result = shap_explainer.explain(base_property, country_code=country_code, deal_type=deal_type)
    except Exception as e:
        st.error(f"SHAP解析エラー: {e}")
        st.stop()

shap_vals = result["shap_values"]
base_val = float(result["base_value"])
feat_names = result["feature_names"]
feat_values = result["feature_values"]
predicted = result["predicted_value"]

# ---- Waterfall chart (Plotly) --------------------------------------------
# Build cumulative waterfall: base → each feature → final
labels = ["基準価格"] + feat_names + ["推定価格"]
values = [base_val] + list(shap_vals) + [0]  # last is total placeholder

# Compute cumulative for positioning
cumulative = [base_val]
for sv in shap_vals:
    cumulative.append(cumulative[-1] + sv)
cumulative.append(predicted)  # final

colors = []
text_vals = []
measures = ["absolute"]
for sv in shap_vals:
    measures.append("relative")
    colors.append("rgba(55,126,184,0.8)" if sv >= 0 else "rgba(228,26,28,0.8)")
    sign = "+" if sv >= 0 else ""
    text_vals.append(f"{sign}{sv:,.0f}")
measures.append("total")

fig = go.Figure(go.Waterfall(
    orientation="v",
    measure=measures,
    x=labels,
    y=[base_val] + list(shap_vals) + [predicted],
    text=[f"{base_val:,.0f}"] + text_vals + [f"{predicted:,.0f}"],
    textposition="outside",
    connector={"line": {"color": "rgb(63,63,63)", "width": 1}},
    increasing={"marker": {"color": "rgba(55,126,184,0.8)"}},
    decreasing={"marker": {"color": "rgba(228,26,28,0.8)"}},
    totals={"marker": {"color": "rgba(100,100,100,0.8)"}},
))

fig.update_layout(
    title="要因別 価格寄与 (ウォーターフォール)",
    yaxis_title=currency_label,
    showlegend=False,
    height=450,
)

st.plotly_chart(fig, use_container_width=True)

# ---- Contribution table --------------------------------------------------
st.subheader("③ 要因別寄与テーブル")

total_abs = sum(abs(s) for s in shap_vals)
table_data = []
for name, val_input, sv in zip(feat_names, feat_values, shap_vals):
    pct = (sv / predicted * 100) if predicted != 0 else 0
    table_data.append({
        "要因": name,
        "入力値": f"{val_input:g}",
        "寄与額": f"{sv:+,.0f} {currency_label}",
        "割合": f"{pct:+.1f}%",
    })

df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# ---- Disclaimer ----------------------------------------------------------
st.divider()
st.caption(
    "⚠ この内訳は SHAP (Kernel SHAP) による推定説明であり、"
    "PriceHubble API 内部の実際のモデル構造を反映するものではありません。"
    "査定価格は参考値としてご利用ください。"
)
