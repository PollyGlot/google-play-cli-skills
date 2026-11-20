# AGENTS.md : google-play-cli-skills

Agent skills pour le CLI [gplay](https://github.com/PollyGlot/google-play-cli)
(Google Play Developer API), un `SKILL.md` par skill sous `skills/<nom>/`,
distribués via [skills.sh](https://skills.sh/PollyGlot/google-play-cli-skills).

- Les skills pilotent `gplay`, le CLI est la source de vérité. Avant de
  pousser, lance `python3 scripts/check-skills.py` : il résout chaque
  invocation documentée contre le binaire installé et échoue sur un flag ou
  une commande qui n'existe pas. La CI le rejoue sur chaque PR et tous les
  lundis, pour attraper la dérive causée par une release de gplay.
- Rédaction en anglais, instructions actionnables pour un agent, suivre
  le skill global `writing-for-agents`.
- Pas de tiret cadratin dans la prose des skills, du README ni de
  `.github/SECURITY.md` : la barrière le refuse. Les blocs de code en sont
  exemptés, ils citent ce que le binaire imprime.
- Pas de commentaire dans le code : `scripts/lint/comments.py check` (en
  CI, à lancer aussi avant de pousser) compte les lignes de commentaire par
  fichier contre `scripts/lint/comments-baseline.json`. Une décision va dans
  un ADR de `docs/adr/`, un contournement dans une issue ; après une
  suppression, `scripts/lint/comments.py update`. Le script est une copie
  octet pour octet d'un outil externe : ne pas l'éditer ici.
- Une skill ajoutée ou renommée doit avoir sa ligne dans le catalogue du
  README, la barrière vérifie la correspondance.
