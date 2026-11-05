```
sudo apt update
sudo apt install python3-numpy
```

Проверка: `python3 -c "import numpy; print(numpy.__version__)"` — печатает номер версии, если установка прошла.

---

Если нужна версия 2.x: в Debian 12 системный python3 помечен как externally-managed (PEP 668), поэтому `pip install numpy` вне venv падает с `error: externally-managed-environment`. Обход — отдельное окружение:

```
sudo apt install python3-venv
python3 -m venv ~/.venv-numpy
~/.venv-numpy/bin/pip install numpy
```

Проверка: `~/.venv-numpy/bin/python -c "import numpy; print(numpy.__version__)"`.

Цена вариантов:
- apt: одна команда, numpy 1.24.2 (версия из bookworm), работает для всех скриптов, запускаемых через `python3`.
- venv: numpy 2.x, но интерпретатор надо вызывать по полному пути `~/.venv-numpy/bin/python`, иначе numpy не виден.

Начните с первой команды — `sudo apt update`.