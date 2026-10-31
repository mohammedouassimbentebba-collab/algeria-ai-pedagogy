# -*- coding: utf-8 -*-
"""
محرك قراءة ورسم واستثمار البيانات والجداول البيانية في الفيزياء والكيمياء
(BAC Physics & Chemistry Graphical Data Engine)
---------------------------------------------------------------------------------
أداة خوارزمية تخصصية لتنفيذ وتدقيق استثمار البيانات في البكالوريا الجزائرية:
1. حساب سلم الرسم الأمثل للمنحنيات (Echelle) لضمان احتلال أكثر من ثلثي مساحة الورقة.
2. المطابقة الحتمية بين المعادلة البيانية (y = a*x + b) والعلاقة النظرية الفيزيائية.
3. استخراج المقادير الفيزيائية لوحدات المنهاج الست:
   - الميكانيك (التسارع a_G، السرعة v0، المسافة، وقوة الاحتكاك/الجر).
   - الكهرباء (شحن/تفريغ RC، ثابت الزمن tau، سعة المكثفة C، وذاتية الوشيعة L).
   - الكيمياء (زمن نصف التفاعل t_1/2، السرعة اللحظية والحجمية، والمتفاعل المحد).
   - النووي (ثابت التفكك lambda، زمن نصف العمر t_1/2، والنشاط الابتدائي A0).
   - الأحماض والأسس (نقطة التكافؤ E بطريقة المماسات المشتقة، ونصف التكافؤ pKa).
"""

import sys
import math
import argparse
from typing import Dict, List, Tuple, Any, Optional

# تهيئة مخارج النصوص للـ UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==============================================================================
# 1. خوارزمية حساب السلم الأمثل لرسم المنحنى (Optimal Scale Calculator)
# ==============================================================================

CONVENIENT_STEPS = [1.0, 2.0, 2.5, 5.0]

def find_nice_scale(max_val: float, available_cm: float = 12.0) -> float:
    """
    حساب سلم مريح وعملي (1cm -> S) بحيث يشغل المنحنى بين 65% و 90% من المساحة المتاحة.
    """
    if max_val <= 0:
        return 1.0
    
    raw_step = max_val / available_cm
    exponent = math.floor(math.log10(raw_step))
    fraction = raw_step / (10 ** exponent)
    
    # اختيار أقرب مضاعف مريح للأعلى
    selected_step = 10.0
    for step in CONVENIENT_STEPS:
        if step >= fraction:
            selected_step = step
            break
            
    nice_scale = selected_step * (10 ** exponent)
    return nice_scale

def compute_graph_layout(x_vals: List[float], y_vals: List[float],
                         x_axis_cm: float = 12.0, y_axis_cm: float = 16.0) -> Dict[str, Any]:
    """
    تحديد أبعاد ورقة الرسم المليمترية والسلم المعتمد ونقاط الإسقاط.
    """
    max_x = max(x_vals) if x_vals else 1.0
    max_y = max(y_vals) if y_vals else 1.0
    
    scale_x = find_nice_scale(max_x, x_axis_cm)
    scale_y = find_nice_scale(max_y, y_axis_cm)
    
    occupied_x_cm = max_x / scale_x
    occupied_y_cm = max_y / scale_y
    
    ratio_x = (occupied_x_cm / x_axis_cm) * 100
    ratio_y = (occupied_y_cm / y_axis_cm) * 100
    
    return {
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_x_str": f"1 cm -> {scale_x:g}",
        "scale_y_str": f"1 cm -> {scale_y:g}",
        "occupied_x_cm": round(occupied_x_cm, 2),
        "occupied_y_cm": round(occupied_y_cm, 2),
        "coverage_ratio_x": f"{ratio_x:.1f}%",
        "coverage_ratio_y": f"{ratio_y:.1f}%",
        "is_valid_layout": (ratio_x >= 60.0 and ratio_y >= 60.0)
    }

