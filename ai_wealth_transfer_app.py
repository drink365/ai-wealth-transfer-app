import streamlit as st
import pandas as pd
import math
import plotly.express as px

# -------------------------------
# 設定頁面
# -------------------------------
def set_config():
    st.set_page_config(page_title="綜合計算與效益評估", layout="wide")

set_config()

# -------------------------------
# Constants（單位：萬）
# -------------------------------
TOTAL_ASSETS = 30000  # 3 億元總資產（單位：萬）
SPOUSE_DEDUCTION_VALUE = 553  # 配偶扣除額（萬）
ADULT_CHILD_DEDUCTION = 56    # 每位子女扣除額（萬）

# 此處其他扣除項目皆設定為 0
FUNERAL_EXPENSE = 138         # 喪葬費扣除額（萬）
DISABLED_DEDUCTION = 693      # 重度身心障礙扣除額（萬）
OTHER_DEPENDENTS_DEDUCTION = 56  # 其他撫養扣除額（萬）

# 台灣 2025 年累進稅率結構 (上限, 稅率)
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# -------------------------------
# 核心計算函式（計算遺產稅）
# -------------------------------
@st.cache_data
def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents):
    """
    計算遺產稅
    回傳：(課稅遺產淨額, 預估遺產稅, 總扣除額)
    """
    deductions = (
        spouse_deduction +
        FUNERAL_EXPENSE +
        (disabled_people * DISABLED_DEDUCTION) +
        (adult_children * ADULT_CHILD_DEDUCTION) +
        (other_dependents * OTHER_DEPENDENTS_DEDUCTION) +
        (parents * 0)  # 此案例父母人數為 0
    )
    if total_assets < 1333 + deductions:  # 1333 萬免稅額
        return 0, 0, deductions

    taxable_amount = int(max(0, total_assets - 1333 - deductions))
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in TAX_BRACKETS:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket
    return taxable_amount, round(tax_due, 2), deductions

# -------------------------------
# 輸入區
# -------------------------------
st.markdown("<h1>綜合計算與效益評估</h1>", unsafe_allow_html=True)

premium_input = st.number_input("購買保險保費（萬）", min_value=0, max_value=100000, value=6000, step=100)
claim_input = st.number_input("保險理賠金（萬）", min_value=0, max_value=100000, value=9000, step=100)
gift_input = st.number_input("提前贈與金額（萬）", min_value=0, max_value=100000, value=2440, step=100)

# 家庭參數：有配偶及2名子女
spouse = True
adult_children = 2
# 其他家庭成員數皆設為 0
other_dependents = 0
disabled_people = 0
parents = 0

# -------------------------------
# 情境計算
# -------------------------------

# 1. 沒有規劃
_, tax_no_plan, _ = calculate_estate_tax(TOTAL_ASSETS, SPOUSE_DEDUCTION_VALUE if spouse else 0, adult_children, other_dependents, disabled_people, parents)
net_no_plan = TOTAL_ASSETS - tax_no_plan

# 2. 提前贈與
effective_gift = TOTAL_ASSETS - gift_input
_, tax_gift, _ = calculate_estate_tax(effective_gift, SPOUSE_DEDUCTION_VALUE if spouse else 0, adult_children, other_dependents, disabled_people, parents)
net_gift = effective_gift - tax_gift + gift_input

# 3. 購買保險（僅保險規劃）
effective_insurance = TOTAL_ASSETS - premium_input
_, tax_insurance, _ = calculate_estate_tax(effective_insurance, SPOUSE_DEDUCTION_VALUE if spouse else 0, adult_children, other_dependents, disabled_people, parents)
net_insurance = effective_insurance - tax_insurance + claim_input

# 4. 提前贈與＋購買保險（未被實質課稅）：保險理賠金不計入遺產
effective_combo_not_tax = TOTAL_ASSETS - gift_input - premium_input
_, tax_combo_not_tax, _ = calculate_estate_tax(effective_combo_not_tax, SPOUSE_DEDUCTION_VALUE if spouse else 0, adult_children, other_dependents, disabled_people, parents)
net_combo_not_tax = effective_combo_not_tax - tax_combo_not_tax + claim_input + gift_input

# 5. 提前贈與＋購買保險（被實質課稅）：保險理賠金列入遺產
effective_combo_tax = TOTAL_ASSETS - gift_input - premium_input + claim_input
_, tax_combo_tax, _ = calculate_estate_tax(effective_combo_tax, SPOUSE_DEDUCTION_VALUE if spouse else 0, adult_children, other_dependents, disabled_people, parents)
net_combo_tax = effective_combo_tax - tax_combo_tax + gift_input

# -------------------------------
# 結果呈現（表格）
# -------------------------------
data = {
    "規劃策略": [
        "沒有規劃",
        "提前贈與",
        "購買保險",
        "提前贈與＋購買保險（未被實質課稅）",
        "提前贈與＋購買保險（被實質課稅）"
    ],
    "遺產稅（萬）": [
        tax_no_plan,
        tax_gift,
        tax_insurance,
        tax_combo_not_tax,
        tax_combo_tax
    ],
    "家人總共取得（萬）": [
        net_no_plan,
        net_gift,
        net_insurance,
        net_combo_not_tax,
        net_combo_tax
    ]
}
df_results = pd.DataFrame(data)
st.markdown("### 計算結果")
st.table(df_results)

# -------------------------------
# 圖表呈現（長條圖）
# -------------------------------
# 建立比較用的 DataFrame
df_viz = df_results.copy()
fig_bar = px.bar(df_viz, x="規劃策略", y="家人總共取得（萬）",
                 title="不同規劃策略下家人總共取得金額比較",
                 text="家人總共取得（萬）")
fig_bar.update_traces(texttemplate='%{text}', textposition='outside')

# 設定「沒有規劃」作為基準
baseline = df_viz.loc[df_viz["規劃策略"] == "沒有規劃", "家人總共取得（萬）"].iloc[0]
for idx, row in df_viz.iterrows():
    if row["規劃策略"] != "沒有規劃":
        diff = row["家人總共取得（萬）"] - baseline
        diff_text = f"+{diff}" if diff >= 0 else f"{diff}"
        fig_bar.add_annotation(
            x=row["規劃策略"],
            y=row["家人總共取得（萬）"],
            text=diff_text,
            showarrow=False,
            font=dict(color="yellow", size=14),
            yshift=-50
        )

# 調整圖表上方空間及 y 軸範圍 (0～40000)
fig_bar.update_layout(margin=dict(t=100), yaxis_range=[0, 40000])
st.plotly_chart(fig_bar, use_container_width=True)
