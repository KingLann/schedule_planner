import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import ScheduleDB, DailyTaskDB, CheckinDB, DiaryDB


class AllTasksView(tk.Frame):

    def __init__(self, parent, theme=None, on_navigate=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f1f5f9")
        self.theme = theme or {
            "bg": "#f1f5f9", "card_bg": "#ffffff", "primary": "#6366f1",
            "primary_light": "#e0e7ff", "success": "#10b981", "danger": "#ef4444",
            "warning": "#f59e0b", "text": "#1e293b", "text_secondary": "#64748b",
            "border": "#e2e8f0", "success_light": "#d1fae5", "danger_light": "#fee2e2",
            "warning_light": "#fef3c7",
        }
        self.current_tab = "all"
        self._on_navigate = on_navigate
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="📊 整体态势", font=("Microsoft YaHei UI", 18, "bold"),
                bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  全局数据总览", font=("Microsoft YaHei UI", 10),
                bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        # 统计卡片
        self.stats_bar = tk.Frame(self, bg=self.theme["bg"])
        self.stats_bar.pack(fill=tk.X, padx=25, pady=5)
        self.stat_labels = {}
        stats = [
            ("today_tasks", "今日任务", self.theme["primary"]),
            ("done_rate", "完成率", self.theme["success"]),
            ("total_tasks", "总任务", self.theme["warning"]),
            ("diaries", "日记数", self.theme["danger"]),
        ]
        for key, label, color in stats:
            card = tk.Frame(self.stats_bar, bg=self.theme["card_bg"],
                          highlightbackground=self.theme["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
            tk.Label(card, text=label, bg=self.theme["card_bg"],
                    font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"]).pack(pady=(8, 0))
            lbl = tk.Label(card, text="0", bg=self.theme["card_bg"],
                          font=("Microsoft YaHei UI", 20, "bold"), fg=color)
            lbl.pack(pady=(0, 8))
            self.stat_labels[key] = lbl

        # 筛选栏
        filter_bar = tk.Frame(self, bg=self.theme["bg"])
        filter_bar.pack(fill=tk.X, padx=25, pady=5)

        tab_buttons = [
            ("all", "全部"), ("today", "今日"), ("week", "本周"),
            ("task", "任务"), ("schedule", "日程"), ("checkin", "打卡"), ("diary", "日记"),
            ("done", "已完成"), ("undone", "未完成"),
        ]
        self.tab_btns = {}
        for key, text in tab_buttons:
            btn = tk.Button(filter_bar, text=text, font=("Microsoft YaHei UI", 10),
                           relief="flat", padx=10, pady=4, cursor="hand2",
                           command=lambda k=key: self._set_filter(k))
            btn.pack(side=tk.LEFT, padx=2)
            self.tab_btns[key] = btn

        # 搜索框
        search_frame = tk.Frame(filter_bar, bg=self.theme["bg"])
        search_frame.pack(side=tk.RIGHT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                              font=("Microsoft YaHei UI", 10), width=18,
                              highlightbackground=self.theme["border"], highlightthickness=1)
        search_entry.pack(side=tk.LEFT, ipady=3)
        tk.Label(search_frame, text="🔍", bg=self.theme["bg"],
                font=("Segoe UI Emoji", 11)).pack(side=tk.LEFT, padx=4)

        # 表格
        card = tk.Frame(self, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=25, pady=(5, 20))

        cols = ("type", "title", "date", "time", "status")
        col_names = {"type": "类型", "title": "标题", "date": "日期",
                    "time": "时间", "status": "状态"}
        col_widths = {"type": 70, "title": 280, "date": 110, "time": 100, "status": 80}

        style = ttk.Style()
        style.configure("AllTasks.Treeview", font=("Microsoft YaHei UI", 10), rowheight=36)
        style.configure("AllTasks.Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

        tree_frame = tk.Frame(card, bg=self.theme["card_bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                style="AllTasks.Treeview", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=col_names[c])
            self.tree.column(c, width=col_widths[c], minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击跳转
        self.tree.bind("<Double-1>", self._on_double_click)

        # 鼠标滚轮
        self.tree.bind("<MouseWheel>", self._on_mousewheel)

        # 底部信息栏
        self.bottom_label = tk.Label(card, text="", font=("Microsoft YaHei UI", 9),
                                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.bottom_label.pack(anchor="w", padx=12, pady=(0, 8))

        self._update_tab_style()

    def _on_mousewheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _set_filter(self, key):
        self.current_tab = key
        self._update_tab_style()
        self.refresh()

    def _update_tab_style(self):
        for key, btn in self.tab_btns.items():
            if key == self.current_tab:
                btn.configure(bg=self.theme["primary"], fg="white")
            else:
                btn.configure(bg=self.theme["card_bg"], fg=self.theme["text"])

    def _on_search(self):
        self.refresh()

    def refresh(self):
        self._load_data()
        self._update_stats()

    def _update_stats(self):
        today_str = date.today().strftime("%Y-%m-%d")

        # 今日所有事项统计（任务+日程+打卡）
        today_tasks = DailyTaskDB.get_by_date(today_str)
        today_schedules = ScheduleDB.get_by_date(today_str)
        today_checkins = CheckinDB.get_by_date(today_str)
        today_all = len(today_tasks) + len(today_schedules) + len(today_checkins)
        today_done = (sum(1 for t in today_tasks if t["is_done"])
                      + sum(1 for s in today_schedules if s["is_done"])
                      + sum(1 for c in today_checkins if c["status"]))

        # 总完成率（任务+日程）
        from database import _db
        total_all = DailyTaskDB.count_all() + ScheduleDB.count_all()
        with _db() as conn:
            total_done = (
                conn.execute("SELECT COUNT(*) as c FROM daily_tasks WHERE is_done=1").fetchone()["c"]
                + conn.execute("SELECT COUNT(*) as c FROM schedules WHERE is_done=1").fetchone()["c"]
            )

        # 今日事项
        if today_all > 0:
            self.stat_labels["today_tasks"].configure(
                text=f"{today_done}/{today_all}")
        else:
            self.stat_labels["today_tasks"].configure(text="0")

        # 总完成率
        if total_all > 0:
            rate = int(total_done / total_all * 100)
            self.stat_labels["done_rate"].configure(text=f"{rate}%")
        else:
            self.stat_labels["done_rate"].configure(text="0%")

        # 总事项数
        self.stat_labels["total_tasks"].configure(text=str(total_all))

        # 日记数
        self.stat_labels["diaries"].configure(text=str(DiaryDB.count_all()))

    def _load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        keyword = self.search_var.get().strip()
        items = []
        tab = self.current_tab
        today_str = date.today().strftime("%Y-%m-%d")

        # 本周范围
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_start_str = week_start.strftime("%Y-%m-%d")
        week_end_str = week_end.strftime("%Y-%m-%d")

        def in_week(date_str):
            return week_start_str <= date_str <= week_end_str

        # 任务
        if tab in ("all", "today", "week", "task", "done", "undone"):
            if keyword:
                tasks = DailyTaskDB.search(keyword)
            else:
                tasks = DailyTaskDB.get_all(500)
            for t in tasks:
                if tab == "today" and t["task_date"] != today_str:
                    continue
                if tab == "week" and not in_week(t["task_date"]):
                    continue
                if tab == "done" and not t["is_done"]:
                    continue
                if tab == "undone" and t["is_done"]:
                    continue
                status = "✅完成" if t["is_done"] else "❌未完成"
                items.append(("📋任务", t["title"], t["task_date"], "", status,
                              "task", t["task_date"]))

        # 日程
        if tab in ("all", "today", "week", "schedule", "done", "undone"):
            if keyword:
                schedules = ScheduleDB.search(keyword)
            else:
                schedules = ScheduleDB.get_all(500)
            for s in schedules:
                if tab == "today" and s["schedule_date"] != today_str:
                    continue
                if tab == "week" and not in_week(s["schedule_date"]):
                    continue
                if tab == "done" and not s["is_done"]:
                    continue
                if tab == "undone" and s["is_done"]:
                    continue
                time_str = s["start_time"] or ""
                if s["end_time"]:
                    time_str += f"-{s['end_time']}"
                status = "✅完成" if s["is_done"] else "❌未完成"
                items.append(("📅日程", s["title"], s["schedule_date"], time_str, status,
                              "schedule", s["schedule_date"]))

        # 打卡
        if tab in ("all", "today", "week", "checkin", "done", "undone"):
            if keyword:
                checkins = CheckinDB.search(keyword)
            else:
                checkins = CheckinDB.get_all_checkins(500)
            for c in checkins:
                if tab == "today" and c["checkin_date"] != today_str:
                    continue
                if tab == "week" and not in_week(c["checkin_date"]):
                    continue
                is_done = c["status"]
                if tab == "done" and not is_done:
                    continue
                if tab == "undone" and is_done:
                    continue
                status = "✅已打卡" if is_done else "❌未打卡"
                items.append(("✅打卡", c["task_title"], c["checkin_date"],
                             c["checkin_time"] or "", status,
                             "checkin", c["checkin_date"]))

        # 日记
        if tab in ("all", "today", "week", "diary"):
            if keyword:
                diaries = DiaryDB.search(keyword)
            else:
                diaries = DiaryDB.get_all(500)
            for d in diaries:
                if tab == "today" and d["diary_date"] != today_str:
                    continue
                if tab == "week" and not in_week(d["diary_date"]):
                    continue
                preview = d["title"][:15] + "..." if len(d["title"]) > 15 else d["title"]
                items.append(("📝日记", preview, d["diary_date"], "",
                             d["mood"] or "—", "diary", d["diary_date"]))

        # 按日期降序排序
        items.sort(key=lambda x: x[2], reverse=True)
        for item in items:
            self.tree.insert("", tk.END, values=item[:5], tags=(item[5],))

        # 底部信息（带状态明细）
        total = len(items)
        done = sum(1 for it in items if "✅" in it[4])
        undone = total - done
        if total > 0 and self.current_tab not in ("diary",):
            self.bottom_label.configure(
                text=f"共 {total} 条记录 | ✅已完成 {done} · ❌未完成 {undone}")
        else:
            self.bottom_label.configure(text=f"共 {total} 条记录")

    def _on_double_click(self, event):
        """双击跳转到对应功能视图"""
        sel = self.tree.selection()
        if not sel or not self._on_navigate:
            return
        item = self.tree.item(sel[0])
        tags = item.get("tags", ())
        if not tags:
            return
        view_key = tags[0]
        self._on_navigate(view_key, force=True)
