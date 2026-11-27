#!/usr/bin/env python3
"""Miss Minutes - canale dati dell'archivio TMDB (indipendente da TVA Live).

Valida un archivio candidato, lo confronta con l'ultima versione pubblicata (protezione dalle regressioni),
calcola lo SHA-256 e prepara la cartella del branch `mm-archivio`:
    tmdb_titoli.<sha8>.json   file immutabile (byte identici al candidato)
    pointer.json              {versione, generato, sha256, file, n, pubblicato, precedente}
    storico.json              ultime versioni (per il ripristino manuale)
Se il candidato NON e' valido o peggiora i dati: nessuna scrittura, la versione valida precedente resta (exit 3).
Uso: mm_archivio.py --src tmdb_titoli.json --dir DATA_DIR [--keep 8] [--dry-run] [--result RESULT.json]
Le regole sono le stesse del client (miss-minutes/archive.js > validate)."""
import argparse, hashlib, json, os, re, sys, datetime
ISO = re.compile(r'^\d{4}-\d{2}-\d{2}$')
MAXB = 1500000

def validate(a, ref=None):
    e = []
    if not isinstance(a, dict): return ["non e' un oggetto"]
    if a.get('versione') not in (1, 2): e.append('versione schema non compatibile')
    if not ISO.match(str(a.get('generato', ''))[:10]): e.append('data di generazione assente')
    v = a.get('voci')
    if not isinstance(v, dict): return e + ['voci assenti']
    if len(v) < 50: e.append('troppe poche voci (%d)' % len(v))
    bad = 0
    for k, x in v.items():
        if not isinstance(x, dict) or not isinstance(x.get('titolo'), str) or not isinstance(x.get('tmdb'), dict) or not x['tmdb'].get('id') or x['tmdb'].get('t') not in ('movie', 'tv'): bad += 1; continue
        for d in x.get('date') or []:
            if not isinstance(d, dict) or not ISO.match(str(d.get('data', ''))): bad += 1
        if x.get('sinossi_it') is not None and not isinstance(x.get('sinossi_it'), str): bad += 1
    if bad: e.append('%d campi/voci malformati' % bad)
    if ref and isinstance(ref.get('voci'), dict):
        rv = ref['voci']
        if ref.get('versione') and a.get('versione', 0) < ref['versione']: e.append("schema piu' vecchio della versione pubblicata")
        keep = sum(1 for k in rv if k in v)
        if rv and keep < 0.9 * len(rv): e.append('perde troppe voci rispetto alla versione pubblicata (%d/%d)' % (keep, len(rv)))
        lost = sum(1 for k in rv if k in v and rv[k].get('sinossi_it') and not v[k].get('sinossi_it'))
        if lost > 0.1 * len(rv): e.append('troppe sinossi perse (%d)' % lost)
        lostc = sum(1 for k in rv if k in v and rv[k].get('cast') and not v[k].get('cast'))
        if lostc > 0.1 * len(rv): e.append('troppi cast persi (%d)' % lostc)
        if ref.get('generato') and str(a.get('generato')) < str(ref['generato']): e.append("piu' vecchio della versione pubblicata")
    return e

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', required=True); ap.add_argument('--dir', required=True)
    ap.add_argument('--keep', type=int, default=8); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--result'); a = ap.parse_args()
    res = {'esito': 'errore', 'motivi': []}
    def done(code):
        if a.result: json.dump(res, open(a.result, 'w'), ensure_ascii=False, indent=1)
        print(json.dumps(res, ensure_ascii=False)); sys.exit(code)
    try: raw = open(a.src, 'rb').read()
    except Exception as ex: res['motivi'] = ['sorgente illeggibile: %s' % ex]; done(2)
    if len(raw) > MAXB: res.update(esito='rifiutato', motivi=['file troppo grande']); done(3)
    try: cand = json.loads(raw.decode('utf-8'))
    except Exception as ex: res.update(esito='rifiutato', motivi=['JSON non valido: %s' % ex]); done(3)
    sha = hashlib.sha256(raw).hexdigest(); res['sha256'] = sha
    ptr_p = os.path.join(a.dir, 'pointer.json'); ref = None; ptr = None
    if os.path.exists(ptr_p):
        try:
            ptr = json.load(open(ptr_p)); rp = os.path.join(a.dir, ptr['file']); rb = open(rp, 'rb').read()
            if hashlib.sha256(rb).hexdigest() != ptr['sha256']: res['avviso'] = 'versione pubblicata con impronta incoerente: si ignora come riferimento'
            else: ref = json.loads(rb.decode('utf-8'))
        except Exception as ex: res['avviso'] = 'puntatore precedente illeggibile: %s' % ex
    if ptr and ptr.get('sha256') == sha: res.update(esito='invariato', motivi=[]); done(0)
    errs = validate(cand, ref)
    if errs: res.update(esito='rifiutato', motivi=errs); done(3)
    res['n'] = len(cand['voci']); res['generato'] = cand['generato']
    if a.dry_run: res.update(esito='prova', motivi=[]); done(0)
    fn = 'tmdb_titoli.%s.json' % sha[:8]
    os.makedirs(a.dir, exist_ok=True); open(os.path.join(a.dir, fn), 'wb').write(raw)
    new = {'versione': 2, 'generato': cand['generato'], 'sha256': sha, 'file': fn, 'n': len(cand['voci']), 'pubblicato': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'precedente': (ptr or {}).get('file')}
    sp = os.path.join(a.dir, 'storico.json')
    try: hist = json.load(open(sp)).get('versioni', [])
    except Exception: hist = []
    hist = [h for h in hist if h.get('file') != fn]; hist.insert(0, {k: new[k] for k in ('generato', 'sha256', 'file', 'n', 'pubblicato')}); hist = hist[:max(2, a.keep)]
    keepf = {h['file'] for h in hist}
    for f in os.listdir(a.dir):
        if re.match(r'^tmdb_titoli\.[0-9a-f]{8}\.json$', f) and f not in keepf: os.remove(os.path.join(a.dir, f))
    json.dump({'versioni': hist}, open(sp, 'w'), indent=1)
    json.dump(new, open(ptr_p, 'w'), indent=1)   # il puntatore si scrive per ULTIMO: se qualcosa fallisce prima, resta quello valido
    res.update(esito='aggiornato', motivi=[], file=fn); done(0)

if __name__ == '__main__': main()
