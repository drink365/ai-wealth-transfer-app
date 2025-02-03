import streamlit as st
import pandas as pd
import math
import plotly.express as px

# -------------------------------
# 設定頁面
# -------------------------------
def set_config():
    st.set_page_config(page_title="遺產稅試算＋建議", layout="wide")
set_config()

# -------------------------------
# Constants（單位：萬）
# -------------------------------
EXEMPT_AMOUNT = 1333          # 免稅額
FUNERAL_EXPENSE = 138         # 喪葬費扣除額
SPOUSE_DEDUCTION_VALUE = 553  # 配偶扣除額
ADULT_CHILD_DEDUCTION = 56    # 每位子女扣除額
PARENTS_DEDUCTION = 138       # 父母扣除額
DISABLED_DEDUCTION = 693      # 重度身心障礙扣除額
OTHER_DEPENDENTS_DEDUCTION = 56  # 其他撫養扣除額

# 台灣 2025 年累進稅率結構 (上限, 稅率)
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# -------------------------------
# 核心計算邏輯（計算遺產稅）函式
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
        (parents * PARENTS_DEDUCTION)
    )
    if total_assets < EXEMPT_AMOUNT + deductions:
        return 0, 0, deductions

    taxable_amount = int(max(0, total_assets - EXEMPT_AMOUNT - deductions))
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in TAX_BRACKETS:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket
    return taxable_amount, int(round(tax_due, 2)), deductions

def generate_basic_advice(taxable_amount, tax_due):
    advice = (
        "<span style='color: blue;'>1. 規劃保單</span>：透過保險預留稅源。<br><br>"
        "<span style='color: blue;'>2. 提前贈與</span>：利用免稅贈與逐年轉移財富。<br><br>"
        "<span style='color: blue;'>3. 分散配置</span>：透過合理資產配置，降低稅率至90%。"
    )
    return advice

