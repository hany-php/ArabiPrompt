# ollama_scraper.py
import psutil
import requests
import re
from bs4 import BeautifulSoup

def get_available_ram():
    """جلب الذاكرة الحرة المتاحة حالياً بالجهاز بالجيجابايت"""
    return round(psutil.virtual_memory().available / (1024**3), 2)

def scrape_ollama_tags(model_name):
    """الاتصال بموقع أولاما وجلب الموديولات المناسبة للجهاز فقط (أخف - مظبوط - أعلى بقليل)"""
    base_url = "https://ollama.com"
    endpoint = f"/library/{model_name}/tags"
    full_url = base_url + endpoint
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    current_free_ram = get_available_ram()
    ram_budget = current_free_ram - 1.5  # حد الأمان الأساسي لويندوز
    
    try:
        response = requests.get(full_url, headers=headers, timeout=12)
        if response.status_code == 404:
            return {"status": "error", "message": f"❌ لم يتم العثور على موديول باسم '{model_name}' في مستودع Ollama."}
        elif response.status_code != 200:
            return {"status": "error", "message": "❌ فشل الاتصال بموقع أولاما. يرجى التحقق من اتصال الإنترنت."}

        soup = BeautifulSoup(response.text, 'html.parser')
        tags_dict = {}

        # التحليل النصي الشامل للـ Tags
        clean_html_text = soup.get_text()
        pattern = r"([\w\.\-\:]+)\s+([\d\.]+)\s*(GB|MB)"
        matches = re.findall(pattern, clean_html_text, re.IGNORECASE)
        
        for tag_name, size_val, size_unit in matches:
            if ":" in tag_name and model_name in tag_name:
                try:
                    size_gb = float(size_val) if size_unit.upper() == 'GB' else float(size_val) / 1024
                    tags_dict[tag_name] = size_gb
                except:
                    pass

        # محاولة احتياطية في حالة تغير بنية الصفحة
        if len(tags_dict) <= 1:
            for element in soup.find_all('div'):
                tag_span = element.find('span', class_=lambda c: c and 'font-mono' in c)
                if tag_span and ':' in tag_span.text:
                    tag_text = tag_span.text.strip()
                    parent = element.find_parent('div')
                    size_text = ""
                    if parent:
                        for s in parent.find_all('span'):
                            if 'GB' in s.text or 'MB' in s.text:
                                size_text = s.text.strip()
                                break
                    if tag_text and size_text:
                        try:
                            size_gb = float(size_text.replace('MB', '').strip()) / 1024 if 'MB' in size_text else float(size_text.replace('GB', '').strip())
                            tags_dict[tag_text] = size_gb
                        except:
                            continue

        if not tags_dict:
            return {"status": "error", "message": "❌ تعذر استخراج نسخ الموديول من صفحة الموقع."}

        # فلترة صارمة: استبعاد نسخ الـ Base ونسخ الضغط الرديئة q2
        eligible_tags = {}
        for k, v in tags_dict.items():
            if "-base" in k:
                continue
            if any(weak_quant in k for weak_quant in ["-q2", "-q3_K_S"]):
                continue
            eligible_tags[k] = v

        if not eligible_tags:
            eligible_tags = tags_dict

        # ترتيب كل النسخ المتاحة تصاعدياً حسب الحجم
        all_sorted = sorted(eligible_tags.items(), key=lambda x: x[1])

        # تصفية الموديولات: نأخذ فقط ما يقع في حدود راماتك الحرة أو أعلى منها بـ 3 جيجا كحد أقصى (منع النماذج الضخمة غير القابلة للتشغيل)
        functional_tags = [item for item in all_sorted if item[1] <= (current_free_ram + 3.0)]

        # تقسيم الموديولات العملية المتاحة إلى مجموعتين: أقل من الميزانية، وأعلى منها بقليل
        lower_than_ram = [item for item in functional_tags if item[1] <= ram_budget]
        higher_than_ram = [item for item in functional_tags if item[1] > ram_budget]

        # 1. تحديد الموديول "المظبوط والنموذجي" (أكبر وأفضل نسخة مدربة تتسع داخل الرام الحرة بأمان)
        best_tag = ""
        best_size = 0.0
        if lower_than_ram:
            instruct_only = [item for item in lower_than_ram if "instruct" in item[0]]
            if instruct_only:
                best_tag, best_size = instruct_only[-1]
            else:
                best_tag, best_size = lower_than_ram[-1]
        else:
            best_tag, best_size = functional_tags[0] if functional_tags else ("غير متوفر", 0.0)

        # 2. جلب الخيارات الأخف والأسرع (نسخ حجمها أصغر من المظبوط)
        lower_picks = [item for item in lower_than_ram if item[0] != best_tag]
        # نأخذ آخر نسختين خفيفتين لتنويع مستويات السرعة
        lower_picks = lower_picks[-2:] if len(lower_picks) >= 2 else lower_picks

        # 3. جلب خيارات أعلى حاجة بسيطة (تمنحك جودة أعلى لكنها ستكون أثقل)
        # نأخذ أول نسختين أكبر من الرام بفرق بسيط فقط ونمنع الباقي الكبير
        higher_picks = higher_than_ram[:2] if len(higher_than_ram) >= 2 else higher_than_ram

        # بناء القائمة النهائية الذكية والتنظيم الفئوي
        final_list = []
        
        # إضافة النسخ الأخف والأسرع
        for tag, size in lower_picks:
            final_list.append({"tag": tag, "size": size, "category": "أخف وأسرع (دقة متوسطة)", "is_best": False})
            
        # إضافة النسخة المظبوطة النموذجية
        if best_tag != "غير متوفر":
            final_list.append({"tag": best_tag, "size": best_size, "category": "المظبوط والمثالي لجهازك حالياً", "is_best": True})
        
        # إضافة النسخ الأعلى حاجة بسيطة
        for tag, size in higher_picks:
            final_list.append({"tag": tag, "size": size, "category": "أعلى جودة لغوية (ولكن سيعمل ببطء)", "is_best": False})

        return {
            "status": "success",
            "best_tag": best_tag,
            "top_5": final_list,
            "free_ram": current_free_ram
        }

    except Exception as e:
        return {"status": "error", "message": f"❌ حدث خطأ أثناء فحص الموديول: {str(e)}"}
