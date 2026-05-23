# -*- coding: utf-8 -*-
"""测试所有导出/导入组合 — 每种组合导出后清空再导入"""

import sys, io, os, tempfile, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import ScheduleDB, DailyTaskDB, DiaryDB, CheckinDB, get_connection


def insert_test_data():
    ScheduleDB.add('测试日程1', '描述1', '2026-05-22', '09:00', '10:00', '办公室', 2)
    ScheduleDB.add('测试日程2', '描述2', '2026-05-23', '14:00', '', '', 1)
    DailyTaskDB.add('测试任务1', '任务描述', '2026-05-22', 1)
    DailyTaskDB.add('测试任务2', '', '2026-05-22', 2, 'weekday')
    DiaryDB.save('2026-05-22', '测试日记', '今天天气不错', 'happy', 'sunny')
    CheckinDB.add_item('早起打卡', '每天7点前起床')
    CheckinDB.add_item('运动打卡', '每天运动30分钟')
    CheckinDB.add_task('早起打卡', '2026-05-22', '', 'daily')
    CheckinDB.add_task('运动打卡', '2026-05-22', '', 'daily')


def clear_all_data():
    ScheduleDB.clear_all()
    DailyTaskDB.clear_all()
    DiaryDB.clear_all()
    CheckinDB.clear_all()


def do_export_excel(export_type, export_dir, timestamp):
    data_frames, sheet_names = [], []
    if export_type in ('schedule', 'all'):
        rows = ScheduleDB.get_all()
        if rows:
            data_frames.append(pd.DataFrame([dict(r) for r in rows]))
            sheet_names.append('日程数据')
    if export_type in ('task', 'all'):
        rows = DailyTaskDB.get_all()
        if rows:
            data_frames.append(pd.DataFrame([dict(r) for r in rows]))
            sheet_names.append('任务数据')
    if export_type in ('diary', 'all'):
        rows = DiaryDB.get_all()
        if rows:
            data_frames.append(pd.DataFrame([dict(r) for r in rows]))
            sheet_names.append('日记数据')
    if export_type == 'all':
        rows = CheckinDB.get_all_checkins()
        if rows:
            data_frames.append(pd.DataFrame([dict(r) for r in rows]))
            sheet_names.append('打卡记录')
        rows = CheckinDB.get_all_items()
        if rows:
            data_frames.append(pd.DataFrame([dict(r) for r in rows]))
            sheet_names.append('打卡项目')
    if not data_frames:
        return None
    names = {'schedule': '日程', 'task': '任务', 'diary': '日记', 'all': '全部'}
    path = os.path.join(export_dir, f'{names[export_type]}数据_{timestamp}.xlsx')
    with pd.ExcelWriter(path, engine='openpyxl') as w:
        for df, name in zip(data_frames, sheet_names):
            df.to_excel(w, sheet_name=name, index=False)
    return path


def do_import_excel(import_type, file_path):
    sheet_map = {
        '日程数据': ('schedules', ['title', 'description', 'schedule_date', 'start_time', 'end_time', 'location', 'priority', 'is_done']),
        '任务数据': ('daily_tasks', ['title', 'description', 'task_date', 'priority', 'repeat', 'is_done', 'sort_order']),
        '日记数据': ('diaries', ['title', 'content', 'mood', 'weather', 'diary_date']),
        '打卡记录': ('checkins', ['task_title', 'checkin_date', 'checkin_time', 'status', 'note', 'repeat']),
        '打卡项目': ('checkin_items', ['title', 'description', 'sort_order']),
    }
    type_map = {
        'schedule': ['日程数据'], 'task': ['任务数据'],
        'diary': ['日记数据'],
        'all': ['日程数据', '任务数据', '日记数据', '打卡记录', '打卡项目'],
    }
    allowed = type_map[import_type]
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    conn = get_connection()
    total = 0
    try:
        for sn in xls.sheet_names:
            if sn not in sheet_map or sn not in allowed:
                continue
            table, expected = sheet_map[sn]
            df = pd.read_excel(xls, sheet_name=sn)
            if all(isinstance(c, int) for c in df.columns):
                continue
            if df.empty:
                continue
            df = df.drop(columns=['id'], errors='ignore')
            cols = [c for c in expected if c in df.columns]
            if not cols:
                continue
            ph = ', '.join(['?'] * len(cols))
            cs = ', '.join(cols)
            sql = f'INSERT INTO {table} ({cs}) VALUES ({ph})'
            for _, row in df.iterrows():
                vals = [None if pd.isna(row[c]) else row[c] for c in cols]
                try:
                    conn.execute(sql, vals)
                    total += 1
                except Exception:
                    pass
        conn.commit()
    finally:
        conn.close()
    return total


