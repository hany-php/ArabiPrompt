# gui_actions.py
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import ollama_scraper
import ollama_engine
import prompt_db

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GuiActions:
    def __init__(self, ui_components):
        self.ui = ui_components
        self.selected_prompt_id = None
        self.favorites_only_mode = False

    # =========================================================================
    # 🔌 إدارة الاتصال بسيرفر Ollama وتشغيله
    # =========================================================================
    def verify_and_start_backend(self):
        """التحقق التلقائي الذكي من السيرفر عند الإقلاع في خيط منفصل لمنع تجميد الواجهة"""
        threading.Thread(target=self._async_backend_check, daemon=True).start()

    def _async_backend_check(self):
        is_up = ollama_engine.is_ollama_server_responsive()
        if not is_up:
            self.ui["root"].after(0, lambda: self._update_server_ui(False, "جاري إطلاق وتشغيل سيرفر Ollama تلقائياً..."))
            start_res = ollama_engine.start_ollama_server()
            is_up = (start_res.get("status") in ["running", "started"])

        self.ui["root"].after(0, lambda: self._finish_server_init(is_up))

    def _update_server_ui(self, is_online, message=""):
        if is_online:
            self.ui["lbl_server_badge"].config(text="🟢 السيرفر يعمل", fg="#2a9d8f", bg="#f0fdfa")
            self.ui["btn_toggle_server"].config(text="🔄 فحص الاتصال", bg="#457b9d", state="normal")
        else:
            self.ui["lbl_server_badge"].config(text="🔴 السيرفر مغلق", fg="#d90429", bg="#fdf0f0")
            self.ui["btn_toggle_server"].config(text="⚡ تشغيل السيرفر", bg="#e63946", state="normal")
        
        if message:
            self.ui["lbl_model_status"].config(text=message, fg="#1d3557" if is_online else "#d90429")

    def _finish_server_init(self, is_online):
        self._update_server_ui(is_online)
        if is_online:
            self.refresh_local_models_dropdown()
        else:
            self.ui["combo_local_models"].config(values=["❌ السيرفر مغلق"], state="disabled")
            self.ui["combo_local_models"].set("❌ السيرفر مغلق")
            self.ui["lbl_active_model"].config(text="لا يوجد")
            self.ui["lbl_model_status"].config(text="⚠️ سيرفر Ollama متوقف حالياً. اضغط على زر 'تشغيل السيرفر' لبدء تشغيله فوراً ⚡", fg="#d90429")

    def handle_server_action(self):
        """التعامل مع زر تشغيل/فحص السيرفر في الشريط العلوي"""
        self.ui["btn_toggle_server"].config(state="disabled", text="⏳ جاري المعالجة...")
        threading.Thread(target=self._async_server_action, daemon=True).start()

    def _async_server_action(self):
        if ollama_engine.is_ollama_server_responsive():
            self.ui["root"].after(0, lambda: self._finish_server_init(True))
            self.ui["root"].after(0, lambda: messagebox.showinfo("حالة السيرفر", "سيرفر Ollama متصل وجاهز للعمل بكفاءة! ✅"))
        else:
            res = ollama_engine.start_ollama_server()
            is_up = (res.get("status") in ["running", "started"])
            self.ui["root"].after(0, lambda: self._finish_server_init(is_up))
            if is_up:
                self.ui["root"].after(0, lambda: messagebox.showinfo("نجاح التشغيل", "تم تشغيل سيرفر Ollama بنجاح والاتصال به! 🚀"))
            else:
                self.ui["root"].after(0, lambda: messagebox.showerror("تعذر التشغيل", res.get("message", "فشل تشغيل سيرفر أولاما.")))

    # =========================================================================
    # 📋 قائمة الموديلات المحلية
    # =========================================================================
    def refresh_local_models_dropdown(self):
        """تحديث قائمة الموديلات المثبتة من سيرفر Ollama"""
        local_models = ollama_engine.get_all_local_models()
        if local_models:
            self.ui["combo_local_models"].config(values=local_models, state="readonly")
            self.ui["combo_local_models"].current(0)
            self.set_active_model(local_models[0])
            self.ui["lbl_server_badge"].config(text="🟢 السيرفر يعمل", fg="#2a9d8f", bg="#f0fdfa")
        else:
            self.ui["combo_local_models"].config(values=["❌ لا توجد موديلات محملة محلياً"], state="disabled")
            self.ui["combo_local_models"].set("❌ لا توجد موديلات محملة محلياً")
            self.ui["lbl_active_model"].config(text="لا يوجد")
            lbl_text = "لا توجد موديلات مثبتة بالسيرفر، يمكنك جلب موديول ونسخ أمره من التبويب الثالث 📥"
            self.ui["lbl_model_status"].config(text=lbl_text, fg="#d90429")

    def on_dropdown_model_selected(self, event):
        selected_model = self.ui["combo_local_models"].get()
        if selected_model and "لا توجد" not in selected_model and "مغلق" not in selected_model:
            self.set_active_model(selected_model)

    def set_active_model(self, tag_name):
        if not tag_name:
            return
        self.ui["lbl_active_model"].config(text=tag_name)
        if ollama_engine.check_local_model_exists(tag_name):
            self.ui["lbl_model_status"].config(text=f"الموديل '{tag_name}' مثبت ومستعد للتوليد فوراً ⚡", fg="#2a9d8f")
        else:
            self.ui["lbl_model_status"].config(text=f"غير محمل محلياً، شغّل الأمر لتنزيله أولاً: ollama pull {tag_name} 📥", fg="#d90429")

    # =========================================================================
    # ✍️ معالجة إدخال النص العربي (حل مشكلة الحروف المقطعة)
    # =========================================================================
    def on_arabic_focus_in(self, event):
        txt = self.ui["txt_arabic_input"]
        current = txt.get("1.0", tk.END).strip()
        if current == "اكتب فكرتك هنا باللغة العربية...":
            txt.delete("1.0", tk.END)
            txt.config(fg="#1d3557")
            txt.tag_add("rtl", "1.0", "end")

    def on_arabic_focus_out(self, event):
        txt = self.ui["txt_arabic_input"]
        current = txt.get("1.0", tk.END).strip()
        if not current:
            txt.delete("1.0", tk.END)
            txt.insert("1.0", "اكتب فكرتك هنا باللغة العربية...", "rtl")
            txt.config(fg="#888888")
        else:
            txt.tag_add("rtl", "1.0", "end")

    # =========================================================================
    # 🚀 توليد وتوسيع البرومبت
    # =========================================================================
    def trigger_generation(self):
        active_model = self.ui["lbl_active_model"].cget("text")
        arabic_text = self.ui["txt_arabic_input"].get("1.0", tk.END).strip()
        task_type = self.ui["combo_task"].get()

        if not active_model or "..." in active_model or "لا يوجد" in active_model:
            messagebox.showwarning("تنبيه", "الرجاء اختيار موديل مثبت من القائمة بالأعلى أو تشغيل سيرفر أولاما.")
            return

        if not ollama_engine.check_local_model_exists(active_model):
            pull_cmd = f"ollama pull {active_model}"
            resp = messagebox.askyesno(
                "الموديل غير محمل محلياً",
                f"الموديل المعتمد '{active_model}' غير محمل على جهازك حالياً.\n\n"
                f"هل تريد نسخ أمر التحميل إلى الحافظة لتنزيله في موجه الأوامر (CMD)؟\n\n{pull_cmd}"
            )
            if resp:
                self.copy_cmd(pull_cmd)
            return

        if not arabic_text or arabic_text == "اكتب فكرتك هنا باللغة العربية...":
            messagebox.showwarning("تنبيه", "الرجاء كتابة الفكرة باللغة العربية أولاً ليتم ترجمتها وتوسيعها.")
            return

        self.ui["btn_generate"].config(state="disabled", text="🔄 جاري التوسيع والترجمة محلياً عبر Ollama...")
        self.ui["txt_english_output"].delete("1.0", tk.END)
        self.ui["txt_english_output"].insert(tk.END, "⏳ يقوم الموديل المعتمد بالمعالجة وصياغة البرومبت الآن...")

        threading.Thread(target=self.process_generation, args=(arabic_text, task_type, active_model), daemon=True).start()

    def process_generation(self, text, task, model):
        output_result = ollama_engine.run_prompt_expansion(text, task, model)
        self.ui["root"].after(0, lambda: self.display_output(output_result))

    def display_output(self, result_text):
        txt = self.ui["txt_english_output"]
        txt.delete("1.0", tk.END)
        txt.insert(tk.END, result_text)
        self.ui["btn_generate"].config(state="normal", text="🚀 توليد وتوسيع البرومبت الإحترافي محلياً")

    def copy_to_clipboard(self):
        final_prompt = self.ui["txt_english_output"].get("1.0", tk.END).strip()
        if final_prompt and "يقوم الموديل" not in final_prompt:
            self.ui["root"].clipboard_clear()
            self.ui["root"].clipboard_append(final_prompt)
            messagebox.showinfo("نجاح النسخ", "تم نسخ البرومبت الإنجليزي النهائي للحافظة بنجاح! 📋")
        else:
            messagebox.showwarning("تنبيه", "لا يوجد برومبت متاح لنسخه حالياً.")

    # =========================================================================
    # 💾 نافذة حفظ البرومبت في قاعدة البيانات
    # =========================================================================
    def open_save_dialog(self):
        final_prompt = self.ui["txt_english_output"].get("1.0", tk.END).strip()
        arabic_text = self.ui["txt_arabic_input"].get("1.0", tk.END).strip()
        if arabic_text == "اكتب فكرتك هنا باللغة العربية...":
            arabic_text = ""
        task_type = self.ui["combo_task"].get()
        active_model = self.ui["lbl_active_model"].cget("text")

        if not final_prompt or "يقوم الموديل" in final_prompt:
            messagebox.showwarning("تنبيه", "يرجى توليد برومبت أولاً قبل محاولة حفظه في المكتبة.")
            return

        # توليد عنوان مقترح تلقائياً
        suggested_title = " ".join(arabic_text.split()[:5]) if arabic_text else f"برومبت {task_type}"

        # إنشاء نافذة الحفظ المنبثقة
        dialog = tk.Toplevel(self.ui["root"])
        dialog.title("💾 حفظ البرومبت في المكتبة")
        dialog.geometry("450x320")
        dialog.resizable(False, False)
        dialog.configure(bg="#f4f6f9")
        dialog.transient(self.ui["root"])
        dialog.grab_set()

        tk.Label(dialog, text="💾 حفظ البرومبت في قاعدة البيانات المحلية", font=("Segoe UI", 11, "bold"), bg="#1a1a2e", fg="white", pady=8).pack(fill="x")

        frame_form = tk.Frame(dialog, bg="#f4f6f9", padx=20, pady=15)
        frame_form.pack(fill="both", expand=True)

        tk.Label(frame_form, text="عنوان أو اسم البرومبت:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(anchor="e", pady=(2, 1))
        entry_title = tk.Entry(frame_form, font=("Segoe UI", 10), justify="right", relief="solid", bd=1)
        entry_title.pack(fill="x", pady=(0, 8))
        entry_title.insert(0, suggested_title)
        entry_title.focus()

        tk.Label(frame_form, text="المجموعة أو التصنيف:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(anchor="e", pady=(2, 1))
        
        categories = prompt_db.get_categories()
        combo_cat = ttk.Combobox(frame_form, values=categories, font=("Segoe UI", 10), justify="right")
        combo_cat.pack(fill="x", pady=(0, 8))
        combo_cat.set("صور / تصميم" if "Image" in task_type else ("برمجة / كود" if "Code" in task_type else "نصوص / مقالات"))

        var_fav = tk.BooleanVar(value=False)
        chk_fav = tk.Checkbutton(frame_form, text="⭐ إضافة إلى المفضلة", variable=var_fav, font=("Segoe UI", 9, "bold"), bg="#f4f6f9", activebackground="#f4f6f9")
        chk_fav.pack(anchor="e", pady=5)

        def do_save():
            title = entry_title.get().strip()
            category = combo_cat.get().strip() or "عام"
            is_fav = var_fav.get()

            if not title:
                messagebox.showwarning("تنبيه", "الرجاء إدخال عنوان للبرومبت.", parent=dialog)
                return

            prompt_db.save_prompt(
                title=title,
                english_prompt=final_prompt,
                arabic_input=arabic_text,
                task_type=task_type,
                model_used=active_model,
                category=category,
                is_favorite=1 if is_fav else 0
            )

            dialog.destroy()
            messagebox.showinfo("تم الحفظ", f"تم حفظ البرومبت '{title}' بنجاح في مكتبتك! 📚")
            self.refresh_library_list()
            self.init_library_categories()

        frame_btns = tk.Frame(dialog, bg="#f4f6f9", pady=10)
        frame_btns.pack(fill="x", side="bottom")

        tk.Button(frame_btns, text="💾 حفظ الآن", font=("Segoe UI", 10, "bold"), bg="#2a9d8f", fg="white", cursor="hand2", relief="flat", padx=15, command=do_save).pack(side="left", padx=20)
        tk.Button(frame_btns, text="إلغاء", font=("Segoe UI", 9), bg="#cccccc", cursor="hand2", relief="flat", padx=10, command=dialog.destroy).pack(side="right", padx=20)

    # =========================================================================
    # 📚 إدارة وعرض وتبويب مكتبة البرومبتات (Tab 2)
    # =========================================================================
    def init_library_view(self):
        """تهيئة مكتبة البرومبتات عند بدء البرنامج"""
        prompt_db.init_db()
        self.init_library_categories()
        self.refresh_library_list()

    def init_library_categories(self):
        """تحديث قائمة المجموعات في كومبوبوكس التصفية"""
        cats = ["الكل"] + prompt_db.get_categories()
        self.ui["combo_filter_category"].config(values=cats)
        if not self.ui["combo_filter_category"].get():
            self.ui["combo_filter_category"].current(0)

    def refresh_library_list(self):
        """إعادة قراءة وتعبئة جدول البرومبتات بناءً على البحث والتصفية"""
        tree = self.ui["tree_library"]
        for row in tree.get_children():
            tree.delete(row)

        search_text = self.ui["entry_search_library"].get().strip()
        category = self.ui["combo_filter_category"].get()
        if not category:
            category = "الكل"

        prompts = prompt_db.get_prompts(
            search_query=search_text,
            category_filter=category,
            favorites_only=self.favorites_only_mode
        )

        for p in prompts:
            fav_star = "⭐" if p["is_favorite"] else "☆"
            tree.insert("", "end", iid=str(p["id"]), values=(fav_star, p["category"], p["title"]))

        # إذا كان البرومبت المختار موجوداً نقوم بتحديده، وإلا نمسح المعاينة
        if self.selected_prompt_id and tree.exists(str(self.selected_prompt_id)):
            tree.selection_set(str(self.selected_prompt_id))
        else:
            self._clear_library_preview()

    def clear_library_search(self):
        self.ui["entry_search_library"].delete(0, tk.END)
        self.refresh_library_list()

    def toggle_library_favorites_filter(self):
        self.favorites_only_mode = not self.favorites_only_mode
        if self.favorites_only_mode:
            self.ui["btn_fav_filter"].config(bg="#d90429", fg="#ffffff", text="⭐ المفضلة (مفعّلة)")
        else:
            self.ui["btn_fav_filter"].config(bg="#ffffff", fg="#d90429", text="⭐ المفضلة فقط")
        self.refresh_library_list()

    def on_library_item_selected(self, event):
        tree = self.ui["tree_library"]
        selected = tree.selection()
        if not selected:
            return
        
        prompt_id = int(selected[0])
        self.selected_prompt_id = prompt_id
        data = prompt_db.get_prompt_by_id(prompt_id)
        if not data:
            return

        star = "⭐" if data["is_favorite"] else ""
        self.ui["lbl_lib_title_display"].config(text=f"{star} {data['title']}")
        
        created = str(data["created_at"])[:16] if data["created_at"] else ""
        meta_info = f"المجموعة: {data['category']}  |  النوع: {data['task_type']}  |  الموديل: {data['model_used'] or 'افتراضي'}  |  التاريخ: {created}"
        self.ui["lbl_lib_meta"].config(text=meta_info)

        # النص العربي
        txt_ar = self.ui["txt_lib_arabic"]
        txt_ar.delete("1.0", tk.END)
        txt_ar.insert("1.0", data["arabic_input"] or "", "rtl")

        # البرومبت الإنجليزي
        txt_en = self.ui["txt_lib_english"]
        txt_en.delete("1.0", tk.END)
        txt_en.insert("1.0", data["english_prompt"] or "")

    def _clear_library_preview(self):
        self.selected_prompt_id = None
        self.ui["lbl_lib_title_display"].config(text="اختر برومبت من القائمة لمعاينته...")
        self.ui["lbl_lib_meta"].config(text="")
        self.ui["txt_lib_arabic"].delete("1.0", tk.END)
        self.ui["txt_lib_english"].delete("1.0", tk.END)

    def copy_selected_library_prompt(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("تنبيه", "يرجى تحديد برومبت من القائمة أولاً.")
            return
        content = self.ui["txt_lib_english"].get("1.0", tk.END).strip()
        if content:
            self.ui["root"].clipboard_clear()
            self.ui["root"].clipboard_append(content)
            messagebox.showinfo("تم النسخ", "تم نسخ البرومبت بنجاح إلى الحافظة! 📋")

    def transfer_selected_to_creator(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("تنبيه", "يرجى تحديد برومبت من القائمة أولاً.")
            return

        ar_content = self.ui["txt_lib_arabic"].get("1.0", tk.END).strip()
        en_content = self.ui["txt_lib_english"].get("1.0", tk.END).strip()

        if ar_content:
            txt_ar = self.ui["txt_arabic_input"]
            txt_ar.delete("1.0", tk.END)
            txt_ar.insert("1.0", ar_content, "rtl")
            txt_ar.config(fg="#1d3557")

        if en_content:
            txt_en = self.ui["txt_english_output"]
            txt_en.delete("1.0", tk.END)
            txt_en.insert("1.0", en_content)

        # التبديل إلى التبويب الأول (صانع وموسع البرومبت)
        self.ui["notebook"].select(0)

    def toggle_selected_favorite(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("تنبيه", "يرجى تحديد برومبت من القائمة أولاً.")
            return
        new_state = prompt_db.toggle_favorite(self.selected_prompt_id)
        self.refresh_library_list()
        msg = "تمت إضافة البرومبت للمفضلة ⭐" if new_state else "تمت إزالة البرومبت من المفضلة."
        messagebox.showinfo("المفضلة", msg)

    def delete_selected_prompt(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("تنبيه", "يرجى تحديد برومبت من القائمة أولاً.")
            return
        confirm = messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من رغبتك في حذف هذا البرومبت نهائياً من مكتبتك؟")
        if confirm:
            prompt_db.delete_prompt(self.selected_prompt_id)
            self._clear_library_preview()
            self.refresh_library_list()
            self.init_library_categories()

    # =========================================================================
    # 🔍 فحص وجلب الموديولات (Tab 3)
    # =========================================================================
    def clear_entry(self):
        self.ui["entry_model"].delete(0, tk.END)
        self.ui["entry_model"].focus()

    def copy_cmd(self, cmd_text):
        self.ui["root"].clipboard_clear()
        self.ui["root"].clipboard_append(cmd_text)
        messagebox.showinfo("نجاح النسخ", f"تم نسخ الأمر إلى الحافظة بنجاح:\n\n{cmd_text}\n\nيمكنك لصقه في موجه الأوامر (CMD أو PowerShell) لتشغيله.")

    def fetch_and_recommend(self):
        raw_name = self.ui["entry_model"].get().strip().lower()
        model_name = raw_name.replace("https://", "").replace("http://", "").replace("://ollama.com", "").replace("ollama.com", "").replace("library/", "").strip("/")
        
        if not model_name:
            messagebox.showwarning("تنبيه", "الرجاء إدخال اسم الموديول الأساسي أولاً (مثل qwen2.5 أو llama3.2).")
            return

        self.ui["btn_analyze"].config(state="disabled", text="🔍 جاري فحص الرام وجلب وتصفية النسخ حياً...")
        for widget in self.ui["scrollable_frame"].winfo_children(): 
            widget.destroy()
            
        tk.Label(self.ui["scrollable_frame"], text="🔄 جاري فحص الرام واستخراج النسخ العملية فقط من Ollama... برجاء الانتظار.", font=("Segoe UI", 10), bg="#ffffff", fg="#028090").pack(pady=40)

        self.ui["lbl_best_command"].config(text="جاري تحديد الموديول النموذجي لجهازك...")
        self.ui["btn_copy_best"].config(state="disabled")
        self.ui["btn_adopt_best"].config(state="disabled")

        threading.Thread(target=self.process_scraping, args=(model_name,), daemon=True).start()

    def process_scraping(self, model_name):
        result = ollama_scraper.scrape_ollama_tags(model_name)
        if result["status"] == "error":
            self.ui["root"].after(0, lambda: self.handle_ui_error(result["message"]))
        else:
            self.ui["root"].after(0, lambda: self.handle_ui_success(result["best_tag"], result["top_5"], result["free_ram"]))

    def handle_ui_error(self, error_msg):
        for widget in self.ui["scrollable_frame"].winfo_children(): 
            widget.destroy()
        tk.Label(self.ui["scrollable_frame"], text=error_msg, font=("Segoe UI", 10, "bold"), fg="#d90429", bg="#ffffff").pack(pady=40)
        self.ui["btn_analyze"].config(state="normal", text="📊 جلب وترتيب موديولات Ollama حياً ومطابقة الرام")
        self.ui["lbl_best_command"].config(text="تعذر تحديد الموديل بسبب الخطأ أعلاه.")

    def handle_ui_success(self, best_tag, top_5, free_ram):
        for widget in self.ui["scrollable_frame"].winfo_children(): 
            widget.destroy()
            
        self.ui["lbl_ram_live"].config(text=f"📉 الذاكرة الحرة الحالية بجهازك الآن: {free_ram} GB")
        self.ui["btn_analyze"].config(state="normal", text="📊 جلب وترتيب موديولات Ollama حياً ومطابقة الرام")

        if not top_5:
            tk.Label(self.ui["scrollable_frame"], text="❌ لم نجد نسخ متوافقة تقنياً مع حجم رامات جهازك الحالية.", font=("Segoe UI", 10, "bold"), fg="#d90429", bg="#ffffff").pack(pady=40)
            return

        for idx, item in enumerate(top_5, 1):
            tag = item["tag"]
            size = item["size"]
            is_best = item["is_best"]
            category_text = item["category"]

            row_frame = tk.Frame(self.ui["scrollable_frame"], bg="#ffffff", pady=6, padx=10, relief="groove", bd=1)
            row_frame.pack(fill="x", pady=4, padx=5)

            if is_best:
                prefix = "🌟"
                fg_color = "#d90429"
                bg_label = "#fdf0f0"
            elif "أخف" in category_text:
                prefix = "⚡"
                fg_color = "#2a9d8f"
                bg_label = "#f0fdfa"
            else:
                prefix = "⏳"
                fg_color = "#f4a261"
                bg_label = "#fffbeb"

            pull_cmd = f"ollama pull {tag}"
            
            btn_row_copy = tk.Button(row_frame, text="📋 نسخ الأمر", font=("Segoe UI", 8, "bold"), bg="#f1faee", fg="#1d3557", cursor="hand2", relief="solid", bd=1, padx=6, command=lambda c=pull_cmd: self.copy_cmd(c))
            btn_row_copy.pack(side="left", padx=3)

            btn_row_select = tk.Button(row_frame, text="🎯 اعتماد للتوليد", font=("Segoe UI", 8, "bold"), bg="#e2eafc", fg="#1d3557", cursor="hand2", relief="solid", bd=1, padx=6, command=lambda t=tag: self.set_active_model(t))
            btn_row_select.pack(side="left", padx=3)

            lbl_cat = tk.Label(row_frame, text=f" {category_text} ", font=("Segoe UI", 8, "bold"), fg=fg_color, bg=bg_label, bd=1, relief="solid")
            lbl_cat.pack(side="left", padx=10)

            lbl_info = tk.Label(row_frame, text=f"{prefix} {idx}. {tag} ({round(size, 2)} GB)", font=("Segoe UI", 10, "bold" if is_best else "normal"), bg="#ffffff", anchor="e")
            lbl_info.pack(side="right", fill="x", expand=True, padx=5)

        if best_tag and best_tag != "غير متوفر":
            best_pull_cmd = f"ollama pull {best_tag}"
            self.ui["lbl_best_command"].config(text=best_pull_cmd)
            self.ui["btn_copy_best"].config(state="normal", command=lambda: self.copy_cmd(best_pull_cmd))
            self.ui["btn_adopt_best"].config(state="normal", command=lambda: self.set_active_model(best_tag))
            self.set_active_model(best_tag)
