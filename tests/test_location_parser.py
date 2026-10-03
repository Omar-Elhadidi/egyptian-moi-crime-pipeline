import json
import sys
from pathlib import Path

# Ensure UTF-8 output for Windows console
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# =============================================================================
# 1. Arabic Text Normalization (Pure string .replace)
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
# 2. Egyptian Governorates (Key -> [Official Name, Keywords...])
# =============================================================================
GOVERNORATES = {
    # Frontier Sinai (checked before generic keywords)
    26: ["شمال سيناء", "العريش", "رفح", "شيخ زويد"],
    27: ["جنوب سيناء", "شرم الشيخ", "طور سيناء", "دهب", "نويبع"],
    23: ["البحر الأحمر", "بحر احمر", "الغردقه", "غردقه", "سفاجا", "قصير"],
    24: ["الوادي الجديد", "وادي جديد", "الخارجه", "الداخله", "فرافره"],
    25: ["مطروح", "مرسي مطروح", "السلوم", "العلمين", "الضبعة"],
    
    # Greater Cairo
    1: ["القاهرة", "قاهره", "شبرا", "حلوان", "مطريه", "عين شمس", "المرج", "المعادي", "التجمع"],
    2: ["الجيزة", "جيزه", "اكتوبر", "زايد", "الهرم", "فيصل", "العجوزه", "الدقي", "بولاق الدكرور", "بدرشين", "الصف"],
    3: ["القليوبية", "قليوبيه", "بنها", "شبرا الخيمه", "القناطر"],
    
    # Alexandria & Delta
    4: ["الإسكندرية", "اسكندريه", "برج العرب", "العامريه", "الرمل", "سيدي جابر", "المنتزه"],
    5: ["البحيرة", "بحيره", "دمنهور", "كفر الدوار", "ايتاي البارود"],
    6: ["كفر الشيخ", "كفرالشيخ", "دسوق", "بلطيم", "فوه"],
    7: ["الغربية", "غربيه", "طنطا", "المحله الكبري", "المحله", "زفتي"],
    8: ["المنوفية", "منوفيه", "شبين الكوم", "اشمون", "قويسنا", "السادات", "منوف"],
    9: ["الدقهلية", "دقهليه", "المنصوره", "منصوره", "ميت غمر", "بلقاس", "دكرنس"],
    10: ["الشرقية", "شرقيه", "الزقازيق", "زقازيق", "العاشر من رمضان", "بلبيس", "فاقوس"],
    11: ["دمياط", "راس البر", "فارسكور"],
    
    # Canal Zone
    12: ["بورسعيد", "بور سعيد"],
    13: ["الإسماعيلية", "اسماعيليه", "فايد", "القنطره"],
    14: ["السويس", "سويس", "العين السخنه"],
    
    # Upper Egypt
    15: ["الفيوم", "فيوم", "طاميه", "سنورس", "اطسا"],
    16: ["بني سويف", "بنسويف", "الواسطي", "ببا", "اهناسيا"],
    17: ["المنيا", "منيا", "ملوي", "مغاغه", "سمالوط", "بني مزار", "ابو قرقاص"],
    18: ["أسيوط", "اسيوط", "ديروط", "القوصيه", "ابنوب", "منفلوط"],
    19: ["سوهاج", "طهطا", "جرجا", "اخميم", "المراغه"],
    20: ["قنا", "نجع حمادي", "دشنا", "ابو تشت", "فرشوط", "قفط"],
    21: ["الأقصر", "اقصر", "اسنا", "ارمنت"],
    22: ["أسوان", "اسوان", "كوم امبو", "ادفو", "النوبه"],
}


def extract_location(title, full_details):
    """
    Scans title first, then body text using simple 'in' checks on normalized keywords.
    Returns (location_id, governorate_name).
    """
    norm_title = normalize_arabic(title)
    norm_body = normalize_arabic(full_details)
    
    # 1. Search in title first (strongest signal)
    for loc_id, keywords in GOVERNORATES.items():
        gov_name = keywords[0]
        for kw in keywords:
            if normalize_arabic(kw) in norm_title:
                return loc_id, gov_name

    # 2. Search in body text
    for loc_id, keywords in GOVERNORATES.items():
        gov_name = keywords[0]
        for kw in keywords:
            if normalize_arabic(kw) in norm_body:
                return loc_id, gov_name

    return 0, "غير محدد"


if __name__ == "__main__":
    bronze_path = Path(__file__).parent / "bronze_crime_news.json"
    if not bronze_path.exists():
        bronze_path = Path(__file__).parent.parent / "bronze_crime_news.json"
    if not bronze_path.exists():
        print(f"Error: {bronze_path} not found.")
        sys.exit(1)

    with open(bronze_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print("=" * 70)
    print(f"🧪 TESTING LOCATION EXTRACTOR ON FIRST 10 ARTICLES")
    print("=" * 70)

    for i, art in enumerate(articles[:10], 1):
        loc_id, gov = extract_location(art["title"], art["full_details"])
        print(f"[{i:2d}] ID: {loc_id:2d} -> {gov:<15} | Title: {art['title'][:55]}...")
