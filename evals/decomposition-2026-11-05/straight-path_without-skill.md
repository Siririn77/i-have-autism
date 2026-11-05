Более читаемый вариант:

```python
def check(user):
    return bool(user and user.active and user.age >= 18)
```

Или чуть более явно:

```python
def check(user):
    if not user:
        return False
    return bool(user.active and user.age >= 18)
```

Оба варианта сохраняют исходную логику: пользователь должен существовать/быть truthy, быть активным и достичь 18 лет.