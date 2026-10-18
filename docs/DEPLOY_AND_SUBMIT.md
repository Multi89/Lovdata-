# Deploy og koble til ChatGPT

Prosjektet støtter to forskjellige veier.

## A. Telefon: egendefinert GPT med Actions

Dette er den anbefalte løsningen når den skal kunne brukes i ChatGPT-appen på Android eller iPhone.

1. Deploy Docker-prosjektet til en permanent HTTPS-adresse.
2. Sett `LOVDATA_SERVER_MODE=actions`.
3. Sett en lang tilfeldig `LOVDATA_ACTIONS_API_KEY`.
4. Kontroller `/health`, `/openapi.json` og `/privacy`.
5. Kjør:

```bash
python scripts/render_openapi.py https://ditt-domene.example
```

6. Opprett GPT-en i ChatGPT på nett og bruk filene i `gpt/`.
7. Åpne den lagrede GPT-en fra GPT-menyen på telefonen.

Se `gpt/MOBILE_SETUP.md` for alle feltene.

## B. MCP-utviklerapp og eventuell kataloginnsending

1. Deploy en separat instans med `LOVDATA_SERVER_MODE=mcp`.
2. Endepunktet blir `https://ditt-domene.example/mcp`.
3. Opprett appen i ChatGPT-utviklermodus på web.
4. Skann verktøy og test alle fem read-only-verktøyene.
5. Bruk `chatgpt-app-submission.json` ved innsending.

Private MCP-utviklerapper er web-only per 5. august 2026. En offentlig godkjent oppføring kan bli distribuert gjennom Plugin-katalogen, men støttede flater bestemmes av OpenAI.

## Lovdata Pro

Ikke legg et vanlig Lovdata Pro-passord eller nettleser-cookie i deploymenten. Pro-integrasjonen krever et godkjent API/gateway-oppsett og en avtale som tillater den aktuelle automatiserte bruken.
