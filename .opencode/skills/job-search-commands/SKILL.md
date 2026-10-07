---
name: job-search-commands
description: Activates when the user requests to search, find, list, or review job opportunities, vacancies, or positions in any language (e.g., English or Spanish).
---

# Job Search Commands

Activate whenever the user asks to search for, list, display, or review jobs or opportunities, regardless of exact wording.

## Trigger rule

Treat the message as a job-search request when it combines:

- **Action:** search, find, look for, show, display, list, view, browse, check / buscar, encontrar, mostrar, listar, ver, revisar, comprobar
- **Target:** job(s), employment, work, role, position(s), vacancy/vacancies, opening(s), offer(s), opportunity/opportunities / trabajo(s), empleo(s), oportunidad(es), vacante(s), oferta(s), puesto(s), laboral(es)
- **Modifiers:** available, current, open, active / disponible(s), abiertos, activas

The rule applies in English and Spanish; wording may change, intent stays the same.

## Examples

**Trigger:** "Search for job opportunities", "Show me the jobs", "Find available positions", "List jobs in my area", "Buscar trabajo", "Buscar oportunidades de trabajo", "Mostrarme vacantes", "Ver ofertas laborales", "Buscar empleos disponibles".

**Do not trigger:** "Show me the website", "Search the document", "Find my files".
