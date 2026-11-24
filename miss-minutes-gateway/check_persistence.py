"""Verifica (solo nomi/tipi, mai valori) che binding e variabili del Worker siano quelli attesi. Legge il JSON delle impostazioni da stdin."""
import json, os, sys
r = json.load(sys.stdin).get("result", {})
b = r.get("bindings", [])
want = os.environ.get("ENABLE_GEMINI") == "true"
have = {x["name"]: x["type"] for x in b}
print("binding:", dict(sorted(have.items())))
fv = [x for x in b if x["name"] == "FREE_TIER_VERIFIED"]
print("FREE_TIER_VERIFIED =", fv[0].get("text") if fv else "(assente)")
need = {"LIMITER": "durable_object_namespace", "SESSION_SECRET": "secret_text"}
if want:
    need["GEMINI_KEY"] = "secret_text"
bad = [k for k, t in need.items() if have.get(k) != t]
if want and (not fv or fv[0].get("text") != "yes"):
    bad.append("FREE_TIER_VERIFIED=yes")
if not want and fv and fv[0].get("text") == "yes":
    bad.append("FREE_TIER_VERIFIED doveva essere no")
if bad:
    print("::error::persistenza incompleta:", bad)
    sys.exit(1)
print("Persistenza verificata.")
