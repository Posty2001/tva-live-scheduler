#!/usr/bin/env python3
"""Prove di scripts/mm_archivio.py. Uso: python3 scripts/test_mm_archivio.py"""
import json, os, subprocess, sys, tempfile, copy, hashlib
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, 'mm_archivio.py')
SRC = os.environ.get('MM_SAMPLE')
n = bad = 0
def ok(t, c, x=''):
    global n, bad; n += 1; bad += (not c); print('PASS' if c else 'FAIL', t, x)
def mk(i): return {'tmdb': {'t': 'movie', 'id': 1000 + i}, 'titolo': 'T%d' % i, 'sinossi_it': 'Sinossi %d.' % i, 'cast': ['A'], 'date': [{'paese': 'IT', 'data': '2020-01-%02d' % (1 + i % 27)}]}
BASE = {'versione': 2, 'generato': '2026-11-27', 'voci': {'%03d' % i: mk(i) for i in range(60)}}
def run(arch, d, *extra, raw=None):
    t = tempfile.mktemp(suffix='.json'); open(t, 'wb').write(raw if raw is not None else json.dumps(arch).encode())
    r = subprocess.run([sys.executable, S, '--src', t, '--dir', d, '--result', t + '.res', *extra], capture_output=True, text=True)
    return r.returncode, json.load(open(t + '.res')) if os.path.exists(t + '.res') else {}
d = tempfile.mkdtemp()
rc, r = run(BASE, d); ok('prima pubblicazione', rc == 0 and r['esito'] == 'aggiornato' and os.path.exists(os.path.join(d, 'pointer.json')), r)
p = json.load(open(os.path.join(d, 'pointer.json'))); ok('puntatore: sha256 = impronta del file', hashlib.sha256(open(os.path.join(d, p['file']), 'rb').read()).hexdigest() == p['sha256'] and p['n'] == 60)
rc, r = run(BASE, d); ok('stesso contenuto: invariato, nessuna scrittura', rc == 0 and r['esito'] == 'invariato')
nx = copy.deepcopy(BASE); nx['generato'] = '2026-12-04'; nx['voci']['000']['titolo'] = 'Nuovo'
rc, r = run(nx, d); p2 = json.load(open(os.path.join(d, 'pointer.json'))); ok('aggiornamento valido', r['esito'] == 'aggiornato' and p2['precedente'] == p['file'] and p2['generato'] == '2026-12-04')
lost = copy.deepcopy(nx); lost['generato'] = '2026-12-11'
for k in list(lost['voci'])[:20]: del lost['voci'][k]
rc, r = run(lost, d); ok('perdita >10% voci: RIFIUTATO e puntatore invariato', rc == 3 and r['esito'] == 'rifiutato' and json.load(open(os.path.join(d, 'pointer.json'))) == p2, r['motivi'])
ns = copy.deepcopy(nx); ns['generato'] = '2026-12-11'
for k in list(ns['voci'])[:12]: ns['voci'][k]['sinossi_it'] = ''
rc, r = run(ns, d); ok('sinossi perse: rifiutato', rc == 3, r['motivi'])
nc = copy.deepcopy(nx); nc['generato'] = '2026-12-11'
for k in list(nc['voci'])[:12]: nc['voci'][k]['cast'] = []
rc, r = run(nc, d); ok('cast persi: rifiutato', rc == 3, r['motivi'])
old = copy.deepcopy(nx); old['generato'] = '2026-01-01'; old['voci']['001']['titolo'] = 'x'
rc, r = run(old, d); ok('archivio piu\' vecchio: rifiutato', rc == 3)
bd = copy.deepcopy(nx); bd['generato'] = '2026-12-11'; bd['voci']['001']['date'] = [{'paese': 'IT', 'data': '07/06/2002'}]
rc, r = run(bd, d); ok('data non ISO: rifiutato', rc == 3)
rc, r = run(None, d, raw=b'{non json'); ok('JSON corrotto: rifiutato', rc == 3 and json.load(open(os.path.join(d, 'pointer.json'))) == p2)
rc, r = run(None, d, raw=b'x' * 1600000); ok('file enorme: rifiutato', rc == 3)
d2 = tempfile.mkdtemp(); rc, r = run(BASE, d2, '--dry-run'); ok('prova a secco: nessuna scrittura', rc == 0 and r['esito'] == 'prova' and not os.listdir(d2))
# pulizia versioni vecchie
d3 = tempfile.mkdtemp()
for i in range(12):
    a = copy.deepcopy(BASE); a['generato'] = '2026-12-%02d' % (1 + i); a['voci']['000']['titolo'] = 'v%d' % i; run(a, d3, '--keep', '4')
fs = [f for f in os.listdir(d3) if f.startswith('tmdb_titoli.')]; ok('conserva solo le ultime 4 versioni', len(fs) == 4, fs)
# puntatore con impronta incoerente: il riferimento si ignora ma non si pubblica nulla di non valido
open(os.path.join(d3, json.load(open(os.path.join(d3, 'pointer.json')))['file']), 'ab').write(b' ')
a = copy.deepcopy(BASE); a['generato'] = '2027-01-01'; rc, r = run(a, d3); ok('riferimento corrotto: avviso, candidato valido pubblicato', rc == 0 and 'avviso' in r)
if SRC and os.path.exists(SRC):
    d4 = tempfile.mkdtemp(); rc, r = run(None, d4, raw=open(SRC, 'rb').read()); ok('archivio REALE accettato', rc == 0 and r['esito'] == 'aggiornato', r)
print('%d/%d' % (n - bad, n)); sys.exit(1 if bad else 0)
