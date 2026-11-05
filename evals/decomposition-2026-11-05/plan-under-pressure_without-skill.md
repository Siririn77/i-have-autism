**Bash/Linux/macOS:**
```bash
for f in *.jpeg; do [ -e "$f" ] && mv -n -- "$f" "${f%.jpeg}.jpg"; done
```
(`-n` = не перезаписывать существующие .jpg; уберите, если нужно перезаписывать)

**PowerShell (Windows):**
```powershell
Get-ChildItem -File *.jpeg | Rename-Item -NewName { $_.Name -replace '\.jpeg$','.jpg' }
```

**Если .jpeg в подпапках (bash, рекурсивно):**
```bash
find . -type f -iname '*.jpeg' -exec sh -c 'mv -n -- "$1" "${1%.*}.jpg"' _ {} \;
```