# -------------------------------
# 模擬策略函式（保險、贈與、分散配置）
# -------------------------------
def simulate_insurance_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, premium_ratio, premium):
    _, tax_no_insurance, _ = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_no_insurance = total_assets - tax_no_insurance
    claim_amount = int(round(premium * premium_ratio))
    new_total_assets = total_assets - premium
    _, tax_new, _ = calculate_estate_tax(
        new_total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_not_taxed = int(round((new_total_assets - tax_new) + claim_amount))
    effect_not_taxed = net_not_taxed - net_no_insurance
    effective_estate = total_assets - premium + claim_amount
    _, tax_effective, _ = calculate_estate_tax(
        effective_estate, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_taxed = int(round(effective_estate - tax_effective))
    effect_taxed = net_taxed - net_no_insurance
    return {
        "沒有規劃": {
            "總資產": total_assets,
            "預估遺產稅": tax_no_insurance,
            "家人總共取得": net_no_insurance
        },
        "有規劃保單 (未被實質課稅)": {
            "預估遺產稅": tax_new,
            "家人總共取得": net_not_taxed,
            "規劃效果": effect_not_taxed
        },
        "有規劃保單 (被實質課稅)": {
            "預估遺產稅": tax_effective,
            "家人總共取得": net_taxed,
            "規劃效果": effect_taxed
        }
    }

def simulate_gift_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, years):
    annual_gift_exemption = 244
    total_gift = years * annual_gift_exemption
    simulated_total_assets = max(total_assets - total_gift, 0)
    _, tax_sim, _ = calculate_estate_tax(
        simulated_total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_after = int(round((simulated_total_assets - tax_sim) + total_gift))
    _, tax_original, _ = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_original = total_assets - tax_original
    effect = net_after - net_original
    return {
        "沒有規劃": {
            "總資產": total_assets,
            "預估遺產稅": tax_original,
            "家人總共取得": net_original
        },
        "提前贈與後": {
            "總資產": simulated_total_assets,
            "預估遺產稅": tax_sim,
            "總贈與金額": total_gift,
            "家人總共取得": net_after,
            "贈與年數": years
        },
        "規劃效果": {
            "較沒有規劃增加": effect
        }
    }

def simulate_diversified_strategy(tax_due):
    tax_factor = 0.90
    simulated_tax_due = int(round(tax_due * tax_factor))
    saved = tax_due - simulated_tax_due
    percent_saved = round((saved / tax_due) * 100, 2) if tax_due else 0
    return {
        "沒有規劃": {
            "預估遺產稅": tax_due
        },
        "分散配置後": {
            "預估遺產稅": simulated_tax_due
        },
        "規劃效果": {
            "較沒有規劃增加": saved,
            "節省百分比": percent_saved
        }
    }

# -------------------------------
# Custom CSS
# -------------------------------
custom_css = """
<style>
div[data-baseweb="radio"] label {
    font-size: 20px;
}
.effect {
    color: green;
    font-weight: bold;
}
.explanation {
    font-size: 18px;
    color: #0077CC;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------
# 原有主介面（資產及家庭資訊輸入、計算結果、策略選擇）
# -------------------------------
st.markdown("<h1 class='main-header'>遺產稅試算＋建議</h1>", unsafe_allow_html=True)
st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)

with st.container():
    st.markdown("### 請輸入資產及家庭資訊", unsafe_allow_html=True)
    total_assets_input = st.number_input("總資產（萬）", min_value=1000, max_value=100000,
                                       value=5000, step=100,
                                       help="請輸入您的總資產（單位：萬）")
    st.markdown("---")
    st.markdown("#### 請輸入家庭成員數")
    has_spouse = st.checkbox("是否有配偶（扣除額 553 萬）", value=False)
    spouse_deduction = SPOUSE_DEDUCTION_VALUE if has_spouse else 0
    adult_children_input = st.number_input("直系血親卑親屬數（每人 56 萬）", min_value=0, max_value=10,
                                         value=0, help="請輸入直系血親或卑親屬人數")
    parents_input = st.number_input("父母數（每人 138 萬，最多 2 人）", min_value=0, max_value=2,
                                  value=0, help="請輸入父母人數")
    max_disabled = (1 if has_spouse else 0) + adult_children_input + parents_input
    disabled_people_input = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max_disabled,
                                          value=0, help="請輸入重度以上身心障礙者人數")
    other_dependents_input = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5,
                                           value=0, help="請輸入兄弟姊妹或祖父母人數")

taxable_amount, tax_due, total_deductions = calculate_estate_tax(
    total_assets_input, spouse_deduction, adult_children_input, other_dependents_input, disabled_people_input, parents_input
)

st.markdown("<div class='data-card'>", unsafe_allow_html=True)
st.subheader(f"預估遺產稅：{tax_due:,.2f} 萬元")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**資產概況**")
    df_assets = pd.DataFrame({"項目": ["總資產"], "金額（萬）": [total_assets_input]})
    st.table(df_assets)
with col2:
    st.markdown("**扣除項目**")
    df_deductions = pd.DataFrame({
        "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "父母扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
        "金額（萬）": [
            EXEMPT_AMOUNT, FUNERAL_EXPENSE, spouse_deduction,
            adult_children_input * ADULT_CHILD_DEDUCTION, parents_input * PARENTS_DEDUCTION,
            disabled_people_input * DISABLED_DEDUCTION, other_dependents_input * OTHER_DEPENDENTS_DEDUCTION
        ]
    })
    st.table(df_deductions)
with col3:
    st.markdown("**稅務計算**")
    df_tax = pd.DataFrame({
        "項目": ["課稅遺產淨額", "預估遺產稅"],
        "金額（萬）": [taxable_amount, tax_due]
    })
    st.table(df_tax.round(2))
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

original_data = {
    "總資產": total_assets_input,
    "預估遺產稅": tax_due,
    "家人總共取得": total_assets_input - tax_due
}
st.markdown("## 家族傳承策略建議")
st.markdown(generate_basic_advice(taxable_amount, tax_due), unsafe_allow_html=True)
strategy = st.radio("請選擇策略", options=["", "保單規劃策略", "提前贈與策略", "分散配置策略"],
                    index=0, horizontal=True)
if strategy == "保單規劃策略":
    st.markdown("<h6 style='color: red;'>【沒有規劃】</h6>", unsafe_allow_html=True)
    st.markdown(f"- 總資產：**{original_data['總資產']:,.2f} 萬元**")
    st.markdown(f"- 預估遺產稅：**{original_data['預估遺產稅']:,.2f} 萬元**")
    st.markdown(f"- 家人總共取得：**{original_data['家人總共取得']:,.2f} 萬元**")
    st.markdown("<h6 style='color: red;'>【保單規劃策略】</h6>", unsafe_allow_html=True)
    with st.expander("您可以自行調整保費與理賠金比例。"):
        premium = st.number_input("請輸入保費（萬）", min_value=0, max_value=100000,
                                  value=int(math.ceil((tax_due / 1.3) / 100) * 100), step=100, key="insurance_premium")
        premium_ratio = st.slider("請設定比例", min_value=1.0, max_value=3.0,
                                  value=1.3, step=0.1, key="insurance_ratio")
        # 計算並顯示預估理賠金
        estimated_claim = premium * premium_ratio
        st.markdown(f"**預估理賠金：{estimated_claim:,.2f} 萬**")
        st.session_state["estimated_claim"] = int(round(estimated_claim))
    if premium * premium_ratio < tax_due:
        st.error("警告：稅源不足！")
    insurance_results = simulate_insurance_strategy(
        total_assets_input, spouse_deduction, adult_children_input, other_dependents_input, disabled_people_input, parents_input,
        premium_ratio, premium
    )
    st.markdown("<h6 style='color: red;'>【有規劃保單（未被實質課稅）】</h6>", unsafe_allow_html=True)
    not_taxed = insurance_results["有規劃保單 (未被實質課稅)"]
    st.markdown(f"- 預估遺產稅：**{not_taxed['預估遺產稅']:,.2f} 萬元**")
    st.markdown(f"- 家人總共取得：**{not_taxed['家人總共取得']:,.2f} 萬元**")
    st.markdown(f"- 規劃效果：<span class='effect'>較沒有規劃增加 {not_taxed['規劃效果']:,.2f} 萬元</span>", unsafe_allow_html=True)
    st.markdown("<h6 style='color: red;'>【有規劃保單（被實質課稅）】</h6>", unsafe_allow_html=True)
    taxed = insurance_results["有規劃保單 (被實質課稅)"]
    st.markdown(f"- 預估遺產稅：**{taxed['預估遺產稅']:,.2f} 萬元**")
    st.markdown(f"- 家人總共取得：**{taxed['家人總共取得']:,.2f} 萬元**")
    st.markdown(f"- 規劃效果：<span class='effect'>較沒有規劃增加 {taxed['規劃效果']:,.2f} 萬元</span>", unsafe_allow_html=True)
elif strategy == "提前贈與策略":
    st.markdown("<h6 style='color: red;'>【沒有規劃】</h6>", unsafe_allow_html=True)
    st.markdown(f"- 總資產：**{original_data['總資產']:,.2f} 萬元**")
    st.markdown(f"- 預估遺產稅：**{original_data['預估遺產稅']:,.2f} 萬元**")
    st.markdown(f"- 家人總共取得：**{original_data['家人總共取得']:,.2f} 萬元**")
    st.markdown("<h6 style='color: red;'>【提前贈與後】</h6>", unsafe_allow_html=True)
    years = st.slider("請設定贈與年數", 1, 10, 3, 1, key="gift_years")
    gift_results = simulate_gift_strategy(
        total_assets_input, spouse_deduction, adult_children_input, other_dependents_input, disabled_people_input, parents_input, years
    )
    after_gift = gift_results["提前贈與後"]
    st.markdown(f"- 贈與年數：**{after_gift['贈與年數']} 年**")
    st.markdown(f"- 總資產：**{after_gift['遺產總額']:,.2f} 萬元**")
    st.markdown(f"- 預估遺產稅：**{after_gift['預估遺產稅']:,.2f} 萬元**")
    st.markdown(f"- 總贈與金額：**{after_gift['總贈與金額']:,.2f} 萬元**")
    st.markdown(f"- 家人總共取得：**{after_gift['家人總共取得']:,.2f} 萬元**")
    effect_gift = gift_results["規劃效果"]
    st.markdown(f"- 規劃效果：<span class='effect'>較沒有規劃增加 {effect_gift['較沒有規劃增加']:,.2f} 萬元</span>", unsafe_allow_html=True)
elif strategy == "分散配置策略":
    st.markdown("<h6 style='color: red;'>【沒有規劃】</h6>", unsafe_allow_html=True)
    original_div = simulate_diversified_strategy(tax_due)["沒有規劃"]
    st.markdown(f"- 預估遺產稅：**{original_div['預估遺產稅']:,.2f} 萬元**")
    st.markdown("<h6 style='color: red;'>【分散配置後】</h6>", unsafe_allow_html=True)
    div_results = simulate_diversified_strategy(tax_due)
    st.markdown(f"- 預估遺產稅：**{div_results['分散配置後']['預估遺產稅']:,.2f} 萬元**")
    effect_div = div_results["規劃效果"]
    st.markdown(f"- 規劃效果：<span class='effect'>較沒有規劃增加 {effect_div['較沒有規劃增加']:,.2f} 萬元</span>", unsafe_allow_html=True)

# -------------------------------
# 綜合計算與效益評估案例區
# -------------------------------
st.markdown("---")
st.markdown("<h2>綜合計算與效益評估</h2>", unsafe_allow_html=True)
st.markdown("（以下以上方用戶輸入的『總資產』及家庭成員狀況為例）")

# 案例總資產及家庭狀況採用上方用戶輸入
CASE_TOTAL_ASSETS = total_assets_input  
CASE_SPOUSE = has_spouse
CASE_ADULT_CHILDREN = adult_children_input
CASE_PARENTS = parents_input
CASE_DISABLED = disabled_people_input
CASE_OTHER = other_dependents_input

# 購買保險保費預設值：抓取保單規劃區的預設值，且不得超過總資產
default_premium = int(math.ceil((tax_due / 1.3) / 100) * 100)
if default_premium > CASE_TOTAL_ASSETS:
    default_premium = CASE_TOTAL_ASSETS

# 保險理賠金預設值：取自 session_state["estimated_claim"]（若不存在則預設 0）
default_claim = st.session_state.get("estimated_claim", 0)
default_claim = int(default_claim)

# 提前贈與金額預設值為 0
default_gift = 0

# 案例區輸入：保費、理賠金、提前贈與金額
premium_case = st.number_input("購買保險保費（萬）", min_value=0, max_value=CASE_TOTAL_ASSETS, value=default_premium, step=100, key="case_premium")
claim_case = st.number_input("保險理賠金（萬）", min_value=0, max_value=100000, value=default_claim, step=100, key="case_claim")
gift_case = st.number_input("提前贈與金額（萬）", min_value=0, max_value=CASE_TOTAL_ASSETS - premium_case, value=default_gift, step=100, key="case_gift")

if premium_case > CASE_TOTAL_ASSETS:
    st.error("錯誤：保費不得高於總資產！")
if gift_case > CASE_TOTAL_ASSETS - premium_case:
    st.error("錯誤：提前贈與金額不得高於【總資產】-【保費】！")

# 1. 沒有規劃
_, tax_case_no_plan, _ = calculate_estate_tax(
    CASE_TOTAL_ASSETS,
    SPOUSE_DEDUCTION_VALUE if CASE_SPOUSE else 0,
    CASE_ADULT_CHILDREN,
    CASE_OTHER,
    CASE_DISABLED,
    CASE_PARENTS
)
net_case_no_plan = CASE_TOTAL_ASSETS - tax_case_no_plan

# 2. 提前贈與
effective_case_gift = CASE_TOTAL_ASSETS - gift_case
_, tax_case_gift, _ = calculate_estate_tax(
    effective_case_gift,
    SPOUSE_DEDUCTION_VALUE if CASE_SPOUSE else 0,
    CASE_ADULT_CHILDREN,
    CASE_OTHER,
    CASE_DISABLED,
    CASE_PARENTS
)
net_case_gift = effective_case_gift - tax_case_gift + gift_case

# 3. 購買保險
effective_case_insurance = CASE_TOTAL_ASSETS - premium_case
_, tax_case_insurance, _ = calculate_estate_tax(
    effective_case_insurance,
    SPOUSE_DEDUCTION_VALUE if CASE_SPOUSE else 0,
    CASE_ADULT_CHILDREN,
    CASE_OTHER,
    CASE_DISABLED,
    CASE_PARENTS
)
net_case_insurance = effective_case_insurance - tax_case_insurance + claim_case

# 4. 提前贈與＋購買保險（未被實質課稅）
effective_case_combo_not_tax = CASE_TOTAL_ASSETS - gift_case - premium_case
_, tax_case_combo_not_tax, _ = calculate_estate_tax(
    effective_case_combo_not_tax,
    SPOUSE_DEDUCTION_VALUE if CASE_SPOUSE else 0,
    CASE_ADULT_CHILDREN,
    CASE_OTHER,
    CASE_DISABLED,
    CASE_PARENTS
)
net_case_combo_not_tax = effective_case_combo_not_tax - tax_case_combo_not_tax + claim_case + gift_case

# 5. 提前贈與＋購買保險（被實質課稅）
effective_case_combo_tax = CASE_TOTAL_ASSETS - gift_case - premium_case + claim_case
_, tax_case_combo_tax, _ = calculate_estate_tax(
    effective_case_combo_tax,
    SPOUSE_DEDUCTION_VALUE if CASE_SPOUSE else 0,
    CASE_ADULT_CHILDREN,
    CASE_OTHER,
    CASE_DISABLED,
    CASE_PARENTS
)
net_case_combo_tax = effective_case_combo_tax - tax_case_combo_tax + gift_case

# 組合案例結果
case_data = {
    "規劃策略": [
        "沒有規劃",
        "提前贈與",
        "購買保險",
        "提前贈與＋購買保險（未被實質課稅）",
        "提前贈與＋購買保險（被實質課稅）"
    ],
    "遺產稅（萬）": [
        tax_case_no_plan,
        tax_case_gift,
        tax_case_insurance,
        tax_case_combo_not_tax,
        tax_case_combo_tax
    ],
    "家人總共取得（萬）": [
        net_case_no_plan,
        net_case_gift,
        net_case_insurance,
        net_case_combo_not_tax,
        net_case_combo_tax
    ]
}
df_case_results = pd.DataFrame(case_data)
st.markdown("### 案例模擬結果")
# 新增家庭狀況說明
family_status = f"家庭狀況：配偶：{'有' if CASE_SPOUSE else '無'}, 子女：{CASE_ADULT_CHILDREN} 人, 父母：{CASE_PARENTS} 人, 重度身心障礙者：{CASE_DISABLED} 人, 其他撫養：{CASE_OTHER} 人"
st.markdown(f"**總資產：{CASE_TOTAL_ASSETS:,.2f} 萬**  |  **{family_status}**")
st.table(df_case_results)

# 圖表呈現（長條圖）
df_viz_case = df_case_results.copy()
fig_bar_case = px.bar(df_viz_case, x="規劃策略", y="家人總共取得（萬）",
                      title="不同規劃策略下家人總共取得金額比較（案例）",
                      text="家人總共取得（萬）")
fig_bar_case.update_traces(texttemplate='%{text}', textposition='outside')
baseline_case = df_viz_case.loc[df_viz_case["規劃策略"]=="沒有規劃", "家人總共取得（萬）"].iloc[0]
for idx, row in df_viz_case.iterrows():
    if row["規劃策略"] != "沒有規劃":
        diff = row["家人總共取得（萬）"] - baseline_case
        diff_text = f"+{diff}" if diff >= 0 else f"{diff}"
        fig_bar_case.add_annotation(
            x=row["規劃策略"],
            y=row["家人總共取得（萬）"],
            text=diff_text,
            showarrow=False,
            font=dict(color="yellow", size=14),
            yshift=-50
        )
fig_bar_case.update_layout(margin=dict(t=100), yaxis_range=[0, 40000], autosize=True)
st.plotly_chart(fig_bar_case, use_container_width=True)

# -------------------------------
# 行銷資訊區塊
# -------------------------------
st.markdown("---")
st.markdown("### 想了解更多？")
st.markdown("歡迎前往 **永傳家族辦公室**，我們提供專業的家族傳承與財富規劃服務。")
st.markdown("[點此前往官網](https://www.gracefo.com)", unsafe_allow_html=True)
