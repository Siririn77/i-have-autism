`hello.py`:

```python
print("hello world")
```

План в 2 строки: входных данных нет; действие — `print` одного строкового литерала; выход — строка `hello world` и код возврата 0.

Проверка:

```
python3 hello.py
echo $?
```

Ожидается вывод `hello world` и затем `0`. Если вывод другой — запущен не тот файл или не тот интерпретатор; проверьте путь `python3 -c "import sys; print(sys.version)"`.