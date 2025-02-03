import streamlit as st
import pandas as pd
import math
import plotly.express as px

def set_config():
    # 此指令必須放在最前面
    st.set_page_config(page_title="遺產稅試算+建議", layout="wide")

# 立即呼叫 set_config()
set_config()

# === Constants ===
EXEMPT_AMOUNT = 1333          # 免稅額（單位：萬）
FUNERAL_EXPENSE = 138         # 喪葬費扣除額（單位：萬）
SPOUSE_DEDUCTION_VALUE = 553  # 配偶扣除額（單位：萬）
ADULT_CHILD_DEDUCTION = 56    # 直系血親卑親屬扣除額（單位：萬）
PARENTS_DEDUCTION = 138       # 父母扣除額（單位：萬）
DISABLED_DEDUCTION = 693      # 重度身心障礙扣除額（單位：萬）
OTHER_DEPENDENTS_DEDUCTION = 56  # 其他撫養扣除額（單位：萬）

# 台灣 2025 年累進稅率結構 (上限, 稅率)
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# === 核心計算邏輯 ===
@st.cache_data
def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents):
    """
    計算遺產稅。
    回傳值：(課稅遺產淨額, 預估遺產稅, 總扣除額)
    
    修改重點：
      - 當 免稅額 + 各項扣除額 總和超過總遺產時，直接回傳 0（不再拋出錯誤提醒）
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
    return taxable_amount, round(tax_due, 2), deductions

def generate_basic_advice(taxable_amount, tax_due):
    """
    提供家族傳承策略建議文案。
    """
    advice = (
        "<span style='color: blue;'>1. 規劃保單</span>：透過保險預留稅源。<br><br>"
        "<span style='color: blue;'>2. 提前贈與</span>：利用免稅贈與逐年轉移財富。<br><br>"
        "<span style='color: blue;'>3. 分散配置</span>：透過合理資產配置，降低稅率至90%。"
    )
    return advice

def simulate_insurance_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, premium_ratio, premium):
    """
    模擬保單策略：
      - 使用者輸入保費（單位：萬）及理賠金比例（預設 1.3，表示理賠金 = 保費 × 1.3）。
      - 模擬兩種情境：
          ① 未被實質課稅：理賠金不納入遺產稅計算；
          ② 被實質課稅：理賠金納入遺產稅計算。
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
        "沒有規劃": {
            "遺產總額": total_assets,
            "預估遺產稅": tax_no_insurance,
            "家人總共取得": net_no_insurance
        },
        "有規劃保單 (未被實質課稅)": {
            "預估遺產稅": tax_new,
            "家人總共取得": net_not_taxed,
            "規劃效果": effect_not_taxed
        },
        "有規劃保單 (被實質課稅)": {
            "家人總共取得": net_taxed,
            "規劃效果": effect_taxed
        }
    }

