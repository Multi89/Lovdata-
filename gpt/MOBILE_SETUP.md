# Oppsett på ChatGPT mobil
1. Bygg indeksen med `lovdata-sync` i et miljø der databasefilen lagres varig.
2. Publiser Actions API med HTTPS. Sett hemmelig `LOVDATA_ACTIONS_API_KEY` i servermiljøet.
3. Besøk GPT-editoren i nettleseren, opprett GPT og lim inn `GPT_INSTRUCTIONS_NB.txt`.
4. Under Actions importer den publiserte `/openapi.json`, og sett Bearer API key.
5. Test status og søk fra editoren før du bruker GPT-en på mobil.
Dette oppsettet er ennå ikke produksjonsvalidert. MCP er et alternativ og krever separat integrasjon.
