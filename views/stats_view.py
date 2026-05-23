import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, date, timedelta
from collections import defaultdict
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import ScheduleDB, DailyTaskDB, CheckinDB, DiaryDB

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei UI", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class StatsView(tk.Frame):

    def __init__(self, parent, theme=None, on_navigate=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f8f9fa")
        self.theme = theme or {
            "bg": "#f8f9fa", "card_bg": "#ffffff", "primary": "#007bff",
            "primary_light": "#e3f2fd", "success": "#28a745", "danger": "#dc3545",
            "warning": "#ffc107", "info": "#17a2b8", "text": "#343a40",
            "text_secondary": "#6c757d", "border": "#dee2e6",
        }
        self._range_var = None
        self._figures = []
        self._canvases = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # 标题栏
        header = tk.Frame(self, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=25, pady=(20, 5))
        tk.Label(header, text="📈 数据统计", font=("Microsoft YaHei UI", 18, "bold"),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  可视化数据分析", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        # 时间范围选择
        ctrl = tk.Frame(self, bg=self.theme["bg"])
        ctrl.pack(fill=tk.X, padx=25, pady=(0, 5))
        tk.Label(ctrl, text="时间范围：", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        self._range_var = tk.StringVar(value="近30天")
        cb = ttk.Combobox(ctrl, textvariable=self._range_var, state="readonly", width=10,
                          values=["近7天", "近30天", "近90天", "全部"])
        cb.pack(side=tk.LEFT, padx=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Button(ctrl, text="🔄 刷新", command=self.refresh, bootstyle="outline").pack(side=tk.LEFT)

        # 数据统计卡片
        self.stats_bar = tk.Frame(self, bg=self.theme["bg"])
        self.stats_bar.pack(fill=tk.X, padx=25, pady=(0, 5))
        self.stat_labels = {}
        stats = [
            ("total", "总数据", self.theme["primary"]),
            ("schedule", "日程管理", self.theme["info"]),
            ("task", "每日任务", self.theme["warning"]),
            ("checkin", "打卡追踪", self.theme["success"]),
            ("diary", "我的日记", self.theme["danger"]),
        ]
        for key, label, color in stats:
            card = tk.Frame(self.stats_bar, bg=self.theme["card_bg"],
                            highlightbackground=self.theme["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
            tk.Label(card, text=label, bg=self.theme["card_bg"],
                     font=("Microsoft YaHei UI", 9), fg=self.theme["text_secondary"]).pack(pady=(8, 0))
            lbl = tk.Label(card, text="0", bg=self.theme["card_bg"],
                           font=("Microsoft YaHei UI", 20, "bold"), fg=color)
            lbl.pack(pady=(0, 4))
            sub = tk.Label(card, text="", bg=self.theme["card_bg"],
                           font=("Microsoft YaHei UI", 8), fg=self.theme["text_secondary"])
            sub.pack(pady=(0, 8))
            self.stat_labels[key] = (lbl, sub)

        # 可滚动图表区域
        container = tk.Frame(self, bg=self.theme["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))

        self._canvas_scroll = tk.Canvas(container, bg=self.theme["bg"], highlightthickness=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas_scroll.yview)
        self._chart_frame = tk.Frame(self._canvas_scroll, bg=self.theme["bg"])

        self._chart_frame.bind("<Configure>",
                               lambda e: self._canvas_scroll.configure(scrollregion=self._canvas_scroll.bbox("all")))
        self._canvas_scroll.create_window((0, 0), window=self._chart_frame, anchor="nw")
        self._canvas_scroll.configure(yscrollcommand=vbar.set)

        self._canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮支持
        self._canvas_scroll.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self._canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # 数据
    # ------------------------------------------------------------------

    def _get_range(self):
        label = self._range_var.get()
        today = date.today()
        if label == "近7天":
            return (today - timedelta(days=6)).isoformat(), today.isoformat()
        elif label == "近30天":
            return (today - timedelta(days=29)).isoformat(), today.isoformat()
        elif label == "近90天":
            return (today - timedelta(days=89)).isoformat(), today.isoformat()
        else:
            return "2000-01-01", today.isoformat()

    def _aggregate_daily(self, start, end):
        """按日期聚合：返回 (dates, schedule_total, schedule_done, task_total, task_done, checkin_total, checkin_done)"""
        s_start = date.fromisoformat(start)
        s_end = date.fromisoformat(end)
        days = (s_end - s_start).days + 1
        dates = [(s_start + timedelta(days=i)).isoformat() for i in range(days)]

        # 日程
        schedules = ScheduleDB.get_range(start, end)
        s_total = defaultdict(int)
        s_done = defaultdict(int)
        for r in schedules:
            d = r["schedule_date"]
            s_total[d] += 1
            s_done[d] += r["is_done"]

        # 每日任务
        tasks = DailyTaskDB.get_range(start, end)
        t_total = defaultdict(int)
        t_done = defaultdict(int)
        for r in tasks:
            d = r["task_date"]
            t_total[d] += 1
            t_done[d] += r["is_done"]

        # 打卡
        checkins = CheckinDB.get_range(start, end)
        c_total = defaultdict(int)
        c_done = defaultdict(int)
        for r in checkins:
            d = r["checkin_date"]
            c_total[d] += 1
            c_done[d] += r["status"]

        return dates, s_total, s_done, t_total, t_done, c_total, c_done

    # ------------------------------------------------------------------
    # 绘图
    # ------------------------------------------------------------------

    def _clear_charts(self):
        for c in self._canvases:
            c.get_tk_widget().destroy()
        for f in self._figures:
            plt.close(f)
        self._figures.clear()
        self._canvases.clear()

    def _add_chart(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill=tk.X, pady=(0, 15))
        self._figures.append(fig)
        self._canvases.append(canvas)

    def _draw_empty(self, title):
        fig = Figure(figsize=(9, 3), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                fontsize=14, color=self.theme["text_secondary"], transform=ax.transAxes)
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.tight_layout()
        self._add_chart(fig)

    def _plot_task_trend(self, dates, s_total, s_done, t_total, t_done):
        title = "任务完成趋势"
        has_data = any(s_total.values()) or any(t_total.values())
        if not has_data:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        x = range(len(dates))
        labels = [d[5:] for d in dates]  # MM-DD

        # 如果数据点太多，只显示部分标签
        step = max(1, len(dates) // 12)

        sch_total = [s_total.get(d, 0) for d in dates]
        sch_done = [s_done.get(d, 0) for d in dates]
        tk_total = [t_total.get(d, 0) for d in dates]
        tk_done = [t_done.get(d, 0) for d in dates]

        lines = []
        lines.append(ax.plot(x, sch_total, label="日程总数", color=self.theme["primary"], marker="o", markersize=4)[0])
        lines.append(ax.plot(x, sch_done, label="日程完成", color=self.theme["success"], marker="o", markersize=4, linestyle="--")[0])
        lines.append(ax.plot(x, tk_total, label="任务总数", color=self.theme["warning"], marker="s", markersize=4)[0])
        lines.append(ax.plot(x, tk_done, label="任务完成", color=self.theme["info"], marker="s", markersize=4, linestyle="--")[0])

        ax.set_xticks(list(x)[::step])
        ax.set_xticklabels(labels[::step], rotation=45, fontsize=8)
        ax.set_ylabel("数量", fontsize=10)
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)

        # 悬浮提示
        annot = ax.annotate("", xy=(0, 0), xytext=(12, 12),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.4", fc="#ffffff", ec="#cccccc", alpha=0.95),
                            fontsize=9, color=self.theme["text"],
                            arrowprops=dict(arrowstyle="->", color="#999999"),
                            visible=False)

        def on_hover(event):
            if event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
                return
            visible = False
            for line in lines:
                contains, info = line.contains(event)
                if contains:
                    idx = info["ind"][0]
                    px, py = line.get_xdata()[idx], line.get_ydata()[idx]
                    annot.xy = (px, py)
                    annot.set_text(f"{labels[idx]}\n{line.get_label()}: {int(py)}")
                    visible = True
                    break
            if annot.get_visible() != visible:
                annot.set_visible(visible)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_hover)

        fig.tight_layout()
        self._add_chart(fig)

    def _plot_checkin_trend(self, dates, c_total, c_done):
        title = "打卡完成率趋势"
        has_data = any(c_total.values())
        if not has_data:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        x = range(len(dates))
        labels = [d[5:] for d in dates]
        step = max(1, len(dates) // 12)

        rates = []
        for d in dates:
            total = c_total.get(d, 0)
            done = c_done.get(d, 0)
            rates.append((done / total * 100) if total > 0 else 0)

        ax.fill_between(x, rates, alpha=0.2, color=self.theme["success"])
        ax.plot(x, rates, color=self.theme["success"], marker="o", markersize=3, label="完成率")

        ax.set_xticks(list(x)[::step])
        ax.set_xticklabels(labels[::step], rotation=45, fontsize=8)
        ax.set_ylabel("完成率 (%)", fontsize=10)
        ax.set_ylim(-5, 105)
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._add_chart(fig)

    def _plot_type_distribution(self, s_total, t_total, c_total):
        title = "数据类型分布"
        values = [sum(s_total.values()), sum(t_total.values()), sum(c_total.values())]
        if sum(values) == 0:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["bg"])

        labels_raw = ["日程管理", "每日任务", "打卡追踪"]
        colors = [self.theme["primary"], self.theme["warning"], self.theme["success"]]
        # 过滤0值
        filtered = [(l, v, c) for l, v, c in zip(labels_raw, values, colors) if v > 0]
        if not filtered:
            self._draw_empty(title)
            return

        f_labels, f_values, f_colors = zip(*filtered)
        wedges, texts, autotexts = ax.pie(
            f_values, labels=f_labels, colors=f_colors, autopct="%1.1f%%",
            startangle=90, textprops={"fontsize": 10}
        )
        for t in autotexts:
            t.set_fontsize(9)
            t.set_color("white")
            t.set_fontweight("bold")
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        fig.tight_layout()
        self._add_chart(fig)

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def _update_stat_cards(self, s_total, s_done, t_total, t_done, c_total, c_done, diary_count):
        s_all = sum(s_total.values())
        s_fin = sum(s_done.values())
        t_all = sum(t_total.values())
        t_fin = sum(t_done.values())
        c_all = sum(c_total.values())
        c_fin = sum(c_done.values())
        total_all = s_all + t_all + c_all + diary_count
        total_fin = s_fin + t_fin + c_fin

        def rate(done, total):
            return f"{done / total * 100:.0f}%" if total > 0 else "-"

        # 总数据
        lbl, sub = self.stat_labels["total"]
        lbl.configure(text=str(total_all))
        sub.configure(text=f"完成 {total_fin} · 完成率 {rate(total_fin, total_all)}")

        # 日程管理
        lbl, sub = self.stat_labels["schedule"]
        lbl.configure(text=str(s_all))
        sub.configure(text=f"完成 {s_fin} · 完成率 {rate(s_fin, s_all)}")

        # 每日任务
        lbl, sub = self.stat_labels["task"]
        lbl.configure(text=str(t_all))
        sub.configure(text=f"完成 {t_fin} · 完成率 {rate(t_fin, t_all)}")

        # 打卡追踪
        lbl, sub = self.stat_labels["checkin"]
        lbl.configure(text=str(c_all))
        sub.configure(text=f"完成 {c_fin} · 完成率 {rate(c_fin, c_all)}")

        # 我的日记
        lbl, sub = self.stat_labels["diary"]
        lbl.configure(text=str(diary_count))
        sub.configure(text="篇")

    def refresh(self):
        self._clear_charts()
        start, end = self._get_range()
        dates, s_total, s_done, t_total, t_done, c_total, c_done = self._aggregate_daily(start, end)
        diary_count = DiaryDB.count_range(start, end)

        self._update_stat_cards(s_total, s_done, t_total, t_done, c_total, c_done, diary_count)

        self._plot_task_trend(dates, s_total, s_done, t_total, t_done)
        self._plot_checkin_trend(dates, c_total, c_done)
        self._plot_type_distribution(s_total, t_total, c_total)

        # 更新滚动区域
        self._chart_frame.update_idletasks()
        self._canvas_scroll.configure(scrollregion=self._canvas_scroll.bbox("all"))
