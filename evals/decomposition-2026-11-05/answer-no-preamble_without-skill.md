На Debian есть два основных способа.

### 1. Через системный пакет (рекомендуется для большинства случаев)

```bash
sudo apt update
sudo apt install python3-numpy
```

Проверка:

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

Это установит NumPy для системного Python 3. Версия может быть немного старше, чем в PyPI, зато всё ставится через пакетный менеджер Debian.

---

### 2. Через pip в виртуальном окружении (если нужна свежая версия)

В Debian 12+ системный pip защищён от установки пакетов глобально, поэтому лучше использовать venv:

```bash
sudo apt update
sudo apt install python3-venv python3-pip

python3 -m venv ~/.venvs/numpy
source ~/.venvs/numpy/bin/activate

pip install --upgrade pip
pip install numpy
```

Проверка:

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

Выйти из окружения:

```bash
deactivate
```

---

Если при `pip install numpy` без venv появляется ошибка вида `externally-managed-environment`, не используйте `--break-system-packages` без необходимости — лучше создать виртуальное окружение или установить `python3-numpy` через `apt`.