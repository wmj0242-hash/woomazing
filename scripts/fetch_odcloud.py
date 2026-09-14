import os, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

KEY = os.environ["ODCLOUD_KEY"]
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()

NEW_CUTOFF = TODAY - timedelta(days=1)     # "신규 공고" 판단 기준: 공고일이 어제~오늘
FETCH_CUTOFF = TODAY - timedelta(days=30)  # 데이터 수집 범위: 최근 30일치 공고까지 (접수시작일이 오늘인 옛 공고도 잡기 위해 넉넉히)

BASE = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1"

# 전용면적 필터: 20평대~30평대
# 아파트 주택형 코드(HOUSE_TY)는 059/066/074/084/099/114/129처럼 반올림된 값으로 나오므로
# 66(=20평형 코드)이 정확히 20*3.3058=66.116보다 작아서 빠지는 걸 막기 위해 하한을 약간 낮춰둠.
MIN_SQM = 65.0    # 약 19.7평 이상 (066 코드 포함)
MAX_SQM = 135.0   # 약 40.8평 미만 (129 코드까지 포함, 40평대 시작 전)


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_list():
    items = []
    for page in range(1, 41):  # 안전장치: 최대 40페이지 (30일치 커버 위해 기존 15페이지에서 상향)
        url = f"{BASE}/getAPTLttotPblancDetail?page={page}&perPage=100&serviceKey={KEY}"
        data = get(url)
        rows = data.get("data", [])
        if not rows:
            break
        items.extend(rows)
        oldest = rows[-1].get("RCRIT_PBLANC_DE", "")
        try:
            oldest_date = datetime.strptime(oldest, "%Y-%m-%d").date()
            if oldest_date < FETCH_CUTOFF:
                break
        except ValueError:
            pass
    return items


def fetch_remndr_list():
    items = []
    for page in range(1, 41):
        url = f"{BASE}/getRemndrLttotPblancDetail?page={page}&perPage=100&serviceKey={KEY}"
        data = get(url)
        rows = data.get("data", [])
        if not rows:
            break
        items.extend(rows)
        oldest = rows[-1].get("RCRIT_PBLANC_DE", "")
        try:
            oldest_date = datetime.strptime(oldest, "%Y-%m-%d").date()
            if oldest_date < FETCH_CUTOFF:
                break
        except ValueError:
            pass
    return items


def fetch_units(house_manage_no):
    url = f"{BASE}/getAPTLttotPblancMdl?page=1&perPage=50&serviceKey={KEY}&cond%5BHOUSE_MANAGE_NO%3A%3AEQ%5D={house_manage_no}"
    data = get(url)
    return data.get("data", [])


def unit_size_ok(house_ty):
    """HOUSE_TY 예: '084.9702' -> 공급면적 유형 84. 20~39평대(약 65~135㎡)만 통과."""
    try:
        nominal = float(house_ty.split(".")[0])
        return MIN_SQM <= nominal < MAX_SQM
    except Exception:
        return False


def build_unit_dict(u):
    return {
        "house_ty": u.get("HOUSE_TY"),
        "suply_ar": u.get("SUPLY_AR"),
        "lttot_top_amount": u.get("LTTOT_TOP_AMOUNT"),
        "suply_hshldco": u.get("SUPLY_HSHLDCO"),
        "spsply_hshldco": u.get("SPSPLY_HSHLDCO"),
        "nwwds_hshldco": u.get("NWWDS_HSHLDCO"),   # 신혼부부
        "lfe_frst_hshldco": u.get("LFE_FRST_HSHLDCO"),  # 생애최초
    }


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def build_regular_item(row, matched_units):
    return {
        "house_manage_no": row.get("HOUSE_MANAGE_NO"),
        "house_nm": row.get("HOUSE_NM"),
        "cnstrct_entrps_nm": row.get("CNSTRCT_ENTRPS_NM"),
        "hssply_adres": row.get("HSSPLY_ADRES"),
        "tot_suply_hshldco": row.get("TOT_SUPLY_HSHLDCO"),
        "rcept_bgnde": row.get("RCEPT_BGNDE"),
        "rcept_endde": row.get("RCEPT_ENDDE"),
        "przwner_presnatn_de": row.get("PRZWNER_PRESNATN_DE"),
        "cntrct_cncls_bgnde": row.get("CNTRCT_CNCLS_BGNDE"),
        "cntrct_cncls_endde": row.get("CNTRCT_CNCLS_ENDDE"),
        "mdhs_telno": row.get("MDHS_TELNO"),
        "pblanc_url": row.get("PBLANC_URL"),
        "rcrit_pblanc_de": row.get("RCRIT_PBLANC_DE"),
        "units": [build_unit_dict(u) for u in matched_units],
    }


