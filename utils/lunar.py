# -*- coding: utf-8 -*-
"""农历转换、传统节日与节气 (基于 lunarcalendar 库)"""

from datetime import date
from lunarcalendar import Converter, Solar
from lunarcalendar import zh_festivals, zh_solarterms

_TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
_LUNAR_NUM = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
_LUNAR_MONTH = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]


def _lunar_day_str(day):
    if day == 10:
        return "初十"
    elif day == 20:
        return "二十"
    elif day == 30:
        return "三十"
    elif day < 10:
        return "初" + _LUNAR_NUM[day]
    elif day < 20:
        return "十" + _LUNAR_NUM[day - 10]
    else:
        return "廿" + _LUNAR_NUM[day - 20]


def get_ganzhi_year(year):
    return _TIANGAN[(year - 4) % 10] + _DIZHI[(year - 4) % 12]


def get_shengxiao(year):
    return _SHENGXIAO[(year - 4) % 12]


def get_lunar_info(year, month, day):
    """
    获取公历日期的农历信息
    返回 dict: lunar_str, festival, solar_term, ganzhi, shengxiao
    """
    solar = Solar(year, month, day)
    lunar = Converter.Solar2Lunar(solar)

    ganzhi = get_ganzhi_year(lunar.year)
    shengxiao = get_shengxiao(lunar.year)

    prefix = "闰" if lunar.isleap else ""
    month_str = prefix + _LUNAR_MONTH[lunar.month - 1] + "月"
    day_str = _lunar_day_str(lunar.day)

    today = date(year, month, day)

    # 查节日
    festival = None
    for f in zh_festivals:
        try:
            d = f.date_func(year)
            if d == today:
                festival = f.get_lang("zh_hans")
                break
        except Exception:
            pass

    # 查节气
    solar_term = None
    for s in zh_solarterms:
        try:
            d = s.date_func(year)
            if d == today:
                solar_term = s.get_lang("zh_hans")
                break
        except Exception:
            pass

    return {
        "lunar_str": f"农历 {ganzhi}年 {month_str}{day_str}",
        "festival": festival,
        "solar_term": solar_term,
        "ganzhi": ganzhi,
        "shengxiao": shengxiao,
    }
