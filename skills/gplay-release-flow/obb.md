# Legacy OBB expansion files

Expansion files are the pre-AAB mechanism for >150 MB out-of-APK assets, and
only APK-based apps use them; most apps use **Play Asset Delivery** instead.
The whole `expansion-files` namespace is `[experimental]`.

```bash
gplay releases expansion-files upload ./main.obb --version-code 42 --type main
gplay releases expansion-files set --version-code 43 --references-version 42 --type main
gplay releases expansion-files view --version-code 42 --type main
```

- `upload` attaches an `.obb` to an already-published APK `--version-code`
  (`--type main|patch`, the two files an APK can have), via the full Edit
  lifecycle.
- `set` points one APK's expansion config at **another** APK's already-uploaded
  file (`--references-version N`); no new binary uploaded.
- `view` reads an APK's expansion config (its own `fileSize`, or the
  `referencesVersion` it points at) inside a read-only Edit.

All three take `--dry-run` and are refused under `GPLAY_READONLY`. Confirm
flags with `gplay releases expansion-files <command> --help`.
