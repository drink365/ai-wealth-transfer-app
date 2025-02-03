import streamlit as st
import pandas as pd
import math

def set_config():
    # This must be the very first Streamlit command.
    st.set_page_config(page_title="遺產稅試算工具", layout="wide")

# Call set_config() immediately.
set_config()

# === Constants ===
EXEMPT_AMOUNT = 1333          # Exemption (in 10,000s)
FUNERAL_EXPENSE = 138         # Funeral expense deduction (in 10,000s)
SPOUSE_DEDUCTION_VALUE = 553  # Spouse deduction (in 10,000s)
ADULT_CHILD_DEDUCTION = 56    # Deduction per direct descendant/ascendant (in 10,000s)
PARENTS_DEDUCTION = 138       # Parents deduction (in 10,000s)
DISABLED_DEDUCTION = 693      # Deduction for severe disability (in 10,000s)
OTHER_DEPENDENTS_DEDUCTION = 56  # Deduction for other dependents (in 10,000s)

# Taiwan's progressive tax brackets for 2025 (upper limit, rate)
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# === Core Calculation Logic ===
@st.cache_data
def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents):
    """
    Calculates estate tax.
    Returns: (Taxable Estate, Estimated Tax, Total Deductions)
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
        raise ValueError("Total deductions exceed the total estate. Please check your inputs!")
    
    taxable_amount = int(max(0, total_assets - EXEMPT_AMOUNT - deductions))
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in TAX_BRACKETS:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket
    return taxable_amount, round(tax_due, 2), deductions

def generate_basic_advice(taxable_amount, tax_due):
    """
    Provides basic estate planning advice.
    """
    advice = (
        "<span style='color: blue;'>1. 規劃保單</span>：透過保險預留稅源。<br><br>"
        "<span style='color: blue;'>2. 提前贈與</span>：利用免稅贈與逐年轉移財富。<br><br>"
        "<span style='color: blue;'>3. 分散配置</span>：透過合理資產配置，降低稅率至90%。"
    )
    return advice

def simulate_insurance_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, premium_ratio, premium):
    """
    Simulates the insurance strategy:
      - User inputs premium (in 10,000s) and claim ratio (default 1.3, meaning Claim Amount = Premium × 1.3).
      - Two scenarios are simulated:
          ① Not actually taxed: Claim amount is not included in the estate.
          ② Actually taxed: Claim amount is included.
    """
    _, tax_no_insurance, _ = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_no_insurance = total_assets - tax_no_insurance
    claim_amount = round(premium * premium_ratio, 2)
    new_total_assets = total_assets - premium
    _, tax_new, _ = calculate_estate_tax(
        new_total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_not_taxed = round((new_total_assets - tax_new) + claim_amount, 2)
    effect_not_taxed = round(net_not_taxed - net_no_insurance, 2)
    effective_estate = total_assets - premium + claim_amount
    _, tax_effective, _ = calculate_estate_tax(
        effective_estate, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_taxed = round(effective_estate - tax_effective, 2)
    effect_taxed = round(net_taxed - net_no_insurance, 2)
    return {
        "原始情況": {
            "遺產總額": total_assets,
            "預估遺產稅": tax_no_insurance,
            "家人總共收到": net_no_insurance
        },
        "有規劃保單 (未被實質課稅)": {
            "保費": premium,
            "理賠金": claim_amount,
            "預估遺產稅": tax_new,
            "家人總共收到": net_not_taxed,
            "規劃效果": effect_not_taxed
        },
        "有規劃保單 (被實質課稅)": {
            "保費": premium,
            "理賠金": claim_amount,
            "家人總共收到": net_taxed,
            "規劃效果": effect_taxed
        }
    }

def simulate_gift_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, years):
    """
    Simulates the gift strategy:
      - Assumes an annual tax-free gift limit of 244 (in 10,000s) and calculates the resulting estate.
    """
    annual_gift_exemption = 244
    total_gift = years * annual_gift_exemption
    simulated_total_assets = max(total_assets - total_gift, 0)
    _, tax_sim, _ = calculate_estate_tax(
        simulated_total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_after = round((simulated_total_assets - tax_sim) + total_gift, 2)
    _, tax_original, _ = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )
    net_original = total_assets - tax_original
    effect = round(net_after - net_original, 2)
    return {
        "原始情況": {
            "遺產總額": total_assets,
            "預估遺產稅": tax_original,
            "家人總共收到": net_original
        },
        "提前贈與後": {
            "遺產總額": simulated_total_assets,
            "預估遺產稅": tax_sim,
            "總贈與金額": round(total_gift, 2),
            "家人總共收到": net_after,
            "贈與年數": years
        },
        "規劃效果": {
            "較原始情況增加": effect
        }
    }

def simulate_diversified_strategy(tax_due):
    """
    Simulates the diversified strategy:
      - Assumes that with proper asset allocation, the final estate tax can be reduced to 90% of the original.
    """
    tax_factor = 0.90
    simulated_tax_due = round(tax_due * tax_factor, 2)
    saved = round(tax_due - simulated_tax_due, 2)
    percent_saved = round((saved / tax_due) * 100, 2) if tax_due else 0
    return {
        "原始情況": {
            "預估遺產稅": tax_due
        },
        "分散配置後": {
            "預估遺產稅": simulated_tax_due
        },
        "規劃效果": {
            "較原始情況增加": saved,
            "節省百分比": percent_saved
        }
    }

# --- Custom CSS for radio buttons and effect styling ---
custom_css = """
<style>
/* Increase the font size for the radio options */
div[data-baseweb="radio"] label {
    font-size: 20px;
}
/* Style for the planning effect */
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

