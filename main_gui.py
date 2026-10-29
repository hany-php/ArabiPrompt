# main_gui.py
import os
import sys
import tkinter as tk
from tkinter import ttk
import gui_actions

# قاموس مركزي لتخزين عناصر الواجهة ومشاركتها مع كلاس الأحداث
ui = {}

def get_resource_path(relative_path):
    """دالة ذكية لجلب المسار الصحيح للأيقونة المدمجة داخل ملف الـ exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

root = tk.Tk()
root.title("منصة صياغة البرومبت ومستشار موديولات Ollama ومكتبة النماذج")
root.geometry("860x780")
root.minsize(800, 700)
root.configure(bg="#f4f6f9")
ui["root"] = root

try:
    icon_path = get_resource_path("app_icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
except Exception:
    pass

actions = gui_actions.GuiActions(ui)

# العنوان الرئيسي
lbl_title = tk.Label(root, text="🌐 النظام المتكامل لهندسة وتوسيع البرومبت وإدارة موديولات Ollama ومكتبة الحفظ", font=("Segoe UI", 11, "bold"), bg="#1a1a2e", fg="white", pady=9)
lbl_title.pack(fill="x")

# --- لوحة التحكم العليا (عرض حالة السيرفر والموديلات المثبتة محلياً) ---
frame_top_bar = tk.LabelFrame(root, text=" 💻 التحكم في سيرفر Ollama والموديلات المثبتة محلياً ", font=("Segoe UI", 9, "bold"), bg="#e2eafc", fg="#1d3557", pady=6, padx=10)
frame_top_bar.pack(fill="x", padx=12, pady=4)

# الصف الأول: حالة السيرفر وزر تشغيله، وقائمة الموديلات المحلية
frame_top_controls = tk.Frame(frame_top_bar, bg="#e2eafc")
frame_top_controls.pack(fill="x", pady=2)

# حالة السيرفر وزر تشغيله/فحصه
btn_toggle_server = tk.Button(frame_top_controls, text="⚡ تشغيل السيرفر", font=("Segoe UI", 8, "bold"), bg="#e63946", fg="white", cursor="hand2", command=actions.handle_server_action, relief="flat", padx=8)
btn_toggle_server.pack(side="left", padx=4)
ui["btn_toggle_server"] = btn_toggle_server

lbl_server_badge = tk.Label(frame_top_controls, text="جاري فحص السيرفر...", font=("Segoe UI", 8, "bold"), bg="#ffffff", fg="#1d3557", padx=8, relief="solid", bd=1)
lbl_server_badge.pack(side="left", padx=4)
ui["lbl_server_badge"] = lbl_server_badge

# اختيار الموديل المثبت وزر التحديث
btn_refresh_list = tk.Button(frame_top_controls, text="🔄 تحديث", font=("Segoe UI", 8, "bold"), bg="#457b9d", fg="white", cursor="hand2", command=actions.refresh_local_models_dropdown, relief="flat", padx=6)
btn_refresh_list.pack(side="right", padx=4)

combo_local_models = ttk.Combobox(frame_top_controls, font=("Consolas", 10, "bold"), width=24, state="disabled")
combo_local_models.pack(side="right", padx=4)
combo_local_models.bind("<<ComboboxSelected>>", actions.on_dropdown_model_selected)
ui["combo_local_models"] = combo_local_models

tk.Label(frame_top_controls, text="الموديلات المثبتة:", font=("Segoe UI", 9, "bold"), bg="#e2eafc").pack(side="right", padx=2)

# الموديل النشط للتوليد
lbl_active_model = tk.Label(frame_top_controls, text="...", font=("Consolas", 10, "bold"), fg="#d90429", bg="#ffffff", padx=6, relief="solid", bd=1)
lbl_active_model.pack(side="right", padx=(10, 4))
ui["lbl_active_model"] = lbl_active_model

tk.Label(frame_top_controls, text="المعتمد للتوليد:", font=("Segoe UI", 9, "bold"), bg="#e2eafc").pack(side="right", padx=2)

# الصف الثاني: سطر حالة الموديل بكامل العرض
frame_status_row = tk.Frame(frame_top_bar, bg="#e2eafc")
frame_status_row.pack(fill="x", pady=(3, 1))

lbl_model_status = tk.Label(frame_status_row, text="", font=("Segoe UI", 9, "bold"), bg="#e2eafc", anchor="e")
lbl_model_status.pack(fill="x", padx=5)
ui["lbl_model_status"] = lbl_model_status


# 🗂️ إنشاء نظام التبويبات (Notebook)
style = ttk.Style()
style.configure("TNotebook", tabposition="ne")
notebook = ttk.Notebook(root, style="TNotebook")
notebook.pack(fill="both", expand=True, padx=12, pady=4)
ui["notebook"] = notebook

tab_prompt = tk.Frame(notebook, bg="#f4f6f9")
tab_library = tk.Frame(notebook, bg="#f4f6f9")
tab_modules = tk.Frame(notebook, bg="#f4f6f9")

notebook.add(tab_prompt, text="  ✍️ صانع وموسع البرومبت  ")
notebook.add(tab_library, text="  📚 مكتبة البرومبتات المحفوظة  ")
notebook.add(tab_modules, text="  📊 مستشار وجلب الموديولات  ")


# =========================================================================
# 📥 محتويات التبويب الأول: محرك صياغة وتوسيع البرومبت (Prompt Expansion)
# =========================================================================
frame_bottom = tk.LabelFrame(tab_prompt, text=" لوحة هندسة البرومبت الذكية ", font=("Segoe UI", 10, "bold"), bg="#f4f6f9", pady=6, padx=10)
frame_bottom.pack(fill="both", expand=True, padx=8, pady=6)

frame_controls = tk.Frame(frame_bottom, bg="#f4f6f9")
frame_controls.pack(fill="x", pady=2)
tk.Label(frame_controls, text="نوع مخرج البرومبت المستهدف للذكاء الاصطناعي:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(side="right", padx=5)
combo_task = ttk.Combobox(frame_controls, values=["Image Generation", "Text/General", "Code/Programming"], font=("Segoe UI", 10), state="readonly", justify="right")
combo_task.pack(side="right", padx=5)
combo_task.current(0)
ui["combo_task"] = combo_task

tk.Label(frame_bottom, text="✍️ أدخل فكرتك أو النص العربي المراد ترجمته وهندسته وتوسيعه:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(anchor="e", pady=2)

# صندوق النص العربي - حل مشكلة الحروف المقطعة بدقة بدون أي KeyRelease مع دعم الـ RTL
txt_arabic_input = tk.Text(frame_bottom, height=4, font=("Segoe UI", 11), relief="solid", bd=1, wrap="word", fg="#888888")
txt_arabic_input.tag_configure("rtl", justify="right")
txt_arabic_input.insert("1.0", "اكتب فكرتك هنا باللغة العربية...", "rtl")
txt_arabic_input.pack(fill="x", pady=2)
txt_arabic_input.bind("<FocusIn>", actions.on_arabic_focus_in)
txt_arabic_input.bind("<FocusOut>", actions.on_arabic_focus_out)
ui["txt_arabic_input"] = txt_arabic_input

btn_generate = tk.Button(frame_bottom, text="🚀 توليد وتوسيع البرومبت الإحترافي محلياً", font=("Segoe UI", 10, "bold"), bg="#2a9d8f", fg="white", cursor="hand2", command=actions.trigger_generation, relief="flat", pady=6)
btn_generate.pack(fill="x", pady=4)
ui["btn_generate"] = btn_generate

frame_output_header = tk.Frame(frame_bottom, bg="#f4f6f9")
frame_output_header.pack(fill="x", pady=2)

tk.Label(frame_output_header, text="📋 البرومبت الإنجليزي الموسّع والجاهز للاستخدام:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(side="right")

btn_save_prompt = tk.Button(frame_output_header, text="💾 حفظ في المكتبة", font=("Segoe UI", 8, "bold"), bg="#2a9d8f", fg="white", cursor="hand2", command=actions.open_save_dialog, relief="flat", padx=8)
btn_save_prompt.pack(side="left", padx=4)

btn_copy_all = tk.Button(frame_output_header, text="📋 نسخ البرومبت", font=("Segoe UI", 8, "bold"), bg="#457b9d", fg="white", cursor="hand2", command=actions.copy_to_clipboard, relief="flat", padx=8)
btn_copy_all.pack(side="left", padx=4)

txt_english_output = tk.Text(frame_bottom, height=8, font=("Consolas", 10), bg="#fafafa", fg="#1d3557", relief="solid", bd=1, wrap="word")
txt_english_output.pack(fill="both", expand=True, pady=2)
ui["txt_english_output"] = txt_english_output


# =========================================================================
# 📚 محتويات التبويب الثاني: مكتبة البرومبتات المحفوظة والمفضلة (Tab 2)
# =========================================================================
frame_lib_top = tk.LabelFrame(tab_library, text=" البحث والتصفية في مكتبة البرومبتات المحفوظة ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", pady=6, padx=10)
frame_lib_top.pack(fill="x", padx=10, pady=6)

frame_lib_search_row = tk.Frame(frame_lib_top, bg="#f4f6f9")
frame_lib_search_row.pack(fill="x", pady=2)

btn_clear_search = tk.Button(frame_lib_search_row, text=" ✖ ", font=("Segoe UI", 8, "bold"), bg="#e63946", fg="white", cursor="hand2", relief="flat", padx=5, command=actions.clear_library_search)
btn_clear_search.pack(side="left", padx=3)

entry_search_library = tk.Entry(frame_lib_search_row, font=("Segoe UI", 10), relief="solid", bd=1, justify="right")
entry_search_library.pack(side="left", fill="x", expand=True, padx=4)
entry_search_library.bind("<KeyRelease>", lambda e: actions.refresh_library_list())
ui["entry_search_library"] = entry_search_library

tk.Label(frame_lib_search_row, text="بحث بالاسم أو بالنص:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(side="left", padx=5)

# تصفية حسب المجموعة
combo_filter_category = ttk.Combobox(frame_lib_search_row, font=("Segoe UI", 9), state="readonly", width=14, justify="right")
combo_filter_category.pack(side="right", padx=5)
combo_filter_category.bind("<<ComboboxSelected>>", lambda e: actions.refresh_library_list())
ui["combo_filter_category"] = combo_filter_category

tk.Label(frame_lib_search_row, text="المجموعة:", font=("Segoe UI", 9, "bold"), bg="#f4f6f9").pack(side="right", padx=2)

btn_fav_filter = tk.Button(frame_lib_search_row, text="⭐ المفضلة فقط", font=("Segoe UI", 8, "bold"), bg="#ffffff", fg="#d90429", relief="solid", bd=1, cursor="hand2", padx=6, command=actions.toggle_library_favorites_filter)
btn_fav_filter.pack(side="right", padx=6)
ui["btn_fav_filter"] = btn_fav_filter

# تقسيم مساحة المكتبة: قائمة البرومبتات في اليمين ومعاينة وتفاصيل في اليسار
frame_lib_split = tk.Frame(tab_library, bg="#f4f6f9")
frame_lib_split.pack(fill="both", expand=True, padx=10, pady=4)

# الجانب الأيمن: قائمة البرومبتات (Treeview)
frame_lib_list = tk.LabelFrame(frame_lib_split, text=" قائمة البرومبتات المحفوظة ", font=("Segoe UI", 9, "bold"), bg="#ffffff", padx=4, pady=4)
frame_lib_list.pack(side="right", fill="both", expand=True, padx=(4, 0))

columns_lib = ("fav", "category", "title")
tree_library = ttk.Treeview(frame_lib_list, columns=columns_lib, show="headings", selectmode="browse")
tree_library.heading("fav", text="⭐")
tree_library.heading("category", text="المجموعة")
tree_library.heading("title", text="عنوان البرومبت")

tree_library.column("fav", width=35, anchor="center")
tree_library.column("category", width=95, anchor="center")
tree_library.column("title", width=220, anchor="e")

scrollbar_tree = ttk.Scrollbar(frame_lib_list, orient="vertical", command=tree_library.yview)
tree_library.configure(yscrollcommand=scrollbar_tree.set)
tree_library.pack(side="right", fill="both", expand=True)
scrollbar_tree.pack(side="left", fill="y")
tree_library.bind("<<TreeviewSelect>>", actions.on_library_item_selected)
ui["tree_library"] = tree_library

# الجانب الأيسر: بطاقة المعاينة والعمليات
frame_lib_preview = tk.LabelFrame(frame_lib_split, text=" تفاصيل وإجراءات البرومبت ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", padx=8, pady=6)
frame_lib_preview.pack(side="left", fill="both", expand=True, padx=(0, 4))

lbl_lib_title_display = tk.Label(frame_lib_preview, text="اختر برومبت من القائمة لمعاينته...", font=("Segoe UI", 10, "bold"), bg="#f4f6f9", fg="#1d3557", anchor="e")
lbl_lib_title_display.pack(fill="x", pady=2)
ui["lbl_lib_title_display"] = lbl_lib_title_display

lbl_lib_meta = tk.Label(frame_lib_preview, text="", font=("Segoe UI", 8), bg="#f4f6f9", fg="#6c757d", anchor="e")
lbl_lib_meta.pack(fill="x", pady=1)
ui["lbl_lib_meta"] = lbl_lib_meta

tk.Label(frame_lib_preview, text="الفكرة الأصلية باللغة العربية:", font=("Segoe UI", 8, "bold"), bg="#f4f6f9", anchor="e").pack(fill="x", pady=(4, 1))
txt_lib_arabic = tk.Text(frame_lib_preview, height=3, font=("Segoe UI", 9), relief="solid", bd=1, wrap="word")
txt_lib_arabic.tag_configure("rtl", justify="right")
txt_lib_arabic.pack(fill="x", pady=1)
ui["txt_lib_arabic"] = txt_lib_arabic

tk.Label(frame_lib_preview, text="البرومبت الموسع باللغة الإنجليزية:", font=("Segoe UI", 8, "bold"), bg="#f4f6f9", anchor="e").pack(fill="x", pady=(4, 1))
txt_lib_english = tk.Text(frame_lib_preview, height=7, font=("Consolas", 9), bg="#ffffff", fg="#1d3557", relief="solid", bd=1, wrap="word")
txt_lib_english.pack(fill="both", expand=True, pady=1)
ui["txt_lib_english"] = txt_lib_english

frame_lib_actions = tk.Frame(frame_lib_preview, bg="#f4f6f9")
frame_lib_actions.pack(fill="x", pady=5)

btn_lib_copy = tk.Button(frame_lib_actions, text="📋 نسخ البرومبت", font=("Segoe UI", 8, "bold"), bg="#457b9d", fg="white", cursor="hand2", relief="flat", padx=6, command=actions.copy_selected_library_prompt)
btn_lib_copy.pack(side="left", padx=2)

btn_lib_transfer = tk.Button(frame_lib_actions, text="✍️ نقل لصانع البرومبت", font=("Segoe UI", 8, "bold"), bg="#2a9d8f", fg="white", cursor="hand2", relief="flat", padx=6, command=actions.transfer_selected_to_creator)
btn_lib_transfer.pack(side="left", padx=2)

btn_lib_fav = tk.Button(frame_lib_actions, text="⭐ تبديل المفضلة", font=("Segoe UI", 8, "bold"), bg="#f4a261", fg="white", cursor="hand2", relief="flat", padx=6, command=actions.toggle_selected_favorite)
btn_lib_fav.pack(side="left", padx=2)

btn_lib_delete = tk.Button(frame_lib_actions, text="🗑️ حذف", font=("Segoe UI", 8, "bold"), bg="#e63946", fg="white", cursor="hand2", relief="flat", padx=6, command=actions.delete_selected_prompt)
btn_lib_delete.pack(side="right", padx=2)


# =========================================================================
# 📥 محتويات التبويب الثالث: فحص وجلب الموديولات المناسبة للجهاز حياً (Tab 3)
# =========================================================================
frame_inputs = tk.LabelFrame(tab_modules, text=" ابحث عن أي موديول حياً من مستودع Ollama ومطابقته مع راماتك ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", pady=6, padx=10)
frame_inputs.pack(fill="x", padx=10, pady=6)

frame_search_row = tk.Frame(frame_inputs, bg="#f4f6f9")
frame_search_row.pack(fill="x", pady=2)

btn_clear = tk.Button(frame_search_row, text=" ✖ ", font=("Segoe UI", 9, "bold"), bg="#e63946", fg="white", cursor="hand2", relief="flat", padx=6, command=actions.clear_entry)
btn_clear.pack(side="left", padx=5)

entry_model = tk.Entry(frame_search_row, font=("Segoe UI", 11), width=28, relief="solid", bd=1, justify="right")
entry_model.pack(side="left", padx=5, fill="x", expand=True)
entry_model.insert(0, "qwen2.5-coder")
ui["entry_model"] = entry_model

tk.Label(frame_search_row, text="أدخل اسم الموديول الأساسي:", font=("Segoe UI", 10, "bold"), bg="#f4f6f9").pack(side="right", padx=5)

btn_analyze = tk.Button(tab_modules, text="📊 جلب وترتيب موديولات Ollama حياً ومطابقة الرام", font=("Segoe UI", 10, "bold"), bg="#028090", fg="white", cursor="hand2", command=actions.fetch_and_recommend, relief="flat", pady=5)
btn_analyze.pack(fill="x", padx=10, pady=3)
ui["btn_analyze"] = btn_analyze

lbl_ram_live = tk.Label(tab_modules, text="📉 قيد فحص عتاد الجهاز والتحقق من سيرفر أولاما بالخلفية...", font=("Segoe UI", 9, "bold"), bg="#e2eafc", fg="#1d3557", pady=4)
lbl_ram_live.pack(fill="x", padx=10, pady=2)
ui["lbl_ram_live"] = lbl_ram_live

# القائمة المفلترة المتجاوبة لعرض النسخ المناسبة
frame_list_container = tk.LabelFrame(tab_modules, text=" القائمة المفلترة للنسخ القابلة للتشغيل المستقر على جهازك ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9")
frame_list_container.pack(pady=4, padx=10, fill="both", expand=True)

canvas = tk.Canvas(frame_list_container, bg="#ffffff", highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_list_container, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#ffffff")

def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=740)
canvas.bind("<Configure>", on_canvas_configure)
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="right", fill="both", expand=True)
scrollbar.pack(side="left", fill="y")
ui["scrollable_frame"] = scrollable_frame

# كادر الخيار المظبوط والنموذجي لجهازك
frame_best = tk.LabelFrame(tab_modules, text=" 🌟 الخيار المظبوط والنموذجي لجهازك حالياً (أعلى كفاءة وأمان) 🌟 ", font=("Segoe UI", 9, "bold"), bg="#e2eafc", fg="#d90429", pady=6, padx=10)
frame_best.pack(pady=6, padx=10, fill="x")

btn_copy_best = tk.Button(frame_best, text="📋 نسخ أمر التحميل", font=("Segoe UI", 9, "bold"), bg="#d90429", fg="white", cursor="hand2", relief="flat", padx=10, state="disabled")
btn_copy_best.pack(side="left", padx=4)
ui["btn_copy_best"] = btn_copy_best

btn_adopt_best = tk.Button(frame_best, text="🎯 اعتماده للتوليد", font=("Segoe UI", 9, "bold"), bg="#2a9d8f", fg="white", cursor="hand2", relief="flat", padx=10, state="disabled")
btn_adopt_best.pack(side="left", padx=4)
ui["btn_adopt_best"] = btn_adopt_best

lbl_best_command = tk.Label(frame_best, text="اضغط على زر الفحص بالأعلى لتحديد الموديول المثالي لجهازك...", font=("Consolas", 10, "bold"), bg="#ffffff", fg="#457b9d", relief="solid", bd=1, pady=5, padx=8, anchor="e")
lbl_best_command.pack(side="right", fill="x", expand=True, padx=5)
ui["lbl_best_command"] = lbl_best_command

# بدء الفحص والتهيئة الفورية في الخلفية
root.after(100, actions.verify_and_start_backend)
root.after(200, actions.init_library_view)

if __name__ == "__main__":
    root.mainloop()