def build_remndr_item(row, matched_units):
    return {
        "house_manage_no": row.get("HOUSE_MANAGE_NO"),
        "house_nm": row.get("HOUSE_NM"),
        "bsns_mby_nm": row.get("BSNS_MBY_NM"),
        "hssply_adres": row.get("HSSPLY_ADRES"),
        "tot_suply_hshldco": row.get("TOT_SUPLY_HSHLDCO"),
        "rcept_bgnde": row.get("SUBSCRPT_RCEPT_BGNDE"),
        "rcept_endde": row.get("SUBSCRPT_RCEPT_ENDDE"),
        "przwner_presnatn_de": row.get("PRZWNER_PRESNATN_DE"),
        "cntrct_cncls_bgnde": row.get("CNTRCT_CNCLS_BGNDE"),
        "cntrct_cncls_endde": row.get("CNTRCT_CNCLS_ENDDE"),
        "mdhs_telno": row.get("MDHS_TELNO"),
        "pblanc_url": row.get("PBLANC_URL"),
        "rcrit_pblanc_de": row.get("RCRIT_PBLANC_DE"),
        "units": [build_unit_dict(u) for u in matched_units],
    }


def main():
    new_regular, rcept_today_regular = [], []
    new_remndr, rcept_today_remndr = [], []

    # ---- 정규 공고 ----
    for row in fetch_list():
        pblanc_de = parse_date(row.get("RCRIT_PBLANC_DE", ""))
        if pblanc_de is None or pblanc_de < FETCH_CUTOFF:
            continue
        if row.get("SUBSCRPT_AREA_CODE_NM") != "서울":
            continue
        if row.get("HOUSE_DTL_SECD_NM") != "민영":
            continue

        is_new = NEW_CUTOFF <= pblanc_de <= TODAY
        rcept_bgnde = parse_date(row.get("RCEPT_BGNDE", ""))
        is_rcept_today = rcept_bgnde == TODAY

        if not (is_new or is_rcept_today):
            continue

        units = fetch_units(row["HOUSE_MANAGE_NO"])
        matched = [u for u in units if unit_size_ok(u.get("HOUSE_TY", ""))]
        if not matched:
            continue

        item = build_regular_item(row, matched)
        if is_new:
            new_regular.append(item)
        if is_rcept_today:
            rcept_today_regular.append(item)

    # ---- 무순위(잔여세대) ----
    for row in fetch_remndr_list():
        pblanc_de = parse_date(row.get("RCRIT_PBLANC_DE", ""))
        if pblanc_de is None or pblanc_de < FETCH_CUTOFF:
            continue
        if row.get("SUBSCRPT_AREA_CODE_NM") != "서울":
            continue

        is_new = NEW_CUTOFF <= pblanc_de <= TODAY
        rcept_bgnde = parse_date(row.get("SUBSCRPT_RCEPT_BGNDE", ""))
        is_rcept_today = rcept_bgnde == TODAY

        if not (is_new or is_rcept_today):
            continue

        house_manage_no = row.get("HOUSE_MANAGE_NO")
        matched = []
        if house_manage_no:
            try:
                units = fetch_units(house_manage_no)
                matched = [u for u in units if unit_size_ok(u.get("HOUSE_TY", ""))]
            except Exception:
                matched = []
        if not matched:
            continue

        item = build_remndr_item(row, matched)
        if is_new:
            new_remndr.append(item)
        if is_rcept_today:
            rcept_today_remndr.append(item)

    total = (
        len(new_regular) + len(new_remndr)
        + len(rcept_today_regular) + len(rcept_today_remndr)
    )

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(KST).isoformat(),
            "count": total,
            "new": {
                "regular": new_regular,
                "remndr": new_remndr,
            },
            "rcept_today": {
                "regular": rcept_today_regular,
                "remndr": rcept_today_remndr,
            },
        }, f, ensure_ascii=False, indent=2)

    with open("data/status.json", "w", encoding="utf-8") as f:
        json.dump({"last_run_kst": datetime.now(KST).isoformat(), "ok": True, "count": total}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
