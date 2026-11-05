```
sudo apt install python3-numpy
```

Это основной путь. Ниже два варианта и их цена.

**План (2 строки):** вариант A — системный пакет через apt, работает без настройки. Вариант B — venv + pip, нужен, если версия из репозитория старая.

---

## Вариант A: системный пакет (рекомендую)

1. `sudo apt update`
2. `sudo apt install python3-numpy`
3. Проверка: `python3 -c "import numpy; print(numpy.__version__)"`

Ожидаемый результат шага 3: печатается номер версии, например `1.24.2`.

- Плюс: пакет обновляется через `apt`, конфликтов с системным Python нет.
- Минус: версия — та, что в репозитории Debian. На Debian 12 (bookworm) это 1.24.2. Проверить точно: `apt-cache policy python3-numpy`.
- Ограничение: пакет ставится только для системного `python3`. Если вы вызываете `python3.11` из другой установки, `import numpy` в ней не найдётся — имя модуля разрешается по путям конкретного интерпретатора.
- Время: 1–2 минуты.

## Вариант B: venv + pip (если нужна свежая версия)

Предпосылка: модуль `venv` в Debian вынесен в отдельный пакет, без него шаг 2 падает с `No module named venv`.

1. `sudo apt install python3-venv`
2. `python3 -m venv ~/venv-numpy`
3. `~/venv-numpy/bin/pip install numpy`
4. Проверка: `~/venv-numpy/bin/python -c "import numpy; print(numpy.__version__)"`

- Плюс: любая версия numpy, изоляция от системного Python.
- Минус: окружение надо активировать (`source ~/venv-numpy/bin/activate`) в каждой новой оболочке, иначе `import numpy` не сработает.
- Время: 2–3 минуты плюс скачивание.

## Чего не делать

`pip install numpy` в системный Python на Debian 12 падает с ошибкой:

```
error: externally-managed-environment
```

Причина: файл `/usr/lib/python3.11/EXTERNALLY-MANAGED` запрещает pip менять системные пакеты. Обход `--break-system-packages` работает, но ломает пакеты, которыми управляет apt, — не применяйте, пока не готовы чинить систему вручную.

---

**Следующее действие:** выполните `python3 -c "import numpy; print(numpy.__version__)"`. Если печатает версию — установка закончена. Если пишет `ModuleNotFoundError` — сообщите вывод `which python3`.