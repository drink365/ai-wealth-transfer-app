import streamlit as st
import numpy as np
import pandas as pd

# ----------------------------
# 遺產稅計算函式
# ----------------------------
def calculate_estate_tax(total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents):
    """
    計算台灣 2025 年遺產稅負，確保課稅遺產淨額為整數
    """
    exempt_amount = 1333  # 免稅額（萬）
    funeral_expense = 138  # 喪葬費扣除額固定

    # 計算總扣除額
    deductions = spouse_deduction + funeral_expense + (disabled_people * 693) + (adult_children * 56) + (other_dependents * 56) + (parents * 138)

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

# ----------------------------
# AI 規劃建議函式（Nana 風格）
# ----------------------------
def generate_advice(taxable_amount, tax_due):
    return (
        "📢 嗨，我是 Nana！根據你的情況，建議你考慮以下策略來降低遺產稅負擔：\n\n"
        "1️⃣ **規劃保單** → 預留遺產稅資金，讓家人不必因突發稅務問題而變賣資產。\n\n"
        "2️⃣ **提前贈與** → 善用『每年贈與免稅額』，逐步轉移財富，降低累積遺產總額。\n\n"
        "3️⃣ **分散資產配置** → 透過多元資產配置，減少單一資產類別帶來的稅務壓力。\n\n"
        "希望這些建議能幫助你更安心地規劃未來傳承，讓家人得到最好的保障！"
    )

# ----------------------------
# Streamlit 介面設定與自我介紹
# ----------------------------
st.set_page_config(page_title="遺產稅試算工具", layout="wide")
st.header("👋 嗨！我是 Nana， 你的 AI 遺產稅助手！")
st.markdown("我可以幫你計算 **遺產稅負、免稅額與各項扣除**，並提供貼心的財務傳承規劃建議，讓你和家人更安心！ 😊")

# ----------------------------
# 基本設定：選擇適用地區
# ----------------------------
region = st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)

# ----------------------------
# 輸入遺產資訊
# ----------------------------
st.subheader("請輸入遺產資訊")
total_assets = st.number_input("遺產總額（萬）", min_value=1000, max_value=100000, value=5000, step=100)

# ----------------------------
# 輸入扣除額資訊（根據家庭成員數）
# ----------------------------
st.subheader("扣除額（根據家庭成員數填寫）")
has_spouse = st.checkbox("是否有配偶（配偶扣除額 553 萬）")
spouse_deduction = 553 if has_spouse else 0

adult_children = st.number_input("直系血親卑親屬扣除額（每人 56 萬）", min_value=0, max_value=10, value=0)
parents = st.number_input("父母扣除額（每人 138 萬，最多 2 人）", min_value=0, max_value=2, value=0)

disabled_people = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max(1, adult_children + parents + (1 if has_spouse else 0)), value=0)
disabled_deduction = disabled_people * 693

other_dependents = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5, value=0)

# ----------------------------
# 遺產稅試算
# ----------------------------
taxable_amount, tax_due, exempt_amount, total_deductions = calculate_estate_tax(
    total_assets, spouse_deduction, adult_children, other_dependents, disabled_people, parents
)

st.subheader(f"📌 預估遺產稅：{tax_due:,.2f} 萬元")

# ----------------------------
# 顯示財務總覽（分三大區塊）
# ----------------------------
section1 = pd.DataFrame({"項目": ["遺產總額"], "金額（萬）": [total_assets]})
st.markdown("**第一區：資產概況**")
st.table(section1)

section2 = pd.DataFrame({
    "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "父母扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
    "金額（萬）": [exempt_amount, 138, spouse_deduction, adult_children * 56, parents * 138, disabled_deduction, other_dependents * 56]
})
st.markdown("**第二區：扣除項目**")
st.table(section2)

section3 = pd.DataFrame({"項目": ["課稅遺產淨額", "預估遺產稅"], "金額（萬）": [taxable_amount, tax_due]})
st.markdown("**第三區：稅務計算**")
st.table(section3)

# ----------------------------
# AI 規劃建議（Nana 的建議）
# ----------------------------
st.markdown("---")
st.subheader("📢 Nana 的規劃建議")
st.markdown(f"**{generate_advice(taxable_amount, tax_due)}**")

# ----------------------------
# 行銷導客資訊
# ----------------------------
st.markdown("---")
st.markdown("🔍 **你知道嗎？許多家庭在面臨遺產稅時，才發現問題比想像中大！**")
st.markdown(f"💰 **你的預估遺產稅為 {tax_due:,.2f} 萬，家人準備好了嗎？**")
st.markdown(
    "📌 如果資金不足，可能需要變賣資產、貸款繳稅，甚至影響家族未來發展。\n"
    "但透過合適的財務規劃，你可以讓傳承更順利，讓家人更安心！"
)
st.markdown("📢 **現在就行動！「永傳家族辦公室」助你規劃最合適的財富傳承方案！**")
st.markdown("📩 **立即預約免費諮詢！**")
st.markdown("🌐 [www.gracefo.com](https://www.gracefo.com)")
