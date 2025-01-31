import streamlit as st
import numpy as np
import pandas as pd

def calculate_estate_tax(total_assets, debts, spouse_deduction, adult_children, other_dependents, disabled_deduction, region):
    """
    計算遺產稅負：目前支持台灣 2025 年稅制
    """
    exempt_amount = 1333  # 免稅額（萬）
    funeral_expense = 138  # 喪葬費扣除額固定
    
    # 計算總扣除額
    deductions = spouse_deduction + funeral_expense + disabled_deduction + (adult_children * 56) + (other_dependents * 56)
    
    # 計算淨遺產與應稅遺產
    net_assets = total_assets - debts
    taxable_amount = max(0, net_assets - exempt_amount - deductions)
    
    # 台灣 2025 年累進稅率
    tax_brackets = [(5621, 0.1), (11242, 0.15), (float('inf'), 0.2)]
    
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in tax_brackets:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket
    
    return tax_due, exempt_amount, deductions

# Streamlit UI 設計
st.set_page_config(page_title="AI 傳承規劃助理", layout="wide")
st.title("AI 傳承規劃助理")
st.header("遺產稅試算工具")

# 用戶輸入財務數據
total_assets = st.number_input("總資產（萬）", min_value=0, value=5000)
debts = st.number_input("債務（萬）", min_value=0, value=1000)
region = st.selectbox("選擇適用地區", ["台灣"], index=0)

st.markdown("---")

st.subheader("扣除額（根據家庭成員數填寫）")
has_spouse = st.checkbox("是否有配偶（配偶扣除額 553 萬）")
spouse_deduction = 553 if has_spouse else 0

disabled_deduction = st.number_input("重度以上身心障礙者扣除額（每人 693 萬）", min_value=0, value=0)
adult_children = st.number_input("直系血親卑親屬扣除額（每人 56 萬）", min_value=0, value=0)
other_dependents = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, value=0)

if st.button("計算遺產稅"):
    # 計算遺產稅
    tax_due, exempt_amount, total_deductions = calculate_estate_tax(
        total_assets, debts, spouse_deduction, adult_children, other_dependents, disabled_deduction, region
    )
    
    st.subheader(f"📌 預計遺產稅：{tax_due:.2f} 萬元")
    
    # 顯示財務總覽
    data = {
        "項目": ["總資產", "債務", "---", "免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "重度身心障礙扣除額", "其他撫養扣除額", "---", "淨遺產", "應稅遺產", "預計遺產稅"],
        "金額（萬）": [
            total_assets, debts, "---", exempt_amount, 138, spouse_deduction, adult_children * 56, 
            disabled_deduction, other_dependents * 56, "---", total_assets - debts, max(0, total_assets - debts - exempt_amount - total_deductions), tax_due
        ]
    }
    df = pd.DataFrame(data)
    st.table(df)

    st.write("### 💡 節稅建議")
    st.markdown("✅ **考慮透過壽險補足遺產稅缺口，減少資產流失**")
    st.markdown("✅ **提前贈與部分資產，以降低總遺產金額**")
    st.markdown("✅ **使用信託來管理與傳承財富，確保資產長期穩定**")