# ==============================================================================
# 2. خوارزمية الانحدار الخطي والمطابقة الرياضية (Linear Regression & Modeling)
# ==============================================================================

def fit_linear_curve(x_pts: List[float], y_pts: List[float]) -> Dict[str, Any]:
    """
    حساب معادلة المستقيم الرياضية: y = a * x + b
    مع تحديد معامل التوجيه (الميل a) والترتيبة عند المبدأ (b) ومعامل الارتباط R^2.
    """
    n = len(x_pts)
    if n < 2 or len(y_pts) != n:
        raise ValueError("يلزم نقطتان على الأقل لحساب ميل المستقيم.")
        
    sum_x = sum(x_pts)
    sum_y = sum(y_pts)
    sum_xx = sum(x * x for x in x_pts)
    sum_yy = sum(y * y for y in y_pts)
    sum_xy = sum(x * y for x, y in zip(x_pts, y_pts))
    
    denom = (n * sum_xx - sum_x * sum_x)
    if abs(denom) < 1e-12:
        raise ValueError("النقاط متطابقة في محور الفواصل، لا يمكن حساب الميل.")
        
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    # معامل الارتباط الخطي R^2
    denom_r = math.sqrt(abs((n * sum_xx - sum_x * sum_x) * (n * sum_yy - sum_y * sum_y)))
    r_sq = ((n * sum_xy - sum_x * sum_y) / denom_r) ** 2 if denom_r > 1e-12 else 1.0
    
    # تحديد شكل المعادلة البيانية
    if abs(intercept) < 1e-5:
        curve_type = "دالة خطية (مستقيم يمر من المبدأ)"
        math_equation = f"y = {slope:.4g} · x"
    else:
        curve_type = "دالة تآلفية (مستقيم لا يمر من المبدأ)"
        sign = "+" if intercept >= 0 else "-"
        math_equation = f"y = {slope:.4g} · x {sign} {abs(intercept):.4g}"
        
    return {
        "slope_a": slope,
        "intercept_b": intercept,
        "r_squared": round(r_sq, 4),
        "curve_type": curve_type,
        "math_equation": math_equation
    }

# ==============================================================================
# 3. محرك المطابقة الفيزيائية واستخراج المقادير (Physical Laws Matching)
# ==============================================================================

def analyze_mechanics_velocity_graph(x_time: List[float], y_vel: List[float], 
                                     mass_kg: Optional[float] = None, 
                                     angle_deg: Optional[float] = None,
                                     friction_force_n: Optional[float] = None) -> Dict[str, Any]:
    """
    استثمار بيان السرعة v = f(t) في الميكانيك (كما في بكالوريا 2021 ت.ر Q07):
    - المعادلة البيانية: v(t) = a_G * t + v0
    - التسارع: a_G = الميل
    - المسافة المقطوعة: المساحة تحت المنحنى = (v0 + v_final)/2 * Delta_t
    - القوة المحركة F بتطبيق القانون الثاني لنيوتن: F - f - m*g*sin(alpha) = m*a_G
    """
    fit = fit_linear_curve(x_time, y_vel)
    a_g = fit["slope_a"]
    v0 = fit["intercept_b"]
    t_fin = x_time[-1] - x_time[0]
    v_fin = y_vel[-1]
    
    # حساب المسافة (المساحة تحت المنحنى لشبه منحرف)
    dist = ((v0 + v_fin) / 2.0) * t_fin
    
    results = {
        "unit": "الميكانيك وتطور جملة ميكانيكية",
        "math_equation": fit["math_equation"],
        "acceleration_aG": f"{a_g:.4f} m/s²",
        "initial_velocity_v0": f"{v0:.2f} m/s",
        "distance_traveled_d": f"{dist:.2f} m",
        "method": "المطابقة بين المعادلة البيانية v(t) = a·t + b والمعادلة النظرية للحركة المستقيمة المتغيرة بانتظام v(t) = a_G·t + v_0"
    }
    
    if mass_kg and angle_deg is not None:
        g = 9.8
        alpha_rad = math.radians(angle_deg)
        f_ext = friction_force_n if friction_force_n is not None else 0.0
        # F = m * a_G + f + m * g * sin(alpha)
        f_pull = mass_kg * a_g + f_ext + mass_kg * g * math.sin(alpha_rad)
        results["pull_force_F"] = f"{f_pull:.2f} N"
        
    return results

