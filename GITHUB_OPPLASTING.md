# Legg Norsk lovhjelp-prosjektet inn på GitHub via GitHub Desktop

Mål: Alle programfilene på toppnivå i `Multi89/norsk-lovhjelp-chatgpt-mobile`, ikke i en ekstra undermappe.

1. Åpne GitHub Desktop. Kontroller at **Current repository** viser `norsk-lovhjelp-chatgpt-mobile` og **Current branch** viser `main`.
2. Klikk **Repository** → **Show in Explorer**. La Filutforsker-vinduet stå åpent. Det skal vise `.gitattributes`, `.gitignore`, `LICENSE` og `README.md`.
3. Last ned ZIP-pakken fra ChatGPT, åpne **Nedlastinger**, høyreklikk ZIP-filen og velg **Pakk ut alle...** → **Pakk ut**.
4. Åpne den utpakkede mappen `norsk_lovhjelp_komplett`. Trykk **Ctrl+A**, deretter **Ctrl+C**. Du skal ha valgt mapper som `src`, `docs`, `gpt`, `tests` og filer som `pyproject.toml` og `Dockerfile`.
5. Gå til det allerede åpne **GitHub-prosjektvinduet**, dvs. toppmappen `norsk-lovhjelp-chatgpt-mobile`, ikke undermappen `lovdata-chat-mcp`.
6. Trykk **Ctrl+V**. Velg **Erstatt filene i målmappen** for eventuelle duplikater av `README.md` og `.gitignore`. Den eksisterende `LICENSE` endres ikke, fordi den ikke er med i pakken.
7. Åpne GitHub Desktop → **Changes**. Kontroller at både `src/lovdata_chat/*.py` og `pyproject.toml` vises.
8. Gå gjennom de endrede filene. Sørg for at ingen `.env`, `.venv`, passord, tokens, lokale databaser eller private dokumenter skal inn på GitHub.
9. Nederst til venstre under **Summary (required)**, skriv `Legg til Lovdata-programkode`.
10. Klikk **Commit to main**. Når knappen blir **Push origin**, klikk den.
11. Kontroller i nettleseren `https://github.com/Multi89/norsk-lovhjelp-chatgpt-mobile` at `src`, `gpt`, `tests` og `pyproject.toml` ligger på toppnivå.

**Merk:** Den gamle ekstra mappen `lovdata-chat-mcp` kan beholdes midlertidig. Ikke slett den før du har bekreftet at alle filer er riktig kopiert og lastet opp.

GitHub-opplasting gir ikke automatisk fungerende nettjeneste. Kjør tester, bygg Lovdata-indeks og sett opp sikker server etterpå. Et Lovdata Pro-abonnement gir ikke uten videre rett til API-bruk, så Pro-integrasjon må være særskilt godkjent.
