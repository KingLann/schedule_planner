"""
独立测试脚本 - 验证日期选择器颜色逻辑
直接运行: python test_date_picker.py
"""
import tkinter as tk
import calendar
from datetime import date


# ========== 模拟数据（替换成真实数据库即可）==========
# 每日任务: {日期: [{"is_done": 0/1}, ...]}
MOCK_TASKS = {
    "2026-05-22": [{"is_done": 0}, {"is_done": 0}],       # 灰色 - 有任务未完成
    "2026-05-23": [{"is_done": 1}, {"is_done": 0}],       # 绿色 - 有已完成
    "2026-05-25": [{"is_done": 1}],                        # 绿色 - 已完成
    "2026-05-28": [{"is_done": 0}],                        # 灰色 - 未完成
}

# 打卡追踪: {日期: [{"status": 0/1}, ...]}
MOCK_CHECKINS = {
    "2026-05-21": [{"status": 0}],                         # 灰色 - 未打卡
    "2026-05-22": [{"status": 1}],                         # 绿色 - 已打卡
    "2026-05-26": [{"status": 0}, {"status": 1}],         # 绿色 - 有已完成
}

# 日程管理: {日期: (max_priority, all_done)}
MOCK_SCHEDULES = {
    "2026-05-21": (3, False),   # 红色 - 紧急
    "2026-05-24": (2, False),   # 橙色 - 重要
    "2026-05-27": (1, False),   # 蓝色 - 普通
    "2026-05-29": (2, True),    # 绿色 - 已完成
}


def get_color_task(ds, today_str):
    """每日任务模式颜色"""
    tasks = MOCK_TASKS.get(ds, [])
    bg = "#ffffff"
    fg = "#333333"
    if tasks:
        if any(t["is_done"] for t in tasks):
            bg = "#10b981"  # 绿色
        else:
            bg = "#b0b8c4"  # 灰色
        fg = "#ffffff"
    if ds == today_str:
        bg = "#3b82f6"      # 蓝色（今天优先级最高）
        fg = "#ffffff"
    return bg, fg


def get_color_checkin(ds, today_str):
    """打卡追踪模式颜色"""
    items = MOCK_CHECKINS.get(ds, [])
    bg = "#ffffff"
    fg = "#333333"
    if items:
        if any(item["status"] for item in items):
            bg = "#10b981"
        else:
            bg = "#b0b8c4"
        fg = "#ffffff"
    if ds == today_str:
        bg = "#3b82f6"
        fg = "#ffffff"
    return bg, fg


def get_color_schedule(ds, today_str):
    """日程管理模式颜色"""
    bg = "#ffffff"
    fg = "#333333"
    if ds in MOCK_SCHEDULES:
        max_pri, all_done = MOCK_SCHEDULES[ds]
        if all_done:
            bg = "#10b981"
        elif max_pri >= 3:
            bg = "#ef4444"  # 红色
        elif max_pri >= 2:
            bg = "#f59e0b"  # 橙色
        else:
            bg = "#6366f1"  # 蓝色
        fg = "#ffffff"
    if ds == today_str:
        bg = "#3b82f6"
        fg = "#ffffff"
    return bg, fg


class TestDatePicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("日期选择器颜色测试")
        self.root.geometry("420x480")
        self.root.configure(bg="#f0f0f0")

        self.today = date.today()
        self.mode = tk.StringVar(value="task")
        self.pick_year = [self.today.year]
        self.pick_month = [self.today.month]

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # 模式切换按钮
        mode_bar = tk.Frame(self.root, bg="#f0f0f0")
        mode_bar.pack(fill=tk.X, padx=15, pady=(10, 5))

        tk.Label(mode_bar, text="模式:", font=("Microsoft YaHei UI", 10),
                 bg="#f0f0f0").pack(side=tk.LEFT)

        for text, val in [("每日任务", "task"), ("打卡追踪", "checkin"), ("日程管理", "schedule")]:
            tk.Radiobutton(mode_bar, text=text, variable=self.mode, value=val,
                           font=("Microsoft YaHei UI", 10), bg="#f0f0f0",
                           command=self.draw).pack(side=tk.LEFT, padx=8)

        # 月份导航
        nav = tk.Frame(self.root, bg="#ffffff")
        nav.pack(fill=tk.X, padx=15, pady=(5, 5))

        tk.Button(nav, text="◀", font=("Segoe UI", 12), relief="flat",
                  bg="#ffffff", cursor="hand2",
                  command=self._prev).pack(side=tk.LEFT, padx=10)
        self.lbl_title = tk.Label(nav, text="", font=("Microsoft YaHei UI", 14, "bold"),
                                  bg="#ffffff", fg="#333333")
        self.lbl_title.pack(side=tk.LEFT, expand=True)
        tk.Button(nav, text="▶", font=("Segoe UI", 12), relief="flat",
                  bg="#ffffff", cursor="hand2",
                  command=self._next).pack(side=tk.RIGHT, padx=10)

        # 日历网格
        self.grid = tk.Frame(self.root, bg="#ffffff")
        self.grid.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for i, wd in enumerate(weekdays):
            tk.Label(self.grid, text=wd, font=("Microsoft YaHei UI", 10, "bold"),
                     bg="#ffffff", fg="#999999", width=5).grid(row=0, column=i, pady=(0, 4))
            self.grid.columnconfigure(i, weight=1)
        for ri in range(7):
            self.grid.rowconfigure(ri, weight=1)

        # 图例
        legend = tk.Frame(self.root, bg="#f0f0f0")
        legend.pack(fill=tk.X, padx=15, pady=(0, 10))
        for color, text in [("#3b82f6", "今天"), ("#b0b8c4", "未完成"), ("#10b981", "已完成"),
                            ("#ef4444", "紧急"), ("#f59e0b", "重要"), ("#6366f1", "普通")]:
            f = tk.Frame(legend, bg=color, width=16, height=16)
            f.pack(side=tk.LEFT, padx=4)
            f.pack_propagate(False)
            tk.Label(f, text="", bg=color).pack(fill=tk.BOTH, expand=True)
            tk.Label(legend, text=text, font=("Microsoft YaHei UI", 9),
                     bg="#f0f0f0", fg="#666666").pack(side=tk.LEFT, padx=(0, 8))

        self.draw()

    def _prev(self):
        self.pick_month[0] -= 1
        if self.pick_month[0] < 1:
            self.pick_month[0] = 12
            self.pick_year[0] -= 1
        self.draw()

    def _next(self):
        self.pick_month[0] += 1
        if self.pick_month[0] > 12:
            self.pick_month[0] = 1
            self.pick_year[0] += 1
        self.draw()

    def draw(self):
        # 销毁旧格子
        for w in self.grid.grid_slaves():
            if int(w.grid_info().get("row", 0)) > 0:
                w.destroy()

        self.lbl_title.configure(text="{}年{}月".format(self.pick_year[0], self.pick_month[0]))
        cal = calendar.monthcalendar(self.pick_year[0], self.pick_month[0])
        today_str = self.today.strftime("%Y-%m-%d")
        mode = self.mode.get()

        color_fn = {"task": get_color_task,
                    "checkin": get_color_checkin,
                    "schedule": get_color_schedule}[mode]

        for row_idx, week in enumerate(cal):
            for col_idx, day_num in enumerate(week):
                r = row_idx + 1
                if day_num == 0:
                    tk.Label(self.grid, text="", bg="#ffffff",
                             width=5).grid(row=r, column=col_idx, sticky="nsew")
                    continue

                d = date(self.pick_year[0], self.pick_month[0], day_num)
                ds = d.strftime("%Y-%m-%d")
                bg, fg = color_fn(ds, today_str)

                cell = tk.Label(self.grid, text=str(day_num),
                                font=("Microsoft YaHei UI", 11),
                                bg=bg, fg=fg, width=5, height=1,
                                cursor="hand2")
                cell.grid(row=r, column=col_idx, padx=3, pady=3, sticky="nsew")


if __name__ == "__main__":
    TestDatePicker()
