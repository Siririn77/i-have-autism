**Bash / Linux / macOS:**
```bash
for f in *.jpeg; do [ -e "$f" ] && mv -- "$f" "${f%.jpeg}.jpg"; done
```

Если нужно и `.JPEG`/`.Jpeg` (без учёта регистра, включая подпапки):
```bash
find . -iname '*.jpeg' -exec bash -c 'mv -- "$1" "${1%.*}.jpg"' _ {} \;
```

**PowerShell (Windows):**
```powershell
Get-ChildItem -Filter *.jpeg | Rename-Item -NewName { $_.Name -replace '\.jpeg$','.jpg' }
```

**Windows CMD:**
```cmd
for %f in (*.jpeg) do ren "%f" "%~nf.jpg"
```