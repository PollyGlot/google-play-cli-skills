# CLAUDE.md

Agent skills pour le CLI [gplay](https://github.com/PollyGlot/google-play-cli)
(Google Play Developer API) — un `SKILL.md` par skill sous `skills/<nom>/`,
distribués via [skills.sh](https://skills.sh/PollyGlot/google-play-cli-skills).

- Les skills pilotent `gplay`, le CLI est la source de vérité. Avant de
  pousser, lance `python3 scripts/check-skills.py` : il résout chaque
  invocation documentée contre le binaire installé et échoue sur un flag ou
  une commande qui n'existe pas. La CI le rejoue sur chaque PR et tous les
  lundis, pour attraper la dérive causée par une release de gplay. Il échoue
  aussi sur toute commande du binaire qu'aucune skill ne nomme : après une
  release de gplay, `brew upgrade gplay` puis relance-le avant d'analyser.
- Merge : `main` exige le check CI `check` vert et un historique linéaire,
  pas de revue humaine. Une PR verte se merge avec `gh pr merge <n> --squash
  --delete-branch`, sans `--admin`. Un lundi rouge ouvre une issue
  `skills-drift` avec la sortie du script : c'est le ticket de la PR de
  rattrapage.
- Ajouter ou renommer une skill change le pack que `gplay install-skills`
  épingle (`commands/installskills/skills-pin.json` dans le repo du CLI, commit
  + liste exacte). Après le merge ici, ouvre la PR jumelle de repin là-bas,
  typée `fix` pour qu'une release la livre.
- Rédaction en anglais, instructions actionnables pour un agent, suivre
  le skill global `writing-for-agents`.
- Pas de tiret cadratin dans la prose des skills, la barrière le refuse. Les
  blocs de code en sont exemptés : ils citent ce que le binaire imprime.
