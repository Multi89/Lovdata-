# Release notes

## 0.3.0 – mobilbrukbar GPT og forklaringsnivåer

- La til FastAPI-basert GPT Actions API for bruk i en egendefinert GPT.
- La til forklaringsnivåene `lett`, `vanlig` og `professor`.
- La til `researchNorwegianLaw`, dokumenthenting og søk inne i dokumenter.
- La til ferdige GPT-instruksjoner, samtalestartere og OpenAPI Action-skjema.
- La til personvern-, vilkårs- og supportsider på API-serveren.
- Docker starter mobil/GPT Actions API som standard; MCP kan velges med `LOVDATA_SERVER_MODE=mcp`.
- Utvidet MCP-serveren med `lovdata_research`.
- Forbedret søkefallback når et strengt søk med alle ordene ikke gir treff.
- Oppdatert publiserings- og mobilveiledning.

## 0.2.0 – publiseringsklar MCP-app

- La til Docker- og Render-oppsett.
- La til innsendingfil, personvern, vilkår og Pro-gatewaykontrakt.
