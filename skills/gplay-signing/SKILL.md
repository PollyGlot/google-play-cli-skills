---
name: gplay-signing
description: Enroll an app into Play App Signing with a self-hosted Cloud KMS key, or rotate to a new KMS key, with gplay `signing`. Use only when the organisation must keep signing-key custody in its own Cloud KMS (compliance or policy); standard Google-managed Play App Signing has no API and stays in the Play Console.
---

# gplay signing (self-hosted Play App Signing key)

Two experimental commands, `signing enroll` and `signing rotate`, both
**irreversible** and `--confirm`-gated. They drive the `appsigning` API for
apps whose signing key lives in the developer's own **Google Cloud KMS**
instance. Shared conventions (auth, `--package` pinning, output, exit codes,
`--dry-run`/`--confirm`) are in `gplay-cli-usage`.

## The wall: this is not standard Play App Signing

The API only handles **self-hosted KMS keys**. Enrolling with a
Google-generated or Google-managed key, and rotating such a key, cannot be
done through the API: those are Play Console operations. When the user wants
"Play App Signing" and has no Cloud KMS key, send them to the Console and stop
here. Reach for this skill when key custody must stay external, which is a
compliance, regulatory or policy requirement, never a convenience.

Prerequisite for both commands: an active Cloud KMS crypto key version whose
IAM policy grants Google Play the **Decrypt** and **Sign** permissions
([Google's guide](https://support.google.com/googleplay/android-developer/answer/9842756)).

## Enroll

```bash
# an app that has already published to Open testing or Production
gplay signing enroll --kms-key projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1 --dry-run
gplay signing enroll --kms-key projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1 --confirm

# a brand-new app (never published to Open testing or Production)
gplay signing enroll --new-app --kms-key <resource> --kms-cert cert.pem --confirm

# register the CI upload certificate in the same call
gplay signing enroll --kms-key <resource> --upload-cert upload.pem --confirm
```

Two shapes, decided by the app's history. An app that has already shipped to
Open testing or Production passes only `--kms-key`. A **new app** passes
`--new-app` and must add `--kms-cert`, the PEM certificate of the KMS key
(`--kms-cert` is refused without `--new-app`). Certificates are always read
from PEM files: never paste base64 on a command line.

The output is the certificate fingerprints (SHA256, SHA1, MD5) of the
enrolled key; `--output json` mirrors the API response verbatim. Record the
SHA256: it is what an API-key restriction or a Firebase/Maps console asks for.

## Rotate

```bash
apksigner rotate --out lineage.bin --old-signer ... --new-signer ...
gplay signing rotate --kms-key <new resource> --kms-cert new-cert.pem \
  --lineage lineage.bin --reason routine-key-upgrade --dry-run
gplay signing rotate --kms-key <new resource> --kms-cert new-cert.pem \
  --lineage lineage.bin --reason routine-key-upgrade --confirm
```

Rotation applies **only to apps enrolled with a self-hosted key**. Four
inputs, all required: the NEW key's KMS resource, its PEM certificate, the
proof-of-rotation **lineage** file, and a `--reason`. The lineage is produced
by `apksigner rotate` from the Android SDK build tools, signed by both the old
and the new key; gplay never creates it. `--reason` takes one of
`compromised-key`, `other`, `routine-key-upgrade`,
`use-same-key-for-multiple-apps`, `use-stronger-key`; anything else exits `2`.

## Safety gates

- Both commands are the **irreversible tier**: missing `--confirm` exits `3`
  naming the flag; `CI=true` never auto-confirms.
- `--dry-run` validates the inputs and reads the PEM and lineage files with
  **zero HTTP**, and reports the `--confirm` requirement (`requires:
  ["confirm"]` under `--output json`). Rehearse every call this way first.
- `GPLAY_READONLY=1` refuses the live write (exit `4`); `--dry-run` is exempt.
- A 404 means the app is not enrolled with a self-hosted key (or does not
  exist); a 403 means the service account lacks the app-level release
  permission or the KMS IAM grant is missing. gplay names the likely cause.
