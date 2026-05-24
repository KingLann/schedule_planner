import sqlite3
import os
import sys
from datetime import datetime, date
from contextlib import contextmanager

_APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SchedulePlanner')
os.makedirs(_APP_DIR, exist_ok=True)

DB_PATH = os.path.join(_APP_DIR, "schedule.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _db():
    """数据库连接上下文管理器，确保异常时也能关闭连接"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                schedule_date TEXT NOT NULL,
                start_time TEXT DEFAULT '',
                end_time TEXT DEFAULT '',
                location TEXT DEFAULT '',
                priority INTEGER DEFAULT 1,
                is_done INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                task_date TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                repeat TEXT DEFAULT '',
                is_done INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS checkin_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_title TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                checkin_time TEXT DEFAULT '',
                status INTEGER DEFAULT 0,
                note TEXT DEFAULT '',
                repeat TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(task_title, checkin_date)
            );

            CREATE TABLE IF NOT EXISTS diaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                mood TEXT DEFAULT '',
                weather TEXT DEFAULT '',
                diary_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(diary_date)
            );
        """)
        # 迁移: 为旧表添加缺失的列
        for ddl in [
            "ALTER TABLE schedules ADD COLUMN sort_order INTEGER DEFAULT 0",
            "ALTER TABLE checkins ADD COLUMN sort_order INTEGER DEFAULT 0",
            "ALTER TABLE schedules ADD COLUMN completed_at TEXT DEFAULT NULL",
            "ALTER TABLE daily_tasks ADD COLUMN completed_at TEXT DEFAULT NULL",
            "ALTER TABLE daily_tasks ADD COLUMN updated_at TEXT DEFAULT NULL",
        ]:
            try:
                conn.execute(ddl)
                conn.commit()
            except sqlite3.OperationalError:
                conn.rollback()
                pass
        # 回填 daily_tasks.updated_at（旧数据为 NULL）
        try:
            conn.execute("UPDATE daily_tasks SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
        except Exception:
            conn.rollback()
        # 索引
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(schedule_date);
            CREATE INDEX IF NOT EXISTS idx_daily_tasks_date ON daily_tasks(task_date);
            CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date);
            CREATE INDEX IF NOT EXISTS idx_diaries_date ON diaries(diary_date);
        """)
        conn.commit()
    finally:
        conn.close()


class ScheduleDB:

    @staticmethod
    def get_by_date(date_str):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules WHERE schedule_date=? ORDER BY sort_order, start_time, priority DESC",
                (date_str,)
            ).fetchall()

    @staticmethod
    def get_all(limit=500):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules ORDER BY schedule_date DESC, start_time LIMIT ?",
                (limit,)
            ).fetchall()

    @staticmethod
    def get_range(start_date, end_date):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules WHERE schedule_date BETWEEN ? AND ? ORDER BY schedule_date, start_time",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def add(title, description, schedule_date, start_time, end_time, location, priority):
        try:
            with _db() as conn:
                conn.execute(
                    "INSERT INTO schedules (title, description, schedule_date, start_time, end_time, location, priority) VALUES (?,?,?,?,?,?,?)",
                    (title, description, schedule_date, start_time, end_time, location, priority)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def update(sid, title, description, schedule_date, start_time, end_time, location, priority):
        with _db() as conn:
            conn.execute(
                "UPDATE schedules SET title=?, description=?, schedule_date=?, start_time=?, end_time=?, location=?, priority=?, updated_at=datetime('now','localtime') WHERE id=?",
                (title, description, schedule_date, start_time, end_time, location, priority, sid)
            )

    @staticmethod
    def toggle_done(sid):
        with _db() as conn:
            conn.execute(
                "UPDATE schedules SET is_done = 1 - is_done, "
                "completed_at = CASE WHEN is_done = 0 THEN datetime('now','localtime') ELSE NULL END, "
                "updated_at = datetime('now','localtime') WHERE id=?",
                (sid,)
            )

    @staticmethod
    def delete(sid):
        with _db() as conn:
            conn.execute("DELETE FROM schedules WHERE id=?", (sid,))

    @staticmethod
    def update_sort_order(sid, sort_order):
        with _db() as conn:
            conn.execute("UPDATE schedules SET sort_order=? WHERE id=?", (sort_order, sid))

    @staticmethod
    def count_by_date(date_str):
        with _db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM schedules WHERE schedule_date=?", (date_str,)
            ).fetchone()
        return row["c"] if row else 0

    @staticmethod
    def done_count_by_date(date_str):
        with _db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM schedules WHERE schedule_date=? AND is_done=1", (date_str,)
            ).fetchone()
        return row["c"] if row else 0

    @staticmethod
    def get_priority_info(date_str):
        """返回某日的最高优先级和是否全部完成"""
        with _db() as conn:
            row = conn.execute(
                "SELECT MAX(priority) as max_pri, MIN(is_done) as all_done, COUNT(*) as total FROM schedules WHERE schedule_date=?",
                (date_str,)
            ).fetchone()
        if row and row["total"] > 0:
            return row["max_pri"], row["all_done"] == 1, row["total"]
        return 0, False, 0

    @staticmethod
    def get_month_summary(start_date, end_date):
        """返回日期范围内每日的汇总信息: {date_str: (count, max_pri, all_done)}"""
        with _db() as conn:
            rows = conn.execute(
                "SELECT schedule_date, COUNT(*) as total, MAX(priority) as max_pri, MIN(is_done) as all_done "
                "FROM schedules WHERE schedule_date BETWEEN ? AND ? GROUP BY schedule_date",
                (start_date, end_date)
            ).fetchall()
        result = {}
        for r in rows:
            result[r["schedule_date"]] = (r["total"], r["max_pri"], r["all_done"] == 1)
        return result

    @staticmethod
    def search(keyword):
        kw = keyword.replace('%', '\\%').replace('_', '\\_')
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules WHERE title LIKE ? OR description LIKE ? ESCAPE '\\' ORDER BY schedule_date DESC, start_time",
                (f"%{kw}%", f"%{kw}%")
            ).fetchall()

    @staticmethod
    def count_all():
        with _db() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM schedules").fetchone()
        return row["c"] if row else 0

    @staticmethod
    def clear_all():
        with _db() as conn:
            conn.execute("DELETE FROM schedules")

    # --- 拖延统计查询 ---

    @staticmethod
    def get_overdue(start_date, end_date):
        """查询指定日期范围内到期未完成的日程"""
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules WHERE schedule_date BETWEEN ? AND ? AND is_done=0 "
                "AND schedule_date < date('now') ORDER BY schedule_date",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def get_postponed():
        """查询被推迟到未来的日程（创建超过1天、日期在未来、未完成、且被编辑过）"""
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM schedules WHERE schedule_date >= date('now') AND is_done=0 "
                "AND created_at < datetime('now', '-1 day', 'localtime') "
                "AND updated_at > created_at ORDER BY schedule_date"
            ).fetchall()

    @staticmethod
    def get_overdue_grouped_by_date(start_date, end_date):
        """按日期分组统计到期未完成数，返回 [(date, count), ...]"""
        with _db() as conn:
            return conn.execute(
                "SELECT schedule_date as d, COUNT(*) as c FROM schedules "
                "WHERE schedule_date BETWEEN ? AND ? AND is_done=0 AND schedule_date < date('now') "
                "GROUP BY schedule_date ORDER BY schedule_date",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def get_overdue_grouped_by_weekday(start_date, end_date):
        """按星期几分组统计拖延数，返回 [(weekday(0=Mon), count), ...]"""
        with _db() as conn:
            return conn.execute(
                "SELECT CAST(strftime('%w', schedule_date) AS INTEGER) as wd, COUNT(*) as c "
                "FROM schedules WHERE schedule_date BETWEEN ? AND ? AND is_done=0 "
                "AND schedule_date < date('now') GROUP BY wd",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def get_overdue_grouped_by_priority(start_date, end_date):
        """按优先级分组统计拖延数，返回 [(priority, count), ...]"""
        with _db() as conn:
            return conn.execute(
                "SELECT priority, COUNT(*) as c FROM schedules "
                "WHERE schedule_date BETWEEN ? AND ? AND is_done=0 AND schedule_date < date('now') "
                "GROUP BY priority ORDER BY priority",
                (start_date, end_date)
            ).fetchall()


class DailyTaskDB:

    @staticmethod
    def get_by_date(date_str):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM daily_tasks WHERE task_date=? ORDER BY sort_order, id",
                (date_str,)
            ).fetchall()

    @staticmethod
    def get_all(limit=500):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM daily_tasks ORDER BY task_date DESC, sort_order LIMIT ?",
                (limit,)
            ).fetchall()

    @staticmethod
    def get_range(start_date, end_date):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM daily_tasks WHERE task_date BETWEEN ? AND ? ORDER BY task_date, sort_order",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def add(title, description, task_date, priority=1, repeat=""):
        try:
            with _db() as conn:
                conn.execute(
                    "INSERT INTO daily_tasks (title, description, task_date, priority, repeat) VALUES (?,?,?,?,?)",
                    (title, description, task_date, priority, repeat)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def add_batch(tasks):
        with _db() as conn:
            count = 0
            for t in tasks:
                try:
                    conn.execute(
                        "INSERT INTO daily_tasks (title, description, task_date, priority, repeat) VALUES (?,?,?,?,?)",
                        (t["title"], t.get("description", ""), t["task_date"], t.get("priority", 1), t.get("repeat", ""))
                    )
                    count += 1
                except Exception:
                    pass
        return count

    @staticmethod
    def update(tid, title, description, task_date, priority=1, repeat=""):
        with _db() as conn:
            conn.execute(
                "UPDATE daily_tasks SET title=?, description=?, task_date=?, priority=?, repeat=? WHERE id=?",
                (title, description, task_date, priority, repeat, tid)
            )

    @staticmethod
    def toggle_done(tid):
        with _db() as conn:
            conn.execute(
                "UPDATE daily_tasks SET is_done = 1 - is_done, "
                "completed_at = CASE WHEN is_done = 0 THEN datetime('now','localtime') ELSE NULL END, "
                "updated_at = datetime('now','localtime') WHERE id=?",
                (tid,)
            )

    @staticmethod
    def update_sort_order(tid, sort_order):
        with _db() as conn:
            conn.execute("UPDATE daily_tasks SET sort_order=? WHERE id=?", (sort_order, tid))

    @staticmethod
    def delete(tid):
        with _db() as conn:
            conn.execute("DELETE FROM daily_tasks WHERE id=?", (tid,))

    @staticmethod
    def search(keyword):
        kw = keyword.replace('%', '\\%').replace('_', '\\_')
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM daily_tasks WHERE title LIKE ? OR description LIKE ? ESCAPE '\\' ORDER BY task_date DESC, sort_order",
                (f"%{kw}%", f"%{kw}%")
            ).fetchall()

    @staticmethod
    def count_all():
        with _db() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM daily_tasks").fetchone()
        return row["c"] if row else 0

    @staticmethod
    def delete_in_range(start_date, end_date):
        with _db() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_tasks WHERE task_date BETWEEN ? AND ?",
                (start_date, end_date)
            )
            return cursor.rowcount

    @staticmethod
    def delete_repeat_in_range(start_date, end_date):
        with _db() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_tasks WHERE task_date BETWEEN ? AND ? AND repeat != ''",
                (start_date, end_date)
            )
            return cursor.rowcount

    @staticmethod
    def clear_all():
        with _db() as conn:
            conn.execute("DELETE FROM daily_tasks")

    # --- 拖延统计查询 ---

    @staticmethod
    def get_overdue(start_date, end_date, exclude_repeat=False):
        """查询指定日期范围内到期未完成的任务"""
        sql = ("SELECT * FROM daily_tasks WHERE task_date BETWEEN ? AND ? AND is_done=0 "
               "AND task_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " ORDER BY task_date"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def get_postponed():
        """查询被推迟到未来的任务"""
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM daily_tasks WHERE task_date >= date('now') AND is_done=0 "
                "AND created_at < datetime('now', '-1 day', 'localtime') "
                "AND updated_at > created_at ORDER BY task_date"
            ).fetchall()

    @staticmethod
    def get_overdue_grouped_by_date(start_date, end_date, exclude_repeat=False):
        """按日期分组统计到期未完成数"""
        sql = ("SELECT task_date as d, COUNT(*) as c FROM daily_tasks "
               "WHERE task_date BETWEEN ? AND ? AND is_done=0 AND task_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " GROUP BY task_date ORDER BY task_date"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def get_overdue_grouped_by_weekday(start_date, end_date, exclude_repeat=False):
        """按星期几分组统计拖延数"""
        sql = ("SELECT CAST(strftime('%w', task_date) AS INTEGER) as wd, COUNT(*) as c "
               "FROM daily_tasks WHERE task_date BETWEEN ? AND ? AND is_done=0 "
               "AND task_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " GROUP BY wd"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def get_overdue_grouped_by_priority(start_date, end_date, exclude_repeat=False):
        """按优先级分组统计拖延数"""
        sql = ("SELECT priority, COUNT(*) as c FROM daily_tasks "
               "WHERE task_date BETWEEN ? AND ? AND is_done=0 AND task_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " GROUP BY priority ORDER BY priority"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()


class CheckinDB:

    @staticmethod
    def get_all_items():
        with _db() as conn:
            return conn.execute("SELECT * FROM checkin_items ORDER BY sort_order, id").fetchall()

    @staticmethod
    def add_item(title, description=''):
        try:
            with _db() as conn:
                conn.execute(
                    "INSERT INTO checkin_items (title, description) VALUES (?,?)",
                    (title, description)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def delete_item(item_id):
        with _db() as conn:
            conn.execute("DELETE FROM checkin_items WHERE id=?", (item_id,))

    @staticmethod
    def get_by_date(date_str):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM checkins WHERE checkin_date=? ORDER BY sort_order, id",
                (date_str,)
            ).fetchall()

    @staticmethod
    def add_task(title, date_str, description='', repeat=''):
        try:
            with _db() as conn:
                conn.execute(
                    "INSERT INTO checkins (task_title, checkin_date, note, repeat) VALUES (?,?,?,?)",
                    (title, date_str, description, repeat)
                )
            return True
        except sqlite3.IntegrityError as e:
            error_msg = str(e)
            if "UNIQUE constraint failed: checkins.task_title" in error_msg and "checkins.checkin_date" in error_msg:
                return False
            else:
                raise
        except Exception:
            return False

    @staticmethod
    def check_in(cid):
        """原子操作：标记为已打卡并记录时间"""
        now = datetime.now().strftime("%H:%M:%S")
        with _db() as conn:
            conn.execute(
                "UPDATE checkins SET status=1, checkin_time=? WHERE id=?",
                (now, cid)
            )

    @staticmethod
    def uncheck(cid):
        """取消打卡"""
        with _db() as conn:
            conn.execute("UPDATE checkins SET status=0 WHERE id=?", (cid,))

    @staticmethod
    def toggle_status(cid):
        with _db() as conn:
            conn.execute(
                "UPDATE checkins SET status = 1 - status WHERE id=?",
                (cid,)
            )

    @staticmethod
    def update_time(cid, time_str):
        with _db() as conn:
            conn.execute(
                "UPDATE checkins SET checkin_time=? WHERE id=?",
                (time_str, cid)
            )

    @staticmethod
    def delete(cid):
        with _db() as conn:
            conn.execute("DELETE FROM checkins WHERE id=?", (cid,))

    @staticmethod
    def update_sort_order(cid, sort_order):
        with _db() as conn:
            conn.execute("UPDATE checkins SET sort_order=? WHERE id=?", (sort_order, cid))

    @staticmethod
    def delete_in_range(start_date, end_date):
        with _db() as conn:
            cursor = conn.execute(
                "DELETE FROM checkins WHERE checkin_date BETWEEN ? AND ?",
                (start_date, end_date)
            )
            return cursor.rowcount

    @staticmethod
    def delete_repeat_in_range(start_date, end_date):
        with _db() as conn:
            cursor = conn.execute(
                "DELETE FROM checkins WHERE checkin_date BETWEEN ? AND ? AND repeat != ''",
                (start_date, end_date)
            )
            return cursor.rowcount

    @staticmethod
    def get_range(start_date, end_date):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM checkins WHERE checkin_date BETWEEN ? AND ? ORDER BY checkin_date",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def get_all_checkins(limit=1000):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM checkins ORDER BY checkin_date DESC, id LIMIT ?",
                (limit,)
            ).fetchall()

    @staticmethod
    def count_all():
        with _db() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM checkins").fetchone()
        return row["c"] if row else 0

    @staticmethod
    def search(keyword):
        kw = keyword.replace('%', '\\%').replace('_', '\\_')
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM checkins WHERE task_title LIKE ? ESCAPE '\\' ORDER BY checkin_date DESC",
                (f"%{kw}%",)
            ).fetchall()

    @staticmethod
    def clear_all():
        with _db() as conn:
            conn.execute("DELETE FROM checkins")
            conn.execute("DELETE FROM checkin_items")

    # --- 拖延统计查询 ---

    @staticmethod
    def get_overdue(start_date, end_date, exclude_repeat=False):
        """查询指定日期范围内到期未完成的打卡"""
        sql = ("SELECT * FROM checkins WHERE checkin_date BETWEEN ? AND ? AND status=0 "
               "AND checkin_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " ORDER BY checkin_date"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def get_overdue_grouped_by_date(start_date, end_date, exclude_repeat=False):
        """按日期分组统计到期未完成数"""
        sql = ("SELECT checkin_date as d, COUNT(*) as c FROM checkins "
               "WHERE checkin_date BETWEEN ? AND ? AND status=0 AND checkin_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " GROUP BY checkin_date ORDER BY checkin_date"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()

    @staticmethod
    def get_overdue_grouped_by_weekday(start_date, end_date, exclude_repeat=False):
        """按星期几分组统计拖延数"""
        sql = ("SELECT CAST(strftime('%w', checkin_date) AS INTEGER) as wd, COUNT(*) as c "
               "FROM checkins WHERE checkin_date BETWEEN ? AND ? AND status=0 "
               "AND checkin_date < date('now')")
        params = [start_date, end_date]
        if exclude_repeat:
            sql += " AND (repeat IS NULL OR repeat = '')"
        sql += " GROUP BY wd"
        with _db() as conn:
            return conn.execute(sql, params).fetchall()


class DiaryDB:

    @staticmethod
    def get_by_date(date_str):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM diaries WHERE diary_date=?",
                (date_str,)
            ).fetchone()

    @staticmethod
    def get_all(limit=500):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM diaries ORDER BY diary_date DESC LIMIT ?",
                (limit,)
            ).fetchall()

    @staticmethod
    def get_range(start_date, end_date):
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM diaries WHERE diary_date BETWEEN ? AND ? ORDER BY diary_date DESC",
                (start_date, end_date)
            ).fetchall()

    @staticmethod
    def save(diary_date, title, content, mood='', weather=''):
        with _db() as conn:
            existing = conn.execute(
                "SELECT id FROM diaries WHERE diary_date=?",
                (diary_date,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE diaries SET title=?, content=?, mood=?, weather=?, updated_at=datetime('now','localtime') WHERE diary_date=?",
                    (title, content, mood, weather, diary_date)
                )
            else:
                conn.execute(
                    "INSERT INTO diaries (diary_date, title, content, mood, weather) VALUES (?,?,?,?,?)",
                    (diary_date, title, content, mood, weather)
                )
        return True

    @staticmethod
    def delete(did):
        with _db() as conn:
            conn.execute("DELETE FROM diaries WHERE id=?", (did,))

    @staticmethod
    def delete_by_date(date_str):
        with _db() as conn:
            conn.execute("DELETE FROM diaries WHERE diary_date=?", (date_str,))

    @staticmethod
    def search(keyword):
        kw = keyword.replace('%', '\\%').replace('_', '\\_')
        with _db() as conn:
            return conn.execute(
                "SELECT * FROM diaries WHERE title LIKE ? OR content LIKE ? ESCAPE '\\' ORDER BY diary_date DESC",
                (f"%{kw}%", f"%{kw}%")
            ).fetchall()

    @staticmethod
    def count_all():
        with _db() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM diaries").fetchone()
        return row["c"] if row else 0

    @staticmethod
    def count_range(start_date, end_date):
        with _db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM diaries WHERE diary_date BETWEEN ? AND ?",
                (start_date, end_date)
            ).fetchone()
        return row["c"] if row else 0

    @staticmethod
    def clear_all():
        with _db() as conn:
            conn.execute("DELETE FROM diaries")

    @staticmethod
    def has_diary(date_str):
        with _db() as conn:
            row = conn.execute(
                "SELECT id FROM diaries WHERE diary_date=?",
                (date_str,)
            ).fetchone()
        return row is not None

    @staticmethod
    def get_dates_with_diary(year, month):
        with _db() as conn:
            month_str = f"{year:04d}-{month:02d}"
            rows = conn.execute(
                "SELECT diary_date FROM diaries WHERE diary_date LIKE ?",
                (month_str + "%",)
            ).fetchall()
        return [r["diary_date"] for r in rows]


init_db()
