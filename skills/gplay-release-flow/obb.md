# Legacy OBB expansion files (APK-only, `[experimental]`)

```bash
gplay releases expansion-files upload ./main.obb --version-code 42 --type main
gplay releases expansion-files set --version-code 43 --references-version 42 --type main
gplay releases expansion-files view --version-code 42 --type main
```

`set` points an APK at another versionCode's already-uploaded file (no
upload). `upload` and `set` take `--dry-run`; `view` is a read.
