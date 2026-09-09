import os, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

KEY = os.environ["ODCLOUD_KEY"]
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()
CUTOFF = TODAY - timedelta(days=1)  # 어제~오늘 공고만 "신규"로 취급
BASE = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1"

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_list():
    items = []
    for page in range(1, 16):  # 안전장치: 최대 15페이지
        url = f"{BASE}/getAPTLttotPblancDetail?page={page}&perPage=100&serviceKey={KEY}"
        data = get(url)
        rows = data.get("data", [])
        if not rows:
            break
        items.extend(rows)
        oldest = rows[-1].get("RCRIT_PBLANC_DE", "")
        try:
            oldest_date = datetime.strptime(oldest, "%Y-%m-%d").date()
            if oldest_date < CUTOFF:
                break
        except ValueError:
            pass
    return items

def fetch_remndr_list():
    items = []
    for page in range(1, 16):
        url = f"{BASE}/getRemndrLttotPblancDetail?page={page}&perPage=100&serviceKey={KEY}"
        data = get(url)
        rows = data.get("data", [])
        if not rows:
            break
        items.extend(rows)
        oldest = rows[-1].get("RCRIT_PBLANC_DE", "")
        try:
            oldest_date = datetime.strptime(oldest, "%Y-%m-%d").date()
            if oldest_date < CUTOFF:
                break
        except ValueError:
            pass
    return items

def fetch_units(house_manage_no):
    cond = urllib.parse.quote(f"HOUSE_MANAGE_NO::EQ", safe="")
    url = f"{BASE}/getAPTLttotPblancMdl?page=1&perPage=50&serviceKey={KEY}&cond%5BHOUSE_MANAGE_NO%3A%3AEQ%5D={house_manage_no}"
    data = get(url)
    return data.get("data", [])

def unit_size_ok(house_ty):
    try:
        return int(float(house_ty.split(".")[0])) <= 84
    except Exception:
        return False

def main():
    raw = fetch_list()
    results = []
    for row in raw:
        try:
            pblanc_de = datetime.strptime(row.get("RCRIT_PBLANC_DE", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if pblanc_de < CUTOFF:
            continue
        if row.get("SUBSCRPT_AREA_CODE_NM") != "서울":
            continue
        if row.get("HOUSE_DTL_SECD_NM") != "민영":
            continue

        units = fetch_units(row["HOUSE_MANAGE_NO"])
        matched = [u for u in units if unit_size_ok(u.get("HOUSE_TY", ""))]
        if not matched:
            continue

        results.append({
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
            "units": [
                {
                    "house_ty": u.get("HOUSE_TY"),
                    "suply_ar": u.get("SUPLY_AR"),
                    "lttot_top_amount": u.get("LTTOT_TOP_AMOUNT"),
                    "suply_hshldco": u.get("SUPLY_HSHLDCO"),
                    "spsply_hshldco": u.get("SPSPLY_HSHLDCO"),
                    "nwwds_hshldco": u.get("NWWDS_HSHLDCO"),   # 신혼부부
                    "lfe_frst_hshldco": u.get("LFE_FRST_HSHLDCO"),  # 생애최초
                }
                for u in matched
            ],
        })

    # 무순위(잔여세대) - 평형 정보가 API에 없어서 84이하 필터는 못하고, 서울인 것만 거른다
    remndr_raw = fetch_remndr_list()
    remndr_results = []
    for row in remndr_raw:
        try:
            pblanc_de = datetime.strptime(row.get("RCRIT_PBLANC_DE", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if pblanc_de < CUTOFF:
            continue
        if row.get("SUBSCRPT_AREA_CODE_NM") != "서울":
            continue
        remndr_results.append({
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
        })

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(KST).isoformat(),
            "count": len(results) + len(remndr_results),
            "regular": results,
            "remndr": remndr_results,
        }, f, ensure_ascii=False, indent=2)

    with open("data/status.json", "w", encoding="utf-8") as f:
        json.dump({"last_run_kst": datetime.now(KST).isoformat(), "ok": True, "count": len(results) + len(remndr_results)}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
