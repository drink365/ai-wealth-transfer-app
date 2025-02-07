import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import math
import plotly.express as px
from typing import Tuple, Dict, Any
from datetime import datetime
import time

# ===============================
# 全域設定：參數與常數（單位：萬）
# ===============================
st.set_page_config(page_title="遺產稅試算", layout="wide")

# 自訂 CSS：響應式設計（調整手機版字型大小）
st.markdown(
    """
    <style>
    @media only screen and (max-width: 600px) {
        .main-header { font-size: 24px !important; }
        .stMarkdown { font-size: 14px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 常數設定
EXEMPT_AMOUNT = 1333          # 免稅額
FUNERAL_EXPENSE = 138         # 喪葬費扣除額
SPOUSE_DEDUCTION_VALUE = 553  # 配偶扣除額
ADULT_CHILD_DEDUCTION = 56    # 每位子女扣除額
PARENTS_DEDUCTION = 138       # 父母扣除額
DISABLED_DEDUCTION = 693      # 重度身心障礙扣除額
OTHER_DEPENDENTS_DEDUCTION = 56  # 其他撫養扣除額

# 台灣 2025 年累進稅率結構
TAX_BRACKETS = [
    (5621, 0.1),
    (11242, 0.15),
    (float('inf'), 0.2)
]

# -------------------------------
# 公開區域：無需授權即可顯示內容
# -------------------------------
st.markdown("<h1 class='main-header'>遺產稅試算</h1>", unsafe_allow_html=True)
st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)

with st.container():
    st.markdown("### 請輸入資產及家庭資訊")
    total_assets_input: float = st.number_input("總資產（萬）", min_value=1000, max_value=100000,
                                                  value=5000, step=100,
                                                  help="請輸入您的總資產（單位：萬）")
    st.markdown("---")
    st.markdown("#### 請輸入家庭成員數")
    has_spouse: bool = st.checkbox("是否有配偶（扣除額 553 萬）", value=False)
    adult_children_input: int = st.number_input("直系血親卑親屬數（每人 56 萬）", min_value=0, max_value=10,
                                                 value=0, help="請輸入直系血親或卑親屬人數")
    parents_input: int = st.number_input("父母數（每人 138 萬，最多 2 人）", min_value=0, max_value=2,
                                          value=0, help="請輸入父母人數")
    max_disabled: int = (1 if has_spouse else 0) + adult_children_input + parents_input
    disabled_people_input: int = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max_disabled,
                                                 value=0, help="請輸入重度以上身心障礙者人數")
    other_dependents_input: int = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5,
                                                  value=0, help="請輸入兄弟姊妹或祖父母人數")

# 定義計算函式
def compute_deductions(spouse: bool, adult_children: int, other_dependents: int,
                       disabled_people: int, parents: int) -> float:
    spouse_deduction = SPOUSE_DEDUCTION_VALUE if spouse else 0
    total_deductions = (
        spouse_deduction +
        FUNERAL_EXPENSE +
        (disabled_people * DISABLED_DEDUCTION) +
        (adult_children * ADULT_CHILD_DEDUCTION) +
        (other_dependents * OTHER_DEPENDENTS_DEDUCTION) +
        (parents * PARENTS_DEDUCTION)
    )
    return total_deductions

@st.cache_data
def calculate_estate_tax(total_assets: float, spouse: bool, adult_children: int,
                          other_dependents: int, disabled_people: int, parents: int
                         ) -> Tuple[float, float, float]:
    deductions = compute_deductions(spouse, adult_children, other_dependents, disabled_people, parents)
    if total_assets < EXEMPT_AMOUNT + deductions:
        return 0, 0, deductions
    taxable_amount = max(0, total_assets - EXEMPT_AMOUNT - deductions)
    tax_due = 0.0
    previous_bracket = 0
    for bracket, rate in TAX_BRACKETS:
        if taxable_amount > previous_bracket:
            taxable_at_rate = min(taxable_amount, bracket) - previous_bracket
            tax_due += taxable_at_rate * rate
            previous_bracket = bracket
    return taxable_amount, round(tax_due, 0), deductions

# 計算遺產稅
taxable_amount, tax_due, total_deductions = calculate_estate_tax(
    total_assets_input, has_spouse, adult_children_input,
    other_dependents_input, disabled_people_input, parents_input
)

st.markdown(f"<h3>預估遺產稅：{tax_due:,.0f} 萬元</h3>", unsafe_allow_html=True)

# 顯示統計表格
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**資產概況**")
    df_assets = pd.DataFrame({"項目": ["總資產"], "金額（萬）": [int(total_assets_input)]})
    st.table(df_assets)
with col2:
    st.markdown("**扣除項目**")
    df_deductions = pd.DataFrame({
        "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額",
                "父母扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
        "金額（萬）": [
            EXEMPT_AMOUNT,
            FUNERAL_EXPENSE,
            SPOUSE_DEDUCTION_VALUE if has_spouse else 0,
            adult_children_input * ADULT_CHILD_DEDUCTION,
            parents_input * PARENTS_DEDUCTION,
            disabled_people_input * DISABLED_DEDUCTION,
            other_dependents_input * OTHER_DEPENDENTS_DEDUCTION
        ]
    })
    df_deductions["金額（萬）"] = df_deductions["金額（萬）"].astype(int)
    st.table(df_deductions)
with col3:
    st.markdown("**稅務計算**")
    df_tax = pd.DataFrame({
        "項目": ["課稅遺產淨額", "預估遺產稅"],
        "金額（萬）": [int(taxable_amount), int(tax_due)]
    })
    st.table(df_tax)

st.markdown("---")
st.markdown("## 家族傳承策略建議")
st.markdown("""
1. 規劃保單：透過保險預留稅源。  
2. 提前贈與：利用免稅贈與逐年轉移財富。  
3. 分散配置：透過合理資產配置降低稅負。
""")

# -------------------------------
# 受保護區域：模擬試算與效益評估（僅限授權使用者）
# -------------------------------
with st.container():
    st.markdown("## 模擬試算與效益評估 (僅限授權使用者)")
    
    # 受保護區域使用獨立的 streamlit_authenticator 物件
    # 此處引用全域的 config 變數
    # 請確認 config 已在本文件前面定義
    authenticator_protected = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    # 定義受保護區域的 fields
    protected_fields = {"username": "帳號", "password": "密碼", "login_button": "登入以檢視詳細模擬結果"}
    
    # 執行登入，僅在此區塊呼叫；預設 location 為 "main"
    name_protected, auth_status_protected, username_protected = authenticator_protected.login(fields=protected_fields)
    
    if auth_status_protected:
        st.success(f"登入成功！歡迎 {name_protected}")
    else:
        st.info("請先登入以檢視模擬試算與效益評估區域內容。")
        st.stop()
    
    # 受保護區域的商業邏輯：
    CASE_TOTAL_ASSETS: float = total_assets_input  
    CASE_SPOUSE: bool = has_spouse
    CASE_ADULT_CHILDREN: int = adult_children_input
    CASE_PARENTS: int = parents_input
    CASE_DISABLED: int = disabled_people_input
    CASE_OTHER: int = other_dependents_input

    default_premium: int = int(math.ceil(tax_due / 10) * 10)
    if default_premium > CASE_TOTAL_ASSETS:
        default_premium = int(CASE_TOTAL_ASSETS)
    premium_val: int = default_premium
    default_claim: int = int(premium_val * 1.5)
    remaining: int = int(CASE_TOTAL_ASSETS - premium_val)
    default_gift: int = 244 if remaining >= 244 else 0

    premium_case: int = st.number_input("購買保險保費（萬）",
                                           min_value=0,
                                           max_value=int(CASE_TOTAL_ASSETS),
                                           value=premium_val,
                                           step=100,
                                           key="premium_case",
                                           format="%d")
    claim_case: int = st.number_input("保險理賠金（萬）",
                                       min_value=0,
                                       max_value=100000,
                                       value=default_claim,
                                       step=100,
                                       key="claim_case",
                                       format="%d")
    gift_case: int = st.number_input("提前贈與金額（萬）",
                                      min_value=0,
                                      max_value=int(CASE_TOTAL_ASSETS - premium_case),
                                      value=min(default_gift, int(CASE_TOTAL_ASSETS - premium_case)),
                                      step=100,
                                      key="case_gift",
                                      format="%d")

    if premium_case > CASE_TOTAL_ASSETS:
        st.error("錯誤：保費不得高於總資產！")
    if gift_case > CASE_TOTAL_ASSETS - premium_case:
        st.error("錯誤：提前贈與金額不得高於【總資產】-【保費】！")
    
    # 這裡可加入模擬試算與效益評估的商業邏輯與計算結果顯示
    st.markdown("這裡顯示受保護區域的模擬試算與效益評估結果……")
    
    # 若需要登出按鈕，可在此區塊或側邊欄中提供
    authenticator_protected.logout("登出", "sidebar")
