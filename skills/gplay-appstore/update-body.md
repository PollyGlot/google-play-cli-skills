# The `appstore update` request body

Reached from [`SKILL.md`](SKILL.md) when assembling a hosted app's review
submission. `gplay appstore update --help` prints the same shape with the
current field set; what follows is how to build and keep the file.

The whole request is one JSON file (`--file <path>`, or `-`/omitted for stdin)
shaped like `UpdateAppStoreHostedAppRequest`. There is no flag set for it: the
policy declarations are a growing oneof, and a versioned file is what a CI job
wants anyway.

```json
{
  "appDetails": { "developerName": "Example Inc.", "contactEmail": "dev@example.com" },
  "activeApks": { "activeApkSets": [ { "baseApkId": "apk-base-1", "splitApkId": ["apk-split-1"] } ] },
  "activeLocalizedStoreListings": [
    { "languageCode": "en-US", "appName": "Example", "shortDescription": "Short blurb",
      "fullDescription": "Full description", "appIconId": "img-icon-1",
      "screenshotId": ["img-shot-1", "img-shot-2"] }
  ],
  "policyDeclarations": [
    { "declarationId": "decl-1", "responses": [
      { "questionId": "q1", "singleChoiceResponse": { "value": "yes" } },
      { "questionId": "q2", "documentResponse": { "documentId": "file-1", "nonExpiring": true } } ] }
  ]
}
```

**Every id comes from a prior upload.** `baseApkId`/`splitApkId` from
`upload apk`, `appIconId`/`screenshotId` from `upload image`, a
`documentResponse.documentId` from `upload policy`. The `declarationId` and
`questionId` values are Google's own, from the review questionnaire, so they
come from Google's documentation for that declaration rather than from gplay.

**The file travels verbatim.** gplay overwrites `packageName` with the resolved
target and re-serialises nothing else, so a field it has never modelled still
submits correctly, and a misspelled one is rejected by Google rather than
dropped from a submission you cannot recall.

**Package resolution.** `--package` wins over a `packageName` in the file; a
file naming a *different* app is refused (**exit 2**) instead of being resolved
silently; a file with no `packageName` inherits the resolved target.

**Keep the file in version control.** The API answers with no fields (the
acknowledgement is the result) and offers no read-back, so this file is the only
record of what was submitted, and the base for the next submission.
