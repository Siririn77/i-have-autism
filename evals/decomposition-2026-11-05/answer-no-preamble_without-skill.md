# Установка NumPy на Debian

## Способ 1: через apt (рекомендуется для системного Python)

```bash
sudo apt update
sudo apt install python3-numpy
```

Проверка:
```bash
python3 -c "import numpy; print(numpy.__version__)"
```

Плюс: не ломает системный Python, обновляется вместе с системой. Минус: версия может быть старше, чем на PyPI.

## Способ 2: через pip в виртуальном окружении (современный способ)

Начиная с Debian 12 (bookworm) системный Python защищён механизмом **PEP 668** — `pip install` в систему выдаст ошибку `externally-managed-environment`. Поэтому используйте venv:

```bash
sudo apt install python3-venv python3-pip
python3 -m venv ~/venv
source ~/venv/bin/activate
pip install --upgrade pip
pip install numpy
```

Выход из окружения: `deactivate`.

## Способ 3: pip с флагом (если очень нужно в системный Python)

```bash
pip install numpy --break-system-packages
```

⚠️ Не рекомендуется — может конфликтовать с пакетами из apt.

## Способ 4: через conda/miniforge (для научных задач)

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
conda install numpy
```

Удобно, если нужны последние версии NumPy, SciPy, pandas и т.д. без возни с зависимостями.

---

**Что выбрать:**
- Просто нужно `import numpy` в скриптах → `apt install python3-numpy`.
- Нужна свежая версия или несколько проектов с разными версиями → venv + pip.
- Активная научная работа → conda/miniforge.