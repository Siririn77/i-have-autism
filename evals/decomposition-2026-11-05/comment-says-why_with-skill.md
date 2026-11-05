```python
def format_seconds(seconds: int) -> str:
    """Переводит секунды в строку вида «1ч 20м».

    seconds: целое число, не меньше нуля.

    0…59     -> «45с»
    60…3599  -> «2м 30с»; «2м», если секунды нулевые
    от 3600  -> «1ч 20м»; «1ч», если минуты нулевые,
                остаток секунд отбрасывается
    """
    if seconds < 0:
        raise ValueError(f"seconds: ожидалось >= 0, получено {seconds}")

    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)

    if hours:
        # Нулевые минуты не печатаем: «1ч» читается, «1ч 0м» — нет.
        return f"{hours}ч {minutes}м" if minutes else f"{hours}ч"

    if minutes:
        # Секунды сохраняем только ниже часа: на масштабе часов они уже шум.
        return f"{minutes}м {secs}с" if secs else f"{minutes}м"

    return f"{secs}с"
```

В задании не было трёх правил, я выбрал их сам. Проверь по порядку, первое — самое неожиданное:
1. `format_seconds(3661) == "1ч 1м"` — 1 секунда потеряна. Если терять нельзя, формат нужен другой.
2. `format_seconds(3600) == "1ч"` — нулевые минуты не печатаются.
3. `format_seconds(-5)` — `ValueError: seconds: ожидалось >= 0, получено -5`.

Проверка:

```python
assert format_seconds(0) == "0с"
assert format_seconds(45) == "45с"
assert format_seconds(60) == "1м"
assert format_seconds(90) == "1м 30с"
assert format_seconds(3600) == "1ч"
assert format_seconds(4800) == "1ч 20м"
```

Скопируй блок `assert` под функцию и запусти файл: шесть строк пройдут без вывода, любая ошибка назовёт вход.