# tva-live-scheduler

Scheduler giornaliero di TVA Live. Contiene **solo** un workflow GitHub Actions: avvia l'aggiornamento del catalogo sul branch di test di `Posty2001/marvel-timeline`, attende l'esito e lo verifica.

- Nessun codice dell'app, nessun dato personale, nessun segreto nel repository.
- Non modifica mai `main` di `marvel-timeline` e non pubblica l'app.
- Esiti: `unchanged`, `heartbeat`, `update` (verde) e `rejected` o errore (rosso, con email di GitHub).
- Dopo un aggiornamento **verificato** pubblica su GitHub Pages i soli JSON pubblici: `v1/current.json` (puntatore) e `v1/c/<versione>/{calendar,trailers,manifest}.json` (versioni immutabili, registrate in `catalog/`).
- Il token (`TVA_DISPATCH_TOKEN`) vive solo nei Secrets di questo repository.

Costo: 0 € (repository pubblico, GitHub Actions gratuito).

## Miss Minutes - archivio TMDB (canale dati)
Workflow `miss-minutes-archivio.yml` (lunedì + manuale): genera l'archivio TMDB in marvel-timeline (branch TEST), lo valida (`scripts/mm_archivio.py`: schema, SHA-256, nessuna regressione) e lo pubblica SOLO sul branch `mm-archivio` (raw.githubusercontent.com). Indipendente da TVA Live: non usa Pages, non tocca `catalog/`. In caso di errore resta l'ultima versione valida. Prove: `python3 scripts/test_mm_archivio.py`.
