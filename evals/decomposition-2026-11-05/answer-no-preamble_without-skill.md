# Установка NumPy на Debian

## Способ 1: из репозитория Debian (проще всего)

```bash
sudo apt update
sudo apt install python3-numpy
```

Проверка:

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

Плюсы: ставится системный пакет, автоматически подтягиваются зависимости (BLAS/LAPACK), обновляется вместе с системой. Минус — версия может быть старше актуальной (в Debian 12 — NumPy 1.24, в Debian 13 — уже 2.x).

Пакет ставится для системного `python3`. Если у вас несколько версий Python, посмотрите `apt search python3-numpy`.

## Способ 2: через pip в виртуальном окружении (рекомендуется для проектов)

Начиная с Debian 12 действует PEP 668: `pip install` в системный Python блокируется ошибкой `externally-managed-environment`. Поэтому создаём venv:

```bash
sudo apt install python3-venv python3-pip

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy
```

Проверка:

```bash
python -c "import numpy; print(numpy.__version__)"
```

Выход из окружения — `deactivate`. Так вы получите свежую версию и не сломаете системные пакеты.

Нужна конкретная версия:

```bash
pip install "numpy==2.1.3"
```

## Способ 3: uv / conda (если нужен менеджер окружений)

```bash
# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv pip install numpy
```

Или Miniforge/conda:

```bash
conda create -n sci python=3.12 numpy
conda activate sci
```

## Чего делать не стоит

```bash
pip install --break-system-packages numpy   # ломает системный Python
```

Это обходит защиту PEP 668 и может конфликтовать с пакетами apt. Используйте venv.

## Если нужна сборка из исходников

Обычно не требуется — для всех популярных платформ есть готовые wheel. Но если pip не нашёл wheel:

```bash
sudo apt install build-essential gfortran python3-dev libopenblas-dev
```

## Итог

- Нужен NumPy «для системы/скриптов» → `sudo apt install python3-numpy`.
- Пишете проект → venv + `pip install numpy`.
- Хотите свежую версию и изоляцию → venv/uv/conda.