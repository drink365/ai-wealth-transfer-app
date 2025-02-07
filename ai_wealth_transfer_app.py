import streamlit as st
import pandas as pd
import math
import plotly.express as px
from typing import Tuple, Dict, Any, List
from datetime import datetime
import time
from dataclasses import dataclass


# ===============================
# 1. 常數與設定
# ===============================
@dataclass
class TaxConstants:
    """遺產稅相關常數"""
    EXEMPT_AMOUNT: float = 1333  # 免稅額
    FUNERAL_EXPENSE: float = 138  # 喪葬費扣除額
    SPOUSE_DEDUCTION_VALUE: float = 553  # 配偶扣除額
    ADULT_CHILD_DEDUCTION: float = 56  # 每位子女扣除額
    PARENTS_DEDUCTION: float = 138  # 父母扣除額
    DISABLED_DEDUCTION: float = 693  # 重度身心障礙扣除額
    OTHER_DEPENDENTS_DEDUCTION: float = 56  # 其他撫養扣除額
    TAX_BRACKETS: List[Tuple[float, float]] = [
        (5621, 0.1),
        (11242, 0.15),
        (float('inf'), 0.2)
    ]


# ===============================
# 2. 稅務計算邏輯
# ===============================
class EstateTaxCalculator:
    """遺產稅計算器"""

    def __init__(self, constants: TaxConstants):
        self.constants = constants

    def compute_deductions(self, spouse: bool, adult_children: int, other_dependents: int,
                           disabled_people: int, parents: int) -> float:
        """計算總扣除額"""
        spouse_deduction = self.constants.SPOUSE_DEDUCTION_VALUE if spouse else 0
        total_deductions = (
                spouse_deduction +
                self.constants.FUNERAL_EXPENSE +
                (disabled_people * self.constants.DISABLED_DEDUCTION) +
                (adult_children * self.constants.ADULT_CHILD_DEDUCTION) +
                (other_dependents * self.constants.OTHER_DEPENDENTS_DEDUCTION) +
                (parents * self.constants.PARENTS_DEDUCTION)
        )
        return total_deductions

    @st.cache_data
    def calculate_estate_tax(_self, total_assets: float, spouse: bool, adult_children: int,
                             other_dependents: int, disabled_people: int, parents: int) -> Tuple[float, float, float]:
        """計算遺產稅"""
        deductions = _self.compute_deductions(spouse, adult_children, other_dependents, disabled_people, parents)
        if total_assets < _self.constants.EXEMPT_AMOUNT + deductions:
            return 0, 0, deductions
        taxable_amount = max(0, total_assets - _self.constants.EXEMPT_AMOUNT - deductions)
        tax_due = 0.0
        previous_bracket = 0
        for bracket, rate in _self.constants.TAX_BRACKETS:
            if taxable_amount > previous_bracket:
                taxable_at_rate = min(taxable_amount, bracket) - previous_bracket
                tax_due += taxable_at_rate * rate
                previous_bracket = bracket
        return taxable_amount, round(tax_due, 0), deductions


# ===============================
# 3. 模擬試算邏輯
# ===============================
class EstateTaxSimulator:
    """遺產稅模擬試算器"""

    def __init__(self, calculator: EstateTaxCalculator):
        self.calculator = calculator

    def simulate_insurance_strategy(self, total_assets: float, spouse: bool, adult_children: int,
                                    other_dependents: int, disabled_people: int, parents: int,
                                    premium_ratio: float, premium: float) -> Dict[str, Any]:
        """模擬保險策略"""
        _, tax_no_insurance, _ = self.calculator.calculate_estate_tax(total_assets, spouse, adult_children,
                                                                     other_dependents, disabled_people, parents)
        net_no_insurance = total_assets - tax_no_insurance
        claim_amount = round(premium * premium_ratio, 0)
        new_total_assets = total_assets - premium
        _, tax_new, _ = self.calculator.calculate_estate_tax(new_total_assets, spouse, adult_children,
                                                            other_dependents, disabled_people, parents)
        net_not_taxed = round(new_total_assets - tax_new + claim_amount, 0)
        effect_not_taxed = net_not_taxed - net_no_insurance
        effective_estate = total_assets - premium + claim_amount
        _, tax_effective, _ = self.calculator.calculate_estate_tax(effective_estate, spouse, adult_children,
                                                                  other_dependents, disabled_people, parents)
        net_taxed = round(effective_estate - tax_effective, 0)
        effect_taxed = net_taxed - net_no_insurance
        return {
            "沒有規劃": {
                "總資產": int(total_assets),
                "預估遺產稅": int(tax_no_insurance),
                "家人總共取得": int(net_no_insurance)
            },
            "有規劃保單": {
                "預估遺產稅": int(tax_new),
                "家人總共取得": int(net_not_taxed),
                "規劃效果": int(effect_not_taxed)
            },
            "有規劃保單 (被實質課稅)": {
                "預估遺產稅": int(tax_effective),
                "家人總共取得": int(net_taxed),
                "規劃效果": int(effect_taxed)
            }
        }

    def simulate_gift_strategy(self, total_assets: float, spouse: bool, adult_children: int,
                               other_dependents: int, disabled_people: int, parents: int,
                               years: int) -> Dict[str, Any]:
        """模擬贈與策略"""
        annual_gift_exemption = 244
        total_gift = years * annual_gift_exemption
        simulated_total_assets = max(total_assets - total_gift, 0)
        _, tax_sim, _ = self.calculator.calculate_estate_tax(simulated_total_assets, spouse, adult_children,
                                                            other_dependents, disabled_people, parents)
        net_after = round(simulated_total_assets - tax_sim + total_gift, 0)
        _, tax_original, _ = self.calculator.calculate_estate_tax(total_assets, spouse, adult_children,
                                                                 other_dependents, disabled_people, parents)
        net_original = total_assets - tax_original
        effect = net_after - net_original
        return {
            "沒有規劃": {
                "總資產": int(total_assets),
                "預估遺產稅": int(tax_original),
                "家人總共取得": int(net_original)
            },
            "提前贈與後": {
                "總資產": int(simulated_total_assets),
                "預估遺產稅": int(tax_sim),
                "總贈與金額": int(total_gift),
                "家人總共取得": int(net_after),
                "贈與年數": years
            },
            "規劃效果": {
                "較沒有規劃增加": int(effect)
            }
        }


