import streamlit as st
import numpy as np
import pandas as pd

def calculate_estate_tax(total_assets, debts, region):
    """
    計算遺產稅負：目前支持台灣 2025 年稅制
    """
    net_assets = total_assets - debts
    exempt_amount = 1333  # 免稅額（萬）
    taxable_amount = max(0, net_assets - exempt_amount)
    
    tax_brackets = [(5621, 0.1), (11242, 0.15), (float('inf'), 0.2)]
    
    tax_due = 0
    previous_bracket = 0
    for bracket, rate in tax_brackets:
        if taxable_amount > previous_bracket:
            taxable_at_this_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_this_rate * rate
            previous_bracket = bracket
    
    return tax_due

# Streamlit UI 設計
st.set_page_config(page_title="AI 傳承規劃助理", layout="wide")
st.title("AI 傳承規劃助理")
st.header("遺產稅試算工具")

# 用戶輸入財務數據
total_assets = st.number_input("總資產（萬）", min_value=0, value=5000)
debts = st.number_input("債務（萬）", min_value=0, value=1000)
region = st.selectbox("選擇適用地區", ["台灣"], index=0)

if st.button("計算遺產稅"):
    # 計算遺產稅
    tax_due = calculate_estate_tax(total_assets, debts, region)
    
    st.subheader(f"📌 預計遺產稅：{tax_due:.2f} 萬元")
    
    # 顯示財務總覽
    data = {
        "項目": ["總資產", "債務", "淨遺產", "預計遺產稅"],
        "金額（萬）": [total_assets, debts, total_assets - debts, tax_due]
    }
    df = pd.DataFrame(data)
    st.table(df)

    st.write("### 💡 節稅建議")
    st.markdown("✅ **考慮透過壽險補足遺產稅缺口，減少資產流失**")
    st.markdown("✅ **提前贈與部分資產，以降低總遺產金額**")
    st.markdown("✅ **使用信託來管理與傳承財富，確保資產長期穩定**")
