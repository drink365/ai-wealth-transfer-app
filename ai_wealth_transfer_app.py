import streamlit as st
import pandas as pd

# === 配置常數 ===
EXEMPT_AMOUNT = 1333  # 免稅額（萬）
FUNERAL_EXPENSE = 138  # 喪葬費扣除額（萬）
SPOUSE_DEDUCTION_VALUE = 553  # 配偶扣除額（萬）
ADULT_CHILD_DEDUCTION_PER_PERSON = 56  # 直系血親卑親屬每人扣除額（萬）
PARENTS_DEDUCTION_PER_PERSON = 138  # 父母每人扣除額（萬）
DISABLED_DEDUCTION_PER_PERSON = 693  # 重度以上身心障礙者每人扣除額（萬）
OTHER_DEPENDENTS_DEDUCTION_PER_PERSON = 56  # 其他撫養親屬每人扣除額（萬）

# 台灣 2025 年累進稅率結構
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# === 計算邏輯 ===
def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents):
    """
    計算台灣 2025 年遺產稅負，並確保課稅遺產淨額為整數
    """
    # 計算總扣除額
    deductions = (
        spouse_deduction +
        FUNERAL_EXPENSE +
        (disabled_people * DISABLED_DEDUCTION_PER_PERSON) +
        (adult_children * ADULT_CHILD_DEDUCTION_PER_PERSON) +
        (other_dependents * OTHER_DEPENDENTS_DEDUCTION_PER_PERSON) +
        (parents * PARENTS_DEDUCTION_PER_PERSON)
    )

    # 課稅遺產淨額（取整數）
    taxable_amount = int(max(0, total_assets - EXEMPT_AMOUNT - deductions))

    # 根據累進稅率計算遺產稅
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in TAX_BRACKETS:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket

    return taxable_amount, round(tax_due, 2), deductions

def generate_advice(taxable_amount, tax_due):
    """
    根據計算結果生成 AI 規劃建議
    """
    return (
        "📢 根據您的情況，建議您考慮以下策略來降低遺產稅負擔：\n\n"
        "1️⃣ **規劃保單** → 預留遺產稅資金，確保家人不用變賣資產繳稅\n\n"
        "2️⃣ **提前贈與** → 善用『每年贈與免稅額』，逐步轉移財富，降低遺產總額\n\n"
        "3️⃣ **分散資產配置** → 透過不同的資產類別，降低遺產稅影響"
    )

# === 介面呈現 ===
def render_input_sidebar():
    """
    在側邊欄中呈現輸入選項
    """
    st.sidebar.header("請輸入遺產資訊")
    total_assets = st.sidebar.number_input(
        "遺產總額（萬）",
        min_value=1000,
        max_value=100000,
        value=5000,
        step=100,
        help="請輸入您的總遺產金額（單位：萬）"
    )
    
    st.sidebar.subheader("扣除額（根據家庭成員數填寫）")
    has_spouse = st.sidebar.checkbox(
        "是否有配偶（配偶扣除額 553 萬）",
        value=False,
        help="如果有配偶，請勾選。"
    )
    spouse_deduction = SPOUSE_DEDUCTION_VALUE if has_spouse else 0

    adult_children = st.sidebar.number_input(
        "直系血親卑親屬數（每人 56 萬）",
        min_value=0,
        max_value=10,
        value=0,
        help="請輸入直系血親或卑親屬的人數"
    )
    parents = st.sidebar.number_input(
        "父母數（每人 138 萬，最多 2 人）",
        min_value=0,
        max_value=2,
        value=0,
        help="請輸入符合資格的父母數量"
    )
    max_disabled = max(1, adult_children + parents + (1 if has_spouse else 0))
    disabled_people = st.sidebar.number_input(
        "重度以上身心障礙者數（每人 693 萬）",
        min_value=0,
        max_value=max_disabled,
        value=0,
        help="請輸入重度以上身心障礙者的人數"
    )
    other_dependents = st.sidebar.number_input(
        "受撫養之兄弟姊妹、祖父母數（每人 56 萬）",
        min_value=0,
        max_value=5,
        value=0,
        help="請輸入符合資格的兄弟姊妹或祖父母數量"
    )
    return total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents

def display_results(total_assets, taxable_amount, tax_due, spouse_deduction, adult_children, parents, disabled_people, other_dependents, total_deductions):
    """
    以多欄格式展示計算結果與相關資訊
    """
    st.subheader(f"📌 預估遺產稅：{tax_due:,.2f} 萬元")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**第一區：資產概況**")
        df_assets = pd.DataFrame({
            "項目": ["遺產總額"],
            "金額（萬）": [total_assets]
        })
        st.table(df_assets)
    
    with col2:
        st.markdown("**第二區：扣除項目**")
        df_deductions = pd.DataFrame({
            "項目": [
                "免稅額",
                "喪葬費扣除額",
                "配偶扣除額",
                "直系血親卑親屬扣除額",
                "父母扣除額",
                "重度身心障礙扣除額",
                "其他撫養扣除額"
            ],
            "金額（萬）": [
                EXEMPT_AMOUNT,
                FUNERAL_EXPENSE,
                spouse_deduction,
                adult_children * ADULT_CHILD_DEDUCTION_PER_PERSON,
                parents * PARENTS_DEDUCTION_PER_PERSON,
                disabled_people * DISABLED_DEDUCTION_PER_PERSON,
                other_dependents * OTHER_DEPENDENTS_DEDUCTION_PER_PERSON
            ]
        })
        st.table(df_deductions)
    
    with col3:
        st.markdown("**第三區：稅務計算**")
        df_tax = pd.DataFrame({
            "項目": ["課稅遺產淨額", "預估遺產稅"],
            "金額（萬）": [taxable_amount, tax_due]
        })
        st.table(df_tax)
    
    with st.expander("查看詳細扣除計算"):
        st.write(f"總扣除額：{total_deductions} 萬")

def main():
    st.set_page_config(page_title="遺產稅試算工具", layout="wide")
    st.header("遺產稅試算工具")
    
    # 地區選擇（目前僅提供台灣 2025 年起的版本）
    region = st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)
    
    # 從側邊欄取得用戶輸入
    total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents = render_input_sidebar()
    
    # 計算遺產稅
    taxable_amount, tax_due, total_deductions = calculate_estate_tax(
        total_assets,
        spouse_deduction,
        adult_children,
        other_dependents,
        disabled_people,
        parents
    )
    
    # 展示計算結果
    display_results(total_assets, taxable_amount, tax_due, spouse_deduction, adult_children, parents, disabled_people, other_dependents, total_deductions)
    
    # AI 規劃建議
    st.markdown("---")
    st.markdown("## 📢 AI 規劃建議")
    st.markdown(f"**{generate_advice(taxable_amount, tax_due)}**")
    
    # 行銷導客資訊
    st.markdown("---")
    st.markdown("🔍 **您知道嗎？許多家庭在面臨遺產稅時，才發現問題比想像中大！**")
    st.markdown(f"💰 **您的預估遺產稅為 {tax_due:,.2f} 萬，家人準備好了嗎？**")
    st.markdown(
        "📌 如果資金不足，可能需要變賣資產、貸款繳稅，甚至影響家族未來發展。\n"
        "但透過合適的財務規劃，您可以讓傳承更順利，讓家人更安心！"
    )
    st.markdown("📢 **現在就行動！「永傳家族辦公室」助您規劃最合適的財富傳承方案！**")
    st.markdown("📩 **立即預約免費諮詢！**")
    st.markdown("🌐 [www.gracefo.com](https://www.gracefo.com)")

if __name__ == '__main__':
    main()
