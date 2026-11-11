import os
import json
import re
import time
import math
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/crawlspace-dehu-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9").strip()
CUSTOM_DEHU = os.environ.get("CUSTOM_DEHU", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_dehus.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

_CACHED_MODELS = None

# Format: (Model / Crawl Space Scenario, Floor Area Sq Ft, Height Ft, AHAM Pints/Day [80F/60%],Saturation Pints/Day, Running Amps 120V, Barrier Mil Spec)
SEED_DEHUS = [
    ("AlorAir Sentinel HD55 / HD55S (55 Pint AHAM / 120 Pint Max)", 1300, 3.5, 55, 120, 3.6, "12-Mil / 20-Mil Reinforced"),
    ("AlorAir Sentinel HDi65S Wi-Fi (65 Pint AHAM w/ Built-In Pump)", 1800, 3.5, 65, 130, 4.7, "20-Mil String-Reinforced"),
    ("AlorAir Sentinel HD90 / HDi90 (90 Pint AHAM / 198 Pint Max)", 2600, 4.0, 90, 198, 5.6, "20-Mil Heavy Encapsulation"),
    ("AlorAir Sentinel HDi100 & HDi120 (100–120 Pint Commercial)", 3300, 4.0, 120, 235, 7.3, "20-Mil Commercial Liner"),
    ("AlorAir Basement/Crawl Space Storm LGR Extreme 85 Pint", 2300, 7.5, 85, 190, 5.9, "12-Mil / 20-Mil Vapor Liner"),
    ("AprilAire E070 (70 Pint AHAM) Crawl Space Dehumidifier", 2000, 3.5, 70, 135, 5.2, "12-Mil / 20-Mil Reinforced"),
    ("AprilAire E080 (80 Pint AHAM) Whole-House & Crawl Space", 2400, 4.0, 80, 155, 5.8, "20-Mil String-Reinforced"),
    ("AprilAire E100 (100 Pint AHAM) High-Capacity Dehumidifier", 3000, 4.0, 100, 195, 6.9, "20-Mil String-Reinforced"),
    ("AprilAire E130 (130 Pint AHAM) Estate Basement/Crawl Space", 3800, 8.0, 130, 240, 8.3, "20-Mil Commercial Liner"),
    ("Santa Fe Compact70 (70 Pint AHAM) Low-Clearance Crawl Space", 1900, 3.0, 70, 140, 5.1, "16-Mil / 20-Mil Liner"),
    ("Santa Fe Advance90 & Advance100 Crawl Space Dehumidifier", 2700, 3.5, 90, 185, 5.7, "20-Mil String-Reinforced"),
    ("Santa Fe Ultra98 & Ultra120 Whole-House Ducted Dehumidifier", 3200, 8.0, 98, 200, 6.4, "20-Mil Encapsulation"),
    ("Waykar 70-Pint & 120-Pint Commercial Crawl Space Dehumidifier", 1800, 3.5, 60, 125, 4.5, "12-Mil / 20-Mil Reinforced"),
    ("Abestorm Guardian SN55 & SNS65 Crawl Space Dehumidifier", 1500, 3.5, 55, 120, 3.8, "12-Mil / 20-Mil Reinforced"),
    ("Abestorm Guardian SNS90 (90 Pint AHAM) w/ Condensate Pump", 2500, 4.0, 90, 198, 5.6, "20-Mil String-Reinforced"),
    ("Tosot / Midea 50-Pint DOE (70-Pint Old AHAM) Basement Unit", 1500, 8.0, 50, 95, 4.8, "10-Mil / 12-Mil Vapor Barrier"),
    ("BaseAire AirWerx 55 & AirWerx 65S Crawl Space Dehumidifier", 1600, 3.5, 65, 130, 4.6, "12-Mil / 20-Mil Reinforced"),
    ("BaseAire AirWerx 90X & 100X Heavy-Duty Crawl Space Unit", 2700, 4.0, 90, 198, 5.8, "20-Mil String-Reinforced"),
    ("Dri-Eaz Revolution LGR & PHD 200 Commercial Dehumidifier", 2800, 4.0, 80, 175, 6.2, "20-Mil String-Reinforced"),
    ("Little Giant VCMA-20ULS Condensate Pump + Dehumidifier Setup", 2000, 3.5, 70, 145, 5.0, "20-Ft Vertical Lift Drain"),
    ("1,000 Sq Ft Crawl Space Encapsulation & Dehumidifier Sizing", 1000, 3.0, 55, 120, 3.6, "12-Mil / 20-Mil Vapor Barrier"),
    ("1,500 Sq Ft Crawl Space Encapsulation & Dehumidifier Sizing", 1500, 3.5, 65, 130, 4.7, "20-Mil String-Reinforced"),
    ("2,000 Sq Ft Crawl Space Encapsulation & Dehumidifier Sizing", 2000, 3.5, 75, 155, 5.4, "20-Mil String-Reinforced"),
    ("2,500 Sq Ft Crawl Space Encapsulation & Dehumidifier Sizing", 2500, 4.0, 90, 198, 5.8, "20-Mil String-Reinforced"),
    ("3,000 Sq Ft Large Crawl Space Encapsulation & Dehumidifier", 3000, 4.0, 105, 215, 6.8, "20-Mil String-Reinforced"),
    ("1,500 Sq Ft Damp Basement (8-Ft Ceiling) Dehumidifier Sizing", 1500, 8.0, 70, 145, 5.1, "50% RH Mold-Stop Target"),
    ("2,200 Sq Ft Wet Basement (8-Ft Ceiling) Dehumidifier Sizing", 2200, 8.0, 90, 195, 5.8, "50% RH Mold-Stop Target"),
    ("12-Mil vs 20-Mil Reinforced Crawl Space Vapor Barrier Roll", 1800, 3.5, 65, 135, 4.7, "Wall + Pier + 15% Overlap"),
    ("50-Pint DOE (65°F) vs 70-Pint AHAM (80°F) Rating Conversion", 1800, 7.5, 70, 135, 5.0, "DOE vs AHAM Psychrometrics"),
    ("Sealed vs Vented Dirt Crawl Space Moisture Load Comparison", 1800, 3.5, 70, 145, 5.1, "IRC R408.3 Unvented Code")
]


def load_json(filepath, default):
    """Self-healing JSON loader: otomatis pulih jika file korup atau kosong."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, type(default)) else default
        except Exception as e:
            print(f"[SELF-HEAL] Recovering {filepath} due to read notice: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=1800.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def get_active_gemini_model(api_key):
    """
    LAPIS 1: Mesin Pemindai Versi Model Free Tier Otomatis berbasis Regex tanpa angka versi manual.
    Otomatis mendeteksi model Gemini Flash STABIL generasi tertinggi lintas tahun.
    """
    global _CACHED_MODELS
    if _CACHED_MODELS is not None:
        return _CACHED_MODELS

    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(list_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            scored_models = []

            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])

                if "generateContent" not in methods or "flash" not in name.lower():
                    continue

                if any(bad in name.lower() for bad in [
                    "preview", "exp", "thinking", "image", "tts", "audio", "vision", "8b"
                ]):
                    continue

                ver_match = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name.lower())
                if ver_match:
                    ver_num = float(ver_match.group(1))
                    if name.lower() == f"gemini-{ver_match.group(1)}-flash":
                        tier_score = 2
                    elif name.lower() == f"gemini-{ver_match.group(1)}-flash-lite":
                        tier_score = 1
                    else:
                        tier_score = 0
                    scored_models.append((ver_num, tier_score, name))
                elif name.lower() == "gemini-flash-latest":
                    scored_models.append((0.1, 0, name))

            if scored_models:
                scored_models.sort(key=lambda x: (x[0], x[1]), reverse=True)
                _CACHED_MODELS = [item[2] for item in scored_models[:2]]
                print(f"[GEMINI] Future-proof active models locked: {_CACHED_MODELS}")
                return _CACHED_MODELS
    except Exception as e:
        print(f"[WARN] Dynamic model discovery notice: {e}")

    _CACHED_MODELS = ["gemini-flash-latest"]
    return _CACHED_MODELS


def discover_google_dehu_queries(published_slugs):
    """
    LAPIS 4: 3-Tier Infinite Keyword Supply:
    Tier A: Seed List -> Tier B: Google Suggest US -> Tier C: Combinatorial Sq Ft × Moisture × Barrier Permutator.
    """
    discovered = []
    seeds = [
        "what size dehumidifier for crawl space ",
        "alorair sentinel ",
        "aprilaire dehumidifier ",
        "crawl space vapor barrier calculator "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "what size" in pref or "calculator" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|chart|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        p_m = re.search(r"\b(50|55|65|70|80|90|100|120)\b", cleaned)
                        ppd_v = int(p_m.group(1)) if p_m else 70
                        sqft_v = int(round(ppd_v * 26.0, -2))
                        discovered.append((cleaned.title(), sqft_v, 3.5, ppd_v, int(ppd_v * 2.1), 4.8, "20-Mil String-Reinforced"))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")

    # Tier C Fallback: Combinatorial Permutator (Anti-Habis Lintas Tahun)
    areas = [800, 1100, 1400, 1700, 2100, 2400, 2800, 3200, 3600]
    conditions = [
        ("Encapsulated Sealed Crawl Space (65% RH)", 55, "20-Mil Reinforced Liner"),
        ("Damp Unsealed Dirt Crawl Space (75% RH)", 70, "12-Mil / 20-Mil Conversion"),
        ("Wet Musty Crawl Space / Basement (85% RH)", 90, "20-Mil Heavy Encapsulation")
    ]
    for sq_ft in areas:
        for cond_desc, base_p, mil_s in conditions:
            combo_title = f"{sq_ft:,} Sq Ft {cond_desc}"
            test_slug = slugify(f"{combo_title}-dehumidifier-vapor-barrier-calculator")
            if test_slug not in published_slugs:
                rec_ppd = 55 if sq_ft <= 1300 else (70 if sq_ft <= 2100 else (90 if sq_ft <= 2800 else 120))
                if "85%" in cond_desc and rec_ppd < 90:
                    rec_ppd = min(120, rec_ppd + 20)
                discovered.append((combo_title, sq_ft, 3.5, rec_ppd, int(rec_ppd * 2.1), 5.2, mil_s))
                if len(discovered) >= 25:
                    return discovered
    return discovered


def build_deterministic_dehu_data(dehu_tuple):
    """
    LAPIS 3: Mesin Fisika Psikrometrika AHAM vs DOE & Geometri Encapsulation Vapor Barrier (100% Bebas Gagal).
    """
    model_name, floor_sqft, height_ft, aham_ppd, sat_ppd, amps_120v, barrier_spec = dehu_tuple

    # 1. Konversi Kapasitas AHAM (80°F / 60% RH) vs 2019 DOE Standard (65°F / 60% RH):
    # Standar DOE 2019 menguji pada suhu 65°F (kondisi ruang bawah tanah yang dingin), menghasilkan angka ~30% lebih kecil dari AHAM:
    doe_65f_ppd = int(round(aham_ppd * 0.71))
    cubic_vol_cuft = int(round(floor_sqft * height_ft))

    # 2. Geometri Luas Plastik Vapor Barrier Encapsulation (Sq Ft) & Butyl Seam Tape (Linear Ft):
    # Keliling dinding fondasi (asumsi rasio persegi panjang 1.5:1): Perimeter = 2 * (sqrt(Area*1.5) + sqrt(Area/1.5))
    est_perimeter_ft = int(round(2.0 * (math.sqrt(floor_sqft * 1.5) + math.sqrt(floor_sqft / 1.5))))
    wall_curtain_sqft = int(round(est_perimeter_ft * min(4.0, height_ft)))
    pier_wrap_sqft = int(round((floor_sqft / 150.0) * 16.0))
    # Tambahkan 15% untuk sambungan tumpang-tindih 12 inci (12-inch seam overlap):
    total_barrier_sqft = int(round((floor_sqft + wall_curtain_sqft + pier_wrap_sqft) * 1.15, -1))
    rolls_1000sqft = round(total_barrier_sqft / 1000.0, 1)
    butyl_tape_lin_ft = int(round((total_barrier_sqft / 12.0) + est_perimeter_ft, -1))

    # 3. Konsumsi Daya Listrik (Running Watts @ 120V) & Target Dew Point / RH:
    running_watts = int(round(amps_120v * 115.0))

    return {
        "dehu_name": model_name,
        "barrier_spec": barrier_spec,
        "seo_title": f"{model_name} Pints/Day, Vapor Barrier & Encapsulation Calculator (2026)",
        "meta_description": f"Calculate exact dehumidifier capacity ({aham_ppd} PPD AHAM / {doe_65f_ppd} PPD DOE / {sat_ppd} PPD max), {barrier_spec} vapor barrier area ({total_barrier_sqft:,} sq ft w/ wall & seam overlap), and {butyl_tape_lin_ft} ft butyl tape for {model_name}.",
        "specs": {
            "floor_area_sqft": floor_sqft,
            "ceiling_height_ft": height_ft,
            "volume_cuft": cubic_vol_cuft,
            "aham_80f_pints_day": aham_ppd,
            "doe_65f_pints_day": doe_65f_ppd,
            "saturation_max_pints_day": sat_ppd,
            "perimeter_walls_ft": est_perimeter_ft,
            "total_vapor_barrier_sqft": total_barrier_sqft,
            "rolls_1000sqft_needed": rolls_1000sqft,
            "butyl_tape_linear_ft": butyl_tape_lin_ft,
            "running_amps_120v": amps_120v,
            "running_watts": running_watts,
            "barrier_spec": barrier_spec
        },
        "psychrometric_verdict": f"Conditioning a {floor_sqft:,} sq. ft. space ({cubic_vol_cuft:,} cu. ft. volume at {height_ft:g}' height) to keep wood floor-joist moisture below the 16% mold threshold (48%–52% Relative Humidity) requires {model_name} rated at {aham_ppd} Pints/Day at AHAM ($80^\\circ\\text{{F}}/60\\%\\text{{ RH}}$, equivalent to {doe_65f_ppd} PPD under $65^\\circ\\text{{F}}$ DOE testing and {sat_ppd} PPD at saturation) while drawing {amps_120v}A ({running_watts}W on 120V). For full IRC R408.3 encapsulation using {barrier_spec}, covering the {floor_sqft:,} sq. ft. floor plus {est_perimeter_ft} linear feet of foundation walls, piers, and 15% seam overlaps requires {total_barrier_sqft:,} total sq. ft. of liner (~{rolls_1000sqft}× 1,000-ft² rolls) and {butyl_tape_lin_ft} linear feet of 4-inch waterproof butyl seam tape.",
        "hardware_bundle": [
            {
                "badge": f"{aham_ppd} PPD AHAM Dehumidifier",
                "title": f"{model_name} ({aham_ppd} PPD AHAM / {sat_ppd} PPD Max Commercial Crawl Space Dehumidifier)",
                "price_range": "$469 - $1,399",
                "amazon_query": f"Crawl Space Dehumidifier {aham_ppd} Pint AlorAir Sentinel AprilAire",
                "dh_note": f"Hot-gas low-temperature defrost coils extract {aham_ppd} pints/day down to 36°F without freezing up in winter crawl spaces."
            },
            {
                "badge": f"{total_barrier_sqft:,} ft² {barrier_spec.split()[0]} Liner",
                "title": f"{barrier_spec} String-Scrim Crawl Space Vapor Barrier Roll + 4\" Butyl Tape & Masonry Fasteners",
                "price_range": "$149 - $449",
                "amazon_query": "20 Mil 12 Mil Reinforced Crawl Space Vapor Barrier Roll Butyl Tape",
                "dh_note": f"Blocks 100% of ground-moisture evaporation across {total_barrier_sqft:,} sq. ft. so your dehumidifier cycles 60% less often."
            },
            {
                "badge": "20-Ft Lift Condensate Pump",
                "title": "Automatic High-Lift Condensate Drain Pump (Little Giant VCMA-20ULS) w/ Safety Float Switch & 20ft Hose",
                "price_range": "$58 - $119",
                "amazon_query": "Little Giant VCMA-20ULS Condensate Pump 20ft Drain Tubing Dehumidifier",
                "dh_note": "Pumps collected dehumidifier water up and out of below-grade crawl spaces or into your sump basin automatically."
            },
            {
                "badge": "Vent Covers & Hanging Kit",
                "title": "Insulated Crawl Space Foundation Vent Covers + Ratchet Suspension Hanging Straps & MERV-10 Filters",
                "price_range": "$54 - $159",
                "amazon_query": "Crawl Space Foundation Vent Covers Dehumidifier Hanging Kit MERV Filter",
                "dh_note": "Seals outside humid summer air vents per IRC R408.3 and suspends the dehumidifier off the floor joists to eliminate vibration."
            }
        ],
        "encapsulation_checklist": [
            f"Never calculate Vapor Barrier Square Footage by Floor Area ({floor_sqft:,} sq. ft.) alone: add Perimeter Foundation Wall Height ({est_perimeter_ft} ft × {min(4.0, height_ft):g} ft = +{wall_curtain_sqft} sq. ft.), internal support piers (+{pier_wrap_sqft} sq. ft.), and a 15% overlap for 12-inch taped seams = {total_barrier_sqft:,} total sq. ft. of {barrier_spec}.",
            f"Understand AHAM ($80^\\circ\\text{{F}}/60\\%\\text{{ RH}}$) vs. DOE ($65^\\circ\\text{{F}}/60\\%\\text{{ RH}}$) Pint Ratings: a commercial {aham_ppd}-Pint AHAM unit removes {doe_65f_ppd} Pints at cool $65^\\circ\\text{{F}}$ underground crawl space temperatures and up to {sat_ppd} Pints at $90^\\circ\\text{{F}}/90\\%$ saturation.",
            "Seal all outside foundation air vents with rigid foam/plastic Vent Covers and air-seal the rim joist with closed-cell spray foam before running a commercial dehumidifier—otherwise you are paying to dehumidify the entire outdoors!",
            "Set your crawl space humidistat to 50%–52% Relative Humidity (never 30%–35%): holding 50% RH keeps wood moisture content (EMC) safely at 9%–11% (stopping all fungal rot and dust mites) without over-drying hardwood floors upstairs."
        ],
        "faqs": [
            {
                "q": f"What size dehumidifier do I need for {model_name} ({floor_sqft:,} sq ft)?",
                "a": f"For a {floor_sqft:,} sq. ft. crawl space or basement ({cubic_vol_cuft:,} cu. ft.), ASHRAE and manufacturer charts recommend a commercial dehumidifier rated at {aham_ppd} Pints/Day under AHAM conditions ($80^\\circ\\text{{F}}/60\\%\\text{{ RH}}$), which equals {doe_65f_ppd} Pints/Day under cool $65^\\circ\\text{{F}}$ DOE地下 testing."
            },
            {
                "q": f"How much 12-mil or 20-mil vapor barrier do I need to encapsulate a {floor_sqft:,} sq ft crawl space?",
                "a": f"Covering the {floor_sqft:,} sq. ft. dirt floor, running the liner up {est_perimeter_ft} linear feet of foundation walls (+{wall_curtain_sqft} sq. ft.), wrapping piers (+{pier_wrap_sqft} sq. ft.), and allowing 15% for 12-inch overlaps requires {total_barrier_sqft:,} sq. ft. of {barrier_spec} (~{rolls_1000sqft} rolls of 1,000 sq. ft.) plus {butyl_tape_lin_ft} linear feet of butyl seam tape."
            },
            {
                "q": f"Why do big-box residential dehumidifiers freeze up in a crawl space?",
                "a": f"Crawl spaces and basements stay around 52°F–62°F year-round. Cheap residential dehumidifiers lack hot-gas bypass defrost valves, so their evaporator coils ice over solid below 65°F. Commercial crawl space units ({model_name}) use low-grain refrigerant (LGR) or hot-gas defrost to operate down to 36°F."
            }
        ]
    }


def generate_dehu_data(dehu_tuple):
    """
    LAPIS 2: Memanggil model Gemini stabil dengan proteksi Cooldown HTTP 429 & Fallback Otomatis.
    """
    if not GEMINI_API_KEY:
        return build_deterministic_dehu_data(dehu_tuple)

    model_name, floor_sqft, height_ft, aham_ppd, sat_ppd, amps_120v, barrier_spec = dehu_tuple
    det_fallback = build_deterministic_dehu_data(dehu_tuple)
    sp = det_fallback["specs"]

    prompt = f"""
You are a Certified Indoor Environmentalist (CIE), Building Science Psychrometric Engineer & Crawl Space Encapsulation Specialist (IRC Section R408.3). Create an accurate 2026 commercial crawl space / basement dehumidifier capacity (AHAM vs DOE Pints/Day), 12-mil/20-mil vapor barrier roll geometry, and butyl seam tape guide for: "{model_name}".
Baseline specs: Floor Area={floor_sqft} sq ft ({height_ft}ft height = {sp['volume_cuft']} cu ft), Dehumidifier={aham_ppd} PPD AHAM (80F/60% RH) / {sp['doe_65f_pints_day']} PPD DOE (65F) / {sat_ppd} PPD Max ({amps_120v}A / {sp['running_watts']}W), Total Vapor Barrier w/ Walls, Piers & 15% Overlap={sp['total_vapor_barrier_sqft']} sq ft ({sp['rolls_1000sqft_needed']}x 1000-sqft rolls of {barrier_spec}), Butyl Seam Tape={sp['butyl_tape_linear_ft']} linear ft.
Return ONLY a valid JSON object matching this exact schema:
{{
  "dehu_name": "{model_name}",
  "barrier_spec": "{barrier_spec}",
  "seo_title": "{model_name} Pints/Day, Vapor Barrier & Encapsulation Calculator (2026)",
  "meta_description": "Calculate exact crawl space dehumidifier AHAM and DOE pint capacity, 12-mil/20-mil vapor barrier square footage (with wall and overlap allowance), and butyl tape length for {model_name}.",
  "specs": {{
    "floor_area_sqft": {floor_sqft},
    "ceiling_height_ft": {height_ft},
    "volume_cuft": {sp['volume_cuft']},
    "aham_80f_pints_day": {aham_ppd},
    "doe_65f_pints_day": {sp['doe_65f_pints_day']},
    "saturation_max_pints_day": {sat_ppd},
    "perimeter_walls_ft": {sp['perimeter_walls_ft']},
    "total_vapor_barrier_sqft": {sp['total_vapor_barrier_sqft']},
    "rolls_1000sqft_needed": {sp['rolls_1000sqft_needed']},
    "butyl_tape_linear_ft": {sp['butyl_tape_linear_ft']},
    "running_amps_120v": {amps_120v},
    "running_watts": {sp['running_watts']},
    "barrier_spec": "{barrier_spec}"
  }},
  "psychrometric_verdict": "3-sentence technical summary stating AHAM vs DOE pints/day for {floor_sqft} sq ft, total vapor barrier sq ft including walls/piers/15% overlap, and butyl tape linear feet.",
  "hardware_bundle": [
    {{
      "badge": "{aham_ppd} PPD Commercial Dehu",
      "title": "{model_name} ({aham_ppd} PPD AHAM Commercial Crawl Space Dehumidifier)",
      "price_range": "$469 - $1,399",
      "amazon_query": "Crawl Space Dehumidifier {aham_ppd} Pint AlorAir Sentinel AprilAire",
      "dh_note": "1-sentence hot-gas defrost and 50% RH wood joist protection note"
    }},
    {{
      "badge": "{sp['total_vapor_barrier_sqft']:,} ft² {barrier_spec.split()[0]} Liner",
      "title": "{barrier_spec} String-Scrim Crawl Space Vapor Barrier Roll + Butyl Seam Tape",
      "price_range": "$149 - $449",
      "amazon_query": "20 Mil 12 Mil Reinforced Crawl Space Vapor Barrier Roll Butyl Tape",
      "dh_note": "1-sentence puncture resistance and soil vapor block note"
    }},
    {{
      "badge": "20-Ft Condensate Pump",
      "title": "Automatic High-Lift Condensate Drain Pump (Little Giant VCMA-20ULS) + 20ft Hose",
      "price_range": "$58 - $119",
      "amazon_query": "Little Giant VCMA-20ULS Condensate Pump 20ft Drain Tubing Dehumidifier",
      "dh_note": "1-sentence vertical head lift and overflow safety switch note"
    }},
    {{
      "badge": "Vent Covers & Hanging Kit",
      "title": "Insulated Crawl Space Foundation Vent Covers + Ratchet Hanging Straps & MERV Filters",
      "price_range": "$54 - $159",
      "amazon_query": "Crawl Space Foundation Vent Covers Dehumidifier Hanging Kit",
      "dh_note": "1-sentence IRC R408.3 air-sealing and joist vibration isolation note"
    }}
  ],
  "encapsulation_checklist": [
    "Step 1 regarding vapor barrier formula (Floor + Perimeter Walls + Piers + 15% seam overlap)",
    "Step 2 regarding AHAM (80F) vs DOE (65F) pint ratings and hot-gas defrost coils",
    "Step 3 regarding sealing foundation vents per IRC R408.3 before running the dehumidifier",
    "Step 4 regarding setting target humidity to 50%-52% RH to keep wood EMC under 14%"
  ],
  "faqs": [
    {{"q": "What size dehumidifier do I need for {model_name}?", "a": "Exact AHAM, DOE, and saturation pints/day for {floor_sqft} sq ft."}},
    {{"q": "How many rolls of vapor barrier and butyl tape do I need for {floor_sqft} sq ft?", "a": "Exact floor, wall, pier, and 15% overlap sq ft plus butyl tape linear feet."}},
    {{"q": "Should I use 12-mil or 20-mil vapor barrier for crawl space encapsulation?", "a": "Direct comparison of polyester string-scrim reinforcement, gravel durability, and radon/moisture blocking."}}
  ]
}}
"""

    for model_id in get_active_gemini_model(GEMINI_API_KEY):
        for attempt in range(2):
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=40) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    parsed = json.loads(raw_text)
                    if "specs" in parsed and "hardware_bundle" in parsed:
                        time.sleep(6)
                        return parsed
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    print(f"[RATE-LIMIT] HTTP 429 on {model_id} (attempt {attempt + 1}). Cooling down 20s...")
                    time.sleep(20)
                else:
                    print(f"[WARN] HTTP {he.code} on {model_id} for '{model_name}': {he}")
                    break
            except Exception as e:
                print(f"[WARN] Gemini ({model_id}) notice for '{model_name}': {e}")
                break

    return det_fallback


def build_dehu_html_page(data, slug, mon_cfg):
    dehu_name = data.get("dehu_name", "Crawl Space Dehumidifier & Encapsulation")
    sp = data.get("specs", {})
    fl_sqft = int(safe_float(sp.get("floor_area_sqft", 1800), 1800))
    ht_ft = round(safe_float(sp.get("ceiling_height_ft", 3.5), 3.5), 1)
    aham_p = int(safe_float(sp.get("aham_80f_pints_day", 70), 70))
    doe_p = int(safe_float(sp.get("doe_65f_pints_day", 50), 50))
    sat_p = int(safe_float(sp.get("saturation_max_pints_day", 145), 145))
    bar_sqft = int(safe_float(sp.get("total_vapor_barrier_sqft", 2790), 2790))
    rolls_cnt = round(safe_float(sp.get("rolls_1000sqft_needed", 2.8), 2.8), 1)
    tape_ft = int(safe_float(sp.get("butyl_tape_linear_ft", 410), 410))
    amps = round(safe_float(sp.get("running_amps_120v", 5.0), 5.0), 1)
    bar_s = sp.get("barrier_spec", "20-Mil String-Reinforced")

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Crawl+Space+Dehumidifier+AlorAir+Sentinel+20+Mil+Vapor+Barrier"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{dehu_name} Pint Capacity & Vapor Barrier Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Crawl Space Dehumidifier")), mon_cfg)
        bundle_html += f"""
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-teal-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Encapsulation Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$58+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-slate-400 mt-2 leading-relaxed">💧 {item.get('dh_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Crawl Space Area vs AHAM Pints, DOE Pints, Vapor Barrier Sq Ft & Tape Matrix Table
    dehu_tiers = [
        ("1,000 Sq Ft Crawl Space", "55 PPD AHAM (39 DOE)", "120 PPD Max", "1,650 Sq Ft (1.7 Rolls)", "270 Linear Ft Tape"),
        ("1,500 Sq Ft Crawl Space", "65–70 PPD AHAM (48 DOE)", "135 PPD Max", "2,380 Sq Ft (2.4 Rolls)", "360 Linear Ft Tape"),
        ("2,000 Sq Ft Crawl Space", "70–80 PPD AHAM (55 DOE)", "160 PPD Max", "3,060 Sq Ft (3.1 Rolls)", "440 Linear Ft Tape"),
        ("2,500 Sq Ft Crawl Space", "90 PPD AHAM (64 DOE)", "198 PPD Max", "3,740 Sq Ft (3.8 Rolls)", "520 Linear Ft Tape"),
        ("3,200 Sq Ft Crawl Space", "110–120 PPD AHAM (85 DOE)", "235 PPD Max", "4,680 Sq Ft (4.7 Rolls)", "630 Linear Ft Tape")
    ]
    matrix_rows_html = ""
    for a_lbl, p_lbl, m_lbl, v_lbl, t_lbl in dehu_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/40">
          <td class="py-3 px-4 font-bold text-white">{a_lbl}</td>
          <td class="py-3 px-4 font-bold text-teal-400">{p_lbl}</td>
          <td class="py-3 px-4 text-slate-300">{m_lbl}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{v_lbl}</td>
          <td class="py-3 px-4 text-xs text-slate-300">{t_lbl}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("encapsulation_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-slate-900 border border-slate-800 rounded-xl p-4 cursor-pointer hover:border-slate-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-teal-500 rounded cursor-pointer dh-check">
          <span class="text-sm text-slate-200 leading-relaxed"><strong>IRC R408.3 Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-slate-900 border border-slate-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-slate-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', dehu_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', dehu_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-teal-500 text-slate-950 px-2 py-0.5 rounded font-black">CRAWLSPACE</span>DehuIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Dehumidifiers & 20-Mil Liners →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-teal-500 text-slate-950 px-3 py-1 rounded-full">{aham_p} PPD AHAM ({doe_p} DOE / {sat_p} Max)</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Liner: {bar_sqft:,} ft² ({rolls_cnt} Rolls)</span>
        <span class="text-xs font-semibold bg-slate-800 text-slate-300 px-3 py-1 rounded-full">{fl_sqft:,} Sq Ft | Tape: {tape_ft}' | {amps}A</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', dehu_name)}</h1>
      <div class="mt-4 bg-slate-900 border-l-4 border-teal-500 p-4 rounded-r-xl text-sm text-slate-200 leading-relaxed">
        <strong>ASHRAE Psychrometric & IRC R408.3 Verdict:</strong> {data.get('psychrometric_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE CRAWL SPACE DEHUMIDIFIER PINT & 20-MIL VAPOR BARRIER CALCULATOR -->
    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {dehu_name} Pint & Vapor Barrier Calculator</h2>
      <p class="text-xs text-slate-400 mb-6">Adjust your crawl space or basement floor square footage, foundation wall height, and starting dampness level to compute required AHAM/DOE Pints Per Day, total 12-mil/20-mil vapor barrier area (with walls & 15% seam overlap), and butyl tape footage.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="sqftSlider" class="text-slate-300">Crawl Space or Basement Floor Area (Sq Ft)</label>
              <span class="text-teal-400 font-bold"><span id="sqftVal">{fl_sqft:,}</span> sq ft</span>
            </div>
            <input id="sqftSlider" type="range" min="400" max="4200" step="100" value="{fl_sqft}" class="w-full accent-teal-500 cursor-pointer">
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="wallSelect" class="block text-xs font-medium text-slate-400 mb-1">Foundation Wall Curtain Height</label>
              <select id="wallSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500">
                <option value="2.5">2.5 ft Low Crawl Space Walls</option>
                <option value="3.5" selected>3.5 ft Standard Crawl Space Walls</option>
                <option value="4.5">4.5 ft Tall Crawl Space Walls</option>
                <option value="0.0">Basement Floor Only (No Wall Liner)</option>
              </select>
            </div>
            <div>
              <label for="dampSelect" class="block text-xs font-medium text-slate-400 mb-1">Moisture & Sealing Condition</label>
              <select id="dampSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500">
                <option value="1.00" selected>Sealed w/ 20-Mil Liner (65%–70% RH)</option>
                <option value="1.25">Damp / Partially Sealed (75% RH)</option>
                <option value="1.50">Wet / Musty / Standing Dampness (85% RH)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-slate-950 border border-teal-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-teal-400 font-bold">Required Dehumidifier</span>
            <div class="text-2xl sm:text-3xl font-black text-white mt-1"><span id="ppdOut">{aham_p}</span> <span class="text-xs font-normal text-slate-400">PPD AHAM</span></div>
            <p id="doeNoteOut" class="text-xs text-teal-400 font-semibold mt-1">{doe_p} PPD DOE / {sat_p} Max</p>
          </div>

          <div class="bg-slate-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">20-Mil Liner + Overlap</span>
            <div class="text-2xl sm:text-3xl font-black text-emerald-400 mt-1"><span id="barSqftOut">{bar_sqft:,}</span> <span class="text-xs font-normal text-slate-400">ft²</span></div>
            <p id="tapeNoteOut" class="text-xs text-slate-300 font-semibold mt-1">{rolls_cnt} Rolls | {tape_ft}' Butyl Tape</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-teal-950/40 border border-teal-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="dhAdviceBanner" class="text-sm text-teal-100 font-medium"></div>
        <a id="dynamicDhBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Dehumidifier & 20-Mil Liner on Amazon →
        </a>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {dehu_name} Dehumidifier, 20-Mil Liner & Pump Bundle</h2>
        <span class="text-xs text-slate-400">IRC Section R408.3 & Energy Star Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Crawl Space Square Footage, AHAM vs. DOE Pint Rating & 20-Mil Vapor Barrier Chart</h2>
      <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase text-xs">
              <th class="py-3.5 px-4">Crawl Space Floor Area</th>
              <th class="py-3.5 px-4 text-teal-400">AHAM Rating (80°F/60%)</th>
              <th class="py-3.5 px-4">Saturation Max PPD</th>
              <th class="py-3.5 px-4 text-emerald-400">Total Liner (w/ Walls + 15%)</th>
              <th class="py-3.5 px-4">4" Butyl Seam Tape</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">IRC R408.3 Encapsulation, Vent Sealing & 50% RH Dew-Point Checklist</h2>
        <span id="dhBadge" class="text-xs font-bold bg-slate-800 text-teal-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({dehu_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500 px-4">
    <p>© {datetime.now(timezone.utc).year} CrawlSpaceDehuIndex. Independent Building Science Psychrometrics & Encapsulation Sizing Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const sqftSlider = document.getElementById('sqftSlider');
    const wallSelect = document.getElementById('wallSelect');
    const dampSelect = document.getElementById('dampSelect');
    const sqftVal = document.getElementById('sqftVal');
    const ppdOut = document.getElementById('ppdOut');
    const doeNoteOut = document.getElementById('doeNoteOut');
    const barSqftOut = document.getElementById('barSqftOut');
    const tapeNoteOut = document.getElementById('tapeNoteOut');
    const dhAdviceBanner = document.getElementById('dhAdviceBanner');
    const dynamicDhBtn = document.getElementById('dynamicDhBtn');

    function recalculateDehu() {{
      const sqft = parseInt(sqftSlider.value, 10);
      const wallHt = parseFloat(wallSelect.value);
      const dampMult = parseFloat(dampSelect.value);

      sqftVal.textContent = sqft.toLocaleString();

      const rawPpd = (sqft / 27.0) * dampMult;
      let stdAhamPpd = 55;
      if (rawPpd <= 56) stdAhamPpd = 55;
      else if (rawPpd <= 68) stdAhamPpd = 65;
      else if (rawPpd <= 76) stdAhamPpd = 70;
      else if (rawPpd <= 94) stdAhamPpd = 90;
      else stdAhamPpd = 120;

      const doePpd = Math.round(stdAhamPpd * 0.71);
      const satPpd = Math.round(stdAhamPpd * 2.15);

      const perimFt = Math.round(2.0 * (Math.sqrt(sqft * 1.5) + Math.sqrt(sqft / 1.5)));
      const wallSqft = Math.round(perimFt * wallHt);
      const pierSqft = wallHt > 0 ? Math.round((sqft / 150.0) * 16.0) : 0;
      const totBarrierSqft = Math.ceil(((sqft + wallSqft + pierSqft) * 1.15) / 10) * 10;
      const rollsCount = (totBarrierSqft / 1000.0).toFixed(1);
      const tapeLinFt = Math.ceil(((totBarrierSqft / 12.0) + perimFt) / 10) * 10;

      ppdOut.textContent = stdAhamPpd;
      doeNoteOut.textContent = `${{doePpd}} PPD DOE / ${{satPpd}} Max`;
      barSqftOut.textContent = totBarrierSqft.toLocaleString();
      tapeNoteOut.textContent = `${{rollsCount}} Rolls | ${{tapeLinFt}}' Butyl Tape`;

      dhAdviceBanner.innerHTML = `💧 <strong>IRC R408.3 Spec:</strong> Encapsulating ${{sqft.toLocaleString()}} sq ft requires <strong>${{totBarrierSqft.toLocaleString()}} sq ft of 20-Mil Reinforced Vapor Barrier</strong> (including walls & 15% seam overlaps), <strong>${{tapeLinFt}} ft of Butyl Seam Tape</strong>, and a <strong>${{stdAhamPpd}}-Pint AHAM Commercial Crawl Space Dehumidifier</strong> + Condensate Pump.`;
      dynamicDhBtn.href = `https://${{amzDomain}}/s?k=Crawl+Space+Dehumidifier+${{stdAhamPpd}}+Pint+AlorAir+Sentinel+20+Mil+Vapor+Barrier&tag=${{amzTag}}`;
    }}

    sqftSlider.addEventListener('input', recalculateDehu);
    wallSelect.addEventListener('change', recalculateDehu);
    dampSelect.addEventListener('change', recalculateDehu);
    recalculateDehu();

    const checks = document.querySelectorAll('.dh-check');
    const badge = document.getElementById('dhBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Crawl+Space+Dehumidifier+AlorAir+Sentinel+20+Mil+Vapor+Barrier"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-slate-900 border border-slate-800 hover:border-teal-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-teal-500 text-slate-950 px-2.5 py-0.5 rounded">{item.get('aham_p', 70)} PPD AHAM ({item.get('sqft', 1800):,} ft²)</span>
            <span class="text-xs text-slate-400">Liner: {item.get('bar_sqft', 2790):,} ft²</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-teal-400 transition">{item['dehu_name']}</h2>
          <p class="text-xs text-slate-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-teal-400">Calculate Pints/Day & 20-Mil Liner →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CrawlSpaceDehuIndex — Crawl Space Dehumidifier Pints/Day & 20-Mil Vapor Barrier Calculator (2026)</title>
  <meta name="description" content="Calculate exact crawl space and basement commercial dehumidifier capacity (AHAM vs DOE Pints/Day), 12-mil and 20-mil reinforced vapor barrier roll square footage (with wall and overlap math), and butyl seam tape length for AlorAir, AprilAire, and Santa Fe units.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="CrawlSpaceDehuIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-teal-500 text-slate-950 px-2 py-0.5 rounded font-black">CRAWLSPACE</span>DehuIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Dehumidifiers & 20-Mil Liners →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Crawl Space Dehumidifier Pint & 20-Mil Vapor Barrier Database</h1>
      <p class="text-slate-400 mt-3 text-base sm:text-lg">Select your commercial dehumidifier model or crawl space square footage below to calculate AHAM vs. DOE Pints Per Day, 12-mil/20-mil encapsulation liner rolls (including walls, piers & 15% seam overlaps), and butyl tape footage.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search dehumidifier or crawl space size (e.g. AlorAir Sentinel HD55, HD90, AprilAire E070, Santa Fe, 1500 Sq Ft, 20-Mil Liner...)" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-teal-500">
      </div>
    </div>

    <div id="dhGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>© {datetime.now(timezone.utc).year} CrawlSpaceDehuIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('dhGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CrawlSpaceDehuIndex Crawl Space Dehumidifier & Encapsulation Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Commercial Crawl Space Dehumidifier Pint Capacity & 20-Mil Vapor Barrier Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    """Multi-Endpoint Search Engine Pinger (IndexNow Global + Bing + Google WebSub)."""
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    for idx_endpoint in ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"]:
        try:
            req = urllib.request.Request(
                idx_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"[INDEXNOW] Pushed {len(new_urls)} URLs to {idx_endpoint} (HTTP {resp.status})")
                break
        except Exception as e:
            print(f"[WARN] IndexNow ({idx_endpoint}) notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published if "slug" in item}

    candidates = []
    if CUSTOM_DEHU:
        candidates.append((CUSTOM_DEHU.strip(), 1800, 3.5, 70, 145, 5.0, "20-Mil String-Reinforced"))
    candidates.extend(SEED_DEHUS)
    candidates.extend(discover_google_dehu_queries(published_slugs))

    new_urls = []
    count = 0

    for dehu_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        d_name = dehu_tuple[0]
        slug = slugify(f"{d_name}-dehumidifier-vapor-barrier-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating crawl space dehumidifier & vapor barrier calculator for: {d_name}...")
        try:
            data = generate_dehu_data(dehu_tuple)
            build_dehu_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "dehu_name": data.get("dehu_name", d_name),
                "slug": slug,
                "title": data.get("seo_title", f"{d_name} Dehumidifier Calculator"),
                "description": data.get("meta_description", ""),
                "sqft": int(safe_float(sp.get("floor_area_sqft", dehu_tuple[1]), dehu_tuple[1])),
                "aham_p": int(safe_float(sp.get("aham_80f_pints_day", dehu_tuple[3]), dehu_tuple[3])),
                "bar_sqft": int(safe_float(sp.get("total_vapor_barrier_sqft", 2790), 2790)),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            if count < PAGES_PER_RUN:
                time.sleep(15)
        except Exception as e:
            print(f"[ERROR] Failed building {d_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new crawl space dehumidifier & vapor barrier calculator pages.")


if __name__ == "__main__":
    main()
