import tkinter as tk
import calendar
from datetime import date


def show_date_picker(parent, on_select, initial_date=None, dot_callback=None,
                     theme=None):
    """
    通用日期选择器弹窗

    Args:
        parent: 父窗口
        on_select: 回调函数，接收选中的 date 对象
        initial_date: 初始年月 (date对象)，默认今天
        dot_callback: 可选回调 (date_str) -> (has_event, bg_color)，用于背景色标注日期
        theme: 主题字典
    """
    theme = theme or {
        "bg": "#f1f5f9", "card_bg": "#ffffff", "primary": "#6366f1",
        "primary_light": "#e0e7ff", "text": "#1e293b", "text_secondary": "#64748b",
    }

    today = date.today()
    init = initial_date or today

    picker = tk.Toplevel(parent)
    picker.title("选择日期")
    picker.geometry("340x340")
    picker.resizable(False, False)
    picker.configure(bg=theme["card_bg"])
    picker.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
    picker.grab_set()

    # 居中
    picker.update_idletasks()
    top = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
    px = top.winfo_x()
    py = top.winfo_y()
    pw = top.winfo_width()
    ph = top.winfo_height()
    picker.geometry("+{}+{}".format(px + pw // 2 - 170, py + ph // 2 - 170))

    pick_year = [init.year]
    pick_month = [init.month]

    # 月份导航
    nav = tk.Frame(picker, bg=theme["card_bg"])
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
             bg=theme["card_bg"], cursor="hand2", command=prev_m).pack(side=tk.LEFT)
    lbl_month = tk.Label(nav, text="", font=("Microsoft YaHei UI", 12, "bold"),
                         bg=theme["card_bg"], fg=theme["text"])
    lbl_month.pack(side=tk.LEFT, expand=True)
    tk.Button(nav, text="▶", font=("Segoe UI", 10), relief="flat",
             bg=theme["card_bg"], cursor="hand2", command=next_m).pack(side=tk.RIGHT)

    # 日历网格
    grid = tk.Frame(picker, bg=theme["card_bg"])
    grid.pack(fill=tk.BOTH, expand=True, padx=15)

    days = ["一", "二", "三", "四", "五", "六", "日"]
    for i, d in enumerate(days):
        tk.Label(grid, text=d, font=("Microsoft YaHei UI", 9, "bold"),
                bg=theme["card_bg"], fg=theme["text_secondary"],
                width=4).grid(row=0, column=i, pady=2, sticky="nsew")
        grid.columnconfigure(i, weight=1)

    def draw():
        for w in grid.winfo_children():
            if int(w.grid_info()["row"]) > 0:
                w.destroy()

        lbl_month.configure(text=f"{pick_year[0]}年{pick_month[0]}月")
        cal = calendar.monthcalendar(pick_year[0], pick_month[0])

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(grid, text="", bg=theme["card_bg"],
                            width=4).grid(row=row_idx + 1, column=col_idx, sticky="nsew")
                    continue

                d = date(pick_year[0], pick_month[0], day)
                is_today = d == today

                # 默认样式
                bg = theme["card_bg"]
                fg = theme["text"]
                ft = ("Microsoft YaHei UI", 10)

                # 背景色标注（方框底色）
                if dot_callback:
                    date_str = d.strftime("%Y-%m-%d")
                    has_event, event_bg = dot_callback(date_str)
                    if has_event:
                        bg = event_bg
                        fg = "#ffffff"

                # 今天高亮优先级最高
                if is_today:
                    bg = theme["primary_light"]
                    fg = theme["primary"]
                    ft = ("Microsoft YaHei UI", 10, "bold")

                cell = tk.Label(grid, text=str(day), font=ft,
                               bg=bg, fg=fg, width=4, cursor="hand2")
                cell.grid(row=row_idx + 1, column=col_idx, pady=2, padx=1, sticky="nsew")

                cell.bind("<Button-1>", lambda e, dd=d: (on_select(dd), picker.destroy()))

    # 底部按钮
    btn_frame = tk.Frame(picker, bg=theme["card_bg"])
    btn_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
    tk.Button(btn_frame, text="今天", font=("Microsoft YaHei UI", 10),
             bg=theme["primary_light"], fg=theme["primary"],
             relief="flat", padx=12, pady=3, cursor="hand2",
             command=lambda: (on_select(today), picker.destroy())).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="关闭", font=("Microsoft YaHei UI", 10),
             bg=theme["text_secondary"], fg="white",
             relief="flat", padx=12, pady=3, cursor="hand2",
             command=picker.destroy).pack(side=tk.RIGHT)

    draw()