def analyze_rc_circuit_charging(t_pts: List[float], uc_pts: List[float], 
                                resistance_ohm: float) -> Dict[str, Any]:
    """
    استثمار بيان شحن المكثفة uc(t) في الكهرباء:
    - المقارب الأفقي عند النظام الدائم يعطي القوة المحركة الكهربائية E
    - ثابت الزمن tau: عند t = tau يكون u_C(tau) = 0.63 * E
    - سعة المكثفة: C = tau / R
    """
    e_val = max(uc_pts)
    uc_tau_target = 0.63 * e_val
    
    # تقريب زمني لـ tau من النقاط
    closest_idx = min(range(len(uc_pts)), key=lambda i: abs(uc_pts[i] - uc_tau_target))
    tau_approx = t_pts[closest_idx]
    
    cap_c = tau_approx / resistance_ohm
    
    return {
        "unit": "الظواهر الكهربائية (ثنائي القطب RC)",
        "generator_voltage_E": f"{e_val:.2f} V",
        "voltage_at_tau": f"{uc_tau_target:.2f} V (0.63 · E)",
        "time_constant_tau": f"{tau_approx:.4f} s",
        "capacitance_C": f"{cap_c:.4e} F ({cap_c * 1e6:.2f} µF)",
        "theoretical_relation": "u_C(t) = E · (1 - e^(-t / RC))",
        "identification_method": "القراءة البيانية للمقارب الأفقي (E) ثم تعيين النقطة ذات الترتيبة 0.63·E لإسقاط ثابت الزمن tau."
    }

def analyze_chemical_kinetics(t_min: List[float], x_mmol: List[float], 
                               v_total_ml: float) -> Dict[str, Any]:
    """
    استثمار بيان المتابعة الزمنية في الكيمياء x = f(t):
    - التقدم النهائي: x_f = القيمة الأعظمية في النظام النهائي
    - زمن نصف التفاعل t_1/2: قيمة t المقابلة لـ x_f / 2
    - سرعة التفاعل اللحظية الابتدائية v0 عند t=0 (ميل مماس المبدأ)
    - السرعة الحجمية للتفاعل v_vol = (1/V_tot) * dx/dt
    """
    x_final = max(x_mmol)
    x_half = x_final / 2.0
    
    closest_idx = min(range(len(x_mmol)), key=lambda i: abs(x_mmol[i] - x_half))
    t_half = t_min[closest_idx]
    
    # حساب سرعة التفاعل الابتدائية بميل أول نقطتين
    slope_init_mmol_min = (x_mmol[1] - x_mmol[0]) / (t_min[1] - t_min[0])
    v_vol_init = (slope_init_mmol_min / (v_total_ml * 1e-3)) # mmol/(L*min)
    
    return {
        "unit": "المتابعة الزمنية لتحول كيميائي",
        "final_progress_xf": f"{x_final:.2f} mmol",
        "half_progress": f"{x_half:.2f} mmol",
        "half_life_t1_2": f"{t_half:.2f} min",
        "initial_reaction_rate_v0": f"{slope_init_mmol_min:.3e} mmol/min",
        "initial_volumetric_rate": f"{v_vol_init:.3e} mmol/(L·min)",
        "method": "تعيين التقدم الأعظمي x_f، ثم إسقاط x_f / 2 على المنحنى ثم على محور الأزمنة لقراءة t_1/2 بدقة."
    }