# ===============================
# 4. Streamlit 介面
# ===============================
class EstateTaxUI:
    """遺產稅試算介面"""

    def __init__(self, calculator: EstateTaxCalculator, simulator: EstateTaxSimulator):
        self.calculator = calculator
        self.simulator = simulator

    def render_ui(self):
        """渲染 Streamlit 介面"""
        st.set_page_config(page_title="遺產稅試算＋建議", layout="wide")
        st.markdown("<h1 class='main-header'>遺產稅試算＋建議</h1>", unsafe_allow_html=True)
        st.selectbox("選擇適用地區", ["台灣（2025年起）"], index=0)

        with st.container():
            st.markdown("### 請輸入資產及家庭資訊")
            total_assets_input = st.number_input("總資產（萬）", min_value=1000, max_value=100000,
                                                 value=5000, step=100, help="請輸入您的總資產（單位：萬）")
            st.markdown("---")
            st.markdown("#### 請輸入家庭成員數")
            has_spouse = st.checkbox("是否有配偶（扣除額 553 萬）", value=False)
            adult_children_input = st.number_input("直系血親卑親屬數（每人 56 萬）", min_value=0, max_value=10,
                                                   value=0, help="請輸入直系血親或卑親屬人數")
            parents_input = st.number_input("父母數（每人 138 萬，最多 2 人）", min_value=0, max_value=2,
                                            value=0, help="請輸入父母人數")
            max_disabled = (1 if has_spouse else 0) + adult_children_input + parents_input
            disabled_people_input = st.number_input("重度以上身心障礙者數（每人 693 萬）", min_value=0, max_value=max_disabled,
                                                    value=0, help="請輸入重度以上身心障礙者人數")
            other_dependents_input = st.number_input("受撫養之兄弟姊妹、祖父母數（每人 56 萬）", min_value=0, max_value=5,
                                                     value=0, help="請輸入兄弟姊妹或祖父母人數")

        try:
            taxable_amount, tax_due, total_deductions = self.calculator.calculate_estate_tax(
                total_assets_input, has_spouse, adult_children_input,
                other_dependents_input, disabled_people_input, parents_input
            )
        except Exception as e:
            st.error(f"計算遺產稅時發生錯誤：{e}")
            return

        st.markdown("<h3>預估遺產稅：{0:,.0f} 萬元</h3>".format(tax_due), unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**資產概況**")
            df_assets = pd.DataFrame({"項目": ["總資產"], "金額（萬）": [int(total_assets_input)]})
            st.table(df_assets)
        with col2:
            st.markdown("**扣除項目**")
            df_deductions = pd.DataFrame({
                "項目": ["免稅額", "喪葬費扣除額", "配偶扣除額", "直系血親卑親屬扣除額", "父母扣除額", "重度身心障礙扣除額", "其他撫養扣除額"],
                "金額（萬）": [
                    self.calculator.constants.EXEMPT_AMOUNT,
                    self.calculator.constants.FUNERAL_EXPENSE,
                    self.calculator.constants.SPOUSE_DEDUCTION_VALUE if has_spouse else 0,
                    adult_children_input * self.calculator.constants.ADULT_CHILD_DEDUCTION,
                    parents_input * self.calculator.constants.PARENTS_DEDUCTION,
                    disabled_people_input * self.calculator.constants.DISABLED_DEDUCTION,
                    other_dependents_input * self.calculator.constants.OTHER_DEPENDENTS_DEDUCTION
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


# ===============================
# 5. 主程式
# ===============================
if __name__ == "__main__":
    constants = TaxConstants()
    calculator = EstateTaxCalculator(constants)
    simulator = EstateTaxSimulator(calculator)
    ui = EstateTaxUI(calculator, simulator)
    ui.render_ui()
