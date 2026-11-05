Более читаемый вариант с guard clauses:

```python
def check(user):
    if not user:
        return False
    if not user.active:
        return False
    return user.age >= 18
```

Или короче, если хочется однострочник:

```python
def check(user):
    return bool(user and user.active and user.age >= 18)
```

Первый вариант обычно предпочтительнее для читаемости: он явно показывает все условия отказа и убирает вложенность.