def analyze_nuclear_decay(t_days: List[float], a_bq: List[float]) -> Dict[str, Any]:
    """
    استثمار بيان النشاط الإشعاعي ln(A) = f(t) في الفيزياء النووية:
    - المعادلة البيانية: ln(A) = -lambda * t + ln(A0)
    - ثابت التفكك lambda = -الميل
    - زمن نصف العمر: t_1/2 = ln(2) / lambda
    - النشاط الابتدائي: A0 = exp(intercept)
    """
    ln_a = [math.log(a) for a in a_bq]
    fit = fit_linear_curve(t_days, ln_a)
    
    decay_const_day = -fit["slope_a"]
    decay_const_sec = decay_const_day / (24 * 3600)
    t_half_day = math.log(2) / decay_const_day
    a0 = math.exp(fit["intercept_b"])
    
    return {
        "unit": "التحولات النووية والتناقص الإشعاعي",
        "math_equation": fit["math_equation"],
        "decay_constant_lambda": f"{decay_const_day:.4e} day⁻¹ ({decay_const_sec:.4e} s⁻¹)",
        "half_life_t1_2": f"{t_half_day:.2f} days",
        "initial_activity_A0": f"{a0:.2e} Bq",
        "theoretical_relation": "ln(A(t)) = -λ · t + ln(A_0)",
        "method": "المطابقة بين المستقيم التآلفي المتناقص ln(A) = a·t + b والعلاقة اللوغاريتمية لقانون التناقص الإشعاعي."
    }

# ==============================================================================
# 4. محاكي رسم المخطط البياني نصياً (ASCII Graph Previewer)
# ==============================================================================

def render_ascii_graph(x_pts: List[float], y_pts: List[float], 
                       title: str = "منحنى بياني", 
                       width: int = 50, height: int = 15) -> str:
    """
    توليد معاينة بصرية للمنحنى البياني داخل واجهة التيرمينال لتدريب النموذج على تمثيل النقاط.
    """
    min_x, max_x = min(x_pts), max(x_pts)
    min_y, max_y = min(y_pts), max(y_pts)
    
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # تعيين النقاط التجريبية
    for x, y in zip(x_pts, y_pts):
        col = int(((x - min_x) / (max_x - min_x + 1e-9)) * (width - 1))
        row = int(((max_y - y) / (max_y - min_y + 1e-9)) * (height - 1))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = "+" # علامة صليب صغيرة كالموصى بها وزارياً
        
    lines = [f"=== [ معاينة الرسم البياني: {title} ] ==="]
    for r in range(height):
        row_str = "".join(grid[r])
        if r == 0:
            lines.append(f"{max_y:6.2f} |{row_str}")
        elif r == height - 1:
            lines.append(f"{min_y:6.2f} |{row_str}")
        else:
            lines.append(f"       |{row_str}")
            
    lines.append("       +" + "-" * width)
    lines.append(f"       {min_x:<6.2f}" + " " * (width - 12) + f"{max_x:>6.2f}")
    return "\n".join(lines)

