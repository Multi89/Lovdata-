# Bruk på Android og iPhone

Denne løsningen bruker en **egendefinert GPT med API-handlinger**.

## 1. Publiser API-et

Deploy prosjektet til en fast HTTPS-adresse. Render-oppsettet i rotmappen starter API-et og bygger den offentlige Lovdata-indeksen automatisk.

Sett minst:

- `LOVDATA_ACTIONS_API_KEY` til en lang tilfeldig verdi.
- `LOVDATA_DB_PATH=/var/data/lovdata.sqlite3`.
- Pro-variablene bare etter skriftlig godkjent integrasjon.

Kontroller at disse adressene virker:

- `https://DITT-DOMENE/health`
- `https://DITT-DOMENE/healthz` (åpen driftskontroll for hosting)
- `https://DITT-DOMENE/openapi.json`
- `https://DITT-DOMENE/privacy`

`/health` krever Bearer-nøkkelen når `LOVDATA_ACTIONS_API_KEY` er satt.
Hostingens automatiske helsekontroll bruker `/healthz`, som bare returnerer
om API-prosessen svarer. Indeks- og Pro-status må kontrolleres separat via `/health`.

## 2. Opprett GPT-en på nett

Oppretting/redigering gjøres i nettleseren:

1. Åpne GPT-byggeren i ChatGPT.
2. Navn: **Norsk lovhjelp**.
3. Beskrivelse: **Finn og forklar norske lover og forskrifter på lett, vanlig eller professor-nivå. Uoffisiell tjeneste.**
4. Lim inn `GPT_INSTRUCTIONS_NB.txt` i instruksjonsfeltet.
5. Legg inn samtalestarterne fra `CONVERSATION_STARTERS.txt`.
6. Under Handlinger velger du ny handling og limer inn `openapi-actions.yaml` etter at serveradressen er erstattet.
7. Velg API-nøkkel, Bearer, og legg inn samme verdi som `LOVDATA_ACTIONS_API_KEY`.
8. Personvernadresse: `https://DITT-DOMENE/privacy`.
9. Test i forhåndsvisningen og lagre GPT-en privat eller del den.

## 3. Åpne på telefonen

1. Oppdater ChatGPT-appen på Android eller iPhone.
2. Åpne GPT-er fra sidepanelet/GPT-menyen.
3. Velg **Norsk lovhjelp**.
4. Skriv for eksempel: `Finn reglene om journalinnsyn i barnevernet og forklar lett.`

På mobil åpnes GPT-en fra GPT-menyen.
