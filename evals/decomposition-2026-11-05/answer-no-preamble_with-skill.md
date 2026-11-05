**Установить пакетом Debian (рекомендую):**
```
sudo apt update && sudo apt install -y python3-numpy
python3 -c "import numpy; print(numpy.__version__)"
```
Проверка: вторая команда печатает версию, например `1.24.2`. Если печатает `ModuleNotFoundError` — пакет не встал, смотри вывод apt.

**Граф решения (4 узла):**

1. **Какой Python используется** — от этого зависит способ. Важно: в Debian 12+ системный Python помечен как externally managed (PEP 668), поэтому `pip install numpy` в систему падает с `error: externally-managed-environment`. Якорь: `ls /usr/lib/python3*/EXTERNALLY-MANAGED`. Когда: до любой установки.
2. **Пакет apt `python3-numpy`** — ставится в системный Python, ничего не ломает, версия старее текущей с PyPI. Якорь: `dpkg -l python3-numpy`. Когда: нужен numpy без изоляции окружения.
3. **Виртуальное окружение + pip** — изоляция, свежая версия. Якорь: `.venv/lib/python3*/site-packages/numpy`. Когда: нужна конкретная версия или свой проект.
4. **Сборка из исходников** — нужна на старых архитектурах и когда для вашей версии Python нет готового wheel. Якорь: сообщение `error: subprocess-exited-with-error` без `gcc`. Когда: pip не нашёл wheel.

**Способ 2 — venv (свежая версия):**
```
sudo apt install -y python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install numpy
python -c "import numpy; print(numpy.__version__)"
```

**Способ 3 — только если pip не нашёл wheel** (сборка займёт 5–20 минут):
```
sudo apt install -y build-essential python3-dev
pip install numpy
```

План: (1) выбрать способ по узлу 1, (2) выполнить команды, (3) проверить импортом. Способ 1 занимает около 1 минуты, способ 2 — около 2 минут.

Следующее действие: выполните `python3 -c "import sys; print(sys.version)"` и пришлите вывод — по нему скажу, какой способ подходит.