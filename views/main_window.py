import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, date, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.password_manager import check_password, has_password, set_password, remove_password, \
    get_security_question, check_security_answer, set_security_question, has_security_question
from utils.app_settings import get_setting, set_setting, set_auto_start, is_auto_start
from utils.lunar import get_lunar_info
from utils import tray_manager

NAV_ITEMS = [
    ("▶", "日程管理", "calendar"),
    ("☰", "每日任务", "task"),
    ("✓", "打卡追踪", "checkin"),
    ("◎", "整体态势", "all_tasks"),
    ("📈", "数据统计", "stats"),
    ("⏳", "拖延统计", "procrastination"),
    ("✎", "我的日记", "diary"),
    ("★", "系统设置", "settings"),
]

THEME = {
    "primary": "#007bff",
    "primary_light": "#e3f2fd",
    "success": "#28a745",
    "success_light": "#d4edda",
    "danger": "#dc3545",
    "danger_light": "#f8d7da",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "bg": "#f8f9fa",
    "card_bg": "#ffffff",
    "dark": "#343a40",
    "light": "#ffffff",
    "text": "#343a40",
    "text_secondary": "#6c757d",
    "border": "#dee2e6"
}


class MainWindow:

    def __init__(self):
        # 使用ttkbootstrap窗口，应用现代化主题
        self.root = ttk.Window(themename="cosmo")
        self.root.title("日程记事本 · DayFlow")
        saved_geo = get_setting("window_geometry", "1280x750")
        self.root.geometry(saved_geo)
        self.root.minsize(1100, 650)

        # 设置程序图标
        if getattr(sys, 'frozen', False):
            _base = sys._MEIPASS
        else:
            _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._icon_path = os.path.join(_base, 'src', 'images', 'bg.ico')
        if os.path.exists(self._icon_path):
            self.root.iconbitmap(self._icon_path)

        # 首次使用时设置安全问题
        if not has_security_question():
            self._show_initial_security_setup()

        self._setup_style()
        self._build_sidebar()
        self._build_content()
        self.current_view = None
        self.current_key = None
        self.views = {}
        self._switch_view("calendar")

        # 系统托盘 & 关闭行为
        self._tray_active = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 通知提醒
        self._notified_schedules = {}
        self._notified_checkin_time = None
        self._notified_checkin_count = 0
        self._scheduler_id = None
        if get_setting("notification_enabled", False):
            self._start_notification_scheduler()

        # 标题栏语录轮播
        self._quotes = [
            "今日事，今日毕",
            "每一个不曾起舞的日子，都是对生命的辜负",
            "不积跬步，无以至千里",
            "种一棵树最好的时间是十年前，其次是现在",
            "把每一天当作一次新的开始",
            "行动是治愈恐惧的良药",
            "成功的秘诀在于坚持自己的目标",
            "时间就像海绵里的水，挤一挤总会有的",
            "千里之行，始于足下",
            "不要等待机会，而要创造机会",
            "做最好的自己，让生活更精彩",
            "自律给我自由",
            "目标坚定的人，全世界都会为你让路",
            "日拱一卒，功不唐捐",
            "保持热爱，奔赴山海",
            "所有幸运，都是努力埋下的伏笔",
            "与其抱怨黑暗，不如点亮蜡烛",
            "慢一点也没关系，只要在走就好",
            "把计划写在纸上，把执行放在手上",
            "今天的努力，是明天的底气",
            "生活不止眼前的苟且，还有诗和远方",
            "你只管努力，最坏不过是大器晚成",
            "没有人可以回到过去，但谁都可以从现在开始",
            "世上没有绝望的处境，只有对处境绝望的人",
            "当才华撑不起野心时，就该静下心来学习",
            "不是因为看到希望才坚持，是因为坚持才看到希望",
            "心之所向，素履以往",
            "愿你出走半生，归来仍是少年",
            "越努力，越幸运",
            "生活明朗，万物可爱",
            "认真生活，就能找到被人生偷藏起来的糖果",
            "万事都要全力以赴，包括开心",
            "愿所有的不安，都是虚惊一场",
            "没关系，天空越黑，星星越亮",
            "熬过无人问津的日子，才有诗和远方",
            "你来人间一趟，你要看看太阳",
            "既然选择了远方，便只顾风雨兼程",
            "活在这珍贵的人间，太阳强烈，水波温柔",
            "星光不问赶路人，时光不负有心人",
            "纵有疾风起，人生不言弃",
            "生活是自己的，尽情打扮，尽情可爱",
            "一个人至少拥有一个梦想，有一个理由去坚强",
            "所谓万丈深渊，下去也是前程万里",
            "凡是过往，皆为序章",
            "愿你以渺小启程，以伟大结束",
            "路虽远行则将至，事虽难做则必成",
            "知足且上进，温柔而坚定",
            "生活原本沉闷，但跑起来就有风",
            "你现在的努力，是为了以后能体面地活着",
            "别在最好的年纪，活得最便宜",
            "未来可期，人间值得",
            "愿你眼中总有光芒，活成你想要的模样",
            "半山腰太挤了，我们山顶见",
            "你的坚持，终将美好",
            "没有横空出世的运气，只有不为人知的努力",
            "将来的你，一定会感谢现在拼命的自己",
            "总不能还没努力，就向生活妥协吧",
            "这个世界不会辜负每一份努力和坚持",
            "最好的投资，是投资自己",
            "今天的月亮很圆，好像在说：一切都会好起来",
            "别让怯弱否定了自己，别让懒惰误了青春",
            "所有光芒的背后，一定藏着汗水",
            "你不能左右天气，但可以改变心情",
            "愿你成为自己的太阳，无需凭借谁的光",
            "不要因为没有掌声而放弃梦想",
            "努力的意义就是，当好运来临时你觉得你值得",
            "每一个优秀的人，都有一段沉默的时光",
            "生活不是等待风暴过去，而是学会在风雨中起舞",
            "不怕万人阻挡，只怕自己投降",
            "当你足够渴望的时候，全世界都会为你让路",
            "最好的状态是：眼里写满故事，脸上却不见风霜",
            "不要让未来的你，讨厌现在的自己",
            "最暗的夜，才会看见最美的星光",
            "人的一切痛苦，本质上都是对自己无能的愤怒",
            "世界以痛吻我，我要报之以歌",
            "有些路很远，走下去会很累，可是不走会后悔",
            "你要悄悄努力，然后惊艳所有人",
            "没有人能定义你的未来，除了你自己",
            "人生的上半场打不好没关系，还有下半场",
            "哪有什么一夜成名，其实都是百炼成钢",
            "每一个不曾努力的日子，都是对生命的辜负",
            "只有一条路不能选择——那就是放弃的路",
            "生命太过短暂，今天放弃了明天不一定能得到",
            "做一个温暖的人，不卑不亢，清澈善良",
            "岁月不负有心人，时光不弃追梦人",
            "努力不一定成功，但放弃一定失败",
            "没有人可以回到过去重新开始，但谁都可以从现在开始",
            "你必须非常努力，才能看起来毫不费力",
            "天再高又怎样，踮起脚尖就更接近阳光",
            "如果你知道去哪，全世界都会为你让路",
            "既然目标是地平线，留给世界的只能是背影",
            "愿你所到之处，遍地阳光",
            "无论明日多落魄，今天也要全力以赴",
            "所有你值得拥有的美好，都在来的路上",
            "世界上只有一种真正的英雄主义，就是认清生活的真相后依然热爱生活",
            "相信自己，你能作茧自缚，就能破茧成蝶",
            "万物皆有裂痕，那是光照进来的地方",
            "向着月亮出发，即使不能到达，也能站在群星之中",
            "人生如逆旅，我亦是行人",
            "愿你有前进一寸的勇气，亦有后退一尺的从容",
            "乾坤未定，你我皆是黑马；但乾坤已定，那就扭转乾坤。",
            "所谓的运气，不过是机会恰好撞上了你的努力。",
            "你只管努力，剩下的交给时间。但别骗自己，因为时间很诚实。",
            "半山腰总是最挤的，你得去山顶看看。",
            "生活不是为了赶路，而是为了感受路。但如果你不赶路，可能永远只在原地感受。",
            "小时候觉得开心就好，现在也是，只是'开心'两个字的门槛变高了。",
            "你看到别人的光鲜，是因为你没看到他们背后的狼狈。",
            "成熟不是心变老，而是眼泪在打转，却还能微笑。",
            "人生就像心电图，如果一帆风顺，那就说明你挂了。",
            "我们对年龄的恐惧，其实并不在于年龄增长带来的苍老，而是随着年龄增长，我们仍然一无所得。",
            "不必太在意别人的看法，因为他们的看法，往往也只是道听途说。",
            "在哪里跌倒，就在哪里躺下睡一觉。",
            "只要我足够懒，'贩卖焦虑'的就别想赚到我的钱。",
            "我的钱包就像个洋葱，每次打开都让我泪流满面。",
            "间歇性踌躇满志，持续性混吃等死。",
            "不要和我谈理想，我的理想就是不工作还能有钱拿。",
            "上帝是公平的，给了你丑的外表，还给了你低的智商，以免让你显得不协调。",
            "你以为有钱人很快乐吗？他们的快乐你根本想象不到。",
            "别动不动就把问题交给'时间'，时间才懒得理你这堆烂摊子。",
            "每次想大吃一顿的时候，我就告诉自己：'美丑有命，胖瘦在天，天叫我吃，我不得不吃。'",
            "世上无难事，只要肯放弃。",
            "别怕自己没能力，也别怕自己平凡，要知道，地球几十亿人，绝大多数都跟你一样，都是来'凑数'的。",
            "今天解决不了的事情，别着急，因为明天你也解决不了。",
            "当你觉得某件事非你不可时，请记住，那只是因为你还没开始休假。",
            "甲方说想要五彩斑斓的黑，我说没问题，然后给他看了张二维码。",
        ]
        # 静默启动：如果开启则隐藏窗口（仅执行一次）
        if get_setting("silent_start", False):
            self.root.withdraw()
            self._ensure_tray()

        self._rotate_title()

    def _rotate_title(self):
        import random
        quote = random.choice(self._quotes)
        self.root.title(f"日程记事本 · DayFlow  —— {quote}")
        self.root.after(30000, self._rotate_title)

    def _show_initial_security_setup(self):
        """首次使用时设置安全问题"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔐 首次使用设置")
        dialog.geometry("440x460")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        # 弹窗居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 220
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 230
        dialog.geometry("+{}+{}".format(x, y))

        # 头部
        header = tk.Frame(dialog, bg=THEME["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="🔐 首次使用设置",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["primary"], fg="white").pack(pady=(14, 14))

        # 表单区域
        form = tk.Frame(dialog, bg=THEME["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=(18, 12))

        tk.Label(form, text="为了您的数据安全，请设置安全问题：",
                font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 14))

        SECURITY_QUESTIONS = [
            "你的第一只宠物名字是什么？",
            "你小学就读的学校名称是什么？",
            "母亲的姓名是什么？",
            "你第一份工作的单位是什么？",
            "儿时的绰号是什么？"
        ]

        # 选择安全问题
        tk.Label(form, text="选择安全问题：",
                font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(0, 4))

        question_var = tk.StringVar(value=SECURITY_QUESTIONS[0])
        question_menu = ttk.Combobox(form, textvariable=question_var,
                                    values=SECURITY_QUESTIONS, state="readonly",
                                    width=40)
        question_menu.pack(anchor="w", pady=(0, 12))

        # 设置答案
        tk.Label(form, text="设置答案：",
                font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(0, 4))

        answer_var = tk.StringVar()
        answer_entry = tk.Entry(form, textvariable=answer_var, show="●",
                                font=("Microsoft YaHei UI", 12),
                                highlightbackground=THEME["border"], highlightthickness=1)
        answer_entry.pack(fill=tk.X, ipady=7)
        answer_entry.focus_set()

        self.security_error = tk.Label(form, text="",
                                     font=("Microsoft YaHei UI", 9),
                                     bg=THEME["card_bg"], fg=THEME["danger"])
        self.security_error.pack(anchor="w", pady=(6, 0))

        # 提示信息
        tk.Label(form, text="请记住您的答案，用于验证敏感操作和找回密码",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(12, 0))

        # 按钮区域（固定在底部）
        btn_frame = tk.Frame(dialog, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, padx=25, pady=(0, 18))

        ok_btn = tk.Button(btn_frame, text="确认设置",
                          font=("Microsoft YaHei UI", 11, "bold"),
                          bg=THEME["primary"], fg="white", relief="flat",
                          padx=25, pady=7, width=10, cursor="hand2",
                          command=lambda: self._save_initial_security(question_var.get(), answer_var.get(), dialog))
        ok_btn.pack(side=tk.RIGHT)

        dialog.wait_window()

    def _save_initial_security(self, question, answer, dialog):
        if not answer.strip():
            self.security_error.configure(text="请输入安全问题答案")
            return

        set_security_question(question, answer.strip())
        dialog.destroy()

    def _setup_style(self):
        pass

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, width=200, bg="#ffffff")
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="DayFlow", font=("Microsoft YaHei UI", 16, "bold"),
                bg="#ffffff", fg=THEME["text"]).pack(pady=(30, 5))
        tk.Label(sidebar, text="日程记事本", font=("Microsoft YaHei UI", 9),
                bg="#ffffff", fg=THEME["text_secondary"]).pack(pady=(0, 30))

        self.nav_buttons = {}
        self.nav_frames = {}
        for icon, label, key in NAV_ITEMS:
            row = tk.Frame(sidebar, bg="#ffffff", cursor="hand2")
            row.pack(fill=tk.X, padx=10)

            icon_lbl = tk.Label(row, text=icon, font=("Segoe UI Emoji", 14),
                                bg="#ffffff", fg=THEME["text"], width=3, anchor="center")
            icon_lbl.pack(side=tk.LEFT, padx=(10, 0), pady=10)

            text_lbl = tk.Label(row, text=label, font=("Microsoft YaHei UI", 11),
                                bg="#ffffff", fg=THEME["text"], anchor="w")
            text_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

            self.nav_buttons[key] = row
            self.nav_frames[key] = (row, icon_lbl, text_lbl)

            for w in (row, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._switch_view(k))
                w.bind("<Enter>", lambda e, k=key: self._nav_hover(k, True))
                w.bind("<Leave>", lambda e, k=key: self._nav_hover(k, False))

        # 底部日期 + 农历
        today = date.today()
        bottom = tk.Frame(sidebar, bg="#ffffff")
        bottom.pack(side=tk.BOTTOM, pady=15)

        tk.Label(bottom, text=today.strftime("%Y年%m月%d日"),
                font=("Microsoft YaHei UI", 9), bg="#ffffff", fg=THEME["text_secondary"]).pack()

        info = get_lunar_info(today.year, today.month, today.day)
        extra = info["festival"] or info["solar_term"]
        lunar_text = info["lunar_str"]
        if extra:
            lunar_text += f" · {extra}"
        tk.Label(bottom, text=lunar_text,
                font=("Microsoft YaHei UI", 8), bg="#ffffff", fg=THEME["text_secondary"]).pack()

    def _nav_hover(self, key, entering):
        if key == self.current_key:
            return
        row, icon_lbl, text_lbl = self.nav_frames[key]
        bg = THEME["primary_light"] if entering else "#ffffff"
        for w in (row, icon_lbl, text_lbl):
            w.configure(bg=bg)

    def _update_nav_active(self):
        for key, (row, icon_lbl, text_lbl) in self.nav_frames.items():
            if key == self.current_key:
                for w in (row, icon_lbl, text_lbl):
                    w.configure(bg=THEME["primary_light"])
                icon_lbl.configure(fg=THEME["primary"])
                text_lbl.configure(fg=THEME["primary"])
            else:
                for w in (row, icon_lbl, text_lbl):
                    w.configure(bg="#ffffff")
                icon_lbl.configure(fg=THEME["text"])
                text_lbl.configure(fg=THEME["text"])

    def _build_content(self):
        self.content_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _switch_view(self, key, force=False):
        # 标签到视图key的映射
        tag_to_view = {"schedule": "calendar", "task": "task",
                       "checkin": "checkin", "diary": "diary"}
        view_key = tag_to_view.get(key, key)

        if view_key == self.current_key and not force:
            return

        # 如果是日记，需要先验证密码
        if view_key == "diary":
            if not self._verify_diary_password():
                return

        if self.current_view:
            self.current_view.pack_forget()

        self.current_key = view_key
        self._update_nav_active()

        if view_key not in self.views:
            self.views[view_key] = self._create_view(view_key)

        self.current_view = self.views[view_key]
        self.current_view.pack(fill=tk.BOTH, expand=True)

        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def _create_view(self, key):
        if key == "calendar":
            from views.calendar_view import CalendarView
            return CalendarView(self.content_frame, theme=THEME)
        elif key == "task":
            from views.task_view import TaskView
            return TaskView(self.content_frame, theme=THEME)
        elif key == "checkin":
            from views.checkin_view import CheckinView
            return CheckinView(self.content_frame, theme=THEME, on_data_change=lambda: None)
        elif key == "all_tasks":
            from views.all_tasks_view import AllTasksView
            return AllTasksView(self.content_frame, theme=THEME, on_navigate=self._switch_view)
        elif key == "stats":
            from views.stats_view import StatsView
            return StatsView(self.content_frame, theme=THEME)
        elif key == "procrastination":
            from views.procrastination_view import ProcrastinationView
            return ProcrastinationView(self.content_frame, theme=THEME)
        elif key == "diary":
            from views.diary_view import DiaryView
            return DiaryView(self.content_frame, theme=THEME)
        elif key == "settings":
            return self._build_settings_view()
        return ttk.Frame(self.content_frame)

    def _build_settings_view(self):
        frame = tk.Frame(self.content_frame, bg=THEME["bg"])

        header = tk.Frame(frame, bg=THEME["bg"])
        header.pack(fill=tk.X, padx=30, pady=(25, 10))
        tk.Label(header, text="⚙️ 系统设置", font=("Microsoft YaHei UI", 18, "bold"),
                bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w")
        tk.Label(header, text="管理应用配置和隐私设置", font=("Microsoft YaHei UI", 10),
                bg=THEME["bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(4, 0))

        # 可滚动区域
        scroll_container = tk.Frame(frame, bg=THEME["bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, bg=THEME["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        scroll_inner = tk.Frame(canvas, bg=THEME["bg"])

        scroll_inner.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_inner, anchor="nw", tags="settings_inner")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig("settings_inner", width=e.width))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # 滚动提示
        scroll_hint = tk.Label(frame, text="↕ 滑动鼠标滚轮查看更多设置",
                               font=("Microsoft YaHei UI", 9),
                               bg=THEME["bg"], fg=THEME["text_secondary"])
        scroll_hint.pack(pady=(0, 5))
        # 3秒后自动隐藏提示
        frame.after(3000, scroll_hint.pack_forget)

        # 缓存清除设置卡片
        card1 = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        card1.pack(fill=tk.X, padx=30, pady=(10, 15))

        inner1 = tk.Frame(card1, bg=THEME["card_bg"])
        inner1.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner1, text="🗑 缓存清除设置", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 15))

        cache_btn_frame = tk.Frame(inner1, bg=THEME["card_bg"])
        cache_btn_frame.pack(fill=tk.X)

        def clear_all_cache():
            if not self._verify_security_question():
                return
            
            if not messagebox.askyesno("⚠️ 危险操作确认", 
                                       "确定要清除所有数据吗？\n\n此操作将删除所有日程、任务、打卡和日记数据，且不可恢复！"):
                return
            
            from database import DailyTaskDB, CheckinDB, DiaryDB, ScheduleDB
            try:
                DailyTaskDB.clear_all()
                CheckinDB.clear_all()
                DiaryDB.clear_all()
                ScheduleDB.clear_all()
                remove_password()
                messagebox.showinfo("成功", "所有数据已清除！")
            except Exception as e:
                messagebox.showerror("错误", f"清除失败：{e}")

        def clear_tasks_cache():
            if not self._verify_security_question():
                return
            
            if not messagebox.askyesno("确认清除", "确定要清除所有任务数据吗？此操作不可恢复！"):
                return
            from database import DailyTaskDB
            try:
                DailyTaskDB.clear_all()
                messagebox.showinfo("成功", "任务数据已清除！")
            except Exception as e:
                messagebox.showerror("错误", f"清除失败：{e}")

        def clear_checkin_cache():
            if not self._verify_security_question():
                return
            
            if not messagebox.askyesno("确认清除", "确定要清除所有打卡数据吗？此操作不可恢复！"):
                return
            from database import CheckinDB
            try:
                CheckinDB.clear_all()
                messagebox.showinfo("成功", "打卡数据已清除！")
            except Exception as e:
                messagebox.showerror("错误", f"清除失败：{e}")

        def clear_diary_cache():
            if not self._verify_security_question():
                return
            
            if not messagebox.askyesno("确认清除", "确定要清除所有日记数据吗？密码设置也将被清除！此操作不可恢复！"):
                return
            from database import DiaryDB
            try:
                DiaryDB.clear_all()
                remove_password()
                messagebox.showinfo("成功", "日记数据和密码已清除！")
            except Exception as e:
                messagebox.showerror("错误", f"清除失败：{e}")

        btn1 = tk.Button(cache_btn_frame, text="清除全部数据", font=("Microsoft YaHei UI", 10),
                        bg=THEME["danger"], fg="white", relief="flat", padx=15, pady=8,
                        cursor="hand2", command=clear_all_cache)
        btn1.pack(side=tk.LEFT, padx=(0, 10))

        btn2 = tk.Button(cache_btn_frame, text="清除任务数据", font=("Microsoft YaHei UI", 10),
                        bg=THEME["warning"], fg="white", relief="flat", padx=15, pady=8,
                        cursor="hand2", command=clear_tasks_cache)
        btn2.pack(side=tk.LEFT, padx=(0, 10))

        btn3 = tk.Button(cache_btn_frame, text="清除打卡数据", font=("Microsoft YaHei UI", 10),
                        bg=THEME["warning"], fg="white", relief="flat", padx=15, pady=8,
                        cursor="hand2", command=clear_checkin_cache)
        btn3.pack(side=tk.LEFT, padx=(0, 10))

        btn4 = tk.Button(cache_btn_frame, text="清除日记数据", font=("Microsoft YaHei UI", 10),
                        bg=THEME["warning"], fg="white", relief="flat", padx=15, pady=8,
                        cursor="hand2", command=clear_diary_cache)
        btn4.pack(side=tk.LEFT)

        # 数据导出与导入设置卡片
        card_export = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                              highlightthickness=1)
        card_export.pack(fill=tk.X, padx=30, pady=(0, 15))

        inner_export = tk.Frame(card_export, bg=THEME["card_bg"])
        inner_export.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner_export, text="📤 数据导出与导入", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 15))

        export_btn_frame = tk.Frame(inner_export, bg=THEME["card_bg"])
        export_btn_frame.pack(fill=tk.X)

        def export_schedule():
            if not self._verify_security_question():
                return
            self._show_export_dialog("schedule")

        def export_tasks():
            if not self._verify_security_question():
                return
            self._show_export_dialog("task")

        def export_diary():
            if not self._verify_security_question():
                return
            self._show_export_dialog("diary")

        def export_all():
            if not self._verify_security_question():
                return
            self._show_export_dialog("all")

        exp_btn1 = tk.Button(export_btn_frame, text="📅 导出日程", font=("Microsoft YaHei UI", 10),
                            bg=THEME["primary"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=export_schedule)
        exp_btn1.pack(side=tk.LEFT, padx=(0, 10))

        exp_btn2 = tk.Button(export_btn_frame, text="📋 导出任务", font=("Microsoft YaHei UI", 10),
                            bg=THEME["primary"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=export_tasks)
        exp_btn2.pack(side=tk.LEFT, padx=(0, 10))

        exp_btn3 = tk.Button(export_btn_frame, text="📝 导出日记", font=("Microsoft YaHei UI", 10),
                            bg=THEME["primary"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=export_diary)
        exp_btn3.pack(side=tk.LEFT, padx=(0, 10))

        exp_btn4 = tk.Button(export_btn_frame, text="📦 导出全部", font=("Microsoft YaHei UI", 10),
                            bg=THEME["success"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=export_all)
        exp_btn4.pack(side=tk.LEFT)

        # 导入按钮区域
        import_btn_frame = tk.Frame(inner_export, bg=THEME["card_bg"])
        import_btn_frame.pack(fill=tk.X, pady=(15, 0))

        def import_schedule():
            if not self._verify_security_question():
                return
            self._show_import_dialog("schedule")

        def import_tasks():
            if not self._verify_security_question():
                return
            self._show_import_dialog("task")

        def import_diary():
            if not self._verify_security_question():
                return
            self._show_import_dialog("diary")

        def import_all():
            if not self._verify_security_question():
                return
            self._show_import_dialog("all")

        imp_btn1 = tk.Button(import_btn_frame, text="📥 导入日程", font=("Microsoft YaHei UI", 10),
                            bg=THEME["success"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=import_schedule)
        imp_btn1.pack(side=tk.LEFT, padx=(0, 10))

        imp_btn2 = tk.Button(import_btn_frame, text="📥 导入任务", font=("Microsoft YaHei UI", 10),
                            bg=THEME["success"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=import_tasks)
        imp_btn2.pack(side=tk.LEFT, padx=(0, 10))

        imp_btn3 = tk.Button(import_btn_frame, text="📥 导入日记", font=("Microsoft YaHei UI", 10),
                            bg=THEME["success"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=import_diary)
        imp_btn3.pack(side=tk.LEFT, padx=(0, 10))

        imp_btn4 = tk.Button(import_btn_frame, text="📥 导入全部", font=("Microsoft YaHei UI", 10),
                            bg=THEME["success"], fg="white", relief="flat", padx=15, pady=8,
                            cursor="hand2", command=import_all)
        imp_btn4.pack(side=tk.LEFT)

        # 日记密码设置卡片
        card2 = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        card2.pack(fill=tk.X, padx=30, pady=(0, 15))

        inner2 = tk.Frame(card2, bg=THEME["card_bg"])
        inner2.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner2, text="🔐 日记隐私保护", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 15))

        # 隐私保护开关
        privacy_frame = tk.Frame(inner2, bg=THEME["card_bg"])
        privacy_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(privacy_frame, text="开启隐私保护", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)

        privacy_enabled = get_setting("diary_privacy_enabled", False) and has_password()
        self._privacy_lbl = tk.Label(privacy_frame, text="✅" if privacy_enabled else "⬜",
                                     bg=THEME["card_bg"], font=("Segoe UI Emoji", 16),
                                     cursor="hand2")
        self._privacy_lbl.pack(side=tk.RIGHT)
        self._privacy_lbl.bind("<Button-1>", lambda e: self._toggle_privacy())

        # 密码管理按钮
        pwd_btn_frame = tk.Frame(inner2, bg=THEME["card_bg"])
        pwd_btn_frame.pack(fill=tk.X)

        def change_password():
            self._show_change_password_dialog()

        def forgot_password():
            self._show_forgot_password(None)

        def disable_password():
            if not self._verify_security_question():
                return
            
            if messagebox.askyesno("确认", "确定要关闭日记隐私保护吗？\n密码将保留，下次开启无需重新设置。"):
                set_setting("diary_privacy_enabled", False)
                self._privacy_lbl.configure(text="⬜")
                messagebox.showinfo("成功", "隐私保护已关闭")

        pwd_btn1 = tk.Button(pwd_btn_frame, text="修改密码", font=("Microsoft YaHei UI", 10),
                            bg=THEME["primary"], fg="white", relief="flat", padx=20, pady=8,
                            cursor="hand2", command=change_password)
        pwd_btn1.pack(side=tk.LEFT, padx=(0, 10))

        pwd_btn2 = tk.Button(pwd_btn_frame, text="找回密码", font=("Microsoft YaHei UI", 10),
                            bg=THEME["text_secondary"], fg="white", relief="flat", padx=20, pady=8,
                            cursor="hand2", command=forgot_password)
        pwd_btn2.pack(side=tk.LEFT, padx=(0, 10))

        pwd_btn3 = tk.Button(pwd_btn_frame, text="关闭保护", font=("Microsoft YaHei UI", 10),
                            bg=THEME["danger"], fg="white", relief="flat", padx=20, pady=8,
                            cursor="hand2", command=disable_password)
        pwd_btn3.pack(side=tk.LEFT)

        # 通知设置卡片
        card_notify = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                               highlightthickness=1)
        card_notify.pack(fill=tk.X, padx=30, pady=(0, 15))

        inner_notify = tk.Frame(card_notify, bg=THEME["card_bg"])
        inner_notify.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner_notify, text="🔔 通知设置", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 15))

        # 开启通知提醒
        self._build_setting_row(inner_notify, "🔔", "开启通知提醒",
                                "开启后将在日程、每日任务和打卡即将到期时提醒您",
                                "notification_enabled",
                                on_toggle=self._toggle_notification)

        # 分隔线
        tk.Frame(inner_notify, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 日程提前提醒时间
        reminder_row = tk.Frame(inner_notify, bg=THEME["card_bg"])
        reminder_row.pack(fill=tk.X, pady=2)
        reminder_left = tk.Frame(reminder_row, bg=THEME["card_bg"])
        reminder_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        reminder_top = tk.Frame(reminder_left, bg=THEME["card_bg"])
        reminder_top.pack(anchor="w")
        tk.Label(reminder_top, text="⏰", font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(reminder_top, text="日程提前提醒时间", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)
        tk.Label(reminder_left, text="日程开始前多少分钟发送提醒",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))

        self._reminder_var = tk.StringVar(value=f"{get_setting('reminder_minutes', 15)} 分钟")
        reminder_combo = ttk.Combobox(reminder_row, textvariable=self._reminder_var,
                                      values=["5 分钟", "10 分钟", "15 分钟", "30 分钟"],
                                      state="readonly", width=10,
                                      font=("Microsoft YaHei UI", 10))
        reminder_combo.pack(side=tk.RIGHT, padx=(10, 0))
        reminder_combo.bind("<<ComboboxSelected>>", self._on_reminder_minutes_change)

        # 分隔线
        tk.Frame(inner_notify, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 每日打卡提醒时间
        checkin_row = tk.Frame(inner_notify, bg=THEME["card_bg"])
        checkin_row.pack(fill=tk.X, pady=2)
        checkin_left = tk.Frame(checkin_row, bg=THEME["card_bg"])
        checkin_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        checkin_top = tk.Frame(checkin_left, bg=THEME["card_bg"])
        checkin_top.pack(anchor="w")
        tk.Label(checkin_top, text="🕔", font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(checkin_top, text="每日打卡提醒时间", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)
        tk.Label(checkin_left, text="到达该时间后提醒当天未完成的打卡任务",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))
        self._checkin_error_label = tk.Label(checkin_left, text="",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["danger"])

        self._checkin_time_var = tk.StringVar(value=get_setting("checkin_reminder_time", "21:00"))
        self._checkin_time_entry = tk.Entry(checkin_row, textvariable=self._checkin_time_var,
                                      font=("Microsoft YaHei UI", 11), width=8,
                                      justify="center",
                                      highlightbackground=THEME["border"], highlightthickness=1)
        self._checkin_time_entry.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)
        self._checkin_time_entry.bind("<FocusOut>", self._on_checkin_time_change)
        self._checkin_time_entry.bind("<Return>", self._on_checkin_time_change)

        # 分隔线
        tk.Frame(inner_notify, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 每日任务提醒时间
        daily_task_row = tk.Frame(inner_notify, bg=THEME["card_bg"])
        daily_task_row.pack(fill=tk.X, pady=2)
        daily_task_left = tk.Frame(daily_task_row, bg=THEME["card_bg"])
        daily_task_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        daily_task_top = tk.Frame(daily_task_left, bg=THEME["card_bg"])
        daily_task_top.pack(anchor="w")
        tk.Label(daily_task_top, text="📋", font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(daily_task_top, text="每日任务提醒时间", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)
        tk.Label(daily_task_left, text="到达该时间后提醒当天未完成的每日任务",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))
        self._daily_task_error_label = tk.Label(daily_task_left, text="",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["danger"])

        self._daily_task_time_var = tk.StringVar(value=get_setting("daily_task_reminder_time", "08:00"))
        self._daily_task_time_entry = tk.Entry(daily_task_row, textvariable=self._daily_task_time_var,
                                      font=("Microsoft YaHei UI", 11), width=8,
                                      justify="center",
                                      highlightbackground=THEME["border"], highlightthickness=1)
        self._daily_task_time_entry.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)
        self._daily_task_time_entry.bind("<FocusOut>", self._on_daily_task_time_change)
        self._daily_task_time_entry.bind("<Return>", self._on_daily_task_time_change)

        # 分隔线
        tk.Frame(inner_notify, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 循环提醒间隔
        repeat_row = tk.Frame(inner_notify, bg=THEME["card_bg"])
        repeat_row.pack(fill=tk.X, pady=2)
        repeat_left = tk.Frame(repeat_row, bg=THEME["card_bg"])
        repeat_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        repeat_top = tk.Frame(repeat_left, bg=THEME["card_bg"])
        repeat_top.pack(anchor="w")
        tk.Label(repeat_top, text="🔁", font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(repeat_top, text="循环提醒间隔", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)
        tk.Label(repeat_left, text="未处理的通知每隔多少分钟重复提醒一次",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))
        self._repeat_error_label = tk.Label(repeat_left, text="",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["danger"])

        self._repeat_var = tk.StringVar(value=str(get_setting('reminder_repeat_interval', 5)))
        self._repeat_entry = tk.Entry(repeat_row, textvariable=self._repeat_var,
                                font=("Microsoft YaHei UI", 11), width=8,
                                justify="center",
                                highlightbackground=THEME["border"], highlightthickness=1)
        self._repeat_entry.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)
        self._repeat_entry.bind("<FocusOut>", self._on_repeat_interval_change)
        self._repeat_entry.bind("<Return>", self._on_repeat_interval_change)

        # 分隔线
        tk.Frame(inner_notify, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 循环提醒次数
        count_row = tk.Frame(inner_notify, bg=THEME["card_bg"])
        count_row.pack(fill=tk.X, pady=2)
        count_left = tk.Frame(count_row, bg=THEME["card_bg"])
        count_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        count_top = tk.Frame(count_left, bg=THEME["card_bg"])
        count_top.pack(anchor="w")
        tk.Label(count_top, text="🔢", font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(count_top, text="循环提醒次数", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)
        tk.Label(count_left, text="0 表示不限次数，填入正整数限制最大提醒次数",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))
        self._count_error_label = tk.Label(count_left, text="",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["danger"])

        self._max_count_var = tk.StringVar(value=str(get_setting('reminder_max_count', 0)))
        self._count_entry = tk.Entry(count_row, textvariable=self._max_count_var,
                               font=("Microsoft YaHei UI", 11), width=8,
                               justify="center",
                               highlightbackground=THEME["border"], highlightthickness=1)
        self._count_entry.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)
        self._count_entry.bind("<FocusOut>", self._on_max_count_change)
        self._count_entry.bind("<Return>", self._on_max_count_change)

        # 数据备份卡片
        card_backup = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                               highlightthickness=1)
        card_backup.pack(fill=tk.X, padx=30, pady=(0, 15))

        inner_backup = tk.Frame(card_backup, bg=THEME["card_bg"])
        inner_backup.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner_backup, text="💾 数据备份", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 4))
        tk.Label(inner_backup, text="程序每次启动时自动备份，最多保留 30 份，也可手动备份和恢复",
                font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(0, 15))

        backup_btn_frame = tk.Frame(inner_backup, bg=THEME["card_bg"])
        backup_btn_frame.pack(fill=tk.X)

        tk.Button(backup_btn_frame, text="💾 立即备份", font=("Microsoft YaHei UI", 10),
                  bg=THEME["primary"], fg="white", relief="flat", padx=15, pady=8,
                  cursor="hand2", command=self._do_manual_backup).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(backup_btn_frame, text="🔄 恢复备份", font=("Microsoft YaHei UI", 10),
                  bg=THEME["warning"], fg="white", relief="flat", padx=15, pady=8,
                  cursor="hand2", command=self._do_restore_backup).pack(side=tk.LEFT)

        # 通用设置卡片
        card3 = tk.Frame(scroll_inner, bg=THEME["card_bg"], highlightbackground=THEME["border"],
                        highlightthickness=1)
        card3.pack(fill=tk.X, padx=30, pady=(0, 15))

        inner3 = tk.Frame(card3, bg=THEME["card_bg"])
        inner3.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner3, text="⚙️ 通用设置", font=("Microsoft YaHei UI", 13, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 15))

        # 开机自启
        self._build_setting_row(inner3, "🚀", "开机自启",
                                "程序随系统启动自动运行",
                                "auto_start",
                                on_toggle=self._toggle_auto_start)

        # 分隔线
        tk.Frame(inner3, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 关闭时最小化到托盘
        self._build_setting_row(inner3, "📌", "关闭时最小化到托盘",
                                "点击关闭按钮时隐藏到系统托盘，不退出程序",
                                "minimize_to_tray")

        # 分隔线
        tk.Frame(inner3, bg=THEME["border"], height=1).pack(fill=tk.X, pady=10)

        # 静默启动
        self._build_setting_row(inner3, "🔇", "静默启动",
                                "程序启动时不显示主窗口，仅在系统托盘运行",
                                "silent_start")

        return frame

    def _build_setting_row(self, parent, icon, title, desc, setting_key, on_toggle=None):
        """构建一个通用设置行：左侧图标+标题+说明，右侧开关"""
        row = tk.Frame(parent, bg=THEME["card_bg"])
        row.pack(fill=tk.X, pady=2)

        left = tk.Frame(row, bg=THEME["card_bg"])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        top_line = tk.Frame(left, bg=THEME["card_bg"])
        top_line.pack(anchor="w")
        tk.Label(top_line, text=icon, font=("Segoe UI Emoji", 13),
                bg=THEME["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(top_line, text=title, font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(side=tk.LEFT)

        tk.Label(left, text=desc, font=("Microsoft YaHei UI", 9),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", padx=(28, 0))

        enabled = get_setting(setting_key, False)

        def on_click(e, sk=setting_key, lbl=None):
            cur = get_setting(sk, False)
            set_setting(sk, not cur)
            lbl.configure(text="✅" if not cur else "⬜")
            if on_toggle:
                on_toggle()

        switch = tk.Label(row, text="✅" if enabled else "⬜",
                          bg=THEME["card_bg"], font=("Segoe UI Emoji", 16),
                          cursor="hand2")
        switch.pack(side=tk.RIGHT, padx=(10, 0))
        switch.bind("<Button-1>", lambda e: on_click(e, setting_key, switch))

    def _toggle_auto_start(self):
        enabled = get_setting("auto_start", False)
        set_auto_start(enabled)

    def _toggle_privacy(self):
        if not get_setting("diary_privacy_enabled", False):
            # 开启隐私保护
            if has_password():
                # 已有密码，直接启用
                set_setting("diary_privacy_enabled", True)
                self._privacy_lbl.configure(text="✅")
                return
            # 没有密码，显示设置向导
            dialog = tk.Toplevel(self.root)
            dialog.title("🔐 设置日记密码")
            dialog.geometry("420x400")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.configure(bg=THEME["card_bg"])

            # 弹窗居中
            dialog.update_idletasks()
            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            parent_w = self.root.winfo_width()
            parent_h = self.root.winfo_height()
            x = parent_x + (parent_w // 2) - 210
            y = parent_y + (parent_h // 2) - 200
            dialog.geometry("+{}+{}".format(x, y))

            header = tk.Frame(dialog, bg=THEME["primary"])
            header.pack(fill=tk.X)
            tk.Label(header, text="🔐 设置日记密码",
                    font=("Microsoft YaHei UI", 14, "bold"),
                    bg=THEME["primary"], fg="white").pack(pady=(15, 15))

            scroll_frame = tk.Frame(dialog, bg=THEME["card_bg"])
            scroll_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

            scrollbar = tk.Scrollbar(scroll_frame, orient=tk.VERTICAL)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            canvas = tk.Canvas(scroll_frame, bg=THEME["card_bg"], yscrollcommand=scrollbar.set,
                              highlightthickness=0)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=canvas.yview)

            form = tk.Frame(canvas, bg=THEME["card_bg"])
            canvas.create_window((0, 0), window=form, anchor=tk.NW)

            tk.Label(form, text="📝 设置密码", font=("Microsoft YaHei UI", 12, "bold"),
                    bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

            tk.Label(form, text="密码：", font=("Microsoft YaHei UI", 11),
                    bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
            password1_var = tk.StringVar()
            password1_entry = tk.Entry(form, textvariable=password1_var, show="●",
                                      font=("Microsoft YaHei UI", 12), width=35,
                                      highlightbackground=THEME["border"], highlightthickness=1)
            password1_entry.pack(anchor="w", ipady=8, pady=(0, 5))

            tk.Label(form, text="确认密码：", font=("Microsoft YaHei UI", 11),
                    bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
            password2_var = tk.StringVar()
            password2_entry = tk.Entry(form, textvariable=password2_var, show="●",
                                      font=("Microsoft YaHei UI", 12), width=35,
                                      highlightbackground=THEME["border"], highlightthickness=1)
            password2_entry.pack(anchor="w", ipady=8, pady=(0, 15))

            tk.Label(form, text="❓ 设置安全问题", font=("Microsoft YaHei UI", 12, "bold"),
                    bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

            security_questions = [
                "你的第一只宠物名字是什么？",
                "你小学就读的学校名称是什么？",
                "母亲的姓名是什么？",
                "你第一份工作的单位是什么？",
                "儿时的绰号是什么？",
            ]

            question_var = tk.StringVar(value=security_questions[0])
            for q in security_questions:
                rb = tk.Radiobutton(form, text=q, variable=question_var, value=q,
                                   font=("Microsoft YaHei UI", 10), bg=THEME["card_bg"],
                                   selectcolor=THEME["primary_light"])
                rb.pack(anchor="w", pady=3)

            tk.Label(form, text="安全问题答案：", font=("Microsoft YaHei UI", 11),
                    bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(10, 0))
            answer_var = tk.StringVar()
            answer_entry = tk.Entry(form, textvariable=answer_var,
                                   font=("Microsoft YaHei UI", 12), width=35,
                                   highlightbackground=THEME["border"], highlightthickness=1)
            answer_entry.pack(anchor="w", ipady=8, pady=(0, 20))

            form.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

            error_label = tk.Label(dialog, text="", font=("Microsoft YaHei UI", 9),
                                  bg=THEME["card_bg"], fg=THEME["danger"])
            error_label.pack(anchor="w", padx=25)

            btn_frame = tk.Frame(dialog, bg=THEME["card_bg"])
            btn_frame.pack(fill=tk.X, padx=25, pady=(10, 15))

            def do_save():
                pwd1 = password1_var.get().strip()
                pwd2 = password2_var.get().strip()
                answer = answer_var.get().strip()

                if not pwd1 or len(pwd1) < 4:
                    error_label.configure(text="密码至少需要4个字符")
                    return
                if pwd1 != pwd2:
                    error_label.configure(text="两次输入的密码不一致")
                    return
                if not answer:
                    error_label.configure(text="请输入安全问题答案")
                    return

                set_password(pwd1)
                set_security_question(question_var.get(), answer)
                set_setting("diary_privacy_enabled", True)
                self._privacy_lbl.configure(text="✅")
                messagebox.showinfo("成功", "密码设置完成！")
                dialog.destroy()

            cancel_btn = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                                  bg=THEME["text_secondary"], fg="white", relief="flat", 
                                  padx=20, pady=8, width=10, cursor="hand2", 
                                  command=lambda: self._cancel_privacy(dialog))
            cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

            ok_btn = tk.Button(btn_frame, text="完成设置", font=("Microsoft YaHei UI", 11, "bold"),
                              bg=THEME["primary"], fg="white", relief="flat", 
                              padx=20, pady=8, width=12, cursor="hand2", command=do_save)
            ok_btn.pack(side=tk.RIGHT)

            dialog.wait_window()
        else:
            # 关闭隐私保护，需要安全验证
            if not self._verify_security_question():
                return
            set_setting("diary_privacy_enabled", False)
            self._privacy_lbl.configure(text="⬜")

    def _cancel_privacy(self, dialog):
        self._privacy_lbl.configure(text="⬜")
        dialog.destroy()

    def _show_change_password_dialog(self):
        if not has_password():
            messagebox.showwarning("提示", "请先开启隐私保护")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("🔐 修改密码")
        dialog.geometry("460x560")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        x = parent_x + (parent_w // 2) - 230
        y = parent_y + (parent_h // 2) - 290
        dialog.geometry("+{}+{}".format(x, y))

        header = tk.Frame(dialog, bg=THEME["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="🔐 修改密码",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["primary"], fg="white").pack(pady=(15, 15))

        content = tk.Frame(dialog, bg=THEME["card_bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        question = get_security_question()
        if not question:
            tk.Label(content, text="未设置安全问题，无法修改密码",
                    font=("Microsoft YaHei UI", 11),
                    bg=THEME["card_bg"], fg=THEME["danger"]).pack(anchor="w", pady=20)
            tk.Button(content, text="关闭", font=("Microsoft YaHei UI", 11),
                      bg=THEME["text_secondary"], fg="white", relief="flat",
                      padx=25, pady=8, cursor="hand2", command=dialog.destroy).pack(anchor="center")
            dialog.wait_window()
            return

        self._show_change_pwd_step1(dialog, content, question)
        dialog.wait_window()

    def _show_change_pwd_step1(self, dialog, content, question):
        self._clear_frame(content)

        tk.Label(content, text="第一步：验证身份", font=("Microsoft YaHei UI", 12, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))
        tk.Label(content, text=f"❓ {question}", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["primary"]).pack(anchor="w", pady=(0, 10))

        answer_var = tk.StringVar()
        answer_entry = tk.Entry(content, textvariable=answer_var,
                                font=("Microsoft YaHei UI", 12), width=35,
                                highlightbackground=THEME["border"], highlightthickness=1)
        answer_entry.pack(anchor="w", ipady=8)
        answer_entry.focus_set()

        error_lbl = tk.Label(content, text="", font=("Microsoft YaHei UI", 9),
                             bg=THEME["card_bg"], fg=THEME["danger"])
        error_lbl.pack(anchor="w", pady=(5, 10))

        btn_frame = tk.Frame(content, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        center = tk.Frame(btn_frame, bg=THEME["card_bg"])
        center.pack(anchor="center")

        tk.Button(center, text="取消", font=("Microsoft YaHei UI", 11),
                  bg=THEME["text_secondary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 5))

        def do_verify():
            answer = answer_var.get().strip()
            if not check_security_answer(answer):
                error_lbl.configure(text="安全问题答案错误")
                answer_var.set("")
                return
            self._show_change_pwd_step2(dialog, content)

        tk.Button(center, text="验证", font=("Microsoft YaHei UI", 11, "bold"),
                  bg=THEME["primary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=do_verify).pack(side=tk.LEFT, padx=(5, 0))

    def _show_change_pwd_step2(self, dialog, content):
        self._clear_frame(content)

        tk.Label(content, text="第二步：修改密码", font=("Microsoft YaHei UI", 12, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 5))
        tk.Label(content, text="✅ 身份验证通过", font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["success"]).pack(anchor="w", pady=(0, 15))

        tk.Label(content, text="原密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
        old_var = tk.StringVar()
        old_entry = tk.Entry(content, textvariable=old_var, show="●",
                             font=("Microsoft YaHei UI", 12), width=35,
                             highlightbackground=THEME["border"], highlightthickness=1)
        old_entry.pack(anchor="w", ipady=8, pady=(0, 5))
        old_entry.focus_set()

        tk.Label(content, text="新密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
        new_var = tk.StringVar()
        new_entry = tk.Entry(content, textvariable=new_var, show="●",
                             font=("Microsoft YaHei UI", 12), width=35,
                             highlightbackground=THEME["border"], highlightthickness=1)
        new_entry.pack(anchor="w", ipady=8, pady=(0, 5))

        tk.Label(content, text="确认新密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(content, textvariable=confirm_var, show="●",
                                 font=("Microsoft YaHei UI", 12), width=35,
                                 highlightbackground=THEME["border"], highlightthickness=1)
        confirm_entry.pack(anchor="w", ipady=8)

        error_lbl = tk.Label(content, text="", font=("Microsoft YaHei UI", 9),
                             bg=THEME["card_bg"], fg=THEME["danger"])
        error_lbl.pack(anchor="w", pady=(5, 5))

        btn_frame = tk.Frame(content, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        center = tk.Frame(btn_frame, bg=THEME["card_bg"])
        center.pack(anchor="center")

        tk.Button(center, text="取消", font=("Microsoft YaHei UI", 11),
                  bg=THEME["text_secondary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 5))

        def do_change():
            old_pwd = old_var.get().strip()
            new_pwd = new_var.get().strip()
            confirm = confirm_var.get().strip()
            if not check_password(old_pwd):
                error_lbl.configure(text="原密码错误")
                return
            if len(new_pwd) < 4:
                error_lbl.configure(text="新密码至少需要4个字符")
                return
            if new_pwd != confirm:
                error_lbl.configure(text="两次输入的密码不一致")
                return
            set_password(new_pwd)
            messagebox.showinfo("成功", "密码修改成功！")
            dialog.destroy()

        tk.Button(center, text="确认修改", font=("Microsoft YaHei UI", 11, "bold"),
                  bg=THEME["primary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=do_change).pack(side=tk.LEFT, padx=(5, 0))

    def _verify_security_question(self):
        # 如果没有设置安全问题，提示用户设置
        if not has_security_question():
            if messagebox.askyesno("安全设置", "尚未设置安全问题！\n\n是否现在设置安全问题以启用安全验证？"):
                self._show_initial_security_setup()
                return self._verify_security_question()  # 设置后重新验证
            else:
                return messagebox.askyesno("确认操作", "⚠️ 未设置安全问题！\n\n确定要继续此操作吗？")
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🔐 安全验证")
        dialog.geometry("420x460")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        # 弹窗居中
        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        x = parent_x + (parent_w // 2) - 210
        y = parent_y + (parent_h // 2) - 230
        dialog.geometry("+{}+{}".format(x, y))

        # 头部
        header = tk.Frame(dialog, bg=THEME["danger"])
        header.pack(fill=tk.X)
        tk.Label(header, text="⚠️ 安全验证",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["danger"], fg="white").pack(pady=(14, 14))

        # 表单区域
        form = tk.Frame(dialog, bg=THEME["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=(15, 10))

        question = get_security_question()

        # 提示文字
        tk.Label(form, text="为了安全，请回答以下问题：",
                font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 8))

        # 安全问题（卡片样式）
        q_card = tk.Frame(form, bg=THEME["primary_light"],
                          highlightbackground=THEME["primary"], highlightthickness=1)
        q_card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(q_card, text=f"❓ {question}",
                font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["primary_light"], fg=THEME["primary"],
                padx=12, pady=8).pack(anchor="w")

        # 答案输入框
        tk.Label(form, text="您的回答：",
                font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(0, 4))

        answer_var = tk.StringVar()
        answer_entry = tk.Entry(form, textvariable=answer_var,
                                font=("Microsoft YaHei UI", 12),
                                highlightbackground=THEME["border"], highlightthickness=1)
        answer_entry.pack(fill=tk.X, ipady=7)
        answer_entry.focus_set()

        # 反馈标签（验证成功/失败提示）
        self.security_feedback = tk.Label(form, text="", font=("Microsoft YaHei UI", 10),
                                         bg=THEME["card_bg"], fg=THEME["text"])
        self.security_feedback.pack(anchor="w", pady=(8, 0))

        # 按钮区域（固定在底部）
        btn_frame = tk.Frame(dialog, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, padx=25, pady=(0, 15))

        # 验证按钮组（初始显示）
        verify_btn_frame = tk.Frame(btn_frame, bg=THEME["card_bg"])
        verify_btn_frame.pack(fill=tk.X)

        cancel_btn = tk.Button(verify_btn_frame, text="取消",
                              font=("Microsoft YaHei UI", 11),
                              bg=THEME["text_secondary"], fg="white", relief="flat",
                              padx=20, pady=8, width=10, cursor="hand2",
                              command=lambda: self._close_security_dialog(dialog, False))
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        ok_btn = tk.Button(verify_btn_frame, text="验证答案",
                          font=("Microsoft YaHei UI", 11, "bold"),
                          bg=THEME["primary"], fg="white", relief="flat",
                          padx=20, pady=8, width=10, cursor="hand2",
                          command=lambda: self._verify_answer(dialog, answer_var, answer_entry, verify_btn_frame, confirm_btn_frame))
        ok_btn.pack(side=tk.RIGHT)

        # 确认按钮组（验证成功后显示）
        confirm_btn_frame = tk.Frame(btn_frame, bg=THEME["card_bg"])

        back_btn = tk.Button(confirm_btn_frame, text="返回修改",
                            font=("Microsoft YaHei UI", 11),
                            bg=THEME["text_secondary"], fg="white", relief="flat",
                            padx=20, pady=8, width=10, cursor="hand2",
                            command=lambda: self._back_to_verify(answer_entry, verify_btn_frame, confirm_btn_frame))
        back_btn.pack(side=tk.RIGHT, padx=(10, 0))

        confirm_btn = tk.Button(confirm_btn_frame, text="确认继续",
                               font=("Microsoft YaHei UI", 11, "bold"),
                               bg=THEME["success"], fg="white", relief="flat",
                               padx=20, pady=8, width=10, cursor="hand2",
                               command=lambda: self._close_security_dialog(dialog, True))
        confirm_btn.pack(side=tk.RIGHT)

        answer_entry.bind("<Return>", lambda e: self._verify_answer(dialog, answer_var, answer_entry, verify_btn_frame, confirm_btn_frame))

        dialog.wait_window()
        
        return hasattr(dialog, 'verified') and dialog.verified

    def _verify_answer(self, dialog, answer_var, answer_entry, verify_btn_frame, confirm_btn_frame):
        answer = answer_var.get().strip()
        if not answer:
            self.security_feedback.configure(text="⚠️ 请输入答案", fg=THEME["danger"])
            return
        if check_security_answer(answer):
            self.security_feedback.configure(text="✅ 验证成功！请确认是否继续操作", fg=THEME["success"])
            answer_entry.configure(state="disabled")
            verify_btn_frame.pack_forget()
            confirm_btn_frame.pack(fill=tk.X)
        else:
            self.security_feedback.configure(text="❌ 答案错误，请重新输入", fg=THEME["danger"])
            answer_var.set("")
            answer_entry.focus_set()

    def _back_to_verify(self, answer_entry, verify_btn_frame, confirm_btn_frame):
        self.security_feedback.configure(text="", fg=THEME["text"])
        answer_entry.configure(state="normal")
        answer_entry.delete(0, tk.END)
        answer_entry.focus_set()
        confirm_btn_frame.pack_forget()
        verify_btn_frame.pack(fill=tk.X)

    def _close_security_dialog(self, dialog, verified):
        dialog.verified = verified
        dialog.destroy()

    def _verify_diary_password(self):
        # 隐私保护未开启或没有密码，直接允许访问
        if not has_password() or not get_setting("diary_privacy_enabled", False):
            return True

        dialog = tk.Toplevel(self.root)
        dialog.title("🔐 日记密码")
        dialog.geometry("380x360")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        # 弹窗居中
        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        x = parent_x + (parent_w // 2) - 190
        y = parent_y + (parent_h // 2) - 180
        dialog.geometry("+{}+{}".format(x, y))

        header = tk.Frame(dialog, bg=THEME["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="🔐 日记隐私保护",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["primary"], fg="white").pack(pady=(15, 15))

        form = tk.Frame(dialog, bg=THEME["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        tk.Label(form, text="请输入日记密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

        password_var = tk.StringVar()
        password_entry = tk.Entry(form, textvariable=password_var, show="●",
                                 font=("Microsoft YaHei UI", 12), width=30,
                                 highlightbackground=THEME["border"], highlightthickness=1)
        password_entry.pack(anchor="w", ipady=8)
        password_entry.focus_set()

        self.login_error = tk.Label(form, text="", font=("Microsoft YaHei UI", 9),
                                   bg=THEME["card_bg"], fg=THEME["danger"])
        self.login_error.pack(anchor="w", pady=(5, 0))

        # 忘记密码链接
        forgot_lbl = tk.Label(form, text="忘记密码？", font=("Microsoft YaHei UI", 9, "underline"),
                              bg=THEME["card_bg"], fg=THEME["primary"], cursor="hand2")
        forgot_lbl.pack(anchor="e", pady=(5, 0))
        forgot_lbl.bind("<Button-1>", lambda e: self._show_forgot_password(dialog))

        btn_frame = tk.Frame(form, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        center = tk.Frame(btn_frame, bg=THEME["card_bg"])
        center.pack(anchor="center")

        cancel_btn = tk.Button(center, text="取消", font=("Microsoft YaHei UI", 11),
                              bg=THEME["text_secondary"], fg="white", relief="flat",
                              padx=20, pady=8, width=10, cursor="hand2",
                              command=lambda: self._close_password_dialog(dialog, False))
        cancel_btn.pack(side=tk.LEFT, padx=(0, 5))

        ok_btn = tk.Button(center, text="确认", font=("Microsoft YaHei UI", 11, "bold"),
                          bg=THEME["primary"], fg="white", relief="flat",
                          padx=20, pady=8, width=10, cursor="hand2",
                          command=lambda: self._check_password_and_close(dialog, password_var))
        ok_btn.pack(side=tk.LEFT, padx=(5, 0))
        ok_btn.pack(side=tk.LEFT)

        password_entry.bind("<Return>", lambda e: self._check_password_and_close(dialog, password_var))

        dialog.wait_window()
        
        return hasattr(dialog, 'verified') and dialog.verified

    def _show_export_dialog(self, export_type):
        type_names = {"schedule": "日程管理", "task": "每日任务", "diary": "我的日记", "all": "全部数据"}
        type_name = type_names.get(export_type, export_type)

        dialog = tk.Toplevel(self.root)
        dialog.title("📤 数据导出与导入")
        dialog.geometry("400x440")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        # 弹窗居中
        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        x = parent_x + (parent_w // 2) - 200
        y = parent_y + (parent_h // 2) - 220
        dialog.geometry("+{}+{}".format(x, y))

        header = tk.Frame(dialog, bg=THEME["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="📤 数据导出与导入",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["primary"], fg="white").pack(pady=(14, 14))

        form = tk.Frame(dialog, bg=THEME["card_bg"])
        form.pack(fill=tk.X, padx=25, pady=(18, 12))

        # 导出内容提示
        hint_card = tk.Frame(form, bg=THEME["primary_light"],
                             highlightbackground=THEME["primary"], highlightthickness=1)
        hint_card.pack(fill=tk.X, pady=(0, 16))
        tk.Label(hint_card, text=f"📦 导出内容：{type_name}",
                font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["primary_light"], fg=THEME["primary"],
                padx=12, pady=8).pack(anchor="w")

        # 格式选择
        tk.Label(form, text="选择导出格式：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

        format_var = tk.StringVar(value="excel")

        excel_radio = tk.Radiobutton(form, text="📊  Excel 表格 (.xlsx)", variable=format_var,
                                     value="excel", bg=THEME["card_bg"], fg=THEME["text"],
                                     font=("Microsoft YaHei UI", 11), padx=4, pady=4)
        excel_radio.pack(anchor="w", pady=(0, 6))

        sql_radio = tk.Radiobutton(form, text="📄  SQL 文件 (.sql)", variable=format_var,
                                   value="sql", bg=THEME["card_bg"], fg=THEME["text"],
                                   font=("Microsoft YaHei UI", 11), padx=4, pady=4)
        sql_radio.pack(anchor="w")

        # 确认提示
        tk.Label(form, text="确认要导出所选数据吗？",
                font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(16, 0))

        # 按钮区域
        btn_frame = tk.Frame(dialog, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, padx=25, pady=(0, 18))

        cancel_btn = tk.Button(btn_frame, text="取消",
                              font=("Microsoft YaHei UI", 11),
                              bg=THEME["text_secondary"], fg="white", relief="flat",
                              padx=20, pady=8, width=10, cursor="hand2", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        ok_btn = tk.Button(btn_frame, text="确认导出",
                          font=("Microsoft YaHei UI", 11, "bold"),
                          bg=THEME["primary"], fg="white", relief="flat",
                          padx=20, pady=8, width=10, cursor="hand2",
                          command=lambda: self._do_export(export_type, format_var.get(), dialog))
        ok_btn.pack(side=tk.RIGHT)

        dialog.wait_window()

    def _do_export(self, export_type, format_type, dialog):
        dialog.destroy()

        try:
            from datetime import datetime

            # 导出到用户桌面
            export_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(export_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format_type == "excel":
                file_path = self._export_to_excel(export_type, export_dir, timestamp)
            else:
                file_path = self._export_to_sql(export_type, export_dir, timestamp)

            messagebox.showinfo("导出成功", f"数据已导出到：\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出失败：{str(e)}")

    def _export_to_excel(self, export_type, export_dir, timestamp):
        import pandas as pd
        from database import ScheduleDB, DailyTaskDB, DiaryDB, CheckinDB

        file_name = ""
        data_frames = []
        sheet_names = []

        if export_type == "schedule" or export_type == "all":
            schedules = ScheduleDB.get_all()
            if schedules:
                df = pd.DataFrame([dict(r) for r in schedules])
                data_frames.append(df)
                sheet_names.append("日程数据")

        if export_type == "task" or export_type == "all":
            tasks = DailyTaskDB.get_all()
            if tasks:
                df = pd.DataFrame([dict(r) for r in tasks])
                data_frames.append(df)
                sheet_names.append("任务数据")

        if export_type == "diary" or export_type == "all":
            diaries = DiaryDB.get_all()
            if diaries:
                df = pd.DataFrame([dict(r) for r in diaries])
                data_frames.append(df)
                sheet_names.append("日记数据")

        if export_type == "all":
            checkins = CheckinDB.get_all_checkins()
            if checkins:
                df = pd.DataFrame([dict(r) for r in checkins])
                data_frames.append(df)
                sheet_names.append("打卡记录")
            items = CheckinDB.get_all_items()
            if items:
                df = pd.DataFrame([dict(r) for r in items])
                data_frames.append(df)
                sheet_names.append("打卡项目")

        if not data_frames:
            raise Exception("没有可导出的数据")
        
        if export_type == "all":
            file_name = f"全部数据_{timestamp}.xlsx"
        else:
            names = {"schedule": "日程", "task": "任务", "diary": "日记"}
            file_name = f"{names[export_type]}数据_{timestamp}.xlsx"
        
        file_path = os.path.join(export_dir, file_name)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for df, name in zip(data_frames, sheet_names):
                df.to_excel(writer, sheet_name=name, index=False)

        return file_path

    def _export_to_sql(self, export_type, export_dir, timestamp):
        from database import ScheduleDB, DailyTaskDB, DiaryDB, CheckinDB
        
        file_name = ""
        sql_content = "-- Schedule Planner 数据导出\n"
        sql_content += f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        def generate_insert(table_name, rows):
            if not rows:
                return ""
            cols = rows[0].keys()
            cols_str = ", ".join(cols)
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES\n"
            values = []
            for row in rows:
                row_values = []
                for col in cols:
                    val = row[col]
                    if val is None:
                        row_values.append("NULL")
                    elif isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        row_values.append("'" + escaped_val + "'")
                    else:
                        row_values.append(str(val))
                values.append("(" + ", ".join(row_values) + ")")
            sql += ",\n".join(values) + ";\n\n"
            return sql
        
        if export_type == "schedule" or export_type == "all":
            schedules = ScheduleDB.get_all()
            sql_content += generate_insert("schedules", schedules)
        
        if export_type == "task" or export_type == "all":
            tasks = DailyTaskDB.get_all()
            sql_content += generate_insert("daily_tasks", tasks)
        
        if export_type == "diary" or export_type == "all":
            diaries = DiaryDB.get_all()
            sql_content += generate_insert("diaries", diaries)
        
        if export_type == "all":
            checkins = CheckinDB.get_all_checkins()
            sql_content += generate_insert("checkins", checkins)
            checkin_items = CheckinDB.get_all_items()
            sql_content += generate_insert("checkin_items", checkin_items)
        
        if sql_content.count("INSERT INTO") == 0:
            raise Exception("没有可导出的数据")
        
        if export_type == "all":
            file_name = f"全部数据_{timestamp}.sql"
        else:
            names = {"schedule": "日程", "task": "任务", "diary": "日记"}
            file_name = f"{names[export_type]}数据_{timestamp}.sql"
        
        file_path = os.path.join(export_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sql_content)

        return file_path

    # --- 数据备份 ---

    def _do_manual_backup(self):
        from utils.backup import manual_backup
        try:
            path = manual_backup()
            messagebox.showinfo("成功", f"备份已保存到\n{path}")
        except Exception as e:
            messagebox.showerror("错误", f"备份失败：{str(e)}")

    def _do_restore_backup(self):
        from tkinter import filedialog
        from utils.backup import list_backups, restore_backup

        backups = list_backups()
        if not backups:
            messagebox.showinfo("提示", "暂无可用的备份文件")
            return

        file_path = filedialog.askopenfilename(
            title="选择要恢复的备份文件",
            initialdir=os.path.dirname(backups[0]),
            filetypes=[("数据库备份", "*.db"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        if not messagebox.askyesno("⚠️ 确认恢复",
                                    "恢复备份将替换当前所有数据，此操作不可撤销！\n\n确定要继续吗？"):
            return

        try:
            restore_backup(file_path)
            messagebox.showinfo("成功", "备份已恢复！\n请重启程序以加载恢复的数据。")
        except Exception as e:
            messagebox.showerror("错误", f"恢复失败：{str(e)}")

    def _show_import_dialog(self, import_type):
        from tkinter import filedialog
        import os

        type_names = {"schedule": "日程管理", "task": "每日任务", "diary": "我的日记", "all": "全部数据"}
        type_name = type_names.get(import_type, import_type)

        file_path = filedialog.askopenfilename(
            title=f"选择要导入的文件 - {type_name}",
            filetypes=[
                ("支持的文件", "*.xlsx *.sql"),
                ("Excel 文件", "*.xlsx"),
                ("SQL 文件", "*.sql"),
                ("所有文件", "*.*")
            ]
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ('.xlsx', '.sql'):
            messagebox.showerror("错误", "不支持的文件格式，请选择 .xlsx 或 .sql 文件")
            return

        self._do_import(import_type, file_path)

    def _do_import(self, import_type, file_path):
        import os
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.xlsx':
                count, errors = self._import_from_excel(import_type, file_path)
            else:
                count, errors = self._import_from_sql(import_type, file_path)
            msg = f"数据导入完成！\n共导入 {count} 条记录"
            if errors:
                msg += f"\n\n有 {len(errors)} 条记录导入失败："
                for err in errors[:5]:
                    msg += f"\n  {err}"
                if len(errors) > 5:
                    msg += f"\n  ... 等共 {len(errors)} 条"
            messagebox.showinfo("导入结果", msg)
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def _import_from_excel(self, import_type, file_path):
        import pandas as pd
        from database import get_connection

        sheet_map = {
            "日程数据": ("schedules", ["title", "description", "schedule_date", "start_time", "end_time", "location", "priority", "is_done"]),
            "任务数据": ("daily_tasks", ["title", "description", "task_date", "priority", "repeat", "is_done", "sort_order"]),
            "日记数据": ("diaries", ["title", "content", "mood", "weather", "diary_date"]),
            "打卡记录": ("checkins", ["task_title", "checkin_date", "checkin_time", "status", "note", "repeat"]),
            "打卡项目": ("checkin_items", ["title", "description", "sort_order"]),
        }
        type_sheet_map = {
            "schedule": ["日程数据"],
            "task": ["任务数据"],
            "diary": ["日记数据"],
            "all": ["日程数据", "任务数据", "日记数据", "打卡记录", "打卡项目"],
        }
        allowed_sheets = type_sheet_map[import_type]

        xls = pd.ExcelFile(file_path, engine='openpyxl')
        conn = get_connection()
        total = 0
        errors = []
        try:
            for sheet_name in xls.sheet_names:
                if sheet_name not in sheet_map or sheet_name not in allowed_sheets:
                    continue
                table, expected_cols = sheet_map[sheet_name]
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if all(isinstance(c, int) for c in df.columns):
                    raise Exception(f"文件格式不正确：工作表「{sheet_name}」的列名无效，请使用新版本导出的文件重新导入")
                if df.empty:
                    continue
                df = df.drop(columns=['id'], errors='ignore')
                cols = [c for c in expected_cols if c in df.columns]
                if not cols:
                    continue
                placeholders = ", ".join(["?"] * len(cols))
                cols_str = ", ".join(cols)
                sql = f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})"
                for _, row in df.iterrows():
                    values = []
                    for c in cols:
                        val = row[c]
                        if pd.isna(val):
                            values.append(None)
                        else:
                            values.append(val)
                    try:
                        conn.execute(sql, values)
                        total += 1
                    except Exception as e:
                        errors.append(f"[{sheet_name}] 第{_}行: {e}")
            conn.commit()
        finally:
            conn.close()
        if total == 0:
            raise Exception("没有找到可导入的数据")
        return total, errors

    def _import_from_sql(self, import_type, file_path):
        from database import get_connection

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        type_table_map = {
            "schedule": ["schedules"],
            "task": ["daily_tasks"],
            "diary": ["diaries"],
            "all": ["schedules", "daily_tasks", "diaries", "checkins", "checkin_items"],
        }
        allowed_tables = type_table_map[import_type]

        # 去掉注释行，避免多行 INSERT 被注释前缀跳过
        lines = content.splitlines()
        content = '\n'.join(l for l in lines if not l.strip().startswith('--'))
        content = content.replace("INSERT INTO", "INSERT OR IGNORE INTO")
        conn = get_connection()
        total = 0
        errors = []
        try:
            for stmt in content.split(';'):
                stmt = stmt.strip()
                if not stmt:
                    continue
                if not stmt.upper().startswith('INSERT'):
                    continue
                table_match = False
                for t in allowed_tables:
                    if f"INTO {t} " in stmt or f"INTO {t}(" in stmt:
                        table_match = True
                        break
                if not table_match:
                    continue
                try:
                    conn.execute(stmt)
                    total += 1
                except Exception as e:
                    preview = stmt[:80].replace('\n', ' ')
                    errors.append(f"{preview}...: {e}")
            conn.commit()
        finally:
            conn.close()
        if total == 0:
            raise Exception("没有找到可导入的数据")
        return total, errors

    def _show_forgot_password(self, parent_dialog):
        if parent_dialog:
            parent_dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("🔐 找回密码")
        dialog.geometry("460x560")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=THEME["card_bg"])

        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        x = parent_x + (parent_w // 2) - 230
        y = parent_y + (parent_h // 2) - 290
        dialog.geometry("+{}+{}".format(x, y))

        header = tk.Frame(dialog, bg=THEME["primary"])
        header.pack(fill=tk.X)
        tk.Label(header, text="🔐 找回密码",
                font=("Microsoft YaHei UI", 14, "bold"),
                bg=THEME["primary"], fg="white").pack(pady=(15, 15))

        content = tk.Frame(dialog, bg=THEME["card_bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        question = get_security_question()
        if not question:
            tk.Label(content, text="未设置安全问题，无法找回密码",
                    font=("Microsoft YaHei UI", 11),
                    bg=THEME["card_bg"], fg=THEME["danger"]).pack(anchor="w", pady=20)
            tk.Button(content, text="关闭", font=("Microsoft YaHei UI", 11),
                      bg=THEME["text_secondary"], fg="white", relief="flat",
                      padx=25, pady=8, cursor="hand2", command=dialog.destroy).pack(anchor="center")
            return

        self._show_forgot_step1(dialog, content, question)
        dialog.wait_window()

    def _clear_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _show_forgot_step1(self, dialog, content, question):
        self._clear_frame(content)

        tk.Label(content, text="第一步：验证身份", font=("Microsoft YaHei UI", 12, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))
        tk.Label(content, text=f"❓ {question}", font=("Microsoft YaHei UI", 11, "bold"),
                bg=THEME["card_bg"], fg=THEME["primary"]).pack(anchor="w", pady=(0, 10))

        answer_var = tk.StringVar()
        answer_entry = tk.Entry(content, textvariable=answer_var,
                                font=("Microsoft YaHei UI", 12), width=35,
                                highlightbackground=THEME["border"], highlightthickness=1)
        answer_entry.pack(anchor="w", ipady=8)
        answer_entry.focus_set()

        error_lbl = tk.Label(content, text="", font=("Microsoft YaHei UI", 9),
                             bg=THEME["card_bg"], fg=THEME["danger"])
        error_lbl.pack(anchor="w", pady=(5, 10))

        btn_frame = tk.Frame(content, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        center = tk.Frame(btn_frame, bg=THEME["card_bg"])
        center.pack(anchor="center")

        tk.Button(center, text="取消", font=("Microsoft YaHei UI", 11),
                  bg=THEME["text_secondary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 5))

        def do_verify():
            answer = answer_var.get().strip()
            if not check_security_answer(answer):
                error_lbl.configure(text="安全问题答案错误")
                answer_var.set("")
                return
            self._show_forgot_step2(dialog, content)

        tk.Button(center, text="验证", font=("Microsoft YaHei UI", 11, "bold"),
                  bg=THEME["primary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=do_verify).pack(side=tk.LEFT, padx=(5, 0))

    def _show_forgot_step2(self, dialog, content):
        self._clear_frame(content)

        tk.Label(content, text="第二步：设置新密码", font=("Microsoft YaHei UI", 12, "bold"),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 5))
        tk.Label(content, text="✅ 身份验证通过", font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["success"]).pack(anchor="w", pady=(0, 15))

        tk.Label(content, text="新密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(content, textvariable=pwd_var, show="●",
                             font=("Microsoft YaHei UI", 12), width=35,
                             highlightbackground=THEME["border"], highlightthickness=1)
        pwd_entry.pack(anchor="w", ipady=8, pady=(0, 5))
        pwd_entry.focus_set()

        tk.Label(content, text="确认新密码：", font=("Microsoft YaHei UI", 11),
                bg=THEME["card_bg"], fg=THEME["text"]).pack(anchor="w")
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(content, textvariable=confirm_var, show="●",
                                 font=("Microsoft YaHei UI", 12), width=35,
                                 highlightbackground=THEME["border"], highlightthickness=1)
        confirm_entry.pack(anchor="w", ipady=8)

        error_lbl = tk.Label(content, text="", font=("Microsoft YaHei UI", 9),
                             bg=THEME["card_bg"], fg=THEME["danger"])
        error_lbl.pack(anchor="w", pady=(5, 5))

        btn_frame = tk.Frame(content, bg=THEME["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        center = tk.Frame(btn_frame, bg=THEME["card_bg"])
        center.pack(anchor="center")

        tk.Button(center, text="取消", font=("Microsoft YaHei UI", 11),
                  bg=THEME["text_secondary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 5))

        def do_reset():
            pwd = pwd_var.get().strip()
            confirm = confirm_var.get().strip()
            if len(pwd) < 4:
                error_lbl.configure(text="新密码至少需要4个字符")
                return
            if pwd != confirm:
                error_lbl.configure(text="两次输入的密码不一致")
                return
            set_password(pwd)
            messagebox.showinfo("找回成功", "密码已重置成功！")
            dialog.destroy()

        tk.Button(center, text="确认重置", font=("Microsoft YaHei UI", 11, "bold"),
                  bg=THEME["primary"], fg="white", relief="flat",
                  padx=20, pady=8, width=10, cursor="hand2", command=do_reset).pack(side=tk.LEFT, padx=(5, 0))

    def _check_password_and_close(self, dialog, password_var):
        password = password_var.get().strip()
        if check_password(password):
            dialog.verified = True
            dialog.destroy()
        else:
            self.login_error.configure(text="密码错误，请重试")
            password_var.set("")

    def _close_password_dialog(self, dialog, verified):
        dialog.verified = verified
        dialog.destroy()

    # --- 系统托盘 & 关闭行为 ---

    def _ensure_tray(self):
        """确保托盘图标已创建"""
        if not self._tray_active:
            tray_manager.create_tray(self._icon_path, self._show_window, self._quit_app)
            self._tray_active = True

    def _on_close(self):
        """窗口关闭时的处理"""
        if get_setting("minimize_to_tray", False):
            set_setting("window_geometry", self.root.geometry())
            self.root.withdraw()
            self._ensure_tray()
        else:
            self._quit_app()

    def _show_window(self):
        """从托盘恢复主窗口"""
        self.root.after(0, self._do_show_window)

    def _do_show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _quit_app(self):
        """彻底退出程序"""
        # 保存窗口几何信息
        set_setting("window_geometry", self.root.geometry())
        if self._scheduler_id:
            self.root.after_cancel(self._scheduler_id)
            self._scheduler_id = None
        tray_manager.destroy_tray()
        self._tray_active = False
        self.root.after(0, self.root.destroy)

    # --- 通知提醒 ---

    def _toggle_notification(self):
        enabled = get_setting("notification_enabled", False)
        if enabled:
            self._start_notification_scheduler()
        else:
            self._stop_notification_scheduler()

    def _on_reminder_minutes_change(self, event=None):
        value = self._reminder_var.get()
        minutes = int(value.split()[0])
        set_setting("reminder_minutes", minutes)

    def _flash_entry(self, entry, valid, error_label=None, error_msg=""):
        color = "#28a745" if valid else "#dc3545"
        entry.configure(highlightbackground=color)
        if error_label:
            if valid:
                error_label.pack_forget()
            else:
                error_label.configure(text=error_msg)
                error_label.pack(anchor="w", padx=(28, 0))
        if valid:
            self.root.after(1500, lambda: entry.configure(highlightbackground=THEME["border"]))

    def _on_checkin_time_change(self, event=None):
        value = self._checkin_time_var.get().strip()
        import re
        if re.match(r'^\d{1,2}:\d{2}$', value):
            parts = value.split(":")
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                set_setting("checkin_reminder_time", f"{h:02d}:{m:02d}")
                self._flash_entry(self._checkin_time_entry, True, self._checkin_error_label)
                return
        self._flash_entry(self._checkin_time_entry, False, self._checkin_error_label,
                          "格式错误，请输入正确的时间格式，如 21:00")

    def _on_daily_task_time_change(self, event=None):
        value = self._daily_task_time_var.get().strip()
        import re
        if re.match(r'^\d{1,2}:\d{2}$', value):
            parts = value.split(":")
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                set_setting("daily_task_reminder_time", f"{h:02d}:{m:02d}")
                self._flash_entry(self._daily_task_time_entry, True, self._daily_task_error_label)
                return
        self._flash_entry(self._daily_task_time_entry, False, self._daily_task_error_label,
                          "格式错误，请输入正确的时间格式，如 08:00")

    def _on_repeat_interval_change(self, event=None):
        value = self._repeat_var.get().strip()
        try:
            minutes = int(value)
            if minutes > 0:
                set_setting("reminder_repeat_interval", minutes)
                self._flash_entry(self._repeat_entry, True, self._repeat_error_label)
                return
        except ValueError:
            pass
        self._flash_entry(self._repeat_entry, False, self._repeat_error_label,
                          "格式错误，请输入大于 0 的正整数")

    def _on_max_count_change(self, event=None):
        value = self._max_count_var.get().strip()
        try:
            count = int(value)
            if count >= 0:
                set_setting("reminder_max_count", count)
                self._flash_entry(self._count_entry, True, self._count_error_label)
                return
        except ValueError:
            pass
        self._flash_entry(self._count_entry, False, self._count_error_label,
                          "格式错误，请输入大于等于 0 的整数")

    def _start_notification_scheduler(self):
        self._notified_schedules = {}
        self._notified_checkin_time = None
        self._notified_checkin_count = 0
        self._notified_daily_task_time = None
        self._notified_daily_task_count = 0
        self._check_reminders()

    def _stop_notification_scheduler(self):
        if self._scheduler_id:
            self.root.after_cancel(self._scheduler_id)
            self._scheduler_id = None

    def _check_reminders(self):
        if not get_setting("notification_enabled", False):
            self._scheduler_id = None
            return

        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        repeat_interval = get_setting("reminder_repeat_interval", 5)
        max_count = get_setting("reminder_max_count", 0)

        # 重置过期的通知记录
        if self._notified_schedules:
            oldest_key = next(iter(self._notified_schedules))
            if self._notified_schedules[oldest_key][0].strftime("%Y-%m-%d") != today:
                self._notified_schedules = {}
        if self._notified_checkin_time and self._notified_checkin_time.strftime("%Y-%m-%d") != today:
            self._notified_checkin_time = None
            self._notified_checkin_count = 0
        if self._notified_daily_task_time and self._notified_daily_task_time.strftime("%Y-%m-%d") != today:
            self._notified_daily_task_time = None
            self._notified_daily_task_count = 0

        # 检查日程提醒
        reminder_minutes = get_setting("reminder_minutes", 15)
        schedules = []
        try:
            from database import ScheduleDB
            schedules = ScheduleDB.get_by_date(today)
            for s in schedules:
                if s["is_done"] or not s["start_time"]:
                    continue
                sid = s["id"]
                try:
                    sched_time = datetime.strptime(f"{today} {s['start_time']}", "%Y-%m-%d %H:%M")
                    reminder_time = sched_time.replace(second=0) - timedelta(minutes=reminder_minutes)
                    if now.replace(second=0, microsecond=0) < reminder_time:
                        continue
                    entry = self._notified_schedules.get(sid)
                    if entry:
                        last_time, count = entry
                        if max_count > 0 and count >= max_count:
                            continue
                        if (now - last_time).total_seconds() < repeat_interval * 60:
                            continue
                        self._notified_schedules[sid] = (now, count + 1)
                    else:
                        self._notified_schedules[sid] = (now, 1)
                    self._send_notification(
                        "📅 日程提醒",
                        f"「{s['title']}」将于 {s['start_time']} 开始"
                    )
                except (ValueError, TypeError):
                    pass
        except Exception:
            pass

        # 检查打卡提醒
        checkin_time_str = get_setting("checkin_reminder_time", "21:00")
        if current_time >= checkin_time_str:
            try:
                should_notify = False
                if self._notified_checkin_time is None:
                    should_notify = True
                elif (now - self._notified_checkin_time).total_seconds() >= repeat_interval * 60:
                    if max_count == 0 or self._notified_checkin_count < max_count:
                        should_notify = True
                if should_notify:
                    from database import CheckinDB
                    checkins = CheckinDB.get_by_date(today)
                    incomplete = [c for c in checkins if c["status"] == 0]
                    if incomplete:
                        names = "、".join([c["task_title"] for c in incomplete[:5]])
                        extra = f"等{len(incomplete)}项" if len(incomplete) > 5 else ""
                        self._send_notification(
                            "✅ 打卡提醒",
                            f"今日还有 {len(incomplete)} 项未打卡：{names}{extra}"
                        )
                        self._notified_checkin_time = now
                        self._notified_checkin_count += 1
            except Exception:
                pass

        # 检查每日任务提醒
        daily_task_time_str = get_setting("daily_task_reminder_time", "08:00")
        if current_time >= daily_task_time_str:
            try:
                should_notify = False
                if self._notified_daily_task_time is None:
                    should_notify = True
                elif (now - self._notified_daily_task_time).total_seconds() >= repeat_interval * 60:
                    if max_count == 0 or self._notified_daily_task_count < max_count:
                        should_notify = True
                if should_notify:
                    from database import DailyTaskDB
                    tasks = DailyTaskDB.get_by_date(today)
                    incomplete = [t for t in tasks if not t["is_done"]]
                    if incomplete:
                        names = "、".join([t["title"] for t in incomplete[:5]])
                        extra = f"等{len(incomplete)}项" if len(incomplete) > 5 else ""
                        self._send_notification(
                            "📋 每日任务提醒",
                            f"今日还有 {len(incomplete)} 项任务未完成：{names}{extra}"
                        )
                        self._notified_daily_task_time = now
                        self._notified_daily_task_count += 1
            except Exception:
                pass

        # 计算下次检查的精确延迟（毫秒），而非固定 60 秒
        next_delay_ms = self._calc_next_delay(now, today, reminder_minutes, schedules)
        self._scheduler_id = self.root.after(next_delay_ms, self._check_reminders)

    def _calc_next_delay(self, now, today, reminder_minutes, schedules):
        """计算距离下次提醒的精确延迟（毫秒），最小 5 秒，最大 60 秒"""
        min_delta = None
        try:
            for s in schedules:
                if s["is_done"] or not s["start_time"]:
                    continue
                try:
                    sched_time = datetime.strptime(f"{today} {s['start_time']}", "%Y-%m-%d %H:%M")
                    reminder_time = sched_time - timedelta(minutes=reminder_minutes)
                    delta = (reminder_time - now).total_seconds()
                    if delta > 0 and (min_delta is None or delta < min_delta):
                        min_delta = delta
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass

        if min_delta is not None:
            return max(5000, int(min_delta * 1000))
        else:
            return 60000

    def _send_notification(self, title, msg):
        # 发送系统 Toast 通知（含提示音）
        try:
            from utils.notification import send_toast
            send_toast(title, msg)
        except Exception:
            pass

        # 无论窗口状态，始终显示应用内弹窗确保可见
        try:
            self._show_notify_popup(title, msg)
        except Exception:
            pass

    def _show_notify_popup(self, title, msg):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=THEME["card_bg"])

        popup_w, popup_h = 340, 110
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - popup_w - 20
        y = screen_h - popup_h - 60
        popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        frame = tk.Frame(popup, bg=THEME["card_bg"], highlightbackground=THEME["primary"],
                         highlightthickness=2)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text=title, font=("Microsoft YaHei UI", 12, "bold"),
                bg=THEME["card_bg"], fg=THEME["primary"], anchor="w").pack(fill=tk.X, padx=15, pady=(12, 2))
        tk.Label(frame, text=msg, font=("Microsoft YaHei UI", 10),
                bg=THEME["card_bg"], fg=THEME["text"], anchor="w",
                wraplength=310).pack(fill=tk.X, padx=15, pady=(0, 10))

        popup.lift()
        popup.attributes("-topmost", True)

        popup.bind("<Button-1>", lambda e: popup.destroy())
        popup.after(10000, lambda: popup.destroy() if popup.winfo_exists() else None)

    def run(self):
        self.root.mainloop()