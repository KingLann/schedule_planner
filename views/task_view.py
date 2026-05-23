import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DailyTaskDB


class TaskView(tk.Frame):

    def __init__(self, parent, theme=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f1f5f9")
        self.theme = theme or {
            "bg": "#f1f5f9", "card_bg": "#ffffff", "primary": "#6366f1",
            "success": "#10b981", "danger": "#ef4444", "warning": "#f59e0b",
            "text": "#1e293b", "text_secondary": "#64748b", "border": "#e2e8f0",
            "success_light": "#d1fae5", "danger_light": "#fee2e2",
            "primary_light": "#e0e7ff",
        }
        self.current_date = date.today()
        self.filter_status = "all"
        self.selected_tasks = set()
        self._drag_card = None
        self._drag_start_y = 0
        self._card_order = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 头部
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="每日任务", font=("Microsoft YaHei UI", 18, "bold"),
                bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  完成每一个小目标", font=("Microsoft YaHei UI", 10),
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
        tk.Button(action_frame, text="添加任务", font=("Microsoft YaHei UI", 10, "bold"),
                 bg=self.theme["primary"], fg="white", relief="flat", padx=14, pady=5,
                 cursor="hand2", command=self._add_task_dialog).pack(side=tk.RIGHT, padx=5)
        tk.Button(action_frame, text="批量清除", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["danger"], fg="white", relief="flat", padx=14, pady=5,
                 cursor="hand2", command=self._clear_tasks_dialog).pack(side=tk.RIGHT, padx=5)

        # 第二行：筛选按钮 + 批量操作
        row2 = tk.Frame(self, bg=self.theme["bg"])
        row2.pack(fill=tk.X, padx=25, pady=(0, 4))

        # 筛选按钮
        filter_frame = tk.Frame(row2, bg=self.theme["bg"])
        filter_frame.pack(side=tk.LEFT)
        self.filter_btns = {}
        for key, text in [("all", "全部"), ("done", "已完成"), ("undone", "未完成")]:
            btn = tk.Button(filter_frame, text=text, font=("Microsoft YaHei UI", 10),
                           relief="flat", padx=14, pady=4, cursor="hand2",
                           command=lambda k=key: self._set_filter(k))
            btn.pack(side=tk.LEFT, padx=3)
            self.filter_btns[key] = btn

        # 批量操作按钮（右侧）
        batch_nav = tk.Frame(row2, bg=self.theme["bg"])
        batch_nav.pack(side=tk.RIGHT)
        tk.Button(batch_nav, text="全选", font=("Microsoft YaHei UI", 10),
                 relief="flat", bg=self.theme["success_light"], cursor="hand2",
                 padx=14, pady=4,
                 command=self._select_all).pack(side=tk.LEFT, padx=3)
        tk.Button(batch_nav, text="批量完成", font=("Microsoft YaHei UI", 10),
                 relief="flat", bg=self.theme["success_light"], cursor="hand2",
                 padx=14, pady=4,
                 command=self._batch_done).pack(side=tk.LEFT, padx=3)
        tk.Button(batch_nav, text="批量删除", font=("Microsoft YaHei UI", 10),
                 relief="flat", bg=self.theme["danger_light"], cursor="hand2",
                 padx=14, pady=4,
                 command=self._batch_delete).pack(side=tk.LEFT, padx=3)
        tk.Button(batch_nav, text="复制到明天", font=("Microsoft YaHei UI", 10),
                 relief="flat", bg=self.theme["primary_light"], cursor="hand2",
                 padx=14, pady=4,
                 command=self._copy_to_tomorrow).pack(side=tk.LEFT, padx=3)

        # 统计卡片
        self.stats_frame = tk.Frame(self, bg=self.theme["bg"])
        self.stats_frame.pack(fill=tk.X, padx=25, pady=(5, 3))
        self.card_total = self._stat_card(self.stats_frame, "总任务", "0", self.theme["primary"])
        self.card_done = self._stat_card(self.stats_frame, "已完成", "0", self.theme["success"])
        self.card_remain = self._stat_card(self.stats_frame, "剩余", "0", self.theme["warning"])
        self.card_rate = self._stat_card(self.stats_frame, "完成率", "0%", self.theme["danger"])

        # 任务列表
        card = tk.Frame(self, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=25, pady=(3, 15))

        # 列表头部
        list_header = tk.Frame(card, bg=self.theme["card_bg"])
        list_header.pack(fill=tk.X, padx=15, pady=(10, 5))
        self.lbl_task_count = tk.Label(list_header, text="", font=("Microsoft YaHei UI", 10),
                                      bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        self.lbl_task_count.pack(side=tk.LEFT)

        list_container = tk.Frame(card, bg=self.theme["card_bg"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.task_canvas = tk.Canvas(list_container, bg=self.theme["card_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.task_canvas.yview)
        self.task_inner = tk.Frame(self.task_canvas, bg=self.theme["card_bg"])

        self.task_inner.bind("<Configure>",
                             lambda e: self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all")))
        self.task_canvas.create_window((0, 0), window=self.task_inner, anchor="nw", tags="inner")
        self.task_canvas.configure(yscrollcommand=scrollbar.set)
        self.task_canvas.bind("<Configure>",
                              lambda e: self.task_canvas.itemconfig("inner", width=e.width))

        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._update_filter_style()

    def _stat_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=self.theme["card_bg"], highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        tk.Label(card, text=title, bg=self.theme["card_bg"], font=("Microsoft YaHei UI", 9),
                fg=self.theme["text_secondary"]).pack(pady=(6, 0))
        lbl = tk.Label(card, text=value, bg=self.theme["card_bg"],
                      font=("Microsoft YaHei UI", 16, "bold"), fg=color)
        lbl.pack(pady=(0, 6))
        return lbl

    def _set_filter(self, key):
        self.filter_status = key
        self._update_filter_style()
        self.refresh()

    def _update_filter_style(self):
        for key, btn in self.filter_btns.items():
            if key == self.filter_status:
                btn.configure(bg=self.theme["primary"], fg="white")
            else:
                btn.configure(bg=self.theme["card_bg"], fg=self.theme["text"])

    def refresh(self):
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_name = day_names[self.current_date.weekday()]
        self.lbl_date.configure(text=f"{self.current_date.strftime('%Y-%m-%d')} {day_name}")
        self.selected_tasks.clear()
        self._load_tasks()
        self._update_stats()

    def _prev_day(self):
        self.current_date -= timedelta(days=1)
        self.refresh()

    def _next_day(self):
        self.current_date += timedelta(days=1)
        self.refresh()

    def _go_today(self):
        self.current_date = date.today()
        self.refresh()

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

                        # 查询当天任务
                        tasks = DailyTaskDB.get_by_date(ds)
                        if tasks:
                            if any(t["is_done"] for t in tasks):
                                bg = "#10b981"
                            else:
                                bg = "#b0b8c4"
                            fg = "#ffffff"

                        # 今天
                        if d == today:
                            bg = "#3b82f6"
                            fg = "#ffffff"

                        lbl.configure(text=str(day_num), bg=bg, fg=fg)
                        lbl.bind("<Button-1>",
                                 lambda ev, _d=d: (setattr(self, 'current_date', _d),
                                                   self.refresh(), picker.destroy()))
                    else:
                        lbl.configure(text="", bg=self.theme["card_bg"])

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

    def _load_tasks(self):
        for w in self.task_inner.winfo_children():
            w.destroy()
        self._card_order = []

        ds = self.current_date.strftime("%Y-%m-%d")
        tasks = DailyTaskDB.get_by_date(ds)

        if self.filter_status == "done":
            tasks = [t for t in tasks if t["is_done"]]
        elif self.filter_status == "undone":
            tasks = [t for t in tasks if not t["is_done"]]

        self.lbl_task_count.configure(text=f"共 {len(tasks)} 项任务")

        if not tasks:
            empty_frame = tk.Frame(self.task_inner, bg=self.theme["card_bg"])
            empty_frame.pack(anchor="center", pady=60)
            tk.Label(empty_frame, text="暂无任务",
                    font=("Microsoft YaHei UI", 14, "bold"), fg=self.theme["text_secondary"],
                    bg=self.theme["card_bg"]).pack()
            tk.Label(empty_frame, text="点击「添加任务」来规划你的一天",
                    font=("Microsoft YaHei UI", 10), fg=self.theme["text_secondary"],
                    bg=self.theme["card_bg"]).pack(pady=(5, 0))
            return

        for i, t in enumerate(tasks):
            self._create_task_card(t, i + 1)

    def _repack_cards(self):
        """只移动被拖拽的卡片到目标位置，避免全部重排导致闪烁"""
        drag_card = self._drag_card
        if not drag_card:
            return
        target_idx = next(i for i, (c, _) in enumerate(self._card_order) if c == drag_card)
        drag_card.pack_forget()
        if target_idx + 1 < len(self._card_order):
            drag_card.pack(in_=self.task_inner, before=self._card_order[target_idx + 1][0],
                          fill=tk.X, padx=2, pady=3)
        else:
            drag_card.pack(in_=self.task_inner, fill=tk.X, padx=2, pady=3)

    def _create_task_card(self, task, index):
        is_done = task["is_done"]
        is_selected = task["id"] in self.selected_tasks
        priority = task["priority"] if "priority" in task.keys() else 1
        bg = "#f0fdf4" if is_done else (self.theme["primary_light"] if is_selected else self.theme["card_bg"])

        card = tk.Frame(self.task_inner, bg=bg, highlightbackground=self.theme["border"],
                       highlightthickness=1)
        card.pack(fill=tk.X, padx=2, pady=3)

        # 拖拽手柄
        drag_handle = tk.Label(card, text="⠿", bg=bg, fg=self.theme["text_secondary"],
                               font=("Segoe UI", 14), cursor="fleur", padx=2)
        drag_handle.pack(side=tk.LEFT, fill=tk.Y)

        self._card_order.append((card, task["id"]))

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
            from database import DailyTaskDB
            for i, (_, tid) in enumerate(self._card_order):
                DailyTaskDB.update_sort_order(tid, i)

        drag_handle.bind("<Button-1>", on_drag_start)
        drag_handle.bind("<B1-Motion>", on_drag_motion)
        drag_handle.bind("<ButtonRelease-1>", on_drag_end)

        inner = tk.Frame(card, bg=bg)
        inner.pack(fill=tk.X, padx=12, pady=10)

        # 选择框（用于批量操作）
        sel_check = tk.Label(inner, text="☑" if is_selected else "☐", bg=bg,
                             font=("Segoe UI", 16), cursor="hand2",
                             fg=self.theme["primary"] if is_selected else self.theme["text_secondary"])
        sel_check.pack(side=tk.LEFT, padx=(0, 4))
        sel_check.bind("<Button-1>", lambda e, tid=task["id"]: self._toggle_select(tid))

        # 完成勾选框
        check = tk.Label(inner, text="✅" if is_done else "⬜", bg=bg,
                         font=("Segoe UI Emoji", 16), cursor="hand2")
        check.pack(side=tk.LEFT)
        def on_check_click(e, tid=task["id"]):
            self._toggle_task_done(tid)
            return "break"
        check.bind("<Button-1>", on_check_click)

        content = tk.Frame(inner, bg=bg)
        content.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        title_fg = self.theme["success"] if is_done else self.theme["text"]
        title_text = f"✓ {task['title']}" if is_done else task["title"]
        
        # 标题行（包含优先级标签和状态图标）
        title_row = tk.Frame(content, bg=bg)
        title_row.pack(anchor="w", fill=tk.X)
        
        tk.Label(title_row, text=title_text, bg=bg,
                font=("Microsoft YaHei UI", 12, "bold"), fg=title_fg,
                anchor="w").pack(side=tk.LEFT)
        
        # 状态图标和优先级标签
        status_frame = tk.Frame(title_row, bg=bg)
        status_frame.pack(side=tk.RIGHT)
        
        # 优先级标签（带方框填充色）
        pri_config = {
            1: ("○", "普通", "#374151", "#f3f4f6"),
            2: ("●", "重要", "#92400e", "#fef3c7"),
            3: ("●", "紧急", "#991b1b", "#fee2e2"),
        }
        pri_icon, pri_text, pri_fg, pri_bg = pri_config.get(
            priority, ("○", "普通", "#374151", "#f3f4f6"))
        pri_lbl = tk.Label(status_frame, text=f" {pri_icon} {pri_text} ",
                          font=("Microsoft YaHei UI", 9, "bold"),
                          relief="solid", borderwidth=1)
        pri_lbl.pack(side=tk.LEFT, padx=(0, 8))
        pri_lbl.configure(bg=pri_bg, fg=pri_fg)

        # 描述和循环信息
        info_frame = tk.Frame(content, bg=bg)
        info_frame.pack(anchor="w", fill=tk.X)
        
        if task["description"]:
            tk.Label(info_frame, text=task["description"], bg=bg,
                    font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"],
                    anchor="w").pack(side=tk.LEFT)
        
        # 循环周期标识（带图标）
        repeat = task["repeat"] if "repeat" in task.keys() else ""
        if repeat:
            repeat_text = ""
            if repeat == "weekday":
                repeat_text = "工作日循环"
            elif repeat:
                week_days = ["一", "二", "三", "四", "五", "六", "日"]
                days = repeat.split(",")
                day_names = [f"周{week_days[int(d)]}" for d in days if d.isdigit()]
                if day_names:
                    repeat_text = f"循环:{','.join(day_names)}"
            
            if repeat_text:
                repeat_label = tk.Label(info_frame, text=repeat_text, bg=bg,
                                      font=("Microsoft YaHei UI", 9), fg=self.theme["primary"],
                                      anchor="w")
                repeat_label.pack(side=tk.RIGHT)

        btn_area = tk.Frame(inner, bg=bg)
        btn_area.pack(side=tk.RIGHT)

        edit_btn = tk.Label(btn_area, text="编辑", bg=bg, font=("Microsoft YaHei UI", 9),
                           cursor="hand2", fg=self.theme["primary"], padx=6, pady=2)
        edit_btn.pack(side=tk.LEFT, padx=3)
        edit_btn.bind("<Button-1>", lambda e, tid=task["id"], t=task: self._edit_task_dialog(tid, t))

        del_btn = tk.Label(btn_area, text="删除", bg=bg, font=("Microsoft YaHei UI", 9),
                          cursor="hand2", fg=self.theme["danger"], padx=6, pady=2)
        del_btn.pack(side=tk.LEFT, padx=3)
        del_btn.bind("<Button-1>", lambda e, tid=task["id"]: self._delete_task(tid))

    def _toggle_select(self, tid):
        if tid in self.selected_tasks:
            self.selected_tasks.discard(tid)
        else:
            self.selected_tasks.add(tid)
        self._load_tasks()

    def _toggle_task_done(self, tid):
        DailyTaskDB.toggle_done(tid)
        self.refresh()

    def _select_all(self):
        ds = self.current_date.strftime("%Y-%m-%d")
        tasks = DailyTaskDB.get_by_date(ds)
        if self.filter_status == "done":
            tasks = [t for t in tasks if t["is_done"]]
        elif self.filter_status == "undone":
            tasks = [t for t in tasks if not t["is_done"]]
        
        if len(self.selected_tasks) == len(tasks):
            self.selected_tasks.clear()
        else:
            self.selected_tasks = {t["id"] for t in tasks}
        self._load_tasks()

    def _batch_done(self):
        if not self.selected_tasks:
            messagebox.showinfo("提示", "请先选择任务")
            return
        for tid in self.selected_tasks:
            DailyTaskDB.toggle_done(tid)
        self.refresh()

    def _batch_delete(self):
        if not self.selected_tasks:
            messagebox.showinfo("提示", "请先选择任务")
            return
        if messagebox.askyesno("确认", f"确定删除选中的 {len(self.selected_tasks)} 个任务？"):
            for tid in self.selected_tasks:
                DailyTaskDB.delete(tid)
            self.selected_tasks.clear()
            self.refresh()

    def _copy_to_tomorrow(self):
        if not self.selected_tasks:
            messagebox.showinfo("提示", "请先通过任务左侧的复选框选择要复制的任务")
            return

        ds = self.current_date.strftime("%Y-%m-%d")
        tasks = DailyTaskDB.get_by_date(ds)
        selected = [t for t in tasks if t["id"] in self.selected_tasks and not t["is_done"]]

        if not selected:
            messagebox.showinfo("提示", "选中的任务中没有未完成的任务")
            return

        tomorrow = (self.current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        tomorrow_day = day_names[(self.current_date + timedelta(days=1)).weekday()]
        tomorrow_display = f"{tomorrow} {tomorrow_day}"

        names = "、".join([t["title"] for t in selected[:5]])
        extra = f"等{len(selected)}项" if len(selected) > 5 else ""
        if not messagebox.askyesno("确认复制",
                                   f"将以下 {len(selected)} 个任务复制到 {tomorrow_display}：\n\n{names}{extra}"):
            return

        count = 0
        for t in selected:
            if DailyTaskDB.add(t["title"], t["description"], tomorrow, t["priority"], ""):
                count += 1

        self.selected_tasks.clear()
        self.refresh()
        messagebox.showinfo("成功", f"已将 {count} 个任务复制到 {tomorrow_display}")

    def _delete_task(self, tid):
        if messagebox.askyesno("确认", "确定删除此任务？"):
            DailyTaskDB.delete(tid)
            self.refresh()

    def _update_stats(self):
        ds = self.current_date.strftime("%Y-%m-%d")
        tasks = DailyTaskDB.get_by_date(ds)
        total = len(tasks)
        done = sum(1 for t in tasks if t["is_done"])
        remain = total - done
        rate = done / total * 100 if total > 0 else 0

        self.card_total.configure(text=str(total))
        self.card_done.configure(text=str(done))
        self.card_remain.configure(text=str(remain))
        self.card_rate.configure(text=f"{rate:.0f}%")

    def _clear_tasks_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("批量清除任务")
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
        tk.Label(header, text="⚠ 批量清除任务",
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

        make_option(options_frame, "清除当月所有周期性任务", "monthly_repeat", "📅")
        make_option(options_frame, "清除本周所有任务", "weekly_all", "📋")

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
                count = DailyTaskDB.delete_repeat_in_range(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
                messagebox.showinfo("成功", f"已清除 {count} 个周期性任务", parent=dialog)
            else:
                weekday = self.current_date.weekday()
                start_of_week = self.current_date - timedelta(days=weekday)
                end_of_week = start_of_week + timedelta(days=6)
                count = DailyTaskDB.delete_in_range(start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"))
                messagebox.showinfo("成功", f"已清除 {count} 个任务", parent=dialog)

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

    def _add_task_dialog(self):
        self._task_dialog(None, None)

    def _edit_task_dialog(self, tid, task):
        self._task_dialog(tid, task)

    def _task_dialog(self, tid, task):
        dialog = tk.Toplevel(self)
        dialog.title("编辑任务" if tid else "添加任务")
        dialog.geometry("480x950")
        dialog.resizable(False, False)
        dialog.configure(bg=self.theme["card_bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 头部
        header = tk.Frame(dialog, bg=self.theme["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="编辑任务" if tid else "添加任务",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=self.theme["primary"], fg="white").pack(pady=(15, 15))

        # 操作按钮 - 先放到底部
        btn_frame = tk.Frame(dialog, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 15))

        form = tk.Frame(dialog, bg=self.theme["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        def add_field(parent, label_text, default="", required=False, is_date=False):
            label_frame = tk.Frame(parent, bg=self.theme["card_bg"])
            label_frame.pack(fill=tk.X, pady=(10, 0))
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
                cal_btn = tk.Button(date_frame, text="选择", font=("Microsoft YaHei UI", 10),
                                   bg=self.theme["primary_light"], fg=self.theme["primary"],
                                   relief=tk.FLAT, padx=8, pady=2, command=lambda e=entry: show_date_picker(e))
                cal_btn.pack(side=tk.RIGHT, padx=(5, 0))
            else:
                entry = tk.Entry(parent, font=("Microsoft YaHei UI", 11),
                               highlightbackground=self.theme["border"], highlightthickness=1)
                entry.insert(0, default)
                entry.pack(fill=tk.X, ipady=5)
            return entry

        # 日期选择器
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
        e_title = add_field(form, "任务标题", task["title"] if task else "", required=True)
        e_title.focus_set()
        e_date = add_field(form, "日期", task["task_date"] if task else self.current_date.strftime("%Y-%m-%d"), is_date=True)

        # 优先级
        tk.Label(form, text="优先级", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(anchor="w", pady=(12, 2))
        priority_var = tk.IntVar(value=task["priority"] if task else 1)
        pri_frame = tk.Frame(form, bg=self.theme["card_bg"])
        pri_frame.pack(fill=tk.X)
        for val, lbl, color in [(1, "普通", self.theme["primary"]), 
                                (2, "重要", self.theme["warning"]), 
                                (3, "紧急", self.theme["danger"])]:
            rb = tk.Radiobutton(pri_frame, text=lbl, variable=priority_var, value=val,
                               font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"],
                               selectcolor=self.theme["primary_light"])
            rb.pack(side=tk.LEFT, padx=8)

        # 描述
        desc_frame = tk.Frame(form, bg=self.theme["card_bg"])
        desc_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Label(desc_frame, text="描述", font=("Microsoft YaHei UI", 10),
                bg=self.theme["card_bg"], fg=self.theme["text"]).pack(anchor="w")

        desc_container = tk.Frame(desc_frame, bg=self.theme["card_bg"])
        desc_container.pack(fill=tk.X)

        e_desc = tk.Text(desc_container, height=4, font=("Microsoft YaHei UI", 11),
                        wrap=tk.WORD, padx=10, pady=8,
                        highlightbackground=self.theme["border"], highlightthickness=1,
                        spacing1=2, spacing3=2)
        e_desc.pack(fill=tk.X)

        if task:
            e_desc.insert("1.0", task["description"])

        # 重复周期变量（在所有情况下都定义）
        repeat_var = tk.StringVar(value="none")
        week_day_vars = []

        # 预填重复值（编辑时）
        existing_repeat = task["repeat"] if task and task["repeat"] else ""

        # 循环类型选择
        repeat_frame = tk.LabelFrame(form, text=" 重复周期 ", font=("Microsoft YaHei UI", 10),
                                    bg=self.theme["card_bg"], fg=self.theme["text_secondary"])
        repeat_frame.pack(fill=tk.X, pady=(12, 0))

        if existing_repeat == "weekday":
            repeat_var.set("weekday")
        elif existing_repeat:
            repeat_var.set("custom")
            existing_days = set(int(d) for d in existing_repeat.split(",") if d.strip().isdigit())

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

        # 星期选择（直接显示在重复周期内）
        tk.Label(repeat_frame, text="选择星期：", font=("Microsoft YaHei UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack(anchor="w", padx=20, pady=(5, 0))

        week_days = [("一", 0), ("二", 1), ("三", 2), ("四", 3), ("五", 4), ("六", 5), ("日", 6)]

        # 第一行：周一到周四
        row1 = tk.Frame(repeat_frame, bg=self.theme["card_bg"])
        row1.pack(fill=tk.X, padx=20, pady=(2, 0))
        for day_name, day_num in week_days[:4]:
            default_val = 1 if existing_repeat and day_num in existing_days else 0
            var = tk.IntVar(value=default_val)
            week_day_vars.append((day_num, var))
            cb = tk.Checkbutton(row1, text=f"周{day_name}", variable=var,
                               font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"])
            cb.pack(side=tk.LEFT, padx=8)

        # 第二行：周五到周日
        row2 = tk.Frame(repeat_frame, bg=self.theme["card_bg"])
        row2.pack(fill=tk.X, padx=20, pady=(2, 8))
        for day_name, day_num in week_days[4:]:
            default_val = 1 if existing_repeat and day_num in existing_days else 0
            var = tk.IntVar(value=default_val)
            week_day_vars.append((day_num, var))
            cb = tk.Checkbutton(row2, text=f"周{day_name}", variable=var,
                               font=("Microsoft YaHei UI", 10), bg=self.theme["card_bg"])
            cb.pack(side=tk.LEFT, padx=8)


        def save():
            title = e_title.get().strip()
            td = e_date.get().strip()
            desc = e_desc.get("1.0", tk.END).strip()
            pri = priority_var.get()
            
            if not title:
                messagebox.showwarning("提示", "请输入任务标题", parent=dialog)
                e_title.focus_set()
                return
            
            try:
                target_date = datetime.strptime(td, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("提示", "日期格式不正确，请使用 YYYY-MM-DD", parent=dialog)
                e_date.focus_set()
                return

            if tid:
                repeat_type = repeat_var.get()
                repeat_str = ""
                if repeat_type == "weekday":
                    repeat_str = "weekday"
                elif repeat_type == "custom":
                    selected_days = [day_num for day_num, var in week_day_vars if var.get() == 1]
                    if not selected_days:
                        messagebox.showwarning("提示", "请选择至少一个星期日期", parent=dialog)
                        return
                    repeat_str = ",".join(map(str, selected_days))
                DailyTaskDB.update(tid, title, desc, td, pri, repeat_str)
                messagebox.showinfo("成功", "任务已更新！", parent=dialog)
            else:
                repeat_type = repeat_var.get()
                repeat_str = ""
                if repeat_type == "weekday":
                    repeat_str = "weekday"
                elif repeat_type == "custom":
                    selected_days = [day_num for day_num, var in week_day_vars if var.get() == 1]
                    if not selected_days:
                        messagebox.showwarning("提示", "请选择至少一个星期日期", parent=dialog)
                        return
                    repeat_str = ",".join(map(str, selected_days))
                
                if repeat_type == "weekday":
                    # 本周工作日
                    weekday = target_date.weekday()
                    start_of_week = target_date - timedelta(days=weekday)
                    count = 0
                    for i in range(5):
                        d = start_of_week + timedelta(days=i)
                        if DailyTaskDB.add(title, desc, d.strftime("%Y-%m-%d"), pri, repeat_str):
                            count += 1
                    messagebox.showinfo("成功", f"已创建 {count} 个任务（本周工作日）", parent=dialog)
                elif repeat_type == "custom":
                    # 每周指定日期 - 在当月范围内生效
                    selected_days = [day_num for day_num, var in week_day_vars if var.get() == 1]
                    if not selected_days:
                        messagebox.showwarning("提示", "请选择至少一个星期日期", parent=dialog)
                        return
                    
                    # 获取当月第一天和最后一天
                    first_day = target_date.replace(day=1)
                    if target_date.month == 12:
                        last_day = target_date.replace(year=target_date.year+1, month=1, day=1) - timedelta(days=1)
                    else:
                        last_day = target_date.replace(month=target_date.month+1, day=1) - timedelta(days=1)
                    
                    count = 0
                    current_day = first_day
                    while current_day <= last_day:
                        if current_day.weekday() in selected_days:
                            if DailyTaskDB.add(title, desc, current_day.strftime("%Y-%m-%d"), pri, repeat_str):
                                count += 1
                        current_day += timedelta(days=1)
                    
                    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    selected_day_names = [day_names[i] for i in selected_days]
                    messagebox.showinfo("成功", f"已在当月创建 {count} 个任务（{','.join(selected_day_names)}）", parent=dialog)
                else:
                    # 不重复
                    DailyTaskDB.add(title, desc, td, pri, repeat_str)
                    messagebox.showinfo("成功", "任务已添加！", parent=dialog)
            
            dialog.destroy()
            self.refresh()

        def cancel():
            dialog.destroy()

        cancel_btn = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                              bg=self.theme["text_secondary"], fg="white", relief="flat", 
                              padx=20, pady=8, cursor="hand2", command=cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        save_btn = tk.Button(btn_frame, text="保存任务", font=("Microsoft YaHei UI", 11, "bold"),
                           bg=self.theme["primary"], fg="white", relief="flat", 
                           padx=25, pady=8, cursor="hand2", command=save)
        save_btn.pack(side=tk.RIGHT)
        
        # 弹窗居中显示
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w // 2) - 240
        y = parent_y + (parent_h // 2) - 475
        dialog.geometry("+{}+{}".format(x, y))
        
        dialog.wait_window()