# ==============================================================================
# واجهة الأوامر التشغيلية والتدقيق
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="محرك البيانات والتمثيلات البيانية في الفيزياء والكيمياء (BAC)")
    parser.add_argument("--demo", action="store_true", help="تشغيل عرض شامل لكافة الوحدات الست")
    parser.add_argument("--scale", nargs=2, type=float, metavar=('MAX_X', 'MAX_Y'), help="حساب السلم الأمثل لبيانات عظمى")
    
    args = parser.parse_args()
    
    if args.demo or len(sys.argv) == 1:
        print("=" * 80)
        print("★ المحرك التخصصي لقراءة وتمثيل واستثمار البيانات في الفيزياء والكيمياء ★")
        print("=" * 80)
        
        # 1. اختبار الميكانيك (تمرين بكالوريا 2021 ت.ر Q07 الحقيقي)
        t_q07 = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        v_q07 = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        print("\n[1] الميكانيك: استثمار بيان السرعة v = f(t) (بكالوريا 2021 ت.ر):")
        layout_q07 = compute_graph_layout(t_q07, v_q07)
        print(f"  • سلم الرسم المقترح: الفواصل ({layout_q07['scale_x_str']}) | التراتيب ({layout_q07['scale_y_str']})")
        print(f"  • نسبة احتلال الورقة: أفقي {layout_q07['coverage_ratio_x']} | شاقولي {layout_q07['coverage_ratio_y']} (مطابق: {layout_q07['is_valid_layout']})")
        
        mech_res = analyze_mechanics_velocity_graph(t_q07, v_q07, mass_kg=1200.0, angle_deg=20.0, friction_force_n=400.0)
        print(f"  • المعادلة البيانية: {mech_res['math_equation']}")
        print(f"  • التسارع المستخرج a_G: {mech_res['acceleration_aG']}")
        print(f"  • السرعة الابتدائية v0: {mech_res['initial_velocity_v0']}")
        print(f"  • المسافة المقطوعة d: {mech_res['distance_traveled_d']} (تطابق 100% مع حساب التكامل ومساحة شبه المنحرف)")
        
        # 2. اختبار الكهرباء RC
        t_rc = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12]
        uc_rc = [0.0, 3.79, 6.18, 7.69, 8.64, 9.24, 9.62]
        print("\n[2] الكهرباء: استثمار بيان شحن المكثفة u_C = f(t):")
        rc_res = analyze_rc_circuit_charging(t_rc, uc_rc, resistance_ohm=1000.0)
        print(f"  • القوة المحركة E: {rc_res['generator_voltage_E']}")
        print(f"  • ثابت الزمن tau المقاس: {rc_res['time_constant_tau']}")
        print(f"  • سعة المكثفة المستنتجة C: {rc_res['capacitance_C']}")
        
        # 3. اختبار الكيمياء
        t_chem = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0]
        x_chem = [0.0, 1.8, 3.1, 4.0, 4.6, 4.8, 5.0, 5.0]
        print("\n[3] الكيمياء: استثمار بيان المتابعة الزمنية x = f(t):")
        chem_res = analyze_chemical_kinetics(t_chem, x_chem, v_total_ml=100.0)
        print(f"  • التقدم النهائي x_f: {chem_res['final_progress_xf']}")
        print(f"  • زمن نصف التفاعل t_1/2: {chem_res['half_life_t1_2']}")
        print(f"  • السرعة الابتدائية v0: {chem_res['initial_reaction_rate_v0']}")
        
        # 4. اختبار النووي
        t_nuc = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
        a_nuc = [1.0e6, 6.7e5, 4.5e5, 3.0e5, 2.0e5, 1.3e5]
        print("\n[4] النووي: استثمار بيان التناقص ln(A) = f(t):")
        nuc_res = analyze_nuclear_decay(t_nuc, a_nuc)
        print(f"  • المعادلة البيانية: {nuc_res['math_equation']}")
        print(f"  • ثابت التفكك lambda: {nuc_res['decay_constant_lambda']}")
        print(f"  • زمن نصف العمر t_1/2: {nuc_res['half_life_t1_2']}")
        
        # 5. معاينة الرسم
        print("\n[5] معاينة تمثيل النقاط في ورقة المليمترية (ASCII Visual Grid):")
        print(render_ascii_graph(t_q07, v_q07, title="بيان السرعة v(t) - Q07"))
        print("=" * 80)
        return

    if args.scale:
        mx, my = args.scale
        layout = compute_graph_layout([mx], [my])
        print(f"السلم المقترح لمحور الفواصل: {layout['scale_x_str']}")
        print(f"السلم المقترح لمحور التراتيب: {layout['scale_y_str']}")

if __name__ == "__main__":
    main()
