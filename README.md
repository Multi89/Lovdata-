# Norsk lovhjelp for ChatGPT

**Uoffisielt, åpent kildekodeprosjekt for søk og forklaring av norsk regelverk.**

> **Status:** Versjon `0.3.0`. Dette er kildekode, ikke en ferdig installert Android-app eller en ferdig publisert ChatGPT-utvidelse. Tjenesten krever installasjon, oppbygging av søkeindeks og konfigurering av et API før den fungerer i ChatGPT. Den offentlige versjonen gir ikke automatisk tilgang til Lovdata Pro.

## Funksjoner

- Søke etter norske lover og forskrifter i en lokal indeks bygget fra Lovdatas offentlige API/datasett.
- Hente dokumenttekst, finne ord og relevante paragrafer og vise originalkilder.
- Forklare jussen på tre nivåer: **lett**, **vanlig** og **professor**.
- Eksponere søk via både HTTP API til GPT Actions og en MCP-server.
- Kun lesetilgang til rettskildene: programmet endrer ikke lovtekster.

Dette er **ikke** en offisiell tjeneste fra Lovdata eller offentlig juridisk rådgivning. Opplysninger om ikrafttredelse, gyldighet og rettskildegrunnlag må alltid kontrolleres mot oppdaterte originalkilder.

## Hvor ligger filene?

| Fil/mappe | Beskrivelse |
| --- | --- |
| [`src/lovdata_chat/`](src/lovdata_chat/) | Python-kildekode |
| [`tests/`](tests/) | Automatiserte tester |
| [`gpt/`](gpt/) | GPT-instruksjoner, API-skjema og mobiloppsett |
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | Dokumenterte tester og begrensninger |
| [`gpt/MOBILE_SETUP.md`](gpt/MOBILE_SETUP.md) | Oppkobling mot ChatGPT |
| [`render.yaml`](render.yaml) | Render-konfigurasjon for hosting |
| [`GITHUB_OPPLASTING.md`](GITHUB_OPPLASTING.md) | Trinnvis opplasting av kildekoden til GitHub |

## Installer lokalt i Windows 10 eller 11

Du trenger [Python](https://www.python.org/downloads/) **3.11 eller nyere**, internett og Windows PowerShell.

1. Åpne prosjektmappen `norsk-lovhjelp-chatgpt-mobile` i GitHub Desktop (Repository → Show in Explorer).
2. Klikk i adressefeltet i Filutforsker, skriv `powershell` og trykk Enter.
3. Lim inn følgende kommandoer, én om gangen:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e . pytest
.\.venv\Scripts\python.exe -m pytest -q
```

`py` kan erstattes med `python` dersom Python Launcher ikke finnes.

For å laste ned og indeksere offentlige rettskilder:

```powershell
.\.venv\Scripts\lovdata-sync.exe --matching gjeldende-lover --matching gjeldende-sentrale-forskrifter
```

Dette krever nettverkstilgang. Sjekk alternative datasett med:

```powershell
.\.venv\Scripts\lovdata-sync.exe --list
```

## Start ChatGPT Actions API lokalt

Bruk en egen tilfeldig hemmelig API-nøkkel. Eksemplet nedenfor er **kun en plassholder** og skal erstattes før reell bruk:

```powershell
$env:LOVDATA_ACTIONS_API_KEY = "ERSTATT_MED_EN_LANG_TILFELDIG_HEMMELIGHET"
.\.venv\Scripts\lovdata-actions-api.exe
```

Når API-et kjører, kan du åpne `http://localhost:8000/healthz` og `http://localhost:8000/openapi.json`. Sistnevnte er API-definisjonen. Lokale HTTP-adresser er **ikke** tilstrekkelige for ChatGPT Actions uten en offentlig tilgjengelig HTTPS-tjeneste. Se [`gpt/MOBILE_SETUP.md`](gpt/MOBILE_SETUP.md).

## Start MCP i stedet

```powershell
.\.venv\Scripts\lovdata-chat-mcp.exe
```

MCP-endepunktet er normalt `http://localhost:8000/mcp`. Start ikke MCP og Actions API samtidig på samme port.

## Oppsett for ChatGPT på mobil

1. Publiser Actions API på en sikker HTTPS-server, for eksempel etter konfigurering av `render.yaml`.
2. Opprett en egen GPT på ChatGPT-nettsiden.
3. Bruk instruksjonene i `gpt/GPT_INSTRUCTIONS_NB.txt`.
4. Konfigurer handlingene med `gpt/openapi-actions.yaml` og en riktig HTTPS-serveradresse.
5. Sett API-nøkkelen som Bearer-autentisering i GPT-oppsettet.
6. Test funksjonene, og åpne GPT-en fra ChatGPT-appen på telefonen.

Detaljer: [`gpt/MOBILE_SETUP.md`](gpt/MOBILE_SETUP.md).

## Lovdata Pro og sikkerhet

Et vanlig Lovdata Pro-abonnement gir ikke automatisk rett til automatisert datatilgang. Pro-integrasjonen skal **ikke** aktiveres uten en uttrykkelig godkjent API-/gateway-avtale. Prosjektet skal ikke automatisere innlogging med Lovdata-passord, sesjonskapsler eller skjulte endepunkter.

**Legg aldri ut:** `.env`, API-nøkler, tokens, passord, databaser, brukeropplysninger eller journaler i GitHub. `.env.example` inneholder kun eksempler og kan publiseres. Sørg for at GitHub-prosjektets synlighet (Public/Private) er bevisst valgt.

## Testing og status

Kjør testene med `pytest` som vist ovenfor. Tidligere dokumenterte tester og hva som **ikke** er verifisert, står i [`docs/VALIDATION.md`](docs/VALIDATION.md). Kodegjennomgang fra Copilot og CodeQL må gjennomføres på de faktiske programfilene. En status som «Skipped» betyr ikke godkjent.

## Lisens

Prosjektets eksisterende [LICENSE](LICENSE) i GitHub-repositoriet gjelder (MPL-2.0). Denne importpakken overskriver ikke lisensfilen.
