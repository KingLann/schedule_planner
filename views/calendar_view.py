import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
import sys, os


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import ScheduleDB
from utils.app_settings import get_setting, set_setting


class CalendarView(tk.Frame):

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
        self._drag_card = None
        self._drag_start_y = 0
        self._card_order = []  # 拖拽排序用: [(card_widget, schedule_id), ...]
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="📅 日程管理", font=("Microsoft YaHei UI", 18, "bold"),
                bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  规划每一天的行程", font=("Microsoft YaHei UI", 10),
                bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        body = tk.Frame(self, bg=self.theme["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=(5, 20))

        saved_width = get_setting("calendar_panel_width", 340)
        left_panel = tk.Frame(body, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                             highlightthickness=1, width=saved_width)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)

        # 可拖拽的分隔条
        splitter = tk.Frame(body, bg=self.theme["border"], width=6, cursor="sb_h_double_arrow")
        splitter.pack(side=tk.LEFT, fill=tk.Y, padx=0)
        self._splitter = splitter
        self._left_panel = left_panel
        self._splitter_bind_events()

        right_panel = tk.Frame(body, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                              highlightthickness=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_calendar(left_panel)
        self._build_schedule_list(right_panel)

    def _splitter_bind_events(self):
        self._drag_start_x = 0
        self._drag_start_width = 340
        self._splitter.bind("<Button-1>", self._on_splitter_press)
        self._splitter.bind("<B1-Motion>", self._on_splitter_drag)
        self._splitter.bind("<ButtonRelease-1>", self._on_splitter_release)
        # 悬停高亮
        self._splitter.bind("<Enter>", lambda e: self._splitter.configure(bg=self.theme["primary"]))
        self._splitter.bind("<Leave>", lambda e: self._splitter.configure(bg=self.theme["border"]))

    def _on_splitter_press(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_width = self._left_panel.winfo_width()
        self._splitter.configure(bg=self.theme["primary"])

    def _on_splitter_drag(self, event):
        dx = event.x_root - self._drag_start_x
        new_width = self._drag_start_width + dx
        new_width = max(200, min(new_width, 600))
        self._left_panel.configure(width=new_width)

    def _on_splitter_release(self, event):
        self._splitter.configure(bg=self.theme["border"])
        set_setting("calendar_panel_width", self._left_panel.winfo_width())

    def _build_calendar(self, parent):
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

        self.cal_grid = tk.Frame(parent, bg=self.theme["card_bg"])
        self.cal_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        days = ["一", "二", "三", "四", "五", "六", "日"]
        for i, d in enumerate(days):
            tk.Label(self.cal_grid, text=d, font=("Microsoft YaHei UI", 9, "bold"),
                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                    width=5).grid(row=0, column=i, pady=(0, 4))
            self.cal_grid.columnconfigure(i, weight=1)
        for ri in range(7):
            self.cal_grid.rowconfigure(ri, weight=1)

        # 预分配 6x7=42 个格子
        self.cal_cells = []
        for ri in range(6):
            row = []
            for ci in range(7):
                lbl = tk.Label(self.cal_grid, text="",
                               font=("Microsoft YaHei UI", 10),
                               bg=self.theme["card_bg"], fg=self.theme["text"],
                               width=5, height=1, cursor="hand2")
                lbl.grid(row=ri + 1, column=ci, padx=2, pady=2, sticky="nsew")
                row.append(lbl)
            self.cal_cells.append(row)

        self.day_buttons = {}
        self.info_label = tk.Label(parent, text="", font=("Microsoft YaHei UI", 9),
                                  bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.info_label.pack(fill=tk.X, padx=10, pady=(5, 2))

        # 倒计时提醒区域
        remind_sep = tk.Frame(parent, bg=self.theme["border"], height=1)
        remind_sep.pack(fill=tk.X, padx=10, pady=2)

        tk.Label(parent, text="⏰ 倒计时提醒", font=("Microsoft YaHei UI", 9, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w", padx=10, pady=(4, 0))

        self.remind_container = tk.Frame(parent, bg=self.theme["card_bg"])
        self.remind_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))

    def _build_schedule_list(self, parent):
        list_header = tk.Frame(parent, bg=self.theme["card_bg"])
        list_header.pack(fill=tk.X, padx=15, pady=(12, 5))

        self.lbl_selected_date = tk.Label(list_header, text="", font=("Microsoft YaHei UI", 14, "bold"),
                                         bg=self.theme["card_bg"], fg=self.theme["text"])
        self.lbl_selected_date.pack(side=tk.LEFT)

        tk.Button(list_header, text="➕ 添加日程", font=("Microsoft YaHei UI", 10, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat", padx=12, pady=4,
                 cursor="hand2", command=self._add_schedule_dialog).pack(side=tk.RIGHT)

        sep = tk.Frame(parent, bg=self.theme["border"], height=1)
        sep.pack(fill=tk.X, padx=15, pady=5)

        list_container = tk.Frame(parent, bg=self.theme["card_bg"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.schedule_canvas = tk.Canvas(list_container, bg=self.theme["card_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.schedule_canvas.yview)
        self.schedule_inner = tk.Frame(self.schedule_canvas, bg=self.theme["card_bg"])

        self.schedule_inner.bind("<Configure>",
                                 lambda e: self.schedule_canvas.configure(scrollregion=self.schedule_canvas.bbox("all")))
        self.schedule_canvas.create_window((0, 0), window=self.schedule_inner, anchor="nw", tags="inner")
        self.schedule_canvas.configure(yscrollcommand=scrollbar.set)
        self.schedule_canvas.bind("<Configure>",
                                  lambda e: self.schedule_canvas.itemconfig("inner", width=e.width))

        self.schedule_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self):
        self._draw_calendar()
        self._load_schedules()
        self._load_reminders()

    def _load_reminders(self):
        for w in self.remind_container.winfo_children():
            w.destroy()

        today = date.today()
        # 获取未来7天内未完成的日程
        end_date = today + timedelta(days=7)
        schedules = ScheduleDB.get_range(today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        pending = [s for s in schedules if not s["is_done"]]
        pending.sort(key=lambda s: (s["schedule_date"], s["start_time"] or ""))

        if not pending:
            tk.Label(self.remind_container, text="暂无待办日程",
                    font=("Microsoft YaHei UI", 9), bg=self.theme["card_bg"],
                    fg=self.theme["text_secondary"]).pack(anchor="w", pady=4)
            return

        for s in pending[:5]:
            countdown = self._calc_countdown(s["schedule_date"], s["start_time"])
            if not countdown:
                continue

            pri = s["priority"]
            if pri >= 3:
                bg, fg, icon = "#fef2f2", "#dc2626", "🔥"
            elif pri >= 2:
                bg, fg, icon = "#fffbeb", "#d97706", "⚡"
            else:
                bg, fg, icon = "#f0fdf4", "#16a34a", "📌"

            row = tk.Frame(self.remind_container, bg=bg, padx=4, pady=2)
            row.pack(fill=tk.X, pady=1)

            date_diff = (datetime.strptime(s["schedule_date"], "%Y-%m-%d").date() - today).days
            if date_diff == 0:
                day_text = "今天"
            elif date_diff == 1:
                day_text = "明天"
            else:
                day_text = f"{date_diff}天后"

            tk.Label(row, text=f"{icon} {s['title'][:10]}", font=("Microsoft YaHei UI", 8, "bold"),
                    bg=bg, fg=fg, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=f"{day_text} · {countdown}", font=("Microsoft YaHei UI", 8),
                    bg=bg, fg=fg).pack(side=tk.RIGHT)

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
        self.lbl_month.configure(text=f"{self.display_year}年{self.display_month}月")
        self.day_buttons.clear()

        cal = calendar.monthcalendar(self.display_year, self.display_month)
        today = date.today()

        # 批量查询当月所有日期的日程汇总
        last_day = calendar.monthrange(self.display_year, self.display_month)[1]
        month_start = date(self.display_year, self.display_month, 1).strftime("%Y-%m-%d")
        month_end = date(self.display_year, self.display_month, last_day).strftime("%Y-%m-%d")
        month_summary = ScheduleDB.get_month_summary(month_start, month_end)

        for ri in range(6):
            for ci in range(7):
                lbl = self.cal_cells[ri][ci]
                lbl.unbind("<Button-1>")

                if ri < len(cal) and ci < len(cal[ri]) and cal[ri][ci] != 0:
                    day_num = cal[ri][ci]
                    d = date(self.display_year, self.display_month, day_num)
                    date_str = d.strftime("%Y-%m-%d")

                    is_today = d == today
                    is_selected = d == self.selected_date

                    bg = self.theme["card_bg"]
                    fg = self.theme["text"]

                    # 日程背景色标注（使用批量查询结果）
                    info = month_summary.get(date_str)
                    if info:
                        count, max_pri, all_done = info
                        if all_done:
                            bg = "#10b981"
                        elif max_pri >= 3:
                            bg = "#ef4444"
                        elif max_pri >= 2:
                            bg = "#f59e0b"
                        else:
                            bg = "#6366f1"
                        fg = "#ffffff"

                    # 今天高亮
                    if is_today:
                        bg = self.theme["primary_light"]
                        fg = self.theme["primary"]

                    # 选中日期（优先级最高）
                    if is_selected:
                        bg = self.theme["primary"]
                        fg = "#ffffff"

                    ft = ("Microsoft YaHei UI", 10, "bold") if (is_today or is_selected) else ("Microsoft YaHei UI", 10)
                    lbl.configure(text=str(day_num), bg=bg, fg=fg, font=ft)
                    lbl.bind("<Button-1>", lambda e, dd=d: self._select_date(dd))
                    lbl.bind("<Double-Button-1>", lambda e, dd=d: self._on_date_double_click(dd))
                    self.day_buttons[d] = lbl
                else:
                    lbl.configure(text="", bg=self.theme["card_bg"])

        ds = self.selected_date.strftime("%Y-%m-%d")
        total = ScheduleDB.count_by_date(ds)
        done = ScheduleDB.done_count_by_date(ds)
        self.info_label.configure(text=f"{ds} | {done}/{total} 已完成")

    def _select_date(self, d):
        self.selected_date = d
        self.refresh()

    def _on_date_double_click(self, d):
        self.selected_date = d
        self.refresh()
        self._add_schedule_dialog()

    def _repack_cards(self):
        """只移动被拖拽的卡片到目标位置，避免全部重排导致闪烁"""
        drag_card = self._drag_card
        if not drag_card:
            return
        target_idx = next(i for i, (c, _) in enumerate(self._card_order) if c == drag_card)
        drag_card.pack_forget()
        if target_idx + 1 < len(self._card_order):
            drag_card.pack(in_=self.schedule_inner, before=self._card_order[target_idx + 1][0],
                          fill=tk.X, padx=2, pady=3)
        else:
            drag_card.pack(in_=self.schedule_inner, fill=tk.X, padx=2, pady=3)

    def _load_schedules(self):
        for w in self.schedule_inner.winfo_children():
            w.destroy()
        self._card_order = []

        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_name = day_names[self.selected_date.weekday()]
        self.lbl_selected_date.configure(
            text=f"{self.selected_date.strftime('%Y-%m-%d')} {day_name}")

        ds = self.selected_date.strftime("%Y-%m-%d")
        schedules = ScheduleDB.get_by_date(ds)

        if not schedules:
            tk.Label(self.schedule_inner,
                    text="📭 当天暂无日程\n点击右上角「添加日程」开始规划\n或双击日历中的日期快速添加",
                    font=("Microsoft YaHei UI", 11), fg=self.theme["text_secondary"],
                    bg=self.theme["card_bg"], justify="center").pack(anchor="center", pady=60)
            return

        for s in schedules:
            self._create_schedule_card(s)

    def _create_schedule_card(self, schedule):
        is_done = schedule["is_done"]
        priority = schedule["priority"]
        priority_colors = {1: self.theme["primary"], 2: self.theme["warning"], 3: self.theme["danger"]}
        priority_labels = {1: "普通", 2: "重要", 3: "紧急"}

        bg = "#f0fdf4" if is_done else self.theme["card_bg"]

        card = tk.Frame(self.schedule_inner, bg=bg, highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(fill=tk.X, padx=2, pady=3)

        # 拖拽手柄
        drag_handle = tk.Label(card, text="⠿", bg=bg, fg=self.theme["text_secondary"],
                               font=("Segoe UI", 14), cursor="fleur", padx=2)
        drag_handle.pack(side=tk.LEFT, fill=tk.Y)

        bar_color = "#10b981" if is_done else priority_colors.get(priority, self.theme["primary"])
        left_bar = tk.Frame(card, bg=bar_color, width=5)
        left_bar.pack(side=tk.LEFT, fill=tk.Y)

        # 记录卡片顺序
        self._card_order.append((card, schedule["id"]))

        # 拖拽事件绑定
        def on_drag_start(e, c=card):
            self._drag_card = c
            self._drag_start_y = e.y_root
            c.configure(highlightbackground=self.theme["primary"], highlightthickness=2)

        def on_drag_motion(e):
            if not self._drag_card:
                return
            # 计算目标位置
            drag_y = e.y_root
            target_idx = None
            for i, (c, _) in enumerate(self._card_order):
                if c == self._drag_card:
                    continue
                cy = c.winfo_rooty() + c.winfo_height() // 2
                if drag_y < cy:
                    target_idx = i
                    break
            # 视觉反馈: 移动卡片
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
            # 持久化排序
            for i, (_, sid) in enumerate(self._card_order):
                ScheduleDB.update_sort_order(sid, i)

        for widget in (drag_handle,):
            widget.bind("<Button-1>", on_drag_start)
            widget.bind("<B1-Motion>", on_drag_motion)
            widget.bind("<ButtonRelease-1>", on_drag_end)

        inner = tk.Frame(card, bg=bg)
        inner.pack(fill=tk.X, padx=10, pady=8)

        check = tk.Label(inner, text="✅" if is_done else "⬜", bg=bg,
                        font=("Segoe UI Emoji", 14), cursor="hand2")
        check.pack(side=tk.LEFT)
        check.bind("<Button-1>", lambda e, sid=schedule["id"]:
                  (ScheduleDB.toggle_done(sid), self.refresh()))

        content = tk.Frame(inner, bg=bg, cursor="hand2")
        content.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        title_fg = self.theme["success"] if is_done else self.theme["text"]
        title_lbl = tk.Label(content, text=schedule["title"], bg=bg,
                font=("Microsoft YaHei UI", 11, "bold"), fg=title_fg,
                anchor="w", cursor="hand2")
        title_lbl.pack(anchor="w")

        detail_parts = []
        if schedule["start_time"]:
            detail_parts.append(f"⏰ {schedule['start_time']}")
            if schedule["end_time"]:
                detail_parts.append(f" → {schedule['end_time']}")
        if schedule["location"]:
            detail_parts.append(f"📍 {schedule['location']}")
        detail_parts.append(f"🏷 {priority_labels.get(priority, '普通')}")

        detail_lbl = tk.Label(content, text="  ".join(detail_parts), bg=bg,
                font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"],
                anchor="w", cursor="hand2")
        detail_lbl.pack(anchor="w")

        # 紧急/重要日程倒计时提醒
        if not is_done and priority >= 2:
            countdown = self._calc_countdown(schedule["schedule_date"], schedule["start_time"])
            if countdown:
                remind_bg = "#fef2f2" if priority >= 3 else "#fffbeb"
                remind_fg = "#dc2626" if priority >= 3 else "#d97706"
                remind_icon = "🔥" if priority >= 3 else "⚡"
                remind_lbl = tk.Label(content, text=f"{remind_icon} {countdown}",
                                     bg=remind_bg, fg=remind_fg,
                                     font=("Microsoft YaHei UI", 9, "bold"),
                                     padx=6, pady=1, anchor="w")
                remind_lbl.pack(anchor="w", pady=(3, 0))

        # 点击卡片内容区域查看详情
        show_detail = lambda e, s=schedule: self._show_schedule_detail(s)
        content.bind("<Button-1>", show_detail)
        title_lbl.bind("<Button-1>", show_detail)
        detail_lbl.bind("<Button-1>", show_detail)

        btn_area = tk.Frame(inner, bg=bg)
        btn_area.pack(side=tk.RIGHT)

        edit_btn = tk.Button(btn_area, text="编辑", bg=self.theme["primary_light"],
                            fg=self.theme["primary"], font=("Microsoft YaHei UI", 9),
                            relief="flat", padx=8, pady=2, cursor="hand2",
                            command=lambda sid=schedule["id"], s=schedule:
                            self._edit_schedule_dialog(sid, s))
        edit_btn.pack(side=tk.LEFT, padx=2)

        del_btn = tk.Button(btn_area, text="删除", bg=self.theme["danger_light"],
                           fg=self.theme["danger"], font=("Microsoft YaHei UI", 9),
                           relief="flat", padx=8, pady=2, cursor="hand2",
                           command=lambda sid=schedule["id"]:
                           self._delete_schedule(sid))
        del_btn.pack(side=tk.LEFT, padx=2)

    def _calc_countdown(self, schedule_date, start_time):
        """计算倒计时文字"""
        try:
            target = datetime.strptime(schedule_date, "%Y-%m-%d")
            if start_time:
                target = datetime.strptime(f"{schedule_date} {start_time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            diff = target - now

            if diff.total_seconds() < 0:
                return "已过期"
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60

            if days > 0:
                return f"还剩 {days}天{hours}小时"
            elif hours > 0:
                return f"还剩 {hours}小时{minutes}分钟"
            elif minutes > 0:
                return f"还剩 {minutes}分钟"
            else:
                return "即将开始！"
        except Exception:
            return None

    def _delete_schedule(self, sid):
        if messagebox.askyesno("确认", "确定删除此日程？"):
            ScheduleDB.delete(sid)
            self.refresh()

    def _show_schedule_detail(self, schedule):
        top = tk.Toplevel(self)
        top.title("日程详情")
        top.geometry("420x480")
        top.resizable(False, False)
        top.configure(bg=self.theme["card_bg"])
        top.transient(self.winfo_toplevel())
        top.grab_set()

        # 居中
        top.update_idletasks()
        px = self.winfo_toplevel().winfo_x()
        py = self.winfo_toplevel().winfo_y()
        pw = self.winfo_toplevel().winfo_width()
        ph = self.winfo_toplevel().winfo_height()
        top.geometry("+{}+{}".format(px + pw // 2 - 210, py + ph // 2 - 240))

        priority_labels = {1: "普通", 2: "重要", 3: "紧急"}
        priority_colors = {1: self.theme["primary"], 2: self.theme["warning"], 3: self.theme["danger"]}
        pri = schedule["priority"]
        is_done = schedule["is_done"]

        # 头部
        header = tk.Frame(top, bg=priority_colors.get(pri, self.theme["primary"]))
        header.pack(fill=tk.X)
        tk.Label(header, text="📋 日程详情", font=("Microsoft YaHei UI", 14, "bold"),
                bg=priority_colors.get(pri, self.theme["primary"]), fg="white").pack(pady=(15, 15))

        # 内容区
        body = tk.Frame(top, bg=self.theme["card_bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        def add_row(parent, label, value, icon=""):
            row = tk.Frame(parent, bg=self.theme["card_bg"])
            row.pack(fill=tk.X, pady=6)
            tk.Label(row, text=f"{icon} {label}", font=("Microsoft YaHei UI", 10),
                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                    width=10, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=str(value) if value else "—", font=("Microsoft YaHei UI", 10),
                    bg=self.theme["card_bg"], fg=self.theme["text"],
                    anchor="w", wraplength=260).pack(side=tk.LEFT, fill=tk.X, expand=True)

        add_row(body, "标题", schedule["title"], "📌")
        add_row(body, "日期", schedule["schedule_date"], "📅")

        time_str = ""
        if schedule["start_time"]:
            time_str = schedule["start_time"]
            if schedule["end_time"]:
                time_str += f" ~ {schedule['end_time']}"
        add_row(body, "时间", time_str or "—", "⏰")
        add_row(body, "地点", schedule["location"] or "—", "📍")
        add_row(body, "优先级", priority_labels.get(pri, "普通"), "🏷")

        status_text = "✅ 已完成" if is_done else "❌ 未完成"
        add_row(body, "状态", status_text, "📊")

        # 描述
        desc_row = tk.Frame(body, bg=self.theme["card_bg"])
        desc_row.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        tk.Label(desc_row, text="📝 描述", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w")

        desc_text = tk.Text(desc_row, height=5, font=("Microsoft YaHei UI", 10),
                           wrap=tk.WORD, padx=8, pady=6, relief="flat",
                           bg="#f8fafc", fg=self.theme["text"],
                           highlightbackground=self.theme["border"], highlightthickness=1)
        desc_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        desc_text.insert("1.0", schedule["description"] or "无描述")
        desc_text.configure(state=tk.DISABLED)

        # 按钮
        btn_frame = tk.Frame(top, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 15))

        tk.Button(btn_frame, text="关闭", font=("Microsoft YaHei UI", 11),
                 bg=self.theme["text_secondary"], fg="white", relief="flat",
                 padx=20, pady=6, cursor="hand2",
                 command=top.destroy).pack(side=tk.RIGHT)

        tk.Button(btn_frame, text="编辑", font=("Microsoft YaHei UI", 11),
                 bg=self.theme["primary"], fg="white", relief="flat",
                 padx=20, pady=6, cursor="hand2",
                 command=lambda: (top.destroy(),
                                  self._edit_schedule_dialog(schedule["id"], schedule))).pack(side=tk.RIGHT, padx=(0, 8))

    def _add_schedule_dialog(self):
        self._schedule_dialog(None, None)

    def _edit_schedule_dialog(self, sid, schedule):
        self._schedule_dialog(sid, schedule)

    def _schedule_dialog(self, sid, schedule):
        dialog = tk.Toplevel(self)
        dialog.title("编辑日程" if sid else "添加日程")
        dialog.geometry("450x750")
        dialog.resizable(False, False)
        dialog.configure(bg=self.theme["card_bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 头部
        header = tk.Frame(dialog, bg=self.theme["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="✏ 编辑日程" if sid else "➕ 添加日程",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["primary"], fg="white").pack(pady=(15, 15))

        # 操作按钮 - 先放到底部
        btn_frame = tk.Frame(dialog, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 15))

        form = tk.Frame(dialog, bg=self.theme["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        def add_field(parent, label_text, default="", required=False, is_date=False):
            label_frame = tk.Frame(parent, bg=self.theme["card_bg"])
            label_frame.pack(fill=tk.X, pady=(8, 0))
            tk.Label(label_frame, text=label_text, font=("Microsoft YaHei UI", 10),
                    bg=self.theme["card_bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
            if required:
                tk.Label(label_frame, text="*", font=("Microsoft YaHei UI", 10),
                        bg=self.theme["card_bg"], fg=self.theme["danger"]).pack(side=tk.LEFT)
            
            if is_date:
                # 日期字段：输入框 + 日历图标按钮
                date_frame = tk.Frame(parent, bg=self.theme["card_bg"])
                date_frame.pack(fill=tk.X)
                entry = tk.Entry(date_frame, font=("Microsoft YaHei UI", 11),
                               highlightbackground=self.theme["border"], highlightthickness=1,
                               width=20)
                entry.insert(0, default)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
                
                # 日历图标按钮
                cal_btn = tk.Button(date_frame, text="📅", font=("Segoe UI Emoji", 12),
                                   bg=self.theme["primary_light"], fg=self.theme["primary"],
                                   relief=tk.FLAT, padx=8, command=lambda: show_date_picker(entry))
                cal_btn.pack(side=tk.RIGHT, padx=(5, 0))
            else:
                entry = tk.Entry(parent, font=("Microsoft YaHei UI", 11),
                               highlightbackground=self.theme["border"], highlightthickness=1)
                entry.insert(0, default)
                entry.pack(fill=tk.X, ipady=5)
            return entry

        # 日期选择器（使用通用组件）
        def show_date_picker(entry_widget):
            today = date.today()
            init = self.selected_date

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

            py_ = [init.year]
            pm_ = [init.month]
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

            # 一次性创建 6x7=42 个格子
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
                            ds = d.strftime("%Y-%m-%d")
                            bg = self.theme["card_bg"]
                            fg = self.theme["text"]

                            count = ScheduleDB.count_by_date(ds)
                            if count > 0:
                                max_pri, all_done, _ = ScheduleDB.get_priority_info(ds)
                                if all_done:
                                    bg = "#10b981"
                                elif max_pri >= 3:
                                    bg = "#ef4444"
                                elif max_pri >= 2:
                                    bg = "#f59e0b"
                                else:
                                    bg = "#6366f1"
                                fg = "#ffffff"

                            if d == today:
                                bg = "#3b82f6"
                                fg = "#ffffff"

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

        # 时间选择器组件
        def add_time_field(parent, label_text, default=""):
            frame = tk.Frame(parent, bg=self.theme["card_bg"])
            frame.pack(fill=tk.X)
            tk.Label(frame, text=label_text, font=("Microsoft YaHei UI", 10),
                    bg=self.theme["card_bg"], fg=self.theme["text"]).pack(anchor="w", pady=(0, 2))
            
            time_frame = tk.Frame(frame, bg=self.theme["card_bg"])
            time_frame.pack(fill=tk.X)
            
            # 小时选择
            hour_var = tk.StringVar(value=default[:2] if len(default) >= 2 else "09")
            hour_spin = tk.Spinbox(time_frame, from_=0, to=23, textvariable=hour_var,
                                  format="%02.0f", font=("Microsoft YaHei UI", 11),
                                  width=5, justify=tk.CENTER)
            hour_spin.pack(side=tk.LEFT)
            
            # 冒号
            tk.Label(time_frame, text=":", font=("Microsoft YaHei UI", 11),
                    bg=self.theme["card_bg"], fg=self.theme["text"]).pack(side=tk.LEFT, padx=2)
            
            # 分钟选择
            minute_var = tk.StringVar(value=default[3:5] if len(default) >= 5 else "00")
            minute_spin = tk.Spinbox(time_frame, from_=0, to=59, textvariable=minute_var,
                                    format="%02.0f", font=("Microsoft YaHei UI", 11),
                                    width=5, justify=tk.CENTER)
            minute_spin.pack(side=tk.LEFT)
            
            # 获取时间字符串
            def get_time():
                h = hour_var.get().zfill(2)
                m = minute_var.get().zfill(2)
                return f"{h}:{m}"
            
            return get_time

        e_title = add_field(form, "日程标题", schedule["title"] if schedule else "", required=True)
        e_title.focus_set()
        e_date = add_field(form, "日期",
                          schedule["schedule_date"] if schedule else self.selected_date.strftime("%Y-%m-%d"),
                          is_date=True)

        # 时间输入
        time_frame = tk.Frame(form, bg=self.theme["card_bg"])
        time_frame.pack(fill=tk.X, pady=(8, 0))
        
        time_left = tk.Frame(time_frame, bg=self.theme["card_bg"])
        time_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        get_start_time = add_time_field(time_left, "开始时间", schedule["start_time"] if schedule else "")

        time_right = tk.Frame(time_frame, bg=self.theme["card_bg"])
        time_right.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        get_end_time = add_time_field(time_right, "结束时间", schedule["end_time"] if schedule else "")

        e_location = add_field(form, "地点", schedule["location"] if schedule else "")

        # 优先级
        tk.Label(form, text="优先级", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(anchor="w", pady=(12, 2))
        priority_var = tk.IntVar(value=schedule["priority"] if schedule else 1)
        pri_frame = tk.Frame(form, bg=self.theme["card_bg"])
        pri_frame.pack(fill=tk.X)
        
        priority_options = [(1, "普通", self.theme["primary"]), 
                           (2, "重要", self.theme["warning"]), 
                           (3, "紧急", self.theme["danger"])]
        for val, lbl, color in priority_options:
            rb = tk.Radiobutton(pri_frame, text=lbl, variable=priority_var, value=val,
                              font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"],
                              selectcolor=self.theme["primary_light"])
            rb.pack(side=tk.LEFT, padx=8)

        # 描述
        desc_frame = tk.Frame(form, bg=self.theme["card_bg"])
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        tk.Label(desc_frame, text="描述", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(anchor="w")

        desc_container = tk.Frame(desc_frame, bg=self.theme["card_bg"])
        desc_container.pack(fill=tk.BOTH, expand=True)

        e_desc = tk.Text(desc_container, height=8, font=("Microsoft YaHei UI", 11),
                        wrap=tk.WORD, padx=10, pady=8,
                        highlightbackground=self.theme["border"], highlightthickness=1,
                        spacing1=2, spacing3=2)
        desc_scroll = ttk.Scrollbar(desc_container, orient=tk.VERTICAL, command=e_desc.yview)
        e_desc.configure(yscrollcommand=desc_scroll.set)
        e_desc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        if schedule:
            e_desc.insert("1.0", schedule["description"])


        def save():
            title = e_title.get().strip()
            sd = e_date.get().strip()
            
            if not title:
                messagebox.showwarning("提示", "请输入日程标题", parent=dialog)
                e_title.focus_set()
                return
            
            if not sd:
                messagebox.showwarning("提示", "请输入日期", parent=dialog)
                e_date.focus_set()
                return
            
            try:
                datetime.strptime(sd, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("提示", "日期格式不正确，请使用 YYYY-MM-DD", parent=dialog)
                e_date.focus_set()
                return

            st = get_start_time()
            et = get_end_time()
            
            # 验证时间格式
            if st:
                try:
                    datetime.strptime(st, "%H:%M")
                except ValueError:
                    messagebox.showwarning("提示", "开始时间格式不正确，请使用 HH:MM", parent=dialog)
                    return
            
            if et:
                try:
                    datetime.strptime(et, "%H:%M")
                except ValueError:
                    messagebox.showwarning("提示", "结束时间格式不正确，请使用 HH:MM", parent=dialog)
                    return

            # 验证结束时间不能早于开始时间
            if st and et and et <= st:
                messagebox.showwarning("提示", "结束时间不能早于或等于开始时间", parent=dialog)
                return

            loc = e_location.get().strip()
            desc = e_desc.get("1.0", tk.END).strip()
            pri = priority_var.get()

            if sid:
                ScheduleDB.update(sid, title, desc, sd, st, et, loc, pri)
                messagebox.showinfo("成功", "日程已更新！", parent=dialog)
            else:
                ScheduleDB.add(title, desc, sd, st, et, loc, pri)
                messagebox.showinfo("成功", "日程已添加！", parent=dialog)
            
            dialog.destroy()
            self.refresh()

        def cancel():
            dialog.destroy()

        cancel_btn = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                              bg=self.theme["text_secondary"], fg="white", relief="flat", 
                              padx=20, pady=8, cursor="hand2", command=cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        save_btn = tk.Button(btn_frame, text="保存日程", font=("Microsoft YaHei UI", 11, "bold"),
                           bg=self.theme["primary"], fg="white", relief="flat", 
                           padx=25, pady=8, cursor="hand2", command=save)
        save_btn.pack(side=tk.RIGHT)
        
        # 弹窗居中显示
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w // 2) - 225
        y = parent_y + (parent_h // 2) - 340
        dialog.geometry("+{}+{}".format(x, y))
        
        dialog.wait_window()