# --- Main Application ---
def main():
    st.markdown("<h1 class='main-header'>遺產稅試算工具</h1>", unsafe_allow_html=True)
    
    st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)
    
    # Input Area: Assets and Family Information
    with st.container():
        st.markdown("### 請輸入資產及家庭資訊", unsafe_allow_html=True)
        total_assets = st.number_input("遺產總額（萬）", min_value=1000, max_value=100000,
                                       value=5000, step=100,
                                       help="請輸入您的總遺產金額（單位：萬）")
        st.markdown("---")
        st.markdown("#### 請輸入家庭成員數")
        has_spouse = st.checkbox("是否有配偶（扣除額 553 萬）", value=False)
        spouse_deduction = SPOUSE_DEDUCTION_VALUE if has_spouse else 0
        adult_children = st.number_input("直系血親卑親屬數（每人 56 萬）", min_value=0, max_value=10,
                                         value=0, help="請輸入直系血親或卑親屬人數")
        parents = st.number_input("父母數（每人 138 萬，最多 2 人）", min_value=0, max_value=2,
                                  value=0, help="請輸入父母人數")
        max_disabled = max(1, adult_children + parents + (1 if has_spouse else 0))
        disabled_people = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max_disabled,
                                          value=0, help="請輸入重度以上身心障礙者人數")
        other_dependents = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5,
                                           value=0, help="請輸入兄弟姊妹或祖父母人數")
    
    total_deductions = (spouse_deduction +
                        FUNERAL_EXPENSE +
                        (disabled_people * DISABLED_DEDUCTION) +
                        (adult_children * ADULT_CHILD_DEDUCTION) +
                        (other_dependents * OTHER_DEPENDENTS_DEDUCTION) +
                        (parents * PARENTS_DEDUCTION))
    if total_assets < EXEMPT_AMOUNT + total_deductions:
        st.error("扣除額總和超過總遺產，請檢查輸入數值！")
        return
    
    try:
        taxable_amount, tax_due, _ = calculate_estate_tax(
            total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
        )
    except Exception as e:
        st.error(f"計算錯誤：{e}")
        return

    st.markdown("<div class='data-card'>", unsafe_allow_html=True)
    st.subheader(f"預估遺產稅：{tax_due:,.2f} 萬元")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**資產概況**")
        df_assets = pd.DataFrame({"項目": ["遺產總額"], "金額（萬）": [total_assets]})
        st.table(df_assets)
    with col2:
        st.markdown("**扣除項目**")
        df_deductions = pd.DataFrame({
            "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "父母扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
            "金額（萬）": [
                EXEMPT_AMOUNT, FUNERAL_EXPENSE, spouse_deduction,
                adult_children * ADULT_CHILD_DEDUCTION, parents * PARENTS_DEDUCTION,
                disabled_people * DISABLED_DEDUCTION, other_dependents * OTHER_DEPENDENTS_DEDUCTION
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
        "遺產總額": total_assets,
        "預估遺產稅": tax_due,
        "家人總共收到": total_assets - tax_due
    }
    
    st.markdown("## 家族傳承策略建議")
    st.markdown(generate_basic_advice(taxable_amount, tax_due), unsafe_allow_html=True)
    
    # Use a radio button for strategy selection with no default (empty string as first option)
    strategy = st.radio("請選擇策略", options=["", "保單規劃策略", "提前贈與策略", "分散配置策略"],
                        index=0, horizontal=True)
    
    if strategy == "保單規劃策略":
        st.markdown("<h6 style='color: red;'>【原始情況】</h6>", unsafe_allow_html=True)
        st.markdown(f"- 遺產總額：**{original_data['遺產總額']:,.2f} 萬元**")
        st.markdown(f"- 預估遺產稅：**{original_data['預估遺產稅']:,.2f} 萬元**")
        st.markdown(f"- 家人總共收到：**{original_data['家人總共收到']:,.2f} 萬元**")
        st.markdown("<h6 style='color: red;'>【保單規劃策略】</h6>", unsafe_allow_html=True)
        # 說明與輸入群組：先顯示說明文字
        st.markdown("<span class='explanation'>您可以自行調整保費與理賠金比例。</span>", unsafe_allow_html=True)
        # 接著使用預設值作為初始輸入（預設保費向上取整到百萬）
        default_premium = int(math.ceil((tax_due / 1.3) / 100) * 100)
        default_ratio = 1.3
        premium = st.number_input("請輸入保費（萬）", min_value=0, max_value=100000,
                                  value=default_premium, step=100, key="insurance_premium")
        premium_ratio = st.slider("請設定比例", min_value=1.0, max_value=3.0,
                                  value=default_ratio, step=0.1, key="insurance_ratio")
        # 顯示根據目前輸入計算的結果，標籤改為「假設保費」及「假設理賠金」
        current_claim = premium * premium_ratio
        st.markdown(f"**假設保費：** {premium:,.2f} 萬元")
        st.markdown(f"**假設理賠金：** {current_claim:,.2f} 萬元")
        if current_claim < tax_due:
            st.error("警告：稅源不足！")
        insurance_results = simulate_insurance_strategy(
            total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents,
            premium_ratio, premium
        )
        st.markdown("<h6 style='color: red;'>【有規劃保單（未被實質課稅）】</h6>", unsafe_allow_html=True)
        not_taxed = insurance_results["有規劃保單 (未被實質課稅)"]
        st.markdown(f"- 保費：**{not_taxed['保費']:,.2f} 萬元**")
        st.markdown(f"- 理賠金：**{not_taxed['理賠金']:,.2f} 萬元**")
        st.markdown(f"- 預估遺產稅：**{not_taxed['預估遺產稅']:,.2f} 萬元**")
        st.markdown(f"- 家人總共收到：**{not_taxed['家人總共收到']:,.2f} 萬元**")
        st.markdown(f"- 規劃效果：<span class='effect'>較原始情況增加 {not_taxed['規劃效果']:,.2f} 萬元</span>", unsafe_allow_html=True)
        st.markdown("<h6 style='color: red;'>【有規劃保單（被實質課稅）】</h6>", unsafe_allow_html=True)
        taxed = insurance_results["有規劃保單 (被實質課稅)"]
        st.markdown(f"- 保費：**{taxed['保費']:,.2f} 萬元**")
        st.markdown(f"- 理賠金：**{taxed['理賠金']:,.2f} 萬元**")
        st.markdown(f"- 家人總共收到：**{taxed['家人總共收到']:,.2f} 萬元**")
        st.markdown(f"- 規劃效果：<span class='effect'>較原始情況增加 {taxed['規劃效果']:,.2f} 萬元</span>", unsafe_allow_html=True)
    
    elif strategy == "提前贈與策略":
        st.markdown("<h6 style='color: red;'>【原始情況】</h6>", unsafe_allow_html=True)
        st.markdown(f"- 遺產總額：**{original_data['遺產總額']:,.2f} 萬元**")
        st.markdown(f"- 預估遺產稅：**{original_data['預估遺產稅']:,.2f} 萬元**")
        st.markdown(f"- 家人總共收到：**{original_data['家人總共收到']:,.2f} 萬元**")
        st.markdown("<h6 style='color: red;'>【提前贈與後】</h6>", unsafe_allow_html=True)
        years = st.slider("請設定贈與年數", 1, 10, 3, 1, key="gift_years")
        gift_results = simulate_gift_strategy(
            total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, years
        )
        after_gift = gift_results["提前贈與後"]
        st.markdown(f"- 贈與年數：**{after_gift['贈與年數']} 年**")
        st.markdown(f"- 遺產總額：**{after_gift['遺產總額']:,.2f} 萬元**")
        st.markdown(f"- 預估遺產稅：**{after_gift['預估遺產稅']:,.2f} 萬元**")
        st.markdown(f"- 總贈與金額：**{after_gift['總贈與金額']:,.2f} 萬元**")
        st.markdown(f"- 家人總共收到：**{after_gift['家人總共收到']:,.2f} 萬元**")
        effect_gift = gift_results["規劃效果"]
        st.markdown(f"- 規劃效果：<span class='effect'>較原始情況增加 {effect_gift['較原始情況增加']:,.2f} 萬元</span>", unsafe_allow_html=True)
    
    elif strategy == "分散配置策略":
        st.markdown("<h6 style='color: red;'>【原始情況】</h6>", unsafe_allow_html=True)
        original_div = simulate_diversified_strategy(tax_due)["原始情況"]
        st.markdown(f"- 預估遺產稅：**{original_div['預估遺產稅']:,.2f} 萬元**")
        st.markdown("<h6 style='color: red;'>【分散配置後】</h6>", unsafe_allow_html=True)
        div_results = simulate_diversified_strategy(tax_due)
        st.markdown(f"- 預估遺產稅：**{div_results['分散配置後']['預估遺產稅']:,.2f} 萬元**")
        effect_div = div_results["規劃效果"]
        st.markdown(f"- 規劃效果：<span class='effect'>較原始情況增加 {effect_div['較原始情況增加']:,.2f} 萬元</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 想了解更多？")
    st.markdown("歡迎前往 **永傳家族辦公室**，我們提供專業的家族傳承與財富規劃服務。")
    st.markdown("[點此前往官網](https://www.gracefo.com)", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
