---
name: gplay-signing
description: "Play App Signing with a self-hosted Cloud KMS key via gplay `signing`: enroll an app or rotate its key. Use when signing-key custody must stay in the organisation's own KMS; Google-managed Play App Signing has no API, Console only."
---

# gplay signing (self-hosted Play App Signing key)

Two experimental commands, `signing enroll` and `signing rotate`, both
irreversible and `--confirm`-gated. They drive the `appsigning` API for apps
whose signing key lives in the developer's own Google Cloud KMS instance.
Shared conventions are in `gplay-cli-usage`.

## The wall: self-hosted keys only

The API handles self-hosted KMS keys only; a Google-managed key is enrolled
and rotated in the Play Console. When the user has no Cloud KMS key, point
them at the Console and stop. The IAM prerequisite on the key is in
`enroll --help`.

## Enroll

```bash
# an app that has already published to Open testing or Production
gplay signing enroll --kms-key projects/p/locations/l/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1 --confirm

# a brand-new app (never published to Open testing or Production)
gplay signing enroll --new-app --kms-key <resource> --kms-cert cert.pem --confirm

# register the CI upload certificate in the same call
gplay signing enroll --kms-key <resource> --upload-cert upload.pem --confirm
```

Record the SHA256 from the output: it is what an API-key restriction or a
Firebase/Maps console asks for.

## Rotate

```bash
apksigner rotate --out lineage.bin --old-signer ... --new-signer ...
gplay signing rotate --kms-key <new resource> --kms-cert new-cert.pem \
  --lineage lineage.bin --reason routine-key-upgrade --confirm
```

The lineage from `apksigner rotate` is signed by both the old and the new
key; `--reason` values are listed in `--help`.

## Diagnosing a refusal

A 404 means the app is not enrolled with a self-hosted key (or does not
exist); a 403 means the service account lacks the app-level release permission
or the KMS IAM grant is missing.
