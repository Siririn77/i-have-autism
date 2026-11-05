```python
def seconds_to_hm(seconds: int) -> str:
    """
    Переводит количество секунд в строку вида '1ч 20м'.
    Секунды не учитываются — они отбрасываются.
    """
    if seconds < 0:
        raise ValueError("Количество секунд не может быть отрицательным")

    # Сначала считаем полное количество минут
    total_minutes = seconds // 60

    # Делим минуты на часы и остаток минут
    hours, minutes = divmod(total_minutes, 60)

    # Если часы есть — выводим и часы, и минуты
    if hours > 0:
        return f"{hours}ч {minutes}м"

    # Если часов нет — выводим только минуты
    return f"{minutes}м"


# Примеры использования:
print(seconds_to_hm(4800))  # 1ч 20м
print(seconds_to_hm(3600))  # 1ч 0м
print(seconds_to_hm(60))    # 1м
print(seconds_to_hm(59))    # 0м
```

Если нужно, чтобы при нулевых минутах выводилось, например, `1ч`, а не `1ч 0м`, можно добавить отдельное условие.