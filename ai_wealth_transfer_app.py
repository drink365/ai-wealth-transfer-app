import streamlit as st
import numpy as np
import pandas as pd

def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_deduction):
    """
    計算台灣 2025 年遺產稅負，確保課稅遺產淨額為整數
    """
    exempt_amount = 1333  # 免稅額（萬）
    funeral_expense = 138  # 喪葬費扣除額固定

    # 計算總扣除額
        max_disabled_people = has_spouse + adult_children + other_dependents
    disabled_people = min(disabled_people, max_disabled_people)
    deductions = spouse_deduction + funeral_expense + (disabled_people * 693) + (adult_children * 56) + (other_dependents * 56)

    # 計算課稅遺產淨額（取整數）
    taxable_amount = int(max(0, total_assets - exempt_amount - deductions))

    # 台灣 2025 年累進稅率
    tax_brackets = [(5621, 0.1), (11242, 0.15), (float('inf'), 0.2)]

    tax_due = 0
    previous_bracket = 0
    for bracket, rate in tax_brackets:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket

    return taxable_amount, round(tax_due, 2), exempt_amount, deductions

# Streamlit UI 設計
st.set_page_config(page_title="遺產稅試算工具", layout="wide")
st.header("遺產稅試算工具")

# **將 '選擇適用地區' 放在最前面**
region = st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)

# 用戶輸入財務數據
total_assets = st.number_input("遺產總額（萬）", min_value=0, value=5000)

st.subheader("扣除額（根據家庭成員數填寫）")
has_spouse = st.checkbox("是否有配偶（配偶扣除額 553 萬）")
spouse_deduction = 553 if has_spouse else 0

adult_children = st.number_input("直系血親卑親屬扣除額（每人 56 萬）", min_value=0, value=0)
disabled_people = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, value=0)
disabled_deduction = disabled_people * 693
other_dependents = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, value=0)

if st.button("計算遺產稅"):
    # 計算遺產稅
    taxable_amount, tax_due, exempt_amount, total_deductions = calculate_estate_tax(
        total_assets, spouse_deduction, adult_children, other_dependents, disabled_deduction
    )

    st.subheader(f"📌 預估遺產稅：{tax_due:,.2f} 萬元")

    # 顯示財務總覽（分三大區塊）
    section1 = pd.DataFrame({
        "項目": ["遺產總額"],
        "金額（萬）": [total_assets]
    })
    st.markdown("**第一區：資產概況**")
    st.table(section1)

    section2 = pd.DataFrame({
        "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
        "金額（萬）": [exempt_amount, 138, spouse_deduction, adult_children * 56, disabled_deduction, other_dependents * 56]
    })
    st.markdown("**第二區：扣除項目**")
    st.table(section2)

    section3 = pd.DataFrame({
        "項目": ["課稅遺產淨額", "預估遺產稅"],
        "金額（萬）": [taxable_amount, tax_due]
    })
    st.markdown("**第三區：稅務計算**")
    st.table(section3)

    st.write("### 💡 節稅建議")
    st.markdown("✅ **考慮透過壽險補足遺產稅缺口，減少資產流失**")
    st.markdown("✅ **提前贈與部分資產，以降低總遺產金額**")
    st.markdown("✅ **使用信託來管理與傳承財富，確保資產長期穩定**")

    # 加入行銷宣傳與聯繫資訊
    st.markdown("---")
    st.subheader("📢 進一步了解家族傳承與節稅策略")
    st.write("想要更深入了解如何透過專業規劃降低遺產稅負擔，確保財富順利傳承？歡迎聯繫我們！")
    st.markdown("💼 **永傳家族辦公室**")
    st.markdown("🌐 [www.gracefo.com](http://www.gracefo.com)")
    st.markdown("📞 預約諮詢，找到最適合您的傳承方案！")
