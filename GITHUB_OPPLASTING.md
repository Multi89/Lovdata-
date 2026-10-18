# Slik legger du hele Lovdata-programmet på GitHub

**Mål:** Legge de faktiske kildefilene i repoet [Hawwe788/Lovdata-](https://github.com/Hawwe788/Lovdata-). Ikke bare ZIP-filen.

## Anbefalt: Windows 10 eller 11 + Google Chrome

1. Last ned `norsk-lovhjelp-chatgpt-mobile-med-readme.zip` fra ChatGPT.
2. Åpne **Filutforsker** (Windows-tasten + E) og velg **Nedlastinger**.
3. Høyreklikk på ZIP-filen og velg **Pakk ut alle...** → **Pakk ut**.
4. Dobbeltklikk på mappen **lovdata-chat-mcp**. Her skal du blant annet se `README.md`, `src`, `tests`, `docs`, `gpt`, `Dockerfile` og `pyproject.toml`.
5. Åpne **Google Chrome** og skriv `https://github.com/Hawwe788/Lovdata-` i adressefeltet. Trykk Enter og logg inn på GitHub.
6. Over fillisten: sjekk at grenvelgeren viser **main**.
7. Trykk **Add file** → **Upload files** (evt. `+` → **Upload files** hvis knappene har endret plassering).
8. Gå tilbake til **Filutforsker**. Trykk `Ctrl + A` **inne i mappen `lovdata-chat-mcp`**, slik at du velger *innholdet*, ikke selve toppmappen.
9. Dra de markerte filene og undermappene inn på GitHubs opplastingsfelt i Chrome. Hvis nettleseren ikke aksepterer mappene, bruk alternativet med Git nedenfor.
10. Kontroller at det står filbaner som `src/lovdata_chat/actions_api.py` og `tests/test_actions_api.py` i listen. **Ikke** last opp `.env`, `.venv`, `__pycache__`, `data/*.sqlite3`, API-nøkler, tokens eller private dokumenter.
11. Nederst under **Commit changes**: skriv meldingen `Add Norwegian legal assistant source code`.
12. Velg eventuelt **Commit directly to the main branch** dersom du har rettighet til det og ønsker direkte opplasting. Trykk **Commit changes**.
13. Gå til reposiden. Kontroller at mappene `src`, `tests`, `gpt`, `docs` finnes. Klikk `README.md` for å se forsiden.

**Viktig:** Repoet har allerede en enkel `README.md`. Hvis GitHub sier at filen finnes, åpne `README.md` i repoet, trykk blyantikonet **Edit this file**, erstatt innholdet med teksten i den nye lokale `README.md` og trykk **Commit changes**. Last deretter opp de andre filene via **Upload files**.

## Alternativ: Git på Windows (best hvis nettleseren ikke håndterer mapper)

Dette er den tryggeste metoden når repositoryet allerede inneholder `README.md`.

1. Installer **Git for Windows** fra https://git-scm.com/download/win hvis det ikke allerede finnes.
2. Åpne **Filutforsker** og gå til **Nedlastinger**. Klikk i adressefeltet, skriv `powershell` og trykk Enter.
3. Lim inn:

```powershell
git clone https://github.com/Hawwe788/Lovdata-.git
```

4. Gå i **Filutforsker** til den utpakkede mappen **lovdata-chat-mcp**. Trykk `Ctrl + A` og `Ctrl + C` for å kopiere **innholdet**.
5. Gå til **Nedlastinger** → **Lovdata-** og trykk `Ctrl + V`. Velg **Erstatt filene i målmappen** dersom Windows spør om `README.md`.
6. Klikk i adressefeltet **inne i Lovdata-**, skriv `powershell` og trykk Enter.
7. Kontroller og last opp med følgende kommandoer:

```powershell
git status
git add .
git status
git commit -m "Add Norwegian legal assistant source code"
git push origin main
```

8. Hvis GitHub ber om innlogging, logg inn med din egen GitHub-konto i vinduet som åpnes. Ikke lim inn API-nøkler eller passord i prosjektfiler.

**Viktig:** Før `git commit` skal du lese filnavnene i `git status`. Ingen `.env`, `.venv`, SQLite-databaser, token-filer eller personopplysninger skal være med. **Ikke bruk `git push --force`**.

## Verifiser opplastingen

Åpne https://github.com/Hawwe788/Lovdata- og bekreft at `src/lovdata_chat/`, `tests/`, `gpt/` og `README.md` vises. Test gjerne lokalt med:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub-opplasting alene starter **ikke** serveren, kobler til Lovdata Pro eller publiserer en ChatGPT-utvidelse. Dette er separate trinn.
