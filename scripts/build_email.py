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

AREA_LABEL = "전용 20평대~30평대(약 66~132㎡)"


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


def units_table(units):
    rows = "".join(
        f"<tr><td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('house_ty','-')}</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{fmt_area(u.get('suply_ar'))}</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('suply_hshldco','-')}세대</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{u.get('spsply_hshldco','-')}세대</td>"
        f"<td style='padding:6px 10px;border:1px solid #e5e5e5;'>{fmt_amount(u.get('lttot_top_amount'))}</td></tr>"
        for u in units
    )
    return f"""
      <table style="border-collapse:collapse;width:100%;font-size:13px;margin-bottom:10px;">
        <thead><tr style="background:#f5f5f5;">
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">주택형</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">공급면적</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">일반공급</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">특별공급</th>
          <th style="padding:6px 10px;border:1px solid #e5e5e5;">분양최고금액</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    """


def regular_card(item, urgent=False):
    units = item.get("units", [])
    target_hshld = sum((u.get("suply_hshldco") or 0) + (u.get("spsply_hshldco") or 0) for u in units)
    my_match = any((u.get("nwwds_hshldco") or 0) > 0 or (u.get("lfe_frst_hshldco") or 0) > 0 for u in units)
    border = "2px solid #e8710a" if urgent else ("2px solid #2e9e4f" if my_match else "1px solid #ddd")
    match_note = "<div style='font-size:12px;color:#2e9e4f;font-weight:700;margin-bottom:6px;'>✓ 신혼부부/생애최초 특별공급 물량 있음</div>" if my_match else ""
    urgent_note = "<div style='font-size:12px;color:#e8710a;font-weight:700;margin-bottom:6px;'>🔔 오늘 접수 시작 — 지금 청약하세요!</div>" if urgent else ""
    return f"""
    <div style="border:{border};border-radius:10px;padding:16px 20px;margin-bottom:16px;">
      <div style="margin-bottom:6px;">{badge('정규', '#1a73e8')}<span style="font-size:17px;font-weight:700;">{item.get('house_nm','-')}</span></div>
      {urgent_note}
      {match_note}
      <div style="color:#555;font-size:13px;margin-bottom:10px;">{item.get('cnstrct_entrps_nm','-')} · {item.get('hssply_adres','-')}</div>
      <div style="font-size:13px;margin-bottom:2px;">
        이번 공고 공급세대수 <b>{item.get('tot_suply_hshldco','-')}세대</b> 중
        {AREA_LABEL} 청약대상 <b style="color:#1a73e8;">{target_hshld}세대</b>
      </div>
      <div style="font-size:12px;color:#999;margin-bottom:10px;">※ 전체 단지 세대수(조합원 물량 등 포함)는 API에 없음 — 공고 링크에서 직접 확인 필요</div>
      {units_table(units)}
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


def remndr_card(item, urgent=False):
    units = item.get("units", [])
    has_units = bool(units)
    units_block = units_table(units) if has_units else ""
    border = "2px solid #e8710a" if urgent else "1px solid #ddd"
    urgent_note = "<div style='font-size:12px;color:#e8710a;font-weight:700;margin-bottom:6px;'>🔔 오늘 접수 시작 — 지금 청약하세요!</div>" if urgent else ""
    note = (
        ""
        if has_units
        else "<div style='margin-top:6px;color:#999;font-size:12px;'>※ 이 공고는 평형 상세를 API에서 가져오지 못해 조건 확인이 안 됐습니다 — 링크에서 직접 확인해주세요.</div>"
    )
    return f"""
    <div style="border:{border};border-radius:10px;padding:16px 20px;margin-bottom:16px;">
      <div style="margin-bottom:6px;">{badge('무순위', '#e8710a')}<span style="font-size:17px;font-weight:700;">{item.get('house_nm','-')}</span></div>
      {urgent_note}
      <div style="color:#555;font-size:13px;margin-bottom:10px;">{item.get('bsns_mby_nm','-')} · {item.get('hssply_adres','-')}</div>
      <div style="font-size:13px;margin-bottom:2px;">무순위 공급세대수 <b style="color:#e8710a;">{item.get('tot_suply_hshldco','-')}세대</b></div>
      <div style="font-size:12px;color:#999;margin-bottom:10px;">※ 전체 단지 세대수는 API에 없음 — 공고 링크에서 직접 확인 필요</div>
      {units_block}
      <table style="font-size:13px;color:#333;line-height:1.7;">
        <tr><td style="color:#888;width:110px;">접수기간</td><td>{item.get('rcept_bgnde','-')} ~ {item.get('rcept_endde','-')}</td></tr>
        <tr><td style="color:#888;">당첨자발표일</td><td>{item.get('przwner_presnatn_de','-')}</td></tr>
        <tr><td style="color:#888;">계약기간</td><td>{item.get('cntrct_cncls_bgnde','-')} ~ {item.get('cntrct_cncls_endde','-')}</td></tr>
        <tr><td style="color:#888;">문의처</td><td>{item.get('mdhs_telno','-')}</td></tr>
      </table>
      {note}
      <div style="margin-top:10px;"><a href="{item.get('pblanc_url','#')}" style="color:#e8710a;font-size:13px;">공고 상세보기 →</a></div>
    </div>
    """


def section(title, subtitle, regular_items, remndr_items, urgent=False):
    total = len(regular_items) + len(remndr_items)
    if total == 0:
        body = f"<div style='color:#888;padding:16px 0;font-size:13px;'>{subtitle}</div>"
    else:
        body = "".join(regular_card(x, urgent=urgent) for x in regular_items) + \
               "".join(remndr_card(x, urgent=urgent) for x in remndr_items)
    header_color = "#e8710a" if urgent else "#222"
    return f"""
    <div style="margin-bottom:28px;">
      <div style="font-size:16px;font-weight:700;color:{header_color};margin-bottom:4px;">{title} ({total}건)</div>
      {body}
    </div>
    """


def build(new_regular, new_remndr, rcept_today_regular, rcept_today_remndr, run_date):
    new_total = len(new_regular) + len(new_remndr)
    rcept_total = len(rcept_today_regular) + len(rcept_today_remndr)

    new_section = section(
        "📢 오늘 새로 뜬 공고",
        "오늘은 조건에 맞는 신규 공고가 없습니다.",
        new_regular, new_remndr, urgent=False,
    )
    rcept_section = section(
        "🔔 오늘 청약 접수 시작하는 공고",
        "오늘 접수를 시작하는 공고가 없습니다.",
        rcept_today_regular, rcept_today_remndr, urgent=True,
    )

    summary = f"{run_date} 기준 — 신규 공고 {new_total}건, 오늘 접수 시작 {rcept_total}건 (서울 · 민영 · {AREA_LABEL})"

    checklist_html = "".join(f"<li style='margin-bottom:4px;'>{c}</li>" for c in CHECKLIST)

    return f"""
    <div style="font-family:'Apple SD Gothic Neo',Malgun Gothic,Arial,sans-serif;color:#222;max-width:640px;margin:0 auto;">
      <div style="margin-bottom:20px;">
        <div style="font-size:12px;color:#999;margin-bottom:4px;">{run_date} 기준 · 서울 · 민영 · {AREA_LABEL}</div>
        <div style="font-size:15px;font-weight:700;">{summary}</div>
      </div>

      {rcept_section}
      {new_section}

      <div style="margin-top:8px;padding:16px 20px;background:#f8f9fa;border-radius:10px;">
        <div style="font-weight:700;font-size:14px;margin-bottom:8px;">📋 청약 신청 전 체크리스트</div>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#444;line-height:1.6;">
          {checklist_html}
        </ul>
      </div>

      <div style="margin-top:20px;font-size:11px;color:#aaa;">
        본 메일은 청약홈 공개 API 데이터를 기반으로 자동 생성되었습니다. 정확한 자격 요건 및 세부 조건은 반드시 각 공고문 원문을 확인하세요.
      </div>
    </div>
    """


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python3 build_email.py <입력 latest.json 경로> <출력 html 경로>", file=sys.stderr)
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new = data.get("new", {})
    rcept_today = data.get("rcept_today", {})

    new_regular = new.get("regular", [])
    new_remndr = new.get("remndr", [])
    rcept_today_regular = rcept_today.get("regular", [])
    rcept_today_remndr = rcept_today.get("remndr", [])

    generated_at = data.get("generated_at", "")
    run_date = generated_at.split("T")[0] if generated_at else ""

    html = build(new_regular, new_remndr, rcept_today_regular, rcept_today_remndr, run_date)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
