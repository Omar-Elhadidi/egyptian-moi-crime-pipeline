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
# 2. Egyptian Crime Taxonomy (Key -> [Category Name, Keywords...])
# Matches schema.sql dim_crime_type IDs EXACTLY.
# =============================================================================
CRIME_TAXONOMY = {
    # 8: غسيل أموال وكسب غير مشروع
    8: [
        "غسيل أموال وكسب غير مشروع",
        "غسيل اموال", "غسل اموال", "كسب غير مشروع", "اخفاء مصدرها", "اصباغها بالصبغه الشرعيه"
    ],
    
    # 7: جرائم إلكترونية وابتزاز
    7: [
        "جرائم إلكترونية وابتزاز",
        "جرائم تقنيه المعلومات", "صفحه بمواقع التواصل", "ابتزاز الكتروني", "ابتزاز", "فيس بوك", "تيك توك"
    ],
    
    # 2: تجارة المواد المخدرة
    2: [
        "تجارة المواد المخدرة",
        "مخدر", "حشيش", "هيروين", "شابو", "ايس", "كبتاجون", "بانجو", "اقراص مخدره",
        "ترامادول", "استروكس", "هيدرو", "مخدرات"
    ],
    
    # 1: بلطجة وفرض سيطرة
    1: [
        "بلطجة وفرض سيطرة",
        "بلطجه", "فرض سيطره", "اتاوات", "بؤره اجراميه شديده الخطوره", "ترويع المواطنين"
    ],
    
    # 6: نصب واحتيال وتوظيف أموال
    6: [
        "نصب واحتيال وتوظيف أموال",
        "توظيف اموال", "نصب", "احتيال", "استيلاء علي اموال", "شهادات مقلده",
        "نقد اجنبي", "عملات اجنبيه", "تجاره عمله"
    ],
    
    # 9: شروع في قتل وقتل عمد
    9: [
        "شروع في قتل وقتل عمد",
        "قتل عمد", "شروع في قتل", "انهاء حياه", "اودت بحياته", "لقي مصرعه في مشاجره"
    ],
    
    # 4: سرقة بالإكراه وتشكيل عصابي
    4: [
        "سرقة بالإكراه وتشكيل عصابي",
        "سرقه بالاكراه", "تشكيل عصابي", "سطو مسلح"
    ],
    
    # 3: حيازة أسلحة نارية وذخائر
    3: [
        "حيازة أسلحة نارية وذخائر",
        "سلاح ناري", "اسلحه ناريه", "اعيره ناريه", "اطلاق اعيره", "اطلاق نار",
        "بنادق", "طبنجه", "فرد خرطوش", "ذخيره", "طلقات"
    ],
    
    # 5: سرقة مساكن ومتاجر
    5: [
        "سرقة مساكن ومتاجر",
        "سرقه مساكن", "سرقه متاجر", "سرقه سيارات", "سرقه دراجات", "نشل", "سرقه"
    ],
    
    # 10: تهريب وجرائم جمركية
    10: [
        "تهريب وجرائم جمركية",
        "تهريب", "جمارك", "بضائع مهربه", "ميناء", "هجره غير شرعيه"
    ],
    
    # 11: تعديات على الأراضي ومباني مخالفة
    11: [
        "تعديات على الأراضي ومباني مخالفة",
        "تعديات", "مباني مخالفه", "تبوير", "اراضي زراعيه", "ازاله تعديات"
    ],
    
    # 12: مخالفات تموينية واحتكار سلع
    12: [
        "مخالفات تموينية واحتكار سلع",
        "تموين", "احتكار", "سلع تموينيه", "اسطوانات بوتاجاز", "سوق سوداء", "دقيق مدعم"
    ]
}


def classify_crime(title, full_details):
    """
    Classifies an incident into one of the 12 dim_crime_type categories.
    Returns (crime_type_id, category_name).
    """
    norm_title = normalize_arabic(title)
    norm_body = normalize_arabic(full_details)
    
    # 1. Search in title first
    for crime_id, keywords in CRIME_TAXONOMY.items():
        cat_name = keywords[0]
        for kw in keywords[1:]:
            if normalize_arabic(kw) in norm_title:
                return crime_id, cat_name

    # 2. Search in body text
    for crime_id, keywords in CRIME_TAXONOMY.items():
        cat_name = keywords[0]
        for kw in keywords[1:]:
            if normalize_arabic(kw) in norm_body:
                return crime_id, cat_name

    return 0, "أخرى / غير مصنف"


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
    print(f"🧪 TESTING CRIME CLASSIFIER ON FIRST 10 ARTICLES")
    print("=" * 80)

    for i, art in enumerate(articles[:10], 1):
        crime_id, cat_name = classify_crime(art["title"], art["full_details"])
        print(f"[{i:2d}] ID: {crime_id:2d} -> {cat_name:<30} | Title: {art['title'][:45]}...")
