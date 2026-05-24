import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, date, timedelta
from collections import defaultdict
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import ScheduleDB, DailyTaskDB, CheckinDB

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei UI", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

WEEKDAY_NAMES = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
PRIORITY_NAMES = {1: "普通", 2: "重要", 3: "紧急"}


class ProcrastinationView(tk.Frame):

    def __init__(self, parent, theme=None):
        super().__init__(parent, bg=theme["bg"] if theme else "#f8f9fa")
        self.theme = theme or {
            "bg": "#f8f9fa", "card_bg": "#ffffff", "primary": "#007bff",
            "primary_light": "#e3f2fd", "success": "#28a745", "danger": "#dc3545",
            "warning": "#ffc107", "info": "#17a2b8", "text": "#343a40",
            "text_secondary": "#6c757d", "border": "#dee2e6",
        }
        self._range_var = None
        self._exclude_repeat_var = None
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
        tk.Label(header, text="⏳ 拖延统计", font=("Microsoft YaHei UI", 18, "bold"),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        tk.Label(header, text="  分析你的拖延习惯", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["bg"], fg=self.theme["text_secondary"]).pack(side=tk.LEFT, pady=5)

        # 控制栏
        ctrl = tk.Frame(self, bg=self.theme["bg"])
        ctrl.pack(fill=tk.X, padx=25, pady=(0, 5))
        tk.Label(ctrl, text="时间范围：", font=("Microsoft YaHei UI", 10),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        self._range_var = tk.StringVar(value="近30天")
        cb = ttk.Combobox(ctrl, textvariable=self._range_var, state="readonly", width=10,
                          values=["近7天", "近30天", "近90天", "全部"])
        cb.pack(side=tk.LEFT, padx=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        self._exclude_repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="排除重复任务", variable=self._exclude_repeat_var,
                        command=self.refresh, bootstyle="round-toggle").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ctrl, text="🔄 刷新", command=self.refresh, bootstyle="outline").pack(side=tk.LEFT)

        # 统计卡片
        self.stats_bar = tk.Frame(self, bg=self.theme["bg"])
        self.stats_bar.pack(fill=tk.X, padx=25, pady=(0, 5))
        self.stat_labels = {}
        stats = [
            ("total", "总拖延", self.theme["danger"]),
            ("overdue", "到期未完成", "#e67700"),
            ("postponed", "推迟任务", self.theme["warning"]),
            ("schedule", "日程拖延", self.theme["info"]),
            ("task", "任务拖延", self.theme["primary"]),
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

        # 智能洞察区域
        self._insight_frame = tk.Frame(self, bg=self.theme["bg"])
        self._insight_frame.pack(fill=tk.X, padx=25, pady=(0, 5))
        self._insight_lbl = tk.Label(self._insight_frame, text="", font=("Microsoft YaHei UI", 9),
                                     bg=self.theme["bg"], fg=self.theme["text_secondary"],
                                     wraplength=900, justify=tk.LEFT, anchor="w")
        self._insight_lbl.pack(fill=tk.X)

        # 可滚动图表区域
        container = tk.Frame(self, bg=self.theme["bg"])
        container.pack(fill=tk.X, padx=25, pady=(0, 10))

        self._canvas_scroll = tk.Canvas(container, bg=self.theme["bg"], highlightthickness=0, height=400)
        vbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas_scroll.yview)
        self._chart_frame = tk.Frame(self._canvas_scroll, bg=self.theme["bg"])

        self._chart_frame.bind("<Configure>",
                               lambda e: self._canvas_scroll.configure(scrollregion=self._canvas_scroll.bbox("all")))
        self._canvas_scroll.create_window((0, 0), window=self._chart_frame, anchor="nw")
        self._canvas_scroll.configure(yscrollcommand=vbar.set)

        self._canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas_scroll.bind("<MouseWheel>", self._on_mousewheel)

        # 拖延明细表格
        detail_header = tk.Frame(self, bg=self.theme["bg"])
        detail_header.pack(fill=tk.X, padx=25, pady=(5, 3))
        tk.Label(detail_header, text="📋 拖延明细", font=("Microsoft YaHei UI", 13, "bold"),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        self._detail_count_lbl = tk.Label(detail_header, text="", font=("Microsoft YaHei UI", 9),
                                          bg=self.theme["bg"], fg=self.theme["text_secondary"])
        self._detail_count_lbl.pack(side=tk.LEFT, padx=(10, 0))

        # 筛选栏
        filter_bar = tk.Frame(self, bg=self.theme["bg"])
        filter_bar.pack(fill=tk.X, padx=25, pady=(0, 3))
        tk.Label(filter_bar, text="筛选：", font=("Microsoft YaHei UI", 9),
                 bg=self.theme["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        self._detail_filter_var = tk.StringVar(value="全部")
        cb2 = ttk.Combobox(filter_bar, textvariable=self._detail_filter_var, state="readonly", width=12,
                           values=["全部", "到期未完成", "推迟任务", "日程", "任务", "打卡"])
        cb2.pack(side=tk.LEFT, padx=(0, 5))
        cb2.bind("<<ComboboxSelected>>", lambda e: self._apply_detail_filter())

        # 表格
        tree_container = tk.Frame(self, bg=self.theme["card_bg"],
                                  highlightbackground=self.theme["border"], highlightthickness=1)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))

        style = ttk.Style()
        style.configure("Procrastination.Treeview", font=("Microsoft YaHei UI", 10), rowheight=32)
        style.configure("Procrastination.Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

        cols = ("module", "title", "date", "count", "priority", "type")
        col_names = {"module": "模块", "title": "标题", "date": "计划日期",
                     "count": "次数", "priority": "优先级", "type": "拖延类型"}
        col_widths = {"module": 70, "title": 240, "date": 200, "count": 55, "priority": 70, "type": 90}

        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings",
                                 style="Procrastination.Treeview", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=col_names[c])
            self.tree.column(c, width=col_widths[c], minwidth=60, anchor="center")

        tree_vbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_vbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_vbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 标签颜色
        self.tree.tag_configure("overdue", foreground="#e67700")
        self.tree.tag_configure("postponed", foreground="#c47400")
        self.tree.tag_configure("overdue_high", foreground=self.theme["danger"])
        self.tree.tag_configure("overdue_mid", foreground="#e67700")
        self.tree.tag_configure("overdue_low", foreground="#8a6d00")

        self._all_detail_items = []

    def _on_mousewheel(self, event):
        self._canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # 数据
    # ------------------------------------------------------------------

    def _get_range(self):
        label = self._range_var.get()
        today = date.today()
        if label == "近7天":
            start = today - timedelta(days=6)
        elif label == "近30天":
            start = today - timedelta(days=29)
        elif label == "近90天":
            start = today - timedelta(days=89)
        else:
            return "2000-01-01", today.isoformat(), None, None

        cur_start = start.isoformat()
        cur_end = today.isoformat()
        days = (today - start).days + 1
        prev_end = (start - timedelta(days=1)).isoformat()
        prev_start = (start - timedelta(days=days)).isoformat()
        return cur_start, cur_end, prev_start, prev_end

    def _get_exclude_repeat(self):
        return self._exclude_repeat_var.get()

    def _load_data(self, start, end, prev_start=None, prev_end=None):
        """加载所有拖延数据，返回统一的字典"""
        er = self._get_exclude_repeat()

        # 到期未完成
        s_overdue = ScheduleDB.get_overdue(start, end)
        t_overdue = DailyTaskDB.get_overdue(start, end, exclude_repeat=er)
        c_overdue = CheckinDB.get_overdue(start, end, exclude_repeat=er)

        # 推迟任务（不依赖时间范围）
        s_postponed = ScheduleDB.get_postponed()
        t_postponed = DailyTaskDB.get_postponed()

        # 按日期分组
        s_by_date = ScheduleDB.get_overdue_grouped_by_date(start, end)
        t_by_date = DailyTaskDB.get_overdue_grouped_by_date(start, end, exclude_repeat=er)
        c_by_date = CheckinDB.get_overdue_grouped_by_date(start, end, exclude_repeat=er)

        # 按星期几分组（合并三个模块）
        s_wd = ScheduleDB.get_overdue_grouped_by_weekday(start, end)
        t_wd = DailyTaskDB.get_overdue_grouped_by_weekday(start, end, exclude_repeat=er)
        c_wd = CheckinDB.get_overdue_grouped_by_weekday(start, end, exclude_repeat=er)

        # 按优先级分组（日程+任务）
        s_pri = ScheduleDB.get_overdue_grouped_by_priority(start, end)
        t_pri = DailyTaskDB.get_overdue_grouped_by_priority(start, end, exclude_repeat=er)

        # 上一周期对比数据
        prev = None
        if prev_start and prev_end:
            prev = {
                "s_overdue": len(ScheduleDB.get_overdue(prev_start, prev_end)),
                "t_overdue": len(DailyTaskDB.get_overdue(prev_start, prev_end, exclude_repeat=er)),
                "c_overdue": len(CheckinDB.get_overdue(prev_start, prev_end, exclude_repeat=er)),
            }

        return {
            "s_overdue": s_overdue, "t_overdue": t_overdue, "c_overdue": c_overdue,
            "s_postponed": s_postponed, "t_postponed": t_postponed,
            "s_by_date": s_by_date, "t_by_date": t_by_date, "c_by_date": c_by_date,
            "s_wd": s_wd, "t_wd": t_wd, "c_wd": c_wd,
            "s_pri": s_pri, "t_pri": t_pri,
            "prev": prev,
        }

    # ------------------------------------------------------------------
    # 绘图工具
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

    # ------------------------------------------------------------------
    # 图表
    # ------------------------------------------------------------------

    def _plot_overdue_trend(self, dates, s_by_date, t_by_date, c_by_date):
        """拖延趋势折线图"""
        title = "拖延趋势"
        has_data = any(r["c"] > 0 for r in s_by_date) or any(r["c"] > 0 for r in t_by_date) or any(r["c"] > 0 for r in c_by_date)
        if not has_data:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        x = range(len(dates))
        labels = [d[5:] for d in dates]
        step = max(1, len(dates) // 12)

        # 构建日期->计数映射
        def to_dict(rows):
            return {r["d"]: r["c"] for r in rows}

        sd, td, cd = to_dict(s_by_date), to_dict(t_by_date), to_dict(c_by_date)
        s_vals = [sd.get(d, 0) for d in dates]
        t_vals = [td.get(d, 0) for d in dates]
        c_vals = [cd.get(d, 0) for d in dates]

        lines = []
        lines.append(ax.plot(x, s_vals, label="日程拖延", color=self.theme["info"], marker="o", markersize=4)[0])
        lines.append(ax.plot(x, t_vals, label="任务拖延", color=self.theme["primary"], marker="s", markersize=4)[0])
        lines.append(ax.plot(x, c_vals, label="打卡拖延", color=self.theme["success"], marker="^", markersize=4)[0])

        ax.set_xticks(list(x)[::step])
        ax.set_xticklabels(labels[::step], rotation=45, fontsize=8)
        ax.set_ylabel("拖延数量", fontsize=10)
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

    def _plot_type_pie(self, overdue_count, postponed_count):
        """拖延类型分布饼图（点击联动筛选）"""
        title = "拖延类型分布"
        if overdue_count + postponed_count == 0:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["bg"])

        labels_raw = ["到期未完成", "推迟任务"]
        values = [overdue_count, postponed_count]
        colors = ["#e67700", self.theme["warning"]]
        filtered = [(l, v, c) for l, v, c in zip(labels_raw, values, colors) if v > 0]
        f_labels, f_values, f_colors = zip(*filtered)

        wedges, texts, autotexts = ax.pie(
            f_values, labels=f_labels, colors=f_colors, autopct="%1.1f%%",
            startangle=90, textprops={"fontsize": 10}
        )
        for t in autotexts:
            t.set_fontsize(9)
            t.set_color("white")
            t.set_fontweight("bold")
        ax.set_title(title + "（点击扇形筛选明细）", fontsize=13, fontweight="bold", color=self.theme["text"])

        # 点击扇形联动筛选
        label_to_filter = {"到期未完成": "到期未完成", "推迟任务": "推迟任务"}

        def on_pie_click(event):
            if event.inaxes != ax:
                return
            for wedge, label in zip(wedges, f_labels):
                contains, _ = wedge.contains(event)
                if contains:
                    filt = label_to_filter.get(label, "全部")
                    self._detail_filter_var.set(filt)
                    self._apply_detail_filter()
                    return

        fig.canvas.mpl_connect("button_press_event", on_pie_click)
        fig.tight_layout()
        self._add_chart(fig)

    def _plot_module_bar(self, s_overdue, t_overdue, c_overdue, s_postponed, t_postponed):
        """模块拖延对比柱状图（点击联动筛选）"""
        title = "模块拖延对比"
        total = len(s_overdue) + len(t_overdue) + len(c_overdue) + len(s_postponed) + len(t_postponed)
        if total == 0:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        modules = ["日程管理", "每日任务", "打卡追踪"]
        module_filters = ["日程", "任务", "打卡"]
        overdue_vals = [len(s_overdue), len(t_overdue), len(c_overdue)]
        postponed_vals = [len(s_postponed), len(t_postponed), 0]

        y = range(len(modules))
        bar_h = 0.35

        bars1 = ax.barh([i - bar_h / 2 for i in y], overdue_vals, bar_h,
                        label="到期未完成", color="#e67700", alpha=0.85)
        bars2 = ax.barh([i + bar_h / 2 for i in y], postponed_vals, bar_h,
                        label="推迟任务", color=self.theme["warning"], alpha=0.85)

        for bars in [bars1, bars2]:
            for bar in bars:
                w = bar.get_width()
                if w > 0:
                    ax.text(w + 0.2, bar.get_y() + bar.get_height() / 2, str(int(w)),
                            va="center", fontsize=9, color=self.theme["text"])

        ax.set_yticks(list(y))
        ax.set_yticklabels(modules, fontsize=10)
        ax.set_xlabel("数量", fontsize=10)
        ax.set_title(title + "（点击柱子筛选明细）", fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.legend(fontsize=8)
        ax.grid(True, axis="x", alpha=0.3)
        fig.tight_layout()

        # 点击柱子联动筛选
        def on_bar_click(event):
            if event.inaxes != ax:
                return
            for i, bar in enumerate(list(bars1) + list(bars2)):
                contains, _ = bar.contains(event)
                if contains:
                    # 找到对应的模块
                    bar_y = bar.get_y() + bar.get_height() / 2
                    mod_idx = int(round(bar_y))
                    if 0 <= mod_idx < len(module_filters):
                        self._detail_filter_var.set(module_filters[mod_idx])
                        self._apply_detail_filter()
                    return

        fig.canvas.mpl_connect("button_press_event", on_bar_click)
        self._add_chart(fig)

    def _plot_weekday_bar(self, s_wd, t_wd, c_wd):
        """星期拖延分布柱状图"""
        title = "星期拖延分布"
        total = sum(r["c"] for r in s_wd) + sum(r["c"] for r in t_wd) + sum(r["c"] for r in c_wd)
        if total == 0:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        # 合并三个模块：注意 SQLite 的 %w 返回 0=周日, 1=周一, ...
        counts = [0] * 7
        for r in s_wd:
            counts[r["wd"]] += r["c"]
        for r in t_wd:
            counts[r["wd"]] += r["c"]
        for r in c_wd:
            counts[r["wd"]] += r["c"]

        # 重排为 周一~周日
        reordered = counts[1:] + counts[:1]  # Mon..Sun
        x = range(7)
        colors = [self.theme["primary"]] * 7
        bars = ax.bar(x, reordered, color=colors, alpha=0.8, edgecolor="white")

        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, str(int(h)),
                        ha="center", fontsize=9, color=self.theme["text"])

        ax.set_xticks(list(x))
        ax.set_xticklabels(WEEKDAY_NAMES[1:] + [WEEKDAY_NAMES[0]], fontsize=10)
        ax.set_ylabel("拖延数量", fontsize=10)
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        self._add_chart(fig)

    def _plot_priority_bar(self, s_pri, t_pri):
        """优先级拖延分析柱状图"""
        title = "优先级拖延分析"
        total = sum(r["c"] for r in s_pri) + sum(r["c"] for r in t_pri)
        if total == 0:
            self._draw_empty(title)
            return

        fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.theme["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.theme["card_bg"])

        # 合并日程+任务的优先级拖延
        pri_counts = defaultdict(int)
        for r in s_pri:
            pri_counts[r["priority"]] += r["c"]
        for r in t_pri:
            pri_counts[r["priority"]] += r["c"]

        prios = sorted(pri_counts.keys())
        labels = [PRIORITY_NAMES.get(p, f"P{p}") for p in prios]
        values = [pri_counts[p] for p in prios]

        color_map = {1: self.theme["success"], 2: self.theme["warning"], 3: self.theme["danger"]}
        colors = [color_map.get(p, self.theme["primary"]) for p in prios]

        x = range(len(prios))
        bars = ax.bar(x, values, color=colors, alpha=0.85, edgecolor="white")

        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, str(int(h)),
                        ha="center", fontsize=9, color=self.theme["text"])

        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=10)
        ax.set_ylabel("拖延数量", fontsize=10)
        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"])
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        self._add_chart(fig)

    # ------------------------------------------------------------------
    # 统计卡片更新 + 环比对比
    # ------------------------------------------------------------------

    @staticmethod
    def _trend_text(cur, prev):
        """生成环比变化文本，如 '↓20%' 或 '↑15%'"""
        if prev is None or prev == 0:
            return "" if cur == 0 else ""
        if cur == 0:
            return " ↓100%"
        pct = (cur - prev) / prev * 100
        if abs(pct) < 1:
            return " 持平"
        arrow = "↑" if pct > 0 else "↓"
        color_hint = "↑" if pct > 0 else "↓"
        return f" {arrow}{abs(pct):.0f}%"

    def _update_stat_cards(self, data):
        s_over = len(data["s_overdue"])
        t_over = len(data["t_overdue"])
        c_over = len(data["c_overdue"])
        s_post = len(data["s_postponed"])
        t_post = len(data["t_postponed"])

        overdue_total = s_over + t_over + c_over
        postponed_total = s_post + t_post
        total = overdue_total + postponed_total
        schedule_total = s_over + s_post
        task_total = t_over + t_post

        prev = data.get("prev")
        if prev:
            prev_overdue = prev["s_overdue"] + prev["t_overdue"] + prev["c_overdue"]
            prev_total = prev_overdue
        else:
            prev_overdue = None
            prev_total = None

        def _colored_trend(cur, prev_val):
            """返回趋势文本，拖延减少用绿色，增加用红色"""
            if prev_val is None or prev_val == 0:
                return ""
            if cur == 0:
                return " ↓100%"
            pct = (cur - prev_val) / prev_val * 100
            if abs(pct) < 1:
                return " 持平"
            arrow = "↑" if pct > 0 else "↓"
            return f" {arrow}{abs(pct):.0f}%"

        trend_total = _colored_trend(total, prev_total)
        trend_overdue = _colored_trend(overdue_total, prev_overdue)

        lbl, sub = self.stat_labels["total"]
        lbl.configure(text=str(total))
        sub.configure(text=f"到期 {overdue_total} · 推迟 {postponed_total}{trend_total}")

        lbl, sub = self.stat_labels["overdue"]
        lbl.configure(text=str(overdue_total))
        sub.configure(text=f"日程{s_over} · 任务{t_over} · 打卡{c_over}{trend_overdue}")

        lbl, sub = self.stat_labels["postponed"]
        lbl.configure(text=str(postponed_total))
        sub.configure(text=f"日程{s_post} · 任务{t_post}")

        lbl, sub = self.stat_labels["schedule"]
        lbl.configure(text=str(schedule_total))
        sub.configure(text=f"到期{s_over} · 推迟{s_post}")

        lbl, sub = self.stat_labels["task"]
        lbl.configure(text=str(task_total))
        sub.configure(text=f"到期{t_over} · 推迟{t_post}")

    # ------------------------------------------------------------------
    # 智能洞察
    # ------------------------------------------------------------------

    def _generate_insights(self, data):
        """根据数据生成智能洞察语句"""
        insights = []

        s_over = len(data["s_overdue"])
        t_over = len(data["t_overdue"])
        c_over = len(data["c_overdue"])
        total = s_over + t_over + c_over + len(data["s_postponed"]) + len(data["t_postponed"])

        if total == 0:
            self._insight_lbl.configure(text="✨ 当前周期内没有拖延记录，继续保持！")
            return

        # 最拖延的模块
        module_counts = {"日程": s_over, "任务": t_over, "打卡": c_over}
        max_module = max(module_counts, key=module_counts.get)
        if module_counts[max_module] > 0:
            pct = module_counts[max_module] / max(total, 1) * 100
            insights.append(f"📊 {max_module}模块是拖延重灾区，占比{pct:.0f}%")

        # 星期分析
        weekday_counts = [0] * 7
        for r in data["s_wd"]:
            weekday_counts[r["wd"]] += r["c"]
        for r in data["t_wd"]:
            weekday_counts[r["wd"]] += r["c"]
        for r in data["c_wd"]:
            weekday_counts[r["wd"]] += r["c"]
        if sum(weekday_counts) > 0:
            wd_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
            worst_wd = max(range(7), key=lambda i: weekday_counts[i])
            insights.append(f"📅 {wd_names[worst_wd]}是你最容易拖延的日子")

        # 优先级分析
        pri_counts = defaultdict(int)
        for r in data["s_pri"]:
            pri_counts[r["priority"]] += r["c"]
        for r in data["t_pri"]:
            pri_counts[r["priority"]] += r["c"]
        if pri_counts.get(3, 0) > 0:
            insights.append(f"🔴 有{pri_counts[3]}项紧急任务拖延未完成")

        # 环比趋势
        prev = data.get("prev")
        if prev:
            prev_total = prev["s_overdue"] + prev["t_overdue"] + prev["c_overdue"]
            cur_overdue = s_over + t_over + c_over
            if prev_total > 0:
                change = (cur_overdue - prev_total) / prev_total * 100
                if change < -5:
                    insights.append(f"📈 较上一周期减少{abs(change):.0f}%，趋势向好")
                elif change > 5:
                    insights.append(f"📉 较上一周期增加{change:.0f}%，需要注意")

        self._insight_lbl.configure(text="  |  ".join(insights))

    # ------------------------------------------------------------------
    # 拖延明细表格
    # ------------------------------------------------------------------

    PRIORITY_LABELS = {1: "普通", 2: "重要", 3: "紧急"}

    def _load_detail_table(self, data):
        """将拖延数据填充到明细表格，相同标题的重复项合并为一行"""
        # 按 (模块, 标题, 拖延类型) 分组
        groups = {}  # key -> {"dates": [], "priority": int, ...}

        def _add_items(rows, module, title_key, date_key, module_key):
            for r in rows:
                title = r[title_key]
                d = r[date_key]
                key = (module, title, "到期未完成", module_key)
                if key not in groups:
                    groups[key] = {
                        "module": module, "title": title, "dates": [],
                        "priority": r["priority"], "proc_type": "到期未完成",
                        "module_key": module_key,
                    }
                groups[key]["dates"].append(d)

        _add_items(data["s_overdue"], "日程", "title", "schedule_date", "schedule")
        _add_items(data["t_overdue"], "任务", "title", "task_date", "task")
        _add_items(data["c_overdue"], "打卡", "task_title", "checkin_date", "checkin")

        # 推迟任务（无日期范围，每个标题独立）
        for r in data["s_postponed"]:
            key = ("日程", r["title"], "推迟任务", "schedule")
            if key not in groups:
                groups[key] = {
                    "module": "日程", "title": r["title"], "dates": [r["schedule_date"]],
                    "priority": r["priority"], "proc_type": "推迟任务",
                    "module_key": "schedule",
                }
            else:
                groups[key]["dates"].append(r["schedule_date"])

        for r in data["t_postponed"]:
            key = ("任务", r["title"], "推迟任务", "task")
            if key not in groups:
                groups[key] = {
                    "module": "任务", "title": r["title"], "dates": [r["task_date"]],
                    "priority": r["priority"], "proc_type": "推迟任务",
                    "module_key": "task",
                }
            else:
                groups[key]["dates"].append(r["task_date"])

        # 转为列表: (module, title, date_display, count, pri_label, proc_type, priority, module_key, latest_date)
        self._all_detail_items = []
        for g in groups.values():
            dates_sorted = sorted(g["dates"])
            count = len(dates_sorted)
            if count == 1:
                date_display = dates_sorted[0]
            else:
                date_display = f"{dates_sorted[0]} ~ {dates_sorted[-1]}"

            self._all_detail_items.append((
                g["module"], g["title"], date_display, str(count),
                self.PRIORITY_LABELS.get(g["priority"], str(g["priority"])),
                g["proc_type"], g["priority"], g["module_key"],
                dates_sorted[-1],  # 最新日期，用于排序
            ))

        # 按最新日期降序
        self._all_detail_items.sort(key=lambda x: x[8], reverse=True)

        self._apply_detail_filter()

    def _apply_detail_filter(self):
        """根据筛选条件显示明细"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filt = self._detail_filter_var.get()
        count = 0
        for item in self._all_detail_items:
            module, title, d, cnt, pri_label, proc_type, pri_val, module_key, _ = item
            show = True
            if filt == "到期未完成" and proc_type != "到期未完成":
                show = False
            elif filt == "推迟任务" and proc_type != "推迟任务":
                show = False
            elif filt == "日程" and module_key != "schedule":
                show = False
            elif filt == "任务" and module_key != "task":
                show = False
            elif filt == "打卡" and module_key != "checkin":
                show = False
            if not show:
                continue

            # 根据优先级选择颜色标签
            if proc_type == "推迟任务":
                tag = "postponed"
            elif pri_val >= 3:
                tag = "overdue_high"
            elif pri_val >= 2:
                tag = "overdue_mid"
            else:
                tag = "overdue_low"

            # 多次的标题加粗提示
            display_title = title if cnt == "1" else f"{title}  ({cnt}次)"

            self.tree.insert("", tk.END,
                             values=(module, display_title, d, cnt, pri_label, proc_type),
                             tags=(tag,))
            count += 1

        self._detail_count_lbl.configure(text=f"共 {count} 条")

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def refresh(self):
        self._clear_charts()
        start, end, prev_start, prev_end = self._get_range()
        data = self._load_data(start, end, prev_start, prev_end)

        self._update_stat_cards(data)
        self._generate_insights(data)

        # 构建完整日期序列
        s_date = date.fromisoformat(start)
        e_date = date.fromisoformat(end)
        days = (e_date - s_date).days + 1
        dates = [(s_date + timedelta(days=i)).isoformat() for i in range(days)]

        self._plot_overdue_trend(dates, data["s_by_date"], data["t_by_date"], data["c_by_date"])

        overdue_count = len(data["s_overdue"]) + len(data["t_overdue"]) + len(data["c_overdue"])
        postponed_count = len(data["s_postponed"]) + len(data["t_postponed"])
        self._plot_type_pie(overdue_count, postponed_count)

        self._plot_module_bar(data["s_overdue"], data["t_overdue"], data["c_overdue"],
                              data["s_postponed"], data["t_postponed"])

        self._plot_weekday_bar(data["s_wd"], data["t_wd"], data["c_wd"])

        self._plot_priority_bar(data["s_pri"], data["t_pri"])

        # 填充明细表格
        self._load_detail_table(data)

        # 更新滚动区域
        self._chart_frame.update_idletasks()
        self._canvas_scroll.configure(scrollregion=self._canvas_scroll.bbox("all"))