def do_export_sql(export_type, export_dir, timestamp):
    sql = '-- Schedule Planner 数据导出\n'
    sql += f'-- 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'

    def gen_insert(table, rows):
        if not rows:
            return ''
        cols = rows[0].keys()
        cs = ', '.join(cols)
        s = f'INSERT INTO {table} ({cs}) VALUES\n'
        vals = []
        for row in rows:
            rv = []
            for col in cols:
                v = row[col]
                if v is None:
                    rv.append('NULL')
                elif isinstance(v, str):
                    rv.append("'" + v.replace("'", "''") + "'")
                else:
                    rv.append(str(v))
            vals.append('(' + ', '.join(rv) + ')')
        return s + ',\n'.join(vals) + ';\n\n'

    if export_type in ('schedule', 'all'):
        sql += gen_insert('schedules', ScheduleDB.get_all())
    if export_type in ('task', 'all'):
        sql += gen_insert('daily_tasks', DailyTaskDB.get_all())
    if export_type in ('diary', 'all'):
        sql += gen_insert('diaries', DiaryDB.get_all())
    if export_type == 'all':
        sql += gen_insert('checkins', CheckinDB.get_all_checkins())
        sql += gen_insert('checkin_items', CheckinDB.get_all_items())

    if sql.count('INSERT INTO') == 0:
        return None

    names = {'schedule': '日程', 'task': '任务', 'diary': '日记', 'all': '全部'}
    path = os.path.join(export_dir, f'{names[export_type]}数据_{timestamp}.sql')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(sql)
    return path


def do_import_sql(import_type, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    type_map = {
        'schedule': ['schedules'], 'task': ['daily_tasks'],
        'diary': ['diaries'],
        'all': ['schedules', 'daily_tasks', 'diaries', 'checkins', 'checkin_items'],
    }
    allowed = type_map[import_type]
    lines = content.splitlines()
    content = '\n'.join(l for l in lines if not l.strip().startswith('--'))
    content = content.replace('INSERT INTO', 'INSERT OR IGNORE INTO')
    conn = get_connection()
    total = 0
    try:
        for stmt in content.split(';'):
            stmt = stmt.strip()
            if not stmt:
                continue
            if not stmt.upper().startswith('INSERT'):
                continue
            match = any(f'INTO {t} ' in stmt or f'INTO {t}(' in stmt for t in allowed)
            if not match:
                continue
            try:
                conn.execute(stmt)
                total += 1
            except Exception as e:
                pass
        conn.commit()
    finally:
        conn.close()
    return total


# ==================== 测试 ====================

def verify_import_counts(label):
    """验证导入后数据条数"""
    s = len(ScheduleDB.get_all())
    t = len(DailyTaskDB.get_all())
    d = len(DiaryDB.get_all())
    c = len(CheckinDB.get_all_checkins())
    ci = len(CheckinDB.get_all_items())
    print(f'  验证: 日程={s}, 任务={t}, 日记={d}, 打卡={c}, 打卡项目={ci}')
    return s, t, d


print('=' * 60)
print('=== Excel 导出/导入 (清空后导入) ===')
print('=' * 60)

export_dir = tempfile.mkdtemp()

for etype in ['schedule', 'task', 'diary', 'all']:
    clear_all_data()
    insert_test_data()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

    path = do_export_excel(etype, export_dir, ts)
    if not path:
        print(f'\n[{etype}] 导出: 无数据')
        continue

    xls = pd.ExcelFile(path, engine='openpyxl')
    print(f'\n[{etype}] 导出: {os.path.basename(path)}  sheets={xls.sheet_names}')

    for itype in ['schedule', 'task', 'diary', 'all']:
        clear_all_data()
        try:
            count = do_import_excel(itype, path)
            s, t, d = verify_import_counts(f'{etype}->{itype}')
            total = s + t + d
            status = f'导入 {count} 条, DB实际 {total} 条' if count > 0 else '无匹配'
        except Exception as e:
            status = f'失败: {e}'
        print(f'  -> 导入为 [{itype}]: {status}')


print()
print('=' * 60)
print('=== SQL 导出/导入 (清空后导入) ===')
print('=' * 60)

for etype in ['schedule', 'task', 'diary', 'all']:
    clear_all_data()
    insert_test_data()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

    path = do_export_sql(etype, export_dir, ts)
    if not path:
        print(f'\n[{etype}] 导出: 无数据')
        continue

    with open(path, 'r', encoding='utf-8') as f:
        inserts = f.read().count('INSERT INTO')
    print(f'\n[{etype}] 导出: {os.path.basename(path)}  INSERT数={inserts}')

    for itype in ['schedule', 'task', 'diary', 'all']:
        clear_all_data()
        try:
            count = do_import_sql(itype, path)
            s, t, d = verify_import_counts(f'{etype}->{itype}')
            total = s + t + d
            status = f'导入 {count} 条, DB实际 {total} 条' if count > 0 else '无匹配'
        except Exception as e:
            status = f'失败: {e}'
        print(f'  -> 导入为 [{itype}]: {status}')


shutil.rmtree(export_dir, ignore_errors=True)
clear_all_data()
print('\n测试完成')
