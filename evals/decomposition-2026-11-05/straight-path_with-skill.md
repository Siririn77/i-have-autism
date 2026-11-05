План: вход — `user` или falsy-объект; действие — заменить три вложенных `if` на стражи с ранним `return`; выход — `bool`; проверка — 4 случая таблицы истинности дают тот же результат, что исходная функция. Время: 5 минут.

```python
def check(user):
    if not user:
        return False
    if not user.active:
        return False
    return user.age >= 18
```

Что теперь работает: `True` возвращается только когда `user` истинен, `user.active` истинно и `user.age >= 18` — так же, как в исходной версии. Ветвление читается сверху вниз, вложенности нет.

Три вещи, которые я не менял (вне задачи):
1. `user.age >= 18` бросает `TypeError`, если `age is None`; в исходной версии — то же.
2. `if not user` проверяет истинность объекта, а не `user is None`; если у класса появится `__bool__` или `__len__`, поведение изменится. Сохранено намеренно.
3. Имя `check` не говорит, что проверяется; переименование меняет API вызывающих.

Проверка — последнее действие:

```python
from types import SimpleNamespace

assert check(None) is False
assert check(SimpleNamespace(active=False, age=30)) is False
assert check(SimpleNamespace(active=True, age=17)) is False
assert check(SimpleNamespace(active=True, age=18)) is True
```