import json
import re
import sys
from pathlib import Path

# Ensure UTF-8 output for Windows console
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# =============================================================================
# 1. Arabic Text Normalization
# =============================================================================
def normalize_arabic(text):
    if not text:
        return ""
    text = text.replace("إ", "ا").replace("أ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    for diacritic in ["َ", "ً", "ُ", "ٌ", "ِ", "ٍ", "ْ", "ّ"]:
        text = text.replace(diacritic, "")
    return text.lower()


# =============================================================================
# 2. Date Key Transformer
# =============================================================================
def extract_date_id(date_str):
    if not date_str:
        return 0
    try:
        clean_date = str(date_str)[:10].replace("-", "")
        return int(clean_date)
    except (ValueError, TypeError):
        return 0


# =============================================================================
# 3. Metrics & Flag Extractor (With Omar's normalization fix for campaigns)
# =============================================================================
def extract_metrics(title, full_details):
    # Normalized combined text so حملة matches حمله
    combined_text = normalize_arabic(f"{title} {full_details}")
    
    # --- A. Campaign Flag (is_campaign) ---
    campaign_keywords = ["حمله", "حملات", "مكبره", "موسعه", "انضباطيه"]
    is_campaign = any(kw in combined_text for kw in campaign_keywords)

    # --- B. Suspects Count (suspects_count) ---
    suspects_count = 1  # Default: 1 suspect per incident
    
    num_match = re.search(r"(?:ضبط|تضم|تشكيل|مصرع|اصابه)\s*\(?\s*(\d+)\s*(?:عناصر|اشخاص|متهمين|عاطلين|عنصر|شخص)", combined_text)
    if num_match:
        val = int(num_match.group(1))
        if 1 <= val <= 100:
            suspects_count = val
    elif any(dual in combined_text for dual in ["شخصين", "عنصرين", "متهمين اثنين"]):
        suspects_count = 2

    # --- C. Weapons Count (weapons_count) ---
    weapons_count = 0
    weapon_keywords = ["سلاح ناري", "اسلحه ناريه", "بندقيه", "بنادق", "طبنجه", "فرد خرطوش", "رشاش"]
    
    has_weapons = any(w in combined_text for w in weapon_keywords)
    if has_weapons:
        weapons_count = 1
        w_match = re.search(r"\(?\s*(\d+)\s*(?:بنادق|بندقيه|طبنجه|طبنجات|سلاح|اسلحه|فرد)", combined_text)
        if w_match:
            w_val = int(w_match.group(1))
            if 1 <= w_val <= 100:
                weapons_count = w_val

    return {
        "suspects_count": suspects_count,
        "weapons_count": weapons_count,
        "is_campaign": is_campaign
    }


if __name__ == "__main__":
    bronze_path = Path(__file__).parent / "bronze_crime_news.json"
    if not bronze_path.exists():
        bronze_path = Path(__file__).parent.parent / "bronze_crime_news.json"
    if not bronze_path.exists():
        print(f"Error: {bronze_path} not found.")
        sys.exit(1)

    with open(bronze_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print("=" * 80)
    print(f"🧪 TESTING DATE & METRICS EXTRACTOR ON FIRST 10 ARTICLES")
    print("=" * 80)

    for i, art in enumerate(articles[:10], 1):
        date_id = extract_date_id(art.get("date_published"))
        metrics = extract_metrics(art.get("title", ""), art.get("full_details", ""))
        
        print(f"\n[{i:2d}] Date Key: {date_id}")
        print(f"     Metrics : Suspects={metrics['suspects_count']} | Weapons={metrics['weapons_count']} | Campaign={metrics['is_campaign']}")
        print(f"     Title   : {art['title'][:65]}...")
