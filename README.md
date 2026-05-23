# DayFlow - 日程记事本

一款基于 Python + Tkinter 的桌面个人效率管理应用，集成日程、任务、打卡、日记等模块，帮助你高效管理每一天。

## 功能特性

- **日程管理** — 日历视图创建/编辑日程，支持时间范围、地点、优先级（1-3级）
- **每日任务** — 按天管理任务，支持每日/工作日/周末等重复模式
- **打卡追踪** — 自定义打卡项目，按日记录习惯养成进度
- **我的日记** — 带心情和天气记录的日记本，支持密码保护与安全问题找回
- **数据统计** — 概览仪表盘与趋势图表，直观了解个人效率
- **整体态势** — 跨模块数据汇总视图
- **系统设置** — 开机自启、通知提醒、数据导入导出、备份恢复、隐私保护

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3 |
| UI 框架 | tkinter + [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) |
| 数据库 | SQLite3 (WAL 模式) |
| 数据导出 | pandas + openpyxl (Excel) |
| 系统托盘 | pystray + Pillow |
| 通知 | winotify (Windows Toast) |
| 农历 | lunarcalendar |
| 打包 | PyInstaller |

## 项目结构

```
├── main.py                # 程序入口
├── database.py            # SQLite 数据库层（5 张表）
├── requirements.txt       # Python 依赖
├── SchedulePlanner.spec   # PyInstaller 打包配置
├── views/                 # UI 视图模块
│   ├── main_window.py     #   主窗口（侧边栏导航）
│   ├── calendar_view.py   #   日程日历视图
│   ├── task_view.py       #   每日任务视图
│   ├── checkin_view.py    #   打卡追踪视图
│   ├── diary_view.py      #   日记视图
│   ├── stats_view.py      #   数据统计视图
│   └── all_tasks_view.py  #   整体态势视图
├── utils/                 # 工具模块
│   ├── app_settings.py    #   设置管理 + 开机自启
│   ├── backup.py          #   自动/手动备份
│   ├── date_picker.py     #   自定义日期选择器
│   ├── lunar.py           #   农历/干支/节气
│   ├── notification.py    #   通知提醒
│   ├── password_manager.py#   密码管理 (PBKDF2-SHA256)
│   └── tray_manager.py    #   系统托盘管理
└── src/images/bg.ico      # 应用图标
```

## 下载安装

前往 [Releases](https://github.com/KingLann/schedule_planner/releases) 下载最新版本的 `SchedulePlanner.exe`，双击即可运行，无需安装 Python 环境。

> 仅支持 Windows 10/11 系统

## 快速开始（从源码运行）

### 环境要求

- Windows 10/11
- Python 3.8+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller SchedulePlanner.spec
```

打包产物位于 `dist/SchedulePlanner.exe`。

## 数据存储

- 运行时数据库：`%APPDATA%\SchedulePlanner\schedule.db`
- 配置文件：`%APPDATA%\SchedulePlanner\config\app_settings.json`
- 自动备份保留最近 30 份，支持手动备份与恢复

## 导出格式

支持将数据导出为 Excel (.xlsx) 和 SQL 文件，方便备份和迁移。

## 页面预览

日程管理：

![image-20260523160956433](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231610572.png)

每日任务：

![image-20260523161132195](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231611305.png)

打卡追踪：

![image-20260523161144752](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231611837.png)

整体态势：

![image-20260523161217877](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231612978.png)

数据统计：

![image-20260523161240733](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231612805.png)

我的日记：

![image-20260523161318140](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231613217.png)

系统设置：

![image-20260523161338907](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231613004.png)

![image-20260523161400168](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231614237.png)

![image-20260523161425600](https://limg33.oss-cn-hangzhou.aliyuncs.com/note/202605231614676.png)













## License

MIT