def simulate_gift_strategy(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents, years):
    """
    模擬提前贈與策略：
      - 假設每年免稅贈與額為 244 萬（單位：萬），計算規劃後遺產情形。
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
        "沒有規劃": {
            "遺產總額": total_assets,
            "預估遺產稅": tax_original,
            "家人總共取得": net_original
        },
        "提前贈與後": {
            "遺產總額": simulated_total_assets,
            "預估遺產稅": tax_sim,
            "總贈與金額": round(total_gift, 2),
            "家人總共取得": net_after,
            "贈與年數": years
        },
        "規劃效果": {
            "較沒有規劃增加": effect
        }
    }

def simulate_diversified_strategy(tax_due):
    """
    模擬分散配置策略：
      - 假設透過合理資產配置，最終遺產稅能降至原稅額的 90%。
    """
    tax_factor = 0.90
    simulated_tax_due = round(tax_due * tax_factor, 2)
    saved = round(tax_due - simulated_tax_due, 2)
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
    st.markdown("<h1 class='main-header'>遺產稅試算＋建議</h1>", unsafe_allow_html=True)
    
    st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)
    
    # 輸入區：資產及家庭資訊
    with st.container():
        st.markdown("### 請輸入資產及家庭資訊", unsafe_allow_html=True)
        total_assets = st.number_input("遺產總額（萬）", min_value=1000, max_value=100000,
                                       value=5000, step=100,
                                       help="請輸入您的總遺產金額（單位：萬）")
        st.markdown("---")
        st.markdown("#### 請輸入家庭成員數")
        has_spouse = st.checkbox("是否有配偶（扣除額 553 萬）", value=True)  # 範例以有配偶
        spouse_deduction = SPOUSE_DEDUCTION_VALUE if has_spouse else 0
        # 範例以 2 名子女
        adult_children = st.number_input("直系血親卑親屬數（每人 56 萬）", min_value=0, max_value=10,
                                         value=2, help="請輸入直系血親或卑親屬人數")
        parents = st.number_input("父母數（每人 138 萬，最多 2 人）", min_value=0, max_value=2,
                                  value=0, help="請輸入父母人數")
        # 更新重度以上身心障礙者數的限制：不得大於 配偶 + 直系血親卑親屬 + 父母 人數
        max_disabled = (1 if has_spouse else 0) + adult_children + parents
        disabled_people = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max_disabled,
                                          value=0, help="請輸入重度以上身心障礙者人數")
        other_dependents = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5,
                                           value=0, help="請輸入兄弟姊妹或祖父母人數")
    
    # 直接由 calculate_estate_tax 判斷，若免稅額加扣除額總和超過總遺產則回傳 0
    taxable_amount, tax_due, total_deductions = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
    )

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
    
    # 以下為案例說明：以 3 億元總資產，有配偶及 2 名子女為例
    st.markdown("### 案例說明 以 3 億元總資產、有配偶及 2 名子女為例")
    st.markdown(
        """
        以下比較了不同規劃策略下家人最終可實際取得的資產情形：
        
        - **沒有規劃**，遺產稅 4727 萬, 家人總共取得 25270 萬
        - **提前贈與**，贈與 2440 萬, 遺產稅 4242 萬, 家人總共取得 25758 萬, 多 488 萬
        - **購買保險**，保費 6000 萬, 理賠金 9000 萬, 遺產稅 3530 萬, 家人總共取得 29470 萬, 多 4200 萬
        - **提前贈與＋購買保險**，贈與 2440 萬, 保費 6000 萬, 理賠金 9000 萬, 遺產稅 3042 萬, 家人總共取得 29958 萬, 多 4688 萬
        - **提前贈與＋購買保險（被實質課稅）**，贈與 2440 萬, 保費 6000 萬, 理賠金 9000 萬, 被實質課稅, 遺產稅 4842 萬, 家人總共取得 28158 萬, 多 2888 萬
        """
    )
    
    # 以表格方式呈現案例數據
    case_data = {
        "規劃策略": ["沒有規劃", "提前贈與", "購買保險", "提前贈與＋購買保險", "提前贈與＋購買保險（被實質課稅）"],
        "主要數據": [
            "遺產稅 4727 萬, 家人總共取得 25270 萬",
            "贈與 2440 萬, 遺產稅 4242 萬, 家人總共取得 25758 萬, 多 488 萬",
            "保費 6000 萬, 理賠金 9000 萬, 遺產稅 3530 萬, 家人總共取得 29470 萬, 多 4200 萬",
            "贈與 2440 萬, 保費 6000 萬, 理賠金 9000 萬, 遺產稅 3042 萬, 家人總共取得 29958 萬, 多 4688 萬",
            "贈與 2440 萬, 保費 6000 萬, 理賠金 9000 萬, 被實質課稅, 遺產稅 4842 萬, 家人總共取得 28158 萬, 多 2888 萬"
        ]
    }
    df_case = pd.DataFrame(case_data)
    st.table(df_case)
    
    # --- 視覺化圖表 ---
    # 長條圖：比較各策略下家人總共取得金額，並在長條上方標示與「沒有規劃」的差額
    df_viz = pd.DataFrame({
        "規劃策略": ["沒有規劃", "提前贈與", "購買保險", "提前贈與＋購買保險", "提前贈與＋購買保險（被實質課稅）"],
        "家人總共取得": [25270, 25758, 29470, 29958, 28158]
    })
    fig_bar = px.bar(df_viz, x="規劃策略", y="家人總共取得",
                     title="不同策略下家人總共取得金額比較",
                     text="家人總共取得")
    fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
    
    # 設定「沒有規劃」的基準金額
    baseline = df_viz.loc[df_viz["規劃策略"]=="沒有規劃", "家人總共取得"].iloc[0]
    for idx, row in df_viz.iterrows():
        if row["規劃策略"] != "沒有規劃":
            diff = row["家人總共取得"] - baseline
            diff_text = f"+{diff}" if diff >= 0 else f"{diff}"
            fig_bar.add_annotation(
                x=row["規劃策略"],
                y=row["家人總共取得"],
                text=diff_text,
                showarrow=False,
                font=dict(color="yellow", size=14),
                yshift=-50  # 調整位置，根據需要微調
            )
    
    # 調整圖表上方空間及 y 軸範圍 (0～40000)
    fig_bar.update_layout(margin=dict(t=100), yaxis_range=[0, 40000])
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # 行銷資訊區塊
    st.markdown("---")
    st.markdown("### 想了解更多？")
    st.markdown("歡迎前往 **永傳家族辦公室**，我們提供專業的家族傳承與財富規劃服務。")
    st.markdown("[點此前往官網](https://www.gracefo.com)", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
