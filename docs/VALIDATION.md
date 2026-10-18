# Validering 16. oktober 2026

Koden er hentet fra den tidligere mobilpakken, versjon 0.3.0, og kontrollert før planlagt GitHub-innsending.

## Kontroller som bestod

- Pakken ble installert på Python 3.12 med `pip install -e . pytest`.
- `python -m pytest -q`: **13 tester bestod**. Testene kontrollerer søk, dokumenthenting, teksttreff, forklaringsnivåer, arkivimport, dokument-ID, rangering, feilrespons og API-autentisering.
- MCP-serveren registrerte alle fem verktøy med read-only-annotasjoner.
- Lovdatas offentlige katalog og `gjeldende-lover.tar.bz2` ble hentet uten API-nøkkel.
- Alle **755 XML-filer** i det nedlastede lovarkivet ble lest. De inneholder **754 ulike dokument-ID-er**, og alle 754 ble indeksert.
- Grunnloven finnes i to språkvarianter med samme dokument-ID. Indeksen beholder én kanonisk oppføring; begge språkvarianter tilbys foreløpig ikke som separate dokumenter.
- API-søk etter `barnevernsloven` ga hovedloven først. Dokumenthenting og teksttreff for `LOV-2021-06-18-97` fungerte med den virkelige indeksen.
- Den nummerløse ID-en `LOV-1687-04-15` og dens Lovdata-lenke ble kontrollert.
- Datasettet inneholdt seks dokument-ID-er fra 2006. Dette er gjeldende dokumenttekst, ikke en bekreftelse på historisk ordlyd slik den var i 2006.

## Rettinger som følger med

- Dokument-ID hentes først fra dokumentets egne metadata, fremfor fra lover det henviser til.
- Fulltekstindeksen bygges etter dokumentimport, slik at oppdaterte og dupliserte dokumenter får riktig indeks.
- Eksakt lovnavn og navn i parentes prioriteres foran endringslover og rene omtaler i andre dokumenter.
- Ugyldige søk returnerer en forståelig HTTP-feil.
- Hostingens helsekontroll bruker `/healthz`. Beskyttede API-endepunkter krever fortsatt Bearer-nøkkel når nøkkelen er konfigurert.

## Ikke bekreftet i denne kontrollen

- Full import av sentrale forskrifter.
- Lovdata Pro-gateway, tilgangsnøkkel eller betalt Pro-innhold.
- Automatisk oppdatering av indeksen etter første import.
- Deploy til en HTTPS-server og tilkobling eller publisering i ChatGPT.
- Hundre prosent rettslig dekning eller riktige juridiske konklusjoner.

Testklienten ga én deprecation-advarsel om Starlette/httpx. Den førte ikke til en testfeil.
En privat API-nøkkel er laget separat for vårt eget API; den er ikke en Lovdata Pro-nøkkel og er ikke lagt i repositoryet.

## Kilder

- [Lovdatas offentlige API](https://api.lovdata.no/)
- [Lovdatas informasjon om gratis API for gjeldende regelverk](https://lovdata.no/artikkel/lovdata_tilrettelegger_for_bruk_tilpasset_var_ki-hverdag_gjor_api_av_oppdatert_regelverk_gratis_tilgjengelig_for_alle/5277)
- [Offisiell dokumentasjon for GPT Actions](https://developers.openai.com/api/docs/actions/introduction)
