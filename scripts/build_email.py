import json, sys

CHECKLIST = [
    "청약통장 정보 (가입일, 납입횟수/금액)",
    "세대주/세대원 구성 (주민등록등본 기준)",
    "무주택기간",
    "부양가족 수 (가점제 대상 시)",
    "해당지역 거주기간",
    "특별공급 해당여부 (신혼부부/생애최초/다자녀 등)",
    "소득/자산 정보 (특별공급 시 소득기준 확인용)",
    "본인인증 수단 (공동인증서 또는 카카오/PASS 등)",
    "계약금 일정 및 자금 계획",
]

def fmt_amount(man_won):
    if man_won in (None, ""):
        return "-"
    try:
        return f"{int(man_won):,}만원"
    except Exception:
        return str(man_won)

def fmt_area(sqm):
    try:
        v = float(sqm)
        pyeong = v / 3.3058
        return f"{v:.2f}㎡ ({pyeong:.1f}평)"
    except Exception:
        return f"{sqm}㎡" if sqm not in (None, "") else "-"

def fmt_ym(ym):
    if not ym or len(str(ym)) != 6:
        return "-"
    s = str(ym)
    return f"{s[:4]}년 {int(s[4:6])}월"

def badge(text, color):
    return f"<span style='display:inline-block;padding:2px 8px;border-radius:5px;font-size:12px;font-weight:700;color:#fff;background:{color};margin-right:6px;'>{text}</span>"

def regular_card(item):
    units = item.get("units", [])
    target_hshld = sum((u.get("suply_hshldco") or 0) + (u.get("spsply_hshldco") or 0) for u in units)
    my_match = any((u.get("nwwds_hshldco") or 0) > 0 or (u.get("lfe_frst_hshldco") or 0) > 0 for u in units)
    border = "2px solid #2e9e4f" if my_match else "1px solid #ddd"
    units_rows = "".join(
        f"<tr><td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('house_ty','-')}</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{fmt_area(u.get('suply_ar'))}</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('suply_hshldco','-')}세대</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('spsply_hshldco','-')}세대</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{fmt_amount(u.get('lttot_top_amount'))}</td></tr>"
        for u in units
    )
    match_note = "<div style='font-size:12px;color:#2e9e4f;font-weight:700;margin-bottom:6px;'>✓ 신혼부부/생애최초 특별공급 물량 있음</div>" if my_match else ""
    return f"""
    <div style="border:{border};border-radius:10px;padding:16px 20px;margin-bottom:16px;">
      <div style="margin-bottom:6px;">{badge('정규', '#1a73e8')}<span style="font-size:17px;font-weight:700;">{item.get('house_nm','-')}</span></div>
      {match_note}
      <div style="color:#555;font-size:13px;margin-bottom:10px;">{item.get('cnstrct_entrps_nm','-')} · {item.get('hssply_adres','-')}</div>
      <div style="font-size:13px;margin-bottom:2px;">
        이번 공고 공급세대수 <b>{item.get('tot_suply_hshldco','-')}세대</b> 중
        84㎡ 이하 청약대상 <b style="color:#1a73e8;">{target_hshld}세대</b>
      </div>
      <div style="font-size:12px;color:#999;margin-bottom:10px;">※ 전체 단지 세대수(조합원 물량 등 포함)는 API에 없음 — 공고 링크에서 직접 확인 필요</div>
      <table style="border-collapse:collapse;width:100%;font-size:13px;margin-bottom:10px;">
        <thead><tr style="background:#f5f5f5;">
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">주택형</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">공급면적</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">일반공급</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">특별공급</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">분양최고금액</th>
        </tr></thead>
        <tbody>{units_rows}</tbody>
      </table>
      <table style="font-size:13px;color:#333;line-height:1.7;">
        <tr><td style="color:#888;width:110px;">접수기간</td><td>{item.get('rcept_bgnde','-')} ~ {item.get('rcept_endde','-')}</td></tr>
        <tr><td style="color:#888;">당첨자발표일</td><td>{item.get('przwner_presnatn_de','-')}</td></tr>
        <tr><td style="color:#888;">계약기간</td><td>{item.get('cntrct_cncls_bgnde','-')} ~ {item.get('cntrct_cncls_endde','-')}</td></tr>
        <tr><td style="color:#888;">입주예정월</td><td>{fmt_ym(item.get('mvn_prearnge_ym'))}</td></tr>
        <tr><td style="color:#888;">문의처</td><td>{item.get('mdhs_telno','-')}</td></tr>
      </table>
      <div style="margin-top:10px;"><a href="{item.get('pblanc_url','#')}" style="color:#1a73e8;font-size:13px;">공고 상세보기 →</a></div>
    </div>
    """

def remndr_card(item):
    return f"""
    <div style="border:1px solid #ddd;border-radius:10px;padding:16px 20px;margin-bottom:16px;">
      <div style="margin-bottom:6px;">{badge('무순위', '#e8710a')}<span style="font-size:17px;font-weight:700;">{item.get('house_nm','-')}</span></div>
      <div style="color:#555;font-size:13px;margin-bottom:10px;">{item.get('bsns_mby_nm','-')} · {item.get('hssply_adres','-')}</div>
      <div style="font-size:13px;margin-bottom:2px;">무순위 공급세대수 <b style="color:#e8710a;">{item.get('tot_suply_hshldco','-')}세대</b></div>
      <div style="font-size:12px;color:#999;margin-bottom:10px;">※ 전체 단지 세대수는 API에 없음 — 공고 링크에서 직접 확인 필요</div>
      <table style="font-size:13px;color:#333;line-height:1.7;">
        <tr><td style="color:#888;width:110px;">접수기간</td><td>{item.get('rcept_bgnde','-')} ~ {item.get('rcept_endde','-')}</td></tr>
        <tr><td style="color:#888;">당첨자발표일</td><td>{item.get('przwner_presnatn_de','-')}</td></tr>
        <tr><td style="color:#888;">계약기간</td><td>{item.get('cntrct_cncls_bgnde','-')} ~ {item.get('cntrct_cncls_endde','-')}</td></tr>
        <tr><td style="color:#888;">문의처</td><td>{item.get('mdhs_telno','-')}</td></tr>
      </table>
      <div style="margin-top:6px;color:#999;font-size:12px;">※ 무순위는 평형/분양가 상세가 API에 제공되지 않아 생략됨</div>
      <div style="margin-top:10px;"><a href="{item.get('pblanc_url','#')}" style="color:#e8710a;font-size:13px;">공고 상세보기 →</a></div>
    </div>
    """

def build(regular, remndr, run_date):
    total = len(regular) + len(remndr)
    if total:
        cards = "".join(regular_card(x) for x in regular) + "".join(remndr_card(x) for x in remndr)
        summary = f"오늘 서울 · 민영 · 전용 84㎡ 이하 신규 공고 {total}건입니다. (정규 {len(regular)} / 무순위 {len(remndr)})"
    else:
        cards = "<div style='color:#888;padding:20px 0;'>오늘은 조건에 맞는 신규 공고가 없습니다.</div>"
        summary = "오늘은 서울 · 민영 · 전용 84㎡ 이하 신규 공고가 없습니다."

    checklist_html = "".join(f"<li
