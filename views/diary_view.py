import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DiaryDB


def _set_bg_recursive(widget, bg):
    try:
        widget.configure(bg=bg)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        _set_bg_recursive(child, bg)


class DiaryView(tk.Frame):

    MOODS = [
        ("😊", "开心", "#fef3c7"),
        ("😐", "平静", "#e2e8f0"),
        ("😢", "难过", "#dbeafe"),
        ("😡", "生气", "#fee2e2"),
        ("😴", "疲惫", "#f3e8ff"),
        ("🥰", "幸福", "#fce7f3"),
        ("🤔", "思考", "#ccfbf1"),
        ("😎", "自信", "#d1fae5"),
    ]

    WEATHERS = [
        ("☀️", "晴", "#fef3c7"),
        ("⛅", "多云", "#e2e8f0"),
        ("🌧️", "雨", "#dbeafe"),
        ("❄️", "雪", "#f1f5f9"),
        ("🌤️", "阴", "#cbd5e1"),
        ("🌈", "彩虹", "#fce7f3"),
    ]

    def __init__(self, parent, theme=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f1f5f9")
        self.theme = theme or {
            "bg": "#f1f5f9", "card_bg": "#ffffff", "primary": "#6366f1",
            "primary_light": "#e0e7ff", "success": "#10b981", "danger": "#ef4444",
            "warning": "#f59e0b", "text": "#1e293b", "text_secondary": "#64748b",
            "border": "#e2e8f0", "success_light": "#d1fae5", "danger_light": "#fee2e2",
        }
        self.selected_date = date.today()
        self.display_year = date.today().year
        self.display_month = date.today().month
        self.selected_mood = ""
        self.selected_weather = ""
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 头部
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="📝 我的日记", font=("Microsoft YaHei UI", 18, "bold"),
                bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  记录生活的点滴", font=("Microsoft YaHei UI", 10),
                bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        # 搜索框
        search_frame = tk.Frame(header, bg=self.theme["bg"])
        search_frame.pack(side=tk.RIGHT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                              font=("Microsoft YaHei UI", 10), width=20,
                              highlightbackground=self.theme["border"], highlightthickness=1)
        search_entry.pack(side=tk.LEFT, ipady=3)
        tk.Label(search_frame, text="🔍", bg=self.theme["bg"],
                font=("Segoe UI Emoji", 12)).pack(side=tk.LEFT, padx=5)

        body = tk.Frame(self, bg=self.theme["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=(5, 20))

        # 左侧面板
        left_panel = tk.Frame(body, bg=self.theme["card_bg"], 
                             highlightbackground=self.theme["border"],
                             highlightthickness=1, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # 右侧面板
        right_panel = tk.Frame(body, bg=self.theme["card_bg"], 
                              highlightbackground=self.theme["border"],
                              highlightthickness=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_calendar(left_panel)
        self._build_editor(right_panel)

    def _build_calendar(self, parent):
        # 日历头部
        cal_header = tk.Frame(parent, bg=self.theme["card_bg"])
        cal_header.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Button(cal_header, text="◀", font=("Segoe UI", 10), relief="flat",
                 bg=self.theme["card_bg"], cursor="hand2",
                 command=self._prev_month).pack(side=tk.LEFT)
        self.lbl_month = tk.Label(cal_header, text="", font=("Microsoft YaHei UI", 12, "bold"),
                                 bg=self.theme["card_bg"], fg=self.theme["text"])
        self.lbl_month.pack(side=tk.LEFT, expand=True)
        tk.Button(cal_header, text="▶", font=("Segoe UI", 10), relief="flat",
                 bg=self.theme["card_bg"], cursor="hand2",
                 command=self._next_month).pack(side=tk.RIGHT)

        # 日历网格
        self.cal_grid = tk.Frame(parent, bg=self.theme["card_bg"])
        self.cal_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 日记列表
        list_label = tk.Label(parent, text="📖 最近日记", font=("Microsoft YaHei UI", 11, "bold"),
                             bg=self.theme["card_bg"], fg=self.theme["text"])
        list_label.pack(anchor="w", padx=10, pady=(10, 5))

        # 查看全部按钮
        view_all_btn = tk.Button(parent, text="查看全部 ▶", font=("Microsoft YaHei UI", 9),
                                 relief="flat", bd=1, bg=self.theme["card_bg"],
                                 fg=self.theme["text"], cursor="hand2",
                                 highlightbackground="#1e293b", highlightthickness=1,
                                 activebackground=self.theme["card_bg"],
                                 command=self._view_all_diaries)
        view_all_btn.pack(anchor="e", padx=10, pady=(0, 5))

        # 统计信息
        self.stats_label = tk.Label(parent, text="", font=("Microsoft YaHei UI", 9),
                                   bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.stats_label.pack(anchor="w", padx=10, pady=(0, 5))

        self.diary_list_frame = tk.Frame(parent, bg=self.theme["card_bg"])
        self.diary_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _build_editor(self, parent):
        # 编辑器头部：日期 + 操作按钮
        editor_header = tk.Frame(parent, bg=self.theme["card_bg"])
        editor_header.pack(fill=tk.X, padx=20, pady=(12, 2))

        # 操作按钮（右上角）
        btn_frame = tk.Frame(editor_header, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.RIGHT)

        self.save_btn = tk.Button(btn_frame, text="保存", font=("Microsoft YaHei UI", 9),
                                 bg=self.theme["primary"], fg="white", relief="flat",
                                 padx=10, pady=3, cursor="hand2", command=self._save_diary)
        self.save_btn.pack(side=tk.LEFT, padx=2)

        self.del_btn = tk.Button(btn_frame, text="删除", font=("Microsoft YaHei UI", 9),
                                bg=self.theme["danger"], fg="white", relief="flat",
                                padx=10, pady=3, cursor="hand2", command=self._delete_diary)
        self.del_btn.pack(side=tk.LEFT, padx=2)

        self.clear_btn = tk.Button(btn_frame, text="清空", font=("Microsoft YaHei UI", 9),
                                  bg=self.theme["warning"], fg="white", relief="flat",
                                  padx=10, pady=3, cursor="hand2", command=self._clear_editor)
        self.clear_btn.pack(side=tk.LEFT, padx=2)

        # 日期（左侧）
        date_frame = tk.Frame(editor_header, bg=self.theme["card_bg"])
        date_frame.pack(side=tk.LEFT)

        self.lbl_date = tk.Label(date_frame, text="", font=("Microsoft YaHei UI", 16, "bold"),
                                bg=self.theme["card_bg"], fg=self.theme["text"])
        self.lbl_date.pack(anchor="w")

        self.lbl_weekday = tk.Label(date_frame, text="", font=("Microsoft YaHei UI", 10),
                                   bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.lbl_weekday.pack(anchor="w")

        # 心情选择
        mood_frame = tk.Frame(parent, bg=self.theme["card_bg"])
        mood_frame.pack(fill=tk.X, padx=20, pady=2)

        tk.Label(mood_frame, text="心情", font=("Microsoft YaHei UI", 9),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))

        self.mood_buttons = {}
        for emoji, label, color in self.MOODS:
            btn = tk.Label(mood_frame, text=emoji,
                          font=("Segoe UI Emoji", 13),
                          bg=self.theme["card_bg"], cursor="hand2",
                          padx=4, pady=2)
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind("<Button-1>", lambda e, m=label, c=color: self._set_mood(m, c))
            self.mood_buttons[label] = (btn, color)

        # 天气选择
        weather_frame = tk.Frame(parent, bg=self.theme["card_bg"])
        weather_frame.pack(fill=tk.X, padx=20, pady=2)

        tk.Label(weather_frame, text="天气", font=("Microsoft YaHei UI", 9),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, padx=(0, 8))

        self.weather_buttons = {}
        for emoji, label, color in self.WEATHERS:
            btn = tk.Label(weather_frame, text=emoji,
                          font=("Segoe UI Emoji", 13),
                          bg=self.theme["card_bg"], cursor="hand2",
                          padx=4, pady=2)
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind("<Button-1>", lambda e, w=label, c=color: self._set_weather(w, c))
            self.weather_buttons[label] = (btn, color)

        # 选中状态提示
        self.meta_hint = tk.Label(parent, text="", font=("Microsoft YaHei UI", 9),
                                  bg=self.theme["card_bg"], fg=self.theme["primary"])
        self.meta_hint.pack(anchor="w", padx=20)

        # 标题输入
        title_frame = tk.Frame(parent, bg=self.theme["card_bg"])
        title_frame.pack(fill=tk.X, padx=20, pady=(4, 4))

        tk.Label(title_frame, text="标题", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT)

        self.entry_title = tk.Entry(title_frame, font=("Microsoft YaHei UI", 12),
                                   highlightbackground=self.theme["border"],
                                   highlightthickness=1)
        self.entry_title.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 内容编辑区（自适应填充剩余空间）
        text_frame = tk.Frame(parent, bg=self.theme["card_bg"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # 工具栏
        toolbar = tk.Frame(text_frame, bg=self.theme["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 4))

        tk.Label(toolbar, text="日记内容", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT)

        self.word_count = tk.Label(toolbar, text="0 字", font=("Microsoft YaHei UI", 9),
                                  bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.word_count.pack(side=tk.RIGHT)

        self.text_content = tk.Text(text_frame, font=("Microsoft YaHei UI", 11),
                                   wrap=tk.WORD, padx=12, pady=12,
                                   highlightbackground=self.theme["border"],
                                   highlightthickness=1,
                                   spacing1=2, spacing3=2)
        self.text_content.bind("<KeyRelease>", self._update_word_count)

        text_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                   command=self.text_content.yview)
        self.text_content.configure(yscrollcommand=text_scroll.set)
        self.text_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self):
        self._draw_calendar()
        self._load_diary()
        self._load_diary_list()
        self._update_stats()

    def _prev_month(self):
        self.display_month -= 1
        if self.display_month < 1:
            self.display_month = 12
            self.display_year -= 1
        self.refresh()

    def _next_month(self):
        self.display_month += 1
        if self.display_month > 12:
            self.display_month = 1
            self.display_year += 1
        self.refresh()

    def _draw_calendar(self):
        for w in self.cal_grid.winfo_children():
            w.destroy()

        self.lbl_month.configure(text=f"{self.display_year}年{self.display_month}月")

        diary_dates = DiaryDB.get_dates_with_diary(self.display_year, self.display_month)
        cal = calendar.monthcalendar(self.display_year, self.display_month)
        today = date.today()

        # 星期表头（每次重建，确保始终显示）
        days = ["一", "二", "三", "四", "五", "六", "日"]
        for i, d in enumerate(days):
            lbl = tk.Label(self.cal_grid, text=d, font=("Microsoft YaHei UI", 9, "bold"),
                          bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
            lbl.grid(row=0, column=i, pady=(0, 4), sticky="nsew")
            self.cal_grid.columnconfigure(i, weight=1)

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    empty = tk.Frame(self.cal_grid, bg=self.theme["card_bg"], width=36, height=30)
                    empty.grid(row=row_idx + 1, column=col_idx, pady=2, padx=1, sticky="nsew")
                    empty.grid_propagate(False)
                    continue

                d = date(self.display_year, self.display_month, day)
                date_str = d.strftime("%Y-%m-%d")

                is_today = d == today
                is_selected = d == self.selected_date
                has_diary = date_str in diary_dates

                if is_selected:
                    bg = self.theme["primary"]
                    fg = "white"
                    font = ("Microsoft YaHei UI", 10, "bold")
                    border_color = self.theme["primary"]
                    hl = 0
                elif is_today:
                    bg = "#3b82f6"
                    fg = "white"
                    font = ("Microsoft YaHei UI", 10, "bold")
                    border_color = "#3b82f6"
                    hl = 2
                else:
                    bg = self.theme["card_bg"]
                    fg = self.theme["text"]
                    font = ("Microsoft YaHei UI", 10)
                    border_color = self.theme["card_bg"]
                    hl = 0

                cell_frame = tk.Frame(self.cal_grid, bg=bg, width=36, height=30,
                                     highlightbackground=border_color, highlightthickness=hl)
                cell_frame.grid(row=row_idx + 1, column=col_idx, pady=2, padx=1, sticky="nsew")
                cell_frame.grid_propagate(False)

                day_lbl = tk.Label(cell_frame, text=str(day), font=font,
                                  bg=bg, fg=fg, cursor="hand2")
                day_lbl.pack(expand=True)

                if has_diary:
                    dot = tk.Canvas(cell_frame, width=6, height=6, bg=bg, highlightthickness=0)
                    dot.create_oval(1, 1, 5, 5, fill=self.theme["primary"], outline="")
                    dot.place(relx=0.5, rely=0.85, anchor="center")

                for widget in (cell_frame, day_lbl):
                    widget.bind("<Button-1>", lambda e, dd=d: self._select_date(dd))

    def _select_date(self, d):
        self.selected_date = d
        self.refresh()

    def _set_mood(self, mood, color):
        self.selected_mood = mood
        for label, (btn, c) in self.mood_buttons.items():
            if label == mood:
                btn.configure(bg=color, relief="solid",
                            highlightbackground=self.theme["primary"],
                            highlightthickness=1)
            else:
                btn.configure(bg=self.theme["card_bg"], relief="flat",
                            highlightthickness=0)
        self._update_meta_hint()

    def _set_weather(self, weather, color):
        self.selected_weather = weather
        for label, (btn, c) in self.weather_buttons.items():
            if label == weather:
                btn.configure(bg=color, relief="solid",
                            highlightbackground=self.theme["primary"],
                            highlightthickness=1)
            else:
                btn.configure(bg=self.theme["card_bg"], relief="flat",
                            highlightthickness=0)
        self._update_meta_hint()

    def _update_meta_hint(self):
        parts = []
        if self.selected_mood:
            parts.append(f"心情: {self.selected_mood}")
        if self.selected_weather:
            parts.append(f"天气: {self.selected_weather}")
        self.meta_hint.configure(text=" | ".join(parts))

    def _load_diary(self):
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_name = day_names[self.selected_date.weekday()]
        
        self.lbl_date.configure(text=self.selected_date.strftime("%Y-%m-%d"))
        self.lbl_weekday.configure(text=day_name)

        ds = self.selected_date.strftime("%Y-%m-%d")
        diary = DiaryDB.get_by_date(ds)

        self.entry_title.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)

        if diary:
            self.entry_title.insert(0, diary["title"])
            self.text_content.insert("1.0", diary["content"])
            self._set_mood(diary["mood"] or "", self._get_mood_color(diary["mood"]))
            self._set_weather(diary["weather"] or "", self._get_weather_color(diary["weather"]))
        else:
            self.selected_mood = ""
            self.selected_weather = ""
            for btn, c in self.mood_buttons.values():
                btn.configure(bg=self.theme["card_bg"], relief="flat", highlightthickness=0)
            for btn, c in self.weather_buttons.values():
                btn.configure(bg=self.theme["card_bg"], relief="flat", highlightthickness=0)
            self._update_meta_hint()
        
        self._update_word_count()

    def _get_mood_color(self, mood):
        for emoji, label, color in self.MOODS:
            if label == mood:
                return color
        return self.theme["card_bg"]

    def _get_weather_color(self, weather):
        for emoji, label, color in self.WEATHERS:
            if label == weather:
                return color
        return self.theme["card_bg"]

    def _load_diary_list(self):
        for w in self.diary_list_frame.winfo_children():
            w.destroy()

        keyword = self.search_var.get().strip()
        if keyword:
            diaries = DiaryDB.search(keyword)
        else:
            diaries = DiaryDB.get_all(15)

        if not diaries:
            tk.Label(self.diary_list_frame, text="暂无日记",
                    font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"],
                    bg=self.theme["card_bg"]).pack(anchor="w", pady=5)
            return

        for d in diaries:
            item = tk.Frame(self.diary_list_frame, bg=self.theme["card_bg"],
                          cursor="hand2", highlightbackground=self.theme["border"],
                          highlightthickness=1)
            item.pack(fill=tk.X, pady=2)
            item.bind("<Enter>", lambda e, f=item: f.configure(bg=self.theme["primary_light"]))
            item.bind("<Leave>", lambda e, f=item: f.configure(bg=self.theme["card_bg"]))

            mood_emoji = ""
            for emoji, label, color in self.MOODS:
                if label == d["mood"]:
                    mood_emoji = emoji
                    break

            content_frame = tk.Frame(item, bg=self.theme["card_bg"])
            content_frame.pack(fill=tk.X, padx=8, pady=6)
            
            title_text = d["title"][:20] + "..." if len(d["title"]) > 20 else d["title"]
            tk.Label(content_frame, 
                    text=f"{mood_emoji} {d['diary_date']}  {title_text}",
                    font=("Microsoft YaHei UI", 9),
                    bg=self.theme["card_bg"], fg=self.theme["text"], anchor="w").pack(anchor="w")
            
            preview = d["content"][:30] + "..." if len(d["content"]) > 30 else d["content"]
            tk.Label(content_frame, text=preview or "（无内容）",
                    font=("Microsoft YaHei UI", 8),
                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"], 
                    anchor="w").pack(anchor="w")

            for child in item.winfo_children():
                child.bind("<Button-1>", lambda e, dd=d["diary_date"]: self._jump_to_date(dd))
            for child in content_frame.winfo_children():
                child.bind("<Button-1>", lambda e, dd=d["diary_date"]: self._jump_to_date(dd))

    def _update_stats(self):
        total = DiaryDB.count_all()

        # 统计本月日记数
        from database import _db
        month_str = f"{self.display_year:04d}-{self.display_month:02d}"
        with _db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM diaries WHERE diary_date LIKE ?",
                (month_str + "%",)
            ).fetchone()
            month_count = row["c"] if row else 0

        self.stats_label.configure(text=f"总计 {total} 篇 | 本月 {month_count} 篇")

    def _jump_to_date(self, date_str):
        try:
            self.selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.display_year = self.selected_date.year
            self.display_month = self.selected_date.month
            self.refresh()
        except ValueError:
            pass

    def _update_word_count(self, event=None):
        content = self.text_content.get("1.0", tk.END).strip()
        count = len(content)
        self.word_count.configure(text=f"{count} 字")

    def _on_search(self):
        self._load_diary_list()

    def _clear_editor(self):
        content = self.entry_title.get().strip() or self.text_content.get("1.0", tk.END).strip()
        if content and not messagebox.askyesno("确认", "清空当前编辑内容？未保存的内容将丢失。"):
            return
        self.entry_title.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)
        self.selected_mood = ""
        self.selected_weather = ""
        for btn, c in self.mood_buttons.values():
            btn.configure(bg=self.theme["card_bg"], relief="flat", highlightthickness=0)
        for btn, c in self.weather_buttons.values():
            btn.configure(bg=self.theme["card_bg"], relief="flat", highlightthickness=0)
        self._update_meta_hint()
        self._update_word_count()

    def _save_diary(self):
        title = self.entry_title.get().strip()
        content = self.text_content.get("1.0", tk.END).strip()

        if not title:
            messagebox.showwarning("提示", "请输入日记标题")
            return

        if not content:
            if not messagebox.askyesno("确认", "日记内容为空，确定保存吗？"):
                return

        ds = self.selected_date.strftime("%Y-%m-%d")
        DiaryDB.save(ds, title, content, self.selected_mood, self.selected_weather)
        self._show_centered_message("日记已保存！")
        self.refresh()

    def _show_centered_message(self, msg):
        top = self.winfo_toplevel()
        dlg = tk.Toplevel(top)
        dlg.title("提示")
        dlg.geometry("300x180")
        dlg.resizable(False, False)
        dlg.transient(top)
        dlg.grab_set()
        dlg.configure(bg=self.theme["card_bg"])

        dlg.update_idletasks()
        x = top.winfo_x() + (top.winfo_width() // 2) - 150
        y = top.winfo_y() + (top.winfo_height() // 2) - 90
        dlg.geometry("+{}+{}".format(x, y))

        tk.Label(dlg, text="✅", font=("Segoe UI Emoji", 18),
                bg=self.theme["card_bg"]).pack(pady=(16, 2))
        tk.Label(dlg, text=msg, font=("Microsoft YaHei UI", 12),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(pady=(0, 10))

        tk.Button(dlg, text="确定", font=("Microsoft YaHei UI", 11, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat",
                 padx=30, pady=6, cursor="hand2",
                 command=dlg.destroy).pack()

        dlg.wait_window()

    def _delete_diary(self):
        ds = self.selected_date.strftime("%Y-%m-%d")
        if not DiaryDB.has_diary(ds):
            messagebox.showinfo("提示", "当天没有日记")
            return
        if messagebox.askyesno("确认", "确定删除这天的日记？"):
            DiaryDB.delete_by_date(ds)
            self._clear_editor()
            self.refresh()

    def _view_all_diaries(self):
        self._all_diaries_dialog = tk.Toplevel(self)
        dialog = self._all_diaries_dialog
        dialog.title("全部日记")
        dialog.geometry("720x560")
        dialog.resizable(True, True)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(bg=self.theme["bg"])

        # 弹窗居中
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w // 2) - 360
        y = parent_y + (parent_h // 2) - 280
        dialog.geometry("+{}+{}".format(x, y))

        # 头部
        header = tk.Frame(dialog, bg=self.theme["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="全部日记",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["primary"], fg="white").pack(pady=(12, 12))

        # 搜索区域
        search_frame = tk.Frame(dialog, bg=self.theme["card_bg"],
                               highlightbackground=self.theme["border"], highlightthickness=1)
        search_frame.pack(fill=tk.X, padx=20, pady=(15, 8))

        search_inner = tk.Frame(search_frame, bg=self.theme["card_bg"])
        search_inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(search_inner, text="🔍", font=("Segoe UI Emoji", 13),
                bg=self.theme["card_bg"]).pack(side=tk.LEFT, padx=(0, 8))

        self.all_search_var = tk.StringVar()
        self.all_search_var.trace_add("write", lambda *a: self._refresh_all_diaries_list())

        search_entry = tk.Entry(search_inner, textvariable=self.all_search_var,
                              font=("Microsoft YaHei UI", 11),
                              highlightbackground=self.theme["border"], highlightthickness=1)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        search_entry.insert(0, self.search_var.get())

        # 统计标签
        self.all_stats_label = tk.Label(dialog, text="", font=("Microsoft YaHei UI", 10),
                                       bg=self.theme["bg"], fg=self.theme["text_secondary"])
        self.all_stats_label.pack(anchor="w", padx=20, pady=(0, 5))

        # 日记列表（滚动区域）
        list_frame = tk.Frame(dialog, bg=self.theme["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        self.all_diaries_canvas = tk.Canvas(list_frame, bg=self.theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.all_diaries_canvas.yview)
        self.all_diaries_inner = tk.Frame(self.all_diaries_canvas, bg=self.theme["bg"])

        self.all_diaries_inner.bind("<Configure>", lambda e: self.all_diaries_canvas.configure(scrollregion=self.all_diaries_canvas.bbox("all")))
        self.all_diaries_canvas.create_window((0, 0), window=self.all_diaries_inner, anchor="nw", tags="inner")
        self.all_diaries_canvas.configure(yscrollcommand=scrollbar.set)
        self.all_diaries_canvas.bind("<Configure>", lambda e: self.all_diaries_canvas.itemconfig("inner", width=e.width))

        self.all_diaries_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮
        def _on_mousewheel(event):
            self.all_diaries_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.all_diaries_canvas.bind("<MouseWheel>", _on_mousewheel)

        self._refresh_all_diaries_list()

    def _refresh_all_diaries_list(self):
        for w in self.all_diaries_inner.winfo_children():
            w.destroy()

        keyword = self.all_search_var.get().strip()
        if keyword:
            diaries = DiaryDB.search(keyword)
        else:
            diaries = DiaryDB.get_all()

        diaries.sort(key=lambda x: x["diary_date"], reverse=True)
        self.all_stats_label.configure(text=f"共 {len(diaries)} 篇日记")

        if not diaries:
            empty = tk.Label(self.all_diaries_inner, text="暂无日记",
                            font=("Microsoft YaHei UI", 12),
                            fg=self.theme["text_secondary"],
                            bg=self.theme["bg"])
            empty.pack(anchor="center", pady=60)
            return

        for d in diaries:
            mood_emoji = ""
            for emoji, label, color in self.MOODS:
                if label == d["mood"]:
                    mood_emoji = emoji
                    break

            weather_emoji = ""
            for emoji, label, color in self.WEATHERS:
                if label == d["weather"]:
                    weather_emoji = emoji
                    break

            # 卡片
            card = tk.Frame(self.all_diaries_inner, bg=self.theme["card_bg"],
                           highlightbackground=self.theme["border"], highlightthickness=1)
            card.pack(fill=tk.X, pady=4, padx=2)

            # hover 效果
            def on_enter(e, f=card):
                f.configure(bg="#f0f4ff")
                for child in f.winfo_children():
                    _set_bg_recursive(child, "#f0f4ff")
            def on_leave(e, f=card):
                f.configure(bg=self.theme["card_bg"])
                for child in f.winfo_children():
                    _set_bg_recursive(child, self.theme["card_bg"])

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            inner = tk.Frame(card, bg=self.theme["card_bg"])
            inner.pack(fill=tk.X, padx=15, pady=12)

            # 第一行：日期 + 心情天气图标
            top_row = tk.Frame(inner, bg=self.theme["card_bg"])
            top_row.pack(fill=tk.X)

            date_lbl = tk.Label(top_row, text=d["diary_date"],
                               font=("Microsoft YaHei UI", 10, "bold"),
                               bg=self.theme["card_bg"], fg=self.theme["primary"])
            date_lbl.pack(side=tk.LEFT)

            icons = []
            if mood_emoji:
                icons.append(mood_emoji)
            if weather_emoji:
                icons.append(weather_emoji)
            if icons:
                tk.Label(top_row, text="  ".join(icons),
                        font=("Segoe UI Emoji", 12),
                        bg=self.theme["card_bg"]).pack(side=tk.RIGHT)

            # 标题
            title_text = d["title"] if d["title"] else "（无标题）"
            title_lbl = tk.Label(inner, text=title_text,
                                font=("Microsoft YaHei UI", 12, "bold"),
                                bg=self.theme["card_bg"], fg=self.theme["text"],
                                anchor="w", justify="left")
            title_lbl.pack(fill=tk.X, pady=(6, 4))

            # 内容预览
            preview = d["content"][:120] + "..." if len(d["content"]) > 120 else d["content"]
            preview_lbl = tk.Label(inner, text=preview or "（无内容）",
                                  font=("Microsoft YaHei UI", 10),
                                  bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                                  anchor="w", justify="left", wraplength=620)
            preview_lbl.pack(fill=tk.X)

            # 绑定点击和悬停事件
            for child in [card, inner, top_row, date_lbl, title_lbl, preview_lbl]:
                child.bind("<Button-1>", lambda e, dd=d: self._show_diary_detail(dd, self._all_diaries_dialog))
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)

    def _show_diary_detail(self, diary, parent_dialog):
        """查看日记详情"""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("日记详情")
        dialog.geometry("500x550")
        dialog.resizable(False, False)
        dialog.transient(parent_dialog)
        dialog.grab_set()
        dialog.configure(bg=self.theme["card_bg"])

        # 居中
        dialog.update_idletasks()
        px = parent_dialog.winfo_x()
        py = parent_dialog.winfo_y()
        pw = parent_dialog.winfo_width()
        ph = parent_dialog.winfo_height()
        dialog.geometry("+{}+{}".format(px + pw // 2 - 250, py + ph // 2 - 275))

        # 头部
        header = tk.Frame(dialog, bg=self.theme["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="日记详情",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["primary"], fg="white").pack(pady=(12, 12))

        # 滚动内容区
        canvas = tk.Canvas(dialog, bg=self.theme["card_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=self.theme["card_bg"])

        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=25, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)

        # 鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # 日期 + 星期
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        try:
            d = datetime.strptime(diary["diary_date"], "%Y-%m-%d").date()
            weekday = day_names[d.weekday()]
        except ValueError:
            weekday = ""

        date_lbl = tk.Label(content_frame, text=diary["diary_date"],
                           font=("Microsoft YaHei UI", 18, "bold"),
                           bg=self.theme["card_bg"], fg=self.theme["text"])
        date_lbl.pack(anchor="w")

        if weekday:
            tk.Label(content_frame, text=weekday,
                    font=("Microsoft YaHei UI", 11),
                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w", pady=(0, 12))

        # 心情 + 天气
        mood_emoji = ""
        mood_label = diary["mood"] or ""
        for emoji, label, color in self.MOODS:
            if label == mood_label:
                mood_emoji = emoji
                break

        weather_emoji = ""
        weather_label = diary["weather"] or ""
        for emoji, label, color in self.WEATHERS:
            if label == weather_label:
                weather_emoji = emoji
                break

        if mood_emoji or weather_emoji:
            meta_parts = []
            if mood_emoji:
                meta_parts.append(f"{mood_emoji} {mood_label}")
            if weather_emoji:
                meta_parts.append(f"{weather_emoji} {weather_label}")
            meta_lbl = tk.Label(content_frame, text="  |  ".join(meta_parts),
                               font=("Microsoft YaHei UI", 11),
                               bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
            meta_lbl.pack(anchor="w", pady=(0, 12))

        # 分隔线
        sep = tk.Frame(content_frame, bg=self.theme["border"], height=1)
        sep.pack(fill=tk.X, pady=(0, 12))

        # 标题
        title_text = diary["title"] if diary["title"] else "（无标题）"
        tk.Label(content_frame, text=title_text,
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text"],
                anchor="w", justify="left", wraplength=430).pack(anchor="w", pady=(0, 12))

        # 正文
        content_text = diary["content"] or "（无内容）"
        tk.Label(content_frame, text=content_text,
                font=("Microsoft YaHei UI", 11),
                bg=self.theme["card_bg"], fg=self.theme["text"],
                anchor="w", justify="left", wraplength=430).pack(anchor="w", fill=tk.X)

        # 底部按钮（固定在弹窗底部）
        btn_frame = tk.Frame(dialog, bg=self.theme["card_bg"])
        btn_frame.pack(fill=tk.X, padx=25, pady=15)

        tk.Button(btn_frame, text="关闭", font=("Microsoft YaHei UI", 11),
                 bg=self.theme["text_secondary"], fg="white", relief="flat",
                 padx=20, pady=6, width=10, cursor="hand2",
                 command=dialog.destroy).pack(side=tk.RIGHT, padx=(10, 0))

        def go_edit():
            dialog.destroy()
            self._open_diary_from_list(diary["diary_date"], parent_dialog)

        tk.Button(btn_frame, text="编辑", font=("Microsoft YaHei UI", 11, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat",
                 padx=20, pady=6, width=10, cursor="hand2",
                 command=go_edit).pack(side=tk.RIGHT)

    def _open_diary_from_list(self, date_str, dialog):
        try:
            self.selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.display_year = self.selected_date.year
            self.display_month = self.selected_date.month
            self.refresh()
            dialog.destroy()
        except ValueError:
            pass
