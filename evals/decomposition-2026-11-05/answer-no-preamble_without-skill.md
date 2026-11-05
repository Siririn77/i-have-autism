## Способ 1: из репозиториев Debian (проще всего)

```bash
sudo apt update
sudo apt install python3-numpy
```

Это самый надёжный вариант для системного Python — пакет уже собран и протестирован для вашего дистрибутива. Версия будет не самой свежей (например, в Debian 12 — 1.24), но стабильной.

Проверка:

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

## Способ 2: через pip в виртуальном окружении (если нужна свежая версия)

Начиная с Debian 12 системный pip блокирует установку в систему (PEP 668, ошибка `externally-managed-environment`), поэтому правильный путь — venv:

```bash
sudo apt install python3-venv python3-pip
python3 -m venv ~/venv-numpy
source ~/venv-numpy/bin/activate
pip install --upgrade pip
pip install numpy
```

Дальше работаете в этом окружении: `source ~/venv-numpy/bin/activate`.

## Способ 3: системный pip с обходом защиты (не рекомендуется)

Если очень нужно поставить именно в систему:

```bash
pip install numpy --user --break-system-packages
```

Но это может конфликтовать с пакетами apt, поэтому лучше так не делать.

## Замечания

- **Для научного стека целиком** удобно ставить через apt: `sudo apt install python3-numpy python3-scipy python3-matplotlib python3-pandas`.
- **Если нужен numpy новее, чем в репозитории**, используйте venv + pip (способ 2) — это чистый и безопасный вариант.
- **Debian 11 (bullseye)** — numpy 1.19, **Debian 12 (bookworm)** — 1.24, **Debian 13 (trixie)** — новее. Для старых версий numpy может не хватать свежих колёс (wheels), так что при старом Python лучше собрать из исходников или взять системный пакет.
- **Conda** — альтернатива, если нужна изоляция без venv: `miniconda` + `conda install numpy`.