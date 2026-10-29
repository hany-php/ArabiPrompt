# ollama_engine.py
import os
import subprocess
import time
import shutil
import urllib.request
import json
import ollama

# إجبار عميل مكتبة أولاما على الاتصال بالعنوان الرقمي الصريح
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"

def sync_windows_env():
    """مزامنة متغيرات بيئة أولاما من سجل ويندوز لضمان قراءة إعدادات المستخدم الرسمية بدون أي مسار ثابت"""
    if os.name != "nt":
        return
    try:
        import winreg
        for root, subkey in [
            (winreg.HKEY_CURRENT_USER, "Environment"),
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
        ]:
            try:
                with winreg.OpenKey(root, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(key, i)
                            if name.upper().startswith("OLLAMA_") and (name not in os.environ or not os.environ[name]):
                                os.environ[name] = str(val)
                            i += 1
                        except OSError:
                            break
            except Exception:
                pass
    except Exception:
        pass

# مزامنة المتغيرات فور استيراد الملف
sync_windows_env()

def get_ollama_executable():
    """الحصول على المسار الدقيق لأمر أو تطبيق ollama في ويندوز"""
    # 1. البحث في PATH
    path_which = shutil.which("ollama")
    if path_which:
        return path_which

    # 2. البحث في مسار التثبيت الافتراضي لبرنامج أولاما
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    default_exe = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
    if os.path.exists(default_exe):
        return default_exe

    default_app = os.path.join(local_app_data, "Programs", "Ollama", "ollama app.exe")
    if os.path.exists(default_app):
        return default_app

    return "ollama"

def is_ollama_server_responsive():
    """فحص قاطع ومباشر إذا كان سيرفر Ollama يستجيب على المنفذ الرقمي الصريح"""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                return True
    except Exception:
        return False
    return False

def start_ollama_server():
    """تشغيل سيرفر Ollama والانتظار حتى يستجيب بنجاح"""
    sync_windows_env()
    if is_ollama_server_responsive():
        return {"status": "running", "message": "✅ سيرفر Ollama يعمل بالفعل ومتصل."}

    ollama_cmd = get_ollama_executable()
    try:
        creation_flags = 0x08000000 | 0x00000200 if os.name == "nt" else 0
        subprocess.Popen(
            [ollama_cmd, "serve"],
            creationflags=creation_flags,
            env=os.environ.copy(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=(True if not os.path.isabs(ollama_cmd) else False)
        )
        
        # مراقبة الإقلاع لمدة تصل إلى 8 ثوانٍ
        for _ in range(8):
            time.sleep(1.0)
            if is_ollama_server_responsive():
                return {"status": "started", "message": "🔄 تم تشغيل سيرفر Ollama بنجاح والاتصال به!"}

        return {"status": "timeout", "message": "⚠️ تم إطلاق أمر التشغيل، ولكن السيرفر استغرق وقتاً طويلاً للاستجابة."}
    except Exception as e:
        return {"status": "error", "message": f"❌ تعذر تشغيل سيرفر Ollama تلقائياً: {str(e)}"}

def manage_backend_service():
    """التحقق من عمل سيرفر Ollama وتشغيله في الخلفية إن كان متوقفاً"""
    sync_windows_env()
    if is_ollama_server_responsive():
        return {"status": "running", "message": "✅ سيرفر Ollama متصل وجاهز للعمل."}
    return start_ollama_server()

def get_all_local_models():
    """جلب قائمة بجميع الموديلات المثبتة من سيرفر Ollama مباشرة وبدون أي مسارات مجلدات"""
    models_found = []

    # 1. الاستعلام عبر REST API المباشر لسيرفر أولاما
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name") or m.get("model")
                if name and str(name).strip():
                    clean_name = str(name).strip()
                    if clean_name not in models_found:
                        models_found.append(clean_name)
        if models_found:
            return models_found
    except Exception:
        pass

    # 2. الاستعلام عبر عميل حزمة ollama الرسمية
    try:
        client = ollama.Client(host="http://127.0.0.1:11434")
        res = client.list()
        raw_list = getattr(res, "models", None)
        if raw_list is None and isinstance(res, dict):
            raw_list = res.get("models", [])
            
        for item in (raw_list or []):
            name = None
            if hasattr(item, "model") and item.model:
                name = item.model
            elif isinstance(item, dict):
                name = item.get("model") or item.get("name")
            elif hasattr(item, "get"):
                name = item.get("model") or item.get("name")
                
            if name and str(name).strip():
                clean_name = str(name).strip()
                if clean_name not in models_found:
                    models_found.append(clean_name)
        if models_found:
            return models_found
    except Exception:
        pass

    # 3. الاستعلام عبر أمر النظام القياسي ollama list
    try:
        ollama_cmd = get_ollama_executable()
        cmd_res = subprocess.run([ollama_cmd, "list"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if cmd_res.returncode == 0 and cmd_res.stdout:
            lines = cmd_res.stdout.strip().split("\n")
            for line in lines[1:]:  # تخطي سطر الترويسة NAME ID SIZE MODIFIED
                parts = line.split()
                if parts:
                    clean_name = parts[0].strip()
                    if clean_name and clean_name not in models_found:
                        models_found.append(clean_name)
    except Exception:
        pass

    return models_found

def check_local_model_exists(model_name):
    """التحقق مما إذا كان موديل معين محملاً وجاهزاً في Ollama"""
    if not model_name:
        return False
    try:
        models = get_all_local_models()
        target = model_name.strip().lower()
        for m in models:
            m_lower = m.lower()
            if target == m_lower or target in m_lower or m_lower in target:
                return True
        return False
    except Exception:
        return False

def run_prompt_expansion(arabic_text, task_type, model_name):
    """الـ System Prompt الاحترافي لترجمة وتوسيع وهندسة البرومبت محلياً"""
    system_prompt = (
        "You are an expert Prompt Engineer and Prompt Expansion specialist.\n"
        "Your task is to take an Arabic text input, translate its core meaning into English, "
        "and expand it into a highly professional, detailed, and optimized prompt based on the user's target goal.\n\n"
        "Follow these strict formatting rules:\n"
        "1. Output ONLY the final expanded English prompt inside a single markdown code block (```). "
        "Do not include any introductions, explanations, or conversational filler.\n"
        f"2. Optimize the output specifically for the task type: '{task_type}'.\n\n"
        "Task-Specific Optimization Rules:\n"
        "- If 'Text/General': Create a detailed structured prompt specifying tone, target audience, format, and constraints.\n"
        "- If 'Image Generation': Use descriptive, sensory words, cinematic lighting terms, aspect ratios, artistic style (e.g., photorealistic, 3D render), and camera specs.\n"
        "- If 'Code/Programming': Specify language, clean code standards, error handling, comments, and efficiency requirements."
    )

    user_payload = f"Target Task: {task_type}\nArabic Input: {arabic_text}"
    try:
        client = ollama.Client(host="http://127.0.0.1:11434")
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload}
            ],
            options={"temperature": 0.6}
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ فشل الاتصال بالموديل المحلي لتوليد النص: {str(e)}"
