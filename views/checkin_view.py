import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import CheckinDB


class CheckinView(tk.Frame):

    def __init__(self, parent, theme=None, on_data_change=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f1f5f9")
        self.theme = theme or {
            "bg": "#f1f5f9", "card_bg": "#ffffff", "primary": "#6366f1",
            "success": "#10b981", "danger": "#ef4444", "warning": "#f59e0b",
            "text": "#1e293b", "text_secondary": "#64748b", "border": "#e2e8f0",
            "success_light": "#d1fae5", "danger_light": "#fee2e2",
            "primary_light": "#e0e7ff",
        }
        self.on_data_change = on_data_change
        self.current_date = date.today()
        self._drag_card = None
        self._drag_start_y = 0
        self._card_order = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 头部
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="打卡追踪", font=("Microsoft YaHei UI", 18, "bold"),
                bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  养成好习惯", font=("Microsoft YaHei UI", 10),
                bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        # 第一行：日期导航 + 操作按钮
        row1 = tk.Frame(self, bg=self.theme["bg"])
        row1.pack(fill=tk.X, padx=25, pady=(8, 4))

        # 日期导航
        date_nav = tk.Frame(row1, bg=self.theme["bg"])
        date_nav.pack(side=tk.LEFT)

        tk.Button(date_nav, text="◀", font=("Microsoft YaHei UI", 10), relief="flat",
                 bg=self.theme["card_bg"], cursor="hand2", padx=8, pady=3,
                 command=self._prev_day).pack(side=tk.LEFT)
        self.lbl_date = tk.Label(date_nav, text="", font=("Microsoft YaHei UI", 14, "bold"),
                                bg=self.theme["bg"], fg=self.theme["text"])
        self.lbl_date.pack(side=tk.LEFT, padx=12)
        tk.Button(date_nav, text="▶", font=("Microsoft YaHei UI", 10), relief="flat",
                 bg=self.theme["card_bg"], cursor="hand2", padx=8, pady=3,
                 command=self._next_day).pack(side=tk.LEFT)
        tk.Button(date_nav, text="今天", font=("Microsoft YaHei UI", 10), relief="flat",
                 bg=self.theme["primary"], fg="white", cursor="hand2", padx=14, pady=3,
                 command=self._go_today).pack(side=tk.LEFT, padx=10)
        tk.Button(date_nav, text="任务总览", font=("Microsoft YaHei UI", 10), relief="flat",
                 bg=self.theme["card_bg"], cursor="hand2", padx=10, pady=3,
                 command=self._pick_date).pack(side=tk.LEFT, padx=5)

        # 操作按钮（右侧）
        action_frame = tk.Frame(row1, bg=self.theme["bg"])
        action_frame.pack(side=tk.RIGHT)
        tk.Button(action_frame, text="新建打卡项", font=("Microsoft YaHei UI", 10, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat", padx=14, pady=5,
                 cursor="hand2", command=self._add_checkin_dialog).pack(side=tk.RIGHT, padx=5)
        tk.Button(action_frame, text="批量清除", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["danger"], fg="white", relief="flat", padx=14, pady=5,
                 cursor="hand2", command=self._clear_checkins_dialog).pack(side=tk.RIGHT, padx=5)

        # 统计卡片
        stats_frame = tk.Frame(self, bg=self.theme["bg"])
        stats_frame.pack(fill=tk.X, padx=25, pady=(5, 3))

        self.card_total = self._create_stat_card(stats_frame, "总打卡项", "0", self.theme["primary"])
        self.card_done = self._create_stat_card(stats_frame, "已完成", "0", self.theme["success"])
        self.card_rate = self._create_stat_card(stats_frame, "完成率", "0%", self.theme["warning"])
        self.card_streak = self._create_stat_card(stats_frame, "连续天数", "0", self.theme["danger"])

        # 打卡列表
        card = tk.Frame(self, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=25, pady=(3, 15))

        list_container = tk.Frame(card, bg=self.theme["card_bg"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 15))

        self.checkin_canvas = tk.Canvas(list_container, bg=self.theme["card_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.checkin_canvas.yview)
        self.checkin_inner = tk.Frame(self.checkin_canvas, bg=self.theme["card_bg"])

        self.checkin_inner.bind("<Configure>", lambda e: self.checkin_canvas.configure(scrollregion=self.checkin_canvas.bbox("all")))
        self.checkin_canvas.create_window((0, 0), window=self.checkin_inner, anchor="nw", tags="inner")
        self.checkin_canvas.configure(yscrollcommand=scrollbar.set)
        self.checkin_canvas.bind("<Configure>", lambda e: self.checkin_canvas.itemconfig("inner", width=e.width))

        self.checkin_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_stat_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        tk.Label(card, text=title, bg=self.theme["card_bg"], font=("Microsoft YaHei UI", 9),
                fg=self.theme["text_secondary"]).pack(pady=(8, 0))
        value_label = tk.Label(card, text=value, bg=self.theme["card_bg"], font=("Microsoft YaHei UI", 18, "bold"),
                             fg=color)
        value_label.pack(pady=(0, 8))
        return value_label

    def refresh(self):
        self._update_date_label()
        self._load_checkins()
        self._update_stats()
        if self.on_data_change:
            self.on_data_change()

    def _update_date_label(self):
        day_name = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][self.current_date.weekday()]
        self.lbl_date.configure(text=f"{self.current_date.strftime('%Y-%m-%d')} {day_name}")

    def _prev_day(self):
        self.current_date -= timedelta(days=1)
        self.refresh()

    def _next_day(self):
        self.current_date += timedelta(days=1)
        self.refresh()

    def _go_today(self):
        self.current_date = date.today()
        self.refresh()

    def _clear_checkins_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("批量清除打卡项")
        dialog.geometry("400x340")
        dialog.resizable(False, False)
        dialog.configure(bg=self.theme["card_bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 弹窗居中显示
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w // 2) - 200
        y = parent_y + (parent_h // 2) - 170
        dialog.geometry("+{}+{}".format(x, y))

        # 头部
        header = tk.Frame(dialog, bg=self.theme["danger"])
        header.pack(fill=tk.X)
        tk.Label(header, text="⚠ 批量清除打卡项",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["danger"], fg="white").pack(pady=(15, 15))

        # 表单区域
        form = tk.Frame(dialog, bg=self.theme["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=30, pady=(15, 5))

        tk.Label(form, text="请选择清除方式：",
                font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w", pady=(0, 5))

        clear_var = tk.StringVar(value="")

        # 选项卡片容器
        options_frame = tk.Frame(form, bg=self.theme["card_bg"])
        options_frame.pack(fill=tk.X)

        def make_option(parent, text, value, icon):
            opt_frame = tk.Frame(parent, bg=self.theme["card_bg"],
                                highlightbackground=self.theme["border"], highlightthickness=1)
            opt_frame.pack(fill=tk.X, pady=4)
            rb = tk.Radiobutton(opt_frame, text=f"  {icon}  {text}", variable=clear_var, value=value,
                               font=("Microsoft YaHei UI", 11), bg=self.theme["card_bg"],
                               selectcolor=self.theme["primary_light"], padx=10, pady=8,
                               activebackground=self.theme["card_bg"])
            rb.pack(fill=tk.X)
            return rb

        make_option(options_frame, "清除当月所有周期性打卡项", "monthly_repeat", "📅")
        make_option(options_frame, "清除本周所有打卡项", "weekly_all", "📋")

        def do_clear():
            option = clear_var.get()
            if not option:
                messagebox.showwarning("提示", "请选择清除方式", parent=dialog)
                return

            if not messagebox.askyesno("⚠️ 危险操作确认", "确定要清除所选数据吗？此操作不可恢复！", parent=dialog):
                return

            count = 0
            if option == "monthly_repeat":
                first_day = self.current_date.replace(day=1)
                if self.current_date.month == 12:
                    last_day = self.current_date.replace(year=self.current_date.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    last_day = self.current_date.replace(month=self.current_date.month+1, day=1) - timedelta(days=1)
                count = CheckinDB.delete_repeat_in_range(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
                messagebox.showinfo("成功", f"已清除 {count} 个周期性打卡项", parent=dialog)
            else:
                weekday = self.current_date.weekday()
                start_of_week = self.current_date - timedelta(days=weekday)
                end_of_week = start_of_week + timedelta(days=6)
                count = CheckinDB.delete_in_range(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))
                messagebox.showinfo("成功", f"已清除 {count} 个打卡项", parent=dialog)

            dialog.destroy()
            self.refresh()

        # 按钮区域
        btn_frame = tk.Frame(form, bg=self.theme["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        cancel_btn = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                              bg=self.theme["text_secondary"], fg="white", relief="flat",
                              padx=25, pady=8, width=10, cursor="hand2", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        clear_btn = tk.Button(btn_frame, text="确认清除", font=("Microsoft YaHei UI", 11, "bold"),
                             bg=self.theme["danger"], fg="white", relief="flat",
                             padx=25, pady=8, width=10, cursor="hand2", command=do_clear)
        clear_btn.pack(side=tk.RIGHT)

    def _pick_date(self):
        today = date.today()
        init = self.current_date

        picker = tk.Toplevel(self)
        picker.title("选择日期")
        picker.geometry("370x390")
        picker.resizable(False, False)
        picker.configure(bg=self.theme["card_bg"])
        picker.transient(self.winfo_toplevel())
        picker.grab_set()

        picker.update_idletasks()
        top = self.winfo_toplevel()
        px = top.winfo_x() + top.winfo_width() // 2 - 185
        py = top.winfo_y() + top.winfo_height() // 2 - 195
        picker.geometry("+{}+{}".format(px, py))

        pick_year = [init.year]
        pick_month = [init.month]

        # 月份导航
        nav = tk.Frame(picker, bg=self.theme["card_bg"])
        nav.pack(fill=tk.X, padx=15, pady=(10, 5))

        def prev_m():
            pick_month[0] -= 1
            if pick_month[0] < 1:
                pick_month[0] = 12
                pick_year[0] -= 1
            draw()

        def next_m():
            pick_month[0] += 1
            if pick_month[0] > 12:
                pick_month[0] = 1
                pick_year[0] += 1
            draw()

        tk.Button(nav, text="◀", font=("Segoe UI", 10), relief="flat",
                  bg=self.theme["card_bg"], cursor="hand2", command=prev_m).pack(side=tk.LEFT)
        lbl_month = tk.Label(nav, text="", font=("Microsoft YaHei UI", 12, "bold"),
                             bg=self.theme["card_bg"], fg=self.theme["text"])
        lbl_month.pack(side=tk.LEFT, expand=True)
        tk.Button(nav, text="▶", font=("Segoe UI", 10), relief="flat",
                  bg=self.theme["card_bg"], cursor="hand2", command=next_m).pack(side=tk.RIGHT)

        # 日历网格
        grid = tk.Frame(picker, bg=self.theme["card_bg"])
        grid.pack(fill=tk.BOTH, expand=True, padx=15)

        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for i, wd in enumerate(weekdays):
            tk.Label(grid, text=wd, font=("Microsoft YaHei UI", 9, "bold"),
                     bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                     width=5).grid(row=0, column=i, pady=(0, 4))
            grid.columnconfigure(i, weight=1)
        for ri in range(7):
            grid.rowconfigure(ri, weight=1)

        # 一次性创建 6x7=42 个格子，之后只更新内容和颜色
        cells = []
        for ri in range(6):
            row = []
            for ci in range(7):
                lbl = tk.Label(grid, text="", font=("Microsoft YaHei UI", 10),
                               bg=self.theme["card_bg"], fg=self.theme["text"],
                               width=5, height=1, cursor="hand2")
                lbl.grid(row=ri + 1, column=ci, padx=3, pady=3, sticky="nsew")
                row.append(lbl)
            cells.append(row)

        def draw():
            lbl_month.configure(text="{}年{}月".format(pick_year[0], pick_month[0]))
            cal = calendar.monthcalendar(pick_year[0], pick_month[0])

            for ri in range(6):
                for ci in range(7):
                    lbl = cells[ri][ci]
                    lbl.unbind("<Button-1>")

                    if ri < len(cal) and ci < len(cal[ri]) and cal[ri][ci] != 0:
                        day_num = cal[ri][ci]
                        d = date(pick_year[0], pick_month[0], day_num)
                        ds = d.strftime("%Y-%m-%d")

                        bg = self.theme["card_bg"]
                        fg = self.theme["text"]

                        # 查询打卡记录
                        items = CheckinDB.get_by_date(ds)
                        if items:
                            if any(item["status"] for item in items):
                                bg = "#10b981"
                            else:
                                bg = "#b0b8c4"
                            fg = "#ffffff"

                        # 今天：最后判断，优先级最高
                        if d == today:
                            bg = "#3b82f6"
                            fg = "#ffffff"

                        lbl.configure(text=str(day_num), bg=bg, fg=fg)
                        lbl.bind("<Button-1>",
                                 lambda ev, _d=d: (setattr(self, 'current_date', _d),
                                                   self.refresh(), picker.destroy()))
                    else:
                        lbl.configure(text="", bg=self.theme["card_bg"])

        # 底部按钮
        btn_frame = tk.Frame(picker, bg=self.theme["card_bg"])
        btn_frame.pack(fill=tk.X, padx=15, pady=(5, 10))
        tk.Button(btn_frame, text="今天", font=("Microsoft YaHei UI", 10),
                  bg=self.theme["primary_light"], fg=self.theme["primary"],
                  relief="flat", padx=12, pady=3, cursor="hand2",
                  command=lambda: (setattr(self, 'current_date', today),
                                   self.refresh(), picker.destroy())).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="关闭", font=("Microsoft YaHei UI", 10),
                  bg=self.theme["text_secondary"], fg="white",
                  relief="flat", padx=12, pady=3, cursor="hand2",
                  command=picker.destroy).pack(side=tk.RIGHT)

        draw()

    def _load_checkins(self):
        for w in self.checkin_inner.winfo_children():
            w.destroy()
        self._card_order = []

        date_str = self.current_date.strftime("%Y-%m-%d")
        checkins = CheckinDB.get_by_date(date_str)

        if not checkins:
            empty = tk.Label(self.checkin_inner, text='📭 当天暂无打卡项\n点击「新建打卡项」开始追踪习惯',
                            font=("Microsoft YaHei UI", 11), fg=self.theme["text_secondary"],
                            bg=self.theme["card_bg"], justify="center")
            empty.pack(anchor="center", pady=50)
            return

        for c in checkins:
            self._create_checkin_card(c)

    def _repack_cards(self):
        """只移动被拖拽的卡片到目标位置，避免全部重排导致闪烁"""
        drag_card = self._drag_card
        if not drag_card:
            return
        target_idx = next(i for i, (c, _) in enumerate(self._card_order) if c == drag_card)
        drag_card.pack_forget()
        if target_idx + 1 < len(self._card_order):
            drag_card.pack(in_=self.checkin_inner, before=self._card_order[target_idx + 1][0],
                          fill=tk.X, padx=5, pady=3)
        else:
            drag_card.pack(in_=self.checkin_inner, fill=tk.X, padx=5, pady=3)

    def _create_checkin_card(self, checkin):
        is_done = checkin["status"]
        bg = self.theme["success_light"] if is_done else self.theme["card_bg"]

        card = tk.Frame(self.checkin_inner, bg=bg, relief="flat", borderwidth=1,
                       highlightbackground=self.theme["border"], highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=3)

        # 拖拽手柄
        drag_handle = tk.Label(card, text="⠿", bg=bg, fg=self.theme["text_secondary"],
                               font=("Segoe UI", 14), cursor="fleur", padx=2)
        drag_handle.pack(side=tk.LEFT, fill=tk.Y)

        self._card_order.append((card, checkin["id"]))

        # 拖拽事件
        def on_drag_start(e, c=card):
            self._drag_card = c
            self._drag_start_y = e.y_root
            c.configure(highlightbackground=self.theme["primary"], highlightthickness=2)

        def on_drag_motion(e):
            if not self._drag_card:
                return
            drag_y = e.y_root
            target_idx = None
            for i, (c, _) in enumerate(self._card_order):
                if c == self._drag_card:
                    continue
                cy = c.winfo_rooty() + c.winfo_height() // 2
                if drag_y < cy:
                    target_idx = i
                    break
            if target_idx is not None:
                cur_idx = next(i for i, (c, _) in enumerate(self._card_order) if c == self._drag_card)
                if cur_idx != target_idx:
                    item = self._card_order.pop(cur_idx)
                    self._card_order.insert(target_idx, item)
                    self._repack_cards()

        def on_drag_end(e):
            if not self._drag_card:
                return
            self._drag_card.configure(highlightbackground=self.theme["border"], highlightthickness=1)
            self._drag_card = None
            from database import CheckinDB
            for i, (_, cid) in enumerate(self._card_order):
                CheckinDB.update_sort_order(cid, i)

        drag_handle.bind("<Button-1>", on_drag_start)
        drag_handle.bind("<B1-Motion>", on_drag_motion)
        drag_handle.bind("<ButtonRelease-1>", on_drag_end)

        inner = tk.Frame(card, bg=bg)
        inner.pack(fill=tk.X, padx=10, pady=8)

        status_btn = tk.Label(inner, text="✅" if is_done else "⬜", bg=bg,
                            font=("Segoe UI Emoji", 16), cursor="hand2")
        status_btn.pack(side=tk.LEFT)
        status_btn.bind("<Button-1>", lambda e, cid=checkin["id"]: self._toggle_checkin(cid))

        content = tk.Frame(inner, bg=bg)
        content.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        title_fg = self.theme["success"] if is_done else self.theme["text"]
        tk.Label(content, text=checkin["task_title"], bg=bg,
                font=("Microsoft YaHei UI", 11, "bold"), fg=title_fg, anchor="w").pack(anchor="w")

        # 显示描述
        note = checkin["note"] if "note" in checkin.keys() else ""
        if note:
            tk.Label(content, text=note, bg=bg,
                    font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"], anchor="w").pack(anchor="w")

        # 显示循环时间
        repeat = checkin["repeat"] if "repeat" in checkin.keys() else ""
        if repeat:
            repeat_text = "🔄 " + repeat
            tk.Label(content, text=repeat_text, bg=bg,
                    font=("Microsoft YaHei UI", 9), fg=self.theme["primary"], anchor="w").pack(anchor="w")

        status_text = "✅ 已打卡" if is_done else "❌ 未打卡"
        time_text = f"  ⏰ {checkin['checkin_time']}" if checkin["checkin_time"] and is_done else ""
        tk.Label(content, text=f"{status_text}{time_text}", bg=bg,
                font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"], anchor="w").pack(anchor="w")

        del_btn = tk.Label(inner, text="🗑", bg=bg, font=("Segoe UI Emoji", 12), cursor="hand2", fg=self.theme["danger"])
        del_btn.pack(side=tk.RIGHT, padx=5)
        del_btn.bind("<Button-1>", lambda e, cid=checkin["id"]: self._delete_checkin(cid))

    def _toggle_checkin(self, checkin_id):
        from database import _db
        with _db() as conn:
            row = conn.execute("SELECT status FROM checkins WHERE id=?", (checkin_id,)).fetchone()
            old_status = row["status"] if row else 0
            new_status = 1 - old_status
            now = datetime.now().strftime("%H:%M:%S") if new_status else ""
            conn.execute(
                "UPDATE checkins SET status=?, checkin_time=? WHERE id=?",
                (new_status, now, checkin_id)
            )
        self.refresh()

    def _delete_checkin(self, checkin_id):
        if messagebox.askyesno("确认", "确定删除此打卡项？"):
            CheckinDB.delete(checkin_id)
            self.refresh()

    def _add_checkin_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("新建打卡项")
        dialog.geometry("480x900")
        dialog.resizable(False, False)
        dialog.configure(bg=self.theme["card_bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 头部
        header = tk.Frame(dialog, bg=self.theme["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="➕ 新建打卡项", font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["primary"], fg="white").pack(pady=(15, 15))

        # 操作按钮 - 先放到底部
        btn_frame = tk.Frame(dialog, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 15))

        form = tk.Frame(dialog, bg=self.theme["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # 打卡项名称
        label_frame = tk.Frame(form, bg=self.theme["card_bg"])
        label_frame.pack(fill=tk.X, pady=(8, 0))
        tk.Label(label_frame, text="打卡项目名称", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(label_frame, text="*", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["danger"]).pack(side=tk.LEFT)
        entry_title = tk.Entry(form, font=("Microsoft YaHei UI", 11),
                              highlightbackground=self.theme["border"], highlightthickness=1)
        entry_title.pack(fill=tk.X, ipady=5)
        entry_title.focus_set()

        # 描述输入框
        desc_label_frame = tk.Frame(form, bg=self.theme["card_bg"])
        desc_label_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Label(desc_label_frame, text="描述", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(side=tk.LEFT)

        desc_container = tk.Frame(form, bg=self.theme["card_bg"])
        desc_container.pack(fill=tk.X)

        text_desc = tk.Text(desc_container, font=("Microsoft YaHei UI", 11),
                           highlightbackground=self.theme["border"], highlightthickness=1,
                           height=3, wrap=tk.WORD, padx=10, pady=8)
        text_desc.pack(fill=tk.X)

        # 日期字段：输入框 + 日历图标按钮
        date_label_frame = tk.Frame(form, bg=self.theme["card_bg"])
        date_label_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Label(date_label_frame, text="日期", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(side=tk.LEFT)

        date_frame = tk.Frame(form, bg=self.theme["card_bg"])
        date_frame.pack(fill=tk.X)
        entry_date = tk.Entry(date_frame, font=("Microsoft YaHei UI", 11),
                             highlightbackground=self.theme["border"], highlightthickness=1,
                             width=20)
        entry_date.insert(0, self.current_date.strftime("%Y-%m-%d"))
        entry_date.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        # 日历图标按钮
        cal_btn = tk.Button(date_frame, text="📅", font=("Segoe UI Emoji", 12),
                           bg=self.theme["primary_light"], fg=self.theme["primary"],
                           relief=tk.FLAT, padx=8, command=lambda: show_date_picker(entry_date))
        cal_btn.pack(side=tk.RIGHT, padx=(5, 0))

        def show_date_picker(entry_widget):
            today = date.today()
            dp = tk.Toplevel(dialog)
            dp.title("选择日期")
            dp.geometry("370x390")
            dp.resizable(False, False)
            dp.configure(bg=self.theme["card_bg"])
            dp.transient(dialog)
            dp.grab_set()
            dp.update_idletasks()
            px, py = dialog.winfo_x(), dialog.winfo_y()
            pw, ph = dialog.winfo_width(), dialog.winfo_height()
            dp.geometry("+{}+{}".format(px + pw // 2 - 185, py + ph // 2 - 195))

            py_ = [today.year]
            pm_ = [today.month]
            nav = tk.Frame(dp, bg=self.theme["card_bg"])
            nav.pack(fill=tk.X, padx=15, pady=(10, 5))

            def prev():
                pm_[0] -= 1
                if pm_[0] < 1: pm_[0] = 12; py_[0] -= 1
                draw()
            def next():
                pm_[0] += 1
                if pm_[0] > 12: pm_[0] = 1; py_[0] += 1
                draw()

            tk.Button(nav, text="◀", font=("Segoe UI", 10), relief="flat",
                      bg=self.theme["card_bg"], cursor="hand2", command=prev).pack(side=tk.LEFT)
            lbl = tk.Label(nav, text="", font=("Microsoft YaHei UI", 12, "bold"),
                           bg=self.theme["card_bg"], fg=self.theme["text"])
            lbl.pack(side=tk.LEFT, expand=True)
            tk.Button(nav, text="▶", font=("Segoe UI", 10), relief="flat",
                      bg=self.theme["card_bg"], cursor="hand2", command=next).pack(side=tk.RIGHT)

            grid = tk.Frame(dp, bg=self.theme["card_bg"])
            grid.pack(fill=tk.BOTH, expand=True, padx=15)
            for i, dd in enumerate(["一","二","三","四","五","六","日"]):
                tk.Label(grid, text=dd, font=("Microsoft YaHei UI", 9, "bold"),
                         bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                         width=5).grid(row=0, column=i, pady=(0, 4))
                grid.columnconfigure(i, weight=1)
            for ri in range(7):
                grid.rowconfigure(ri, weight=1)

            cells = []
            for ri in range(6):
                row = []
                for ci in range(7):
                    c = tk.Label(grid, text="", font=("Microsoft YaHei UI", 10),
                                 bg=self.theme["card_bg"], fg=self.theme["text"],
                                 width=5, height=1, cursor="hand2")
                    c.grid(row=ri + 1, column=ci, padx=3, pady=3, sticky="nsew")
                    row.append(c)
                cells.append(row)

            def draw():
                lbl.configure(text="{}年{}月".format(py_[0], pm_[0]))
                cal = calendar.monthcalendar(py_[0], pm_[0])
                for ri in range(6):
                    for ci in range(7):
                        cl = cells[ri][ci]
                        cl.unbind("<Button-1>")
                        if ri < len(cal) and ci < len(cal[ri]) and cal[ri][ci] != 0:
                            day_num = cal[ri][ci]
                            d = date(py_[0], pm_[0], day_num)
                            bg = "#3b82f6" if d == today else self.theme["card_bg"]
                            fg = "#ffffff" if d == today else self.theme["text"]
                            cl.configure(text=str(day_num), bg=bg, fg=fg)
                            cl.bind("<Button-1>", lambda e, x=d: (entry_widget.delete(0, tk.END), entry_widget.insert(0, x.strftime("%Y-%m-%d")), dp.destroy()))
                        else:
                            cl.configure(text="", bg=self.theme["card_bg"])

            bf = tk.Frame(dp, bg=self.theme["card_bg"])
            bf.pack(fill=tk.X, padx=15, pady=(5, 10))
            tk.Button(bf, text="今天", font=("Microsoft YaHei UI", 10),
                      bg=self.theme["primary_light"], fg=self.theme["primary"],
                      relief="flat", padx=12, pady=3, cursor="hand2",
                      command=lambda: (entry_widget.delete(0, tk.END), entry_widget.insert(0, today.strftime("%Y-%m-%d")), dp.destroy())).pack(side=tk.LEFT)
            tk.Button(bf, text="关闭", font=("Microsoft YaHei UI", 10),
                      bg=self.theme["text_secondary"], fg="white",
                      relief="flat", padx=12, pady=3, cursor="hand2",
                      command=dp.destroy).pack(side=tk.RIGHT)
            draw()

        # 重复周期
        repeat_frame = tk.LabelFrame(form, text=" 重复周期 ", font=("Microsoft YaHei UI", 10),
                                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        repeat_frame.pack(fill=tk.X, pady=(12, 0))

        repeat_var = tk.StringVar(value="none")
        week_day_vars = []

        # 不重复
        rb_none = tk.Radiobutton(repeat_frame, text="不重复", variable=repeat_var, value="none",
                               font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"],
                               selectcolor=self.theme["primary_light"])
        rb_none.pack(anchor="w", padx=10, pady=2)

        # 本周工作日
        rb_weekday = tk.Radiobutton(repeat_frame, text="本周所有工作日", variable=repeat_var, value="weekday",
                                   font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"],
                                   selectcolor=self.theme["primary_light"])
        rb_weekday.pack(anchor="w", padx=10, pady=2)

        # 每周指定日期（当月内）
        rb_custom = tk.Radiobutton(repeat_frame, text="每周指定日期（当月内）", variable=repeat_var, value="custom",
                                  font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"],
                                  selectcolor=self.theme["primary_light"])
        rb_custom.pack(anchor="w", padx=10, pady=2)

        # 星期选择（始终显示）
        tk.Label(repeat_frame, text="选择星期：", font=("Microsoft YaHei UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w", padx=20, pady=(5, 0))

        week_days = [("一", 0), ("二", 1), ("三", 2), ("四", 3), ("五", 4), ("六", 5), ("日", 6)]

        # 第一行：周一到周四
        row1 = tk.Frame(repeat_frame, bg=self.theme["card_bg"])
        row1.pack(fill=tk.X, padx=20, pady=(2, 0))
        for day_name, day_num in week_days[:4]:
            var = tk.IntVar(value=0)
            week_day_vars.append((day_num, var))
            tk.Checkbutton(row1, text=f"周{day_name}", variable=var,
                          font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"]).pack(side=tk.LEFT, padx=8)

        # 第二行：周五到周日
        row2 = tk.Frame(repeat_frame, bg=self.theme["card_bg"])
        row2.pack(fill=tk.X, padx=20, pady=(2, 8))
        for day_name, day_num in week_days[4:]:
            var = tk.IntVar(value=0)
            week_day_vars.append((day_num, var))
            tk.Checkbutton(row2, text=f"周{day_name}", variable=var,
                          font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"]).pack(side=tk.LEFT, padx=8)


        def save():
            title = entry_title.get().strip()
            if not title:
                messagebox.showwarning("提示", "请输入打卡项名称", parent=dialog)
                return

            target_date_str = entry_date.get().strip()
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("提示", "日期格式不正确，请使用 YYYY-MM-DD", parent=dialog)
                return

            # 获取描述
            description = text_desc.get("1.0", tk.END).strip()

            repeat_type = repeat_var.get()
            repeat_text = ""
            count = 0

            if repeat_type == "weekday":
                # 本周工作日
                repeat_text = "本周工作日"
                weekday = target_date.weekday()
                start_of_week = target_date - timedelta(days=weekday)
                for i in range(5):
                    d = start_of_week + timedelta(days=i)
                    if CheckinDB.add_task(title, d.strftime("%Y-%m-%d"), description, repeat_text):
                        count += 1
                messagebox.showinfo("成功", f"已创建 {count} 个打卡项（本周工作日）", parent=dialog)
            elif repeat_type == "custom":
                # 每周指定日期 - 在当月范围内生效
                selected_days = [day_num for day_num, var in week_day_vars if var.get() == 1]
                if not selected_days:
                    messagebox.showwarning("提示", "请选择至少一个星期日期", parent=dialog)
                    return

                week_day_names = ["一", "二", "三", "四", "五", "六", "日"]
                selected_day_names = [f"周{week_day_names[d]}" for d in selected_days]
                repeat_text = ", ".join(selected_day_names)

                # 获取当月第一天和最后一天
                first_day = target_date.replace(day=1)
                if target_date.month == 12:
                    last_day = target_date.replace(year=target_date.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    last_day = target_date.replace(month=target_date.month+1, day=1) - timedelta(days=1)

                current_day = first_day
                while current_day <= last_day:
                    if current_day.weekday() in selected_days:
                        if CheckinDB.add_task(title, current_day.strftime("%Y-%m-%d"), description, repeat_text):
                            count += 1
                    current_day += timedelta(days=1)

                messagebox.showinfo("成功", f"已在当月创建 {count} 个打卡项（{repeat_text}）", parent=dialog)
            else:
                # 不重复
                result = CheckinDB.add_task(title, target_date_str, description, "")
                if not result:
                    messagebox.showinfo("提示", f"日期 {target_date_str} 已存在名为 \"{title}\" 的打卡项", parent=dialog)
                    return
                count = 1
                messagebox.showinfo("成功", "打卡项已创建！", parent=dialog)

            dialog.destroy()
            self.refresh()

        tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                 bg=self.theme["bg"], fg=self.theme["text_secondary"], relief="flat",
                 padx=14, pady=5, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="保存", font=("Microsoft YaHei UI", 11, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat",
                 padx=14, pady=5, cursor="hand2", command=save).pack(side=tk.RIGHT, padx=5)

        # 弹窗居中显示
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w // 2) - 240
        y = parent_y + (parent_h // 2) - 450
        dialog.geometry("+{}+{}".format(x, y))

        dialog.wait_window()

    def _update_stats(self):
        date_str = self.current_date.strftime("%Y-%m-%d")
        checkins = CheckinDB.get_by_date(date_str)
        total = len(checkins)
        done = sum(1 for c in checkins if c["status"])
        rate = done / total * 100 if total > 0 else 0

        self.card_total.configure(text=str(total))
        self.card_done.configure(text=str(done))
        self.card_rate.configure(text=f"{rate:.0f}%")

        streak = self._calc_streak()
        self.card_streak.configure(text=str(streak))

    def _calc_streak(self):
        # 批量查询最近 365 天的打卡记录，避免每天一次查询
        today = date.today()
        start = (today - timedelta(days=364)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        all_checkins = CheckinDB.get_range(start, end)

        # 按日期分组
        from collections import defaultdict
        daily = defaultdict(list)
        for c in all_checkins:
            daily[c["checkin_date"]].append(c)

        streak = 0
        d = today
        while True:
            date_str = d.strftime("%Y-%m-%d")
            day_checkins = daily.get(date_str, [])
            if not day_checkins:
                break
            if not any(c["status"] for c in day_checkins):
                break
            streak += 1
            d -= timedelta(days=1)
        return streak
