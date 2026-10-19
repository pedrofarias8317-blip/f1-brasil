import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.jolpi.ca/ergast/f1"
PASTA = Path(__file__).resolve().parent.parent / "dados"
PASTA.mkdir(exist_ok=True)

PEDIDOS = {
    "pilotos.json": "/current/driverstandings.json",
    "equipes.json": "/current/constructorstandings.json",
    "calendario.json": "/current.json",
}


def buscar(caminho):
    for tentativa in range(8):
        req = urllib.request.Request(BASE + caminho, headers={"User-Agent": "f1-brasil"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resposta:
                return json.load(resposta)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as erro:
            codigo = getattr(erro, "code", 0)
            if codigo == 429 or codigo >= 500 or codigo == 0:
                espera = (90 if codigo == 429 else 20) * (tentativa + 1)
                print("erro", codigo, "- esperando", espera, "segundos e tentando de novo...")
                time.sleep(espera)
                continue
            raise
    raise RuntimeError("muitas tentativas")


for nome, caminho in PEDIDOS.items():
    dados = buscar(caminho)
    (PASTA / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ok:", nome)
    time.sleep(1)

from datetime import date

calendario = json.loads((PASTA / "calendario.json").read_text(encoding="utf-8"))
hoje = date.today().isoformat()
resultados = {}
for corrida in calendario["MRData"]["RaceTable"]["Races"]:
    if corrida["date"] > hoje:
        continue
    rodada = corrida["round"]
    dados = buscar("/current/" + rodada + "/results.json")
    lista = dados["MRData"]["RaceTable"]["Races"]
    if lista:
        resultados[rodada] = lista[0]
        print("ok: rodada", rodada)
    time.sleep(1)

(PASTA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

arq = PASTA / "campeoes.json"
anos = {}
if arq.exists():
    for lista in json.loads(arq.read_text(encoding="utf-8"))["MRData"]["StandingsTable"]["StandingsLists"]:
        anos[lista["season"]] = lista
ano_atual = date.today().year
for ano in range(1950, ano_atual + 1):
    chave = str(ano)
    if chave in anos and ano != ano_atual:
        continue
    dados = buscar("/" + chave + "/driverstandings.json")
    listas = dados["MRData"]["StandingsTable"]["StandingsLists"]
    if listas:
        lider = listas[0]
        lider["DriverStandings"] = lider["DriverStandings"][:1]
        anos[chave] = lider
        print("ok: campeao", chave)
    time.sleep(1)
saida = {"MRData": {"StandingsTable": {"StandingsLists": [anos[k] for k in sorted(anos)]}}}
arq.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")

arq2 = PASTA / "temporadas.json"
temporadas = json.loads(arq2.read_text(encoding="utf-8")) if arq2.exists() else {}
for ano in range(1950, ano_atual + 1):
    chave = str(ano)
    if chave in temporadas and ano != ano_atual:
        continue
    pil = buscar("/" + chave + "/driverstandings.json?limit=100")
    listas = pil["MRData"]["StandingsTable"]["StandingsLists"]
    if not listas:
        continue
    time.sleep(1)
    eq = buscar("/" + chave + "/constructorstandings.json?limit=100")
    listas_eq = eq["MRData"]["StandingsTable"]["StandingsLists"]
    temporadas[chave] = {
        "rodada": listas[0]["round"],
        "pilotos": [
            [d.get("position") or str(i + 1), d["Driver"]["givenName"] + " " + d["Driver"]["familyName"], " / ".join(c["name"] for c in d["Constructors"]), d["points"], d["wins"], d["Driver"].get("nationality", "")]
            for i, d in enumerate(listas[0]["DriverStandings"])
        ],
        "equipes": [
            [t.get("position") or str(i + 1), t["Constructor"]["name"], t["points"], t["wins"]]
            for i, t in enumerate(listas_eq[0]["ConstructorStandings"])
        ] if listas_eq else [],
    }
    print("ok: temporada", chave)
    arq2.write_text(json.dumps(temporadas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    time.sleep(1.5)
arq2.write_text(json.dumps(temporadas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def total_opcional(caminho):
    try:
        return int(buscar(caminho + "?limit=1")["MRData"]["total"])
    except urllib.error.HTTPError:
        return None


arq3 = PASTA / "estatisticas.json"
estat = json.loads(arq3.read_text(encoding="utf-8")) if arq3.exists() else {"pilotos": {}}
atual = json.loads((PASTA / "pilotos.json").read_text(encoding="utf-8"))["MRData"]["StandingsTable"]["StandingsLists"][0]
camp = json.loads((PASTA / "campeoes.json").read_text(encoding="utf-8"))["MRData"]["StandingsTable"]["StandingsLists"]
titulos = {}
for lista in camp:
    if int(lista["season"]) < ano_atual:
        pid_campeao = lista["DriverStandings"][0]["Driver"]["driverId"]
        titulos[pid_campeao] = titulos.get(pid_campeao, 0) + 1

for d in atual["DriverStandings"]:
    pid = d["Driver"]["driverId"]
    if estat["pilotos"].get(pid, {}).get("rodada") == atual["round"]:
        continue
    linhas = []
    pos = 0
    while True:
        r = buscar("/drivers/" + pid + "/results.json?limit=100&offset=" + str(pos))
        for corrida in r["MRData"]["RaceTable"]["Races"]:
            linhas.append((corrida["Circuit"]["circuitName"], corrida["Results"][0]["positionText"]))
        pos += 100
        if pos >= int(r["MRData"]["total"]):
            break
        time.sleep(1.2)
    time.sleep(1.2)
    circuitos = {}
    for nome_circ, colocacao in linhas:
        c = circuitos.setdefault(nome_circ, [0, 0, 0])
        c[0] += 1
        if colocacao == "1":
            c[1] += 1
        if colocacao in ("1", "2", "3"):
            c[2] += 1
    melhores = sorted(([n] + v for n, v in circuitos.items() if v[0] >= 3), key=lambda x: (-x[2], -x[3], -x[1]))[:5]
    poles = total_opcional("/drivers/" + pid + "/qualifying/1.json")
    time.sleep(1.2)
    voltas = total_opcional("/drivers/" + pid + "/fastest/1/results.json")
    time.sleep(1.2)
    dr = d["Driver"]
    estat["pilotos"][pid] = {
        "rodada": atual["round"],
        "nome": dr["givenName"] + " " + dr["familyName"],
        "numero": dr.get("permanentNumber", ""),
        "codigo": dr.get("code", ""),
        "nasc": dr.get("dateOfBirth", ""),
        "nac": dr.get("nationality", ""),
        "equipe": d["Constructors"][0]["name"] if d["Constructors"] else "",
        "titulos": titulos.get(pid, 0),
        "corridas": len(linhas),
        "vitorias": sum(1 for _, p in linhas if p == "1"),
        "podios": sum(1 for _, p in linhas if p in ("1", "2", "3")),
        "poles": poles,
        "voltas": voltas,
        "melhores": melhores,
    }
    print("ok: estatisticas", pid)
    arq3.write_text(json.dumps(estat, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


arq4 = PASTA / "circuitos.json"
circ = json.loads(arq4.read_text(encoding="utf-8")) if arq4.exists() else {}
calendario = json.loads((PASTA / "calendario.json").read_text(encoding="utf-8"))
for corrida in calendario["MRData"]["RaceTable"]["Races"]:
    cid = corrida["Circuit"]["circuitId"]
    ja_correu = corrida["date"] <= date.today().isoformat()
    if cid in circ and not (ja_correu and circ[cid]["ate"] < ano_atual):
        circ[cid]["rodada"] = int(corrida["round"])
        continue
    vitorias = []
    pos = 0
    while True:
        r = buscar("/circuits/" + cid + "/results/1.json?limit=100&offset=" + str(pos))
        for c in r["MRData"]["RaceTable"]["Races"]:
            ganhador = c["Results"][0]
            vitorias.append((int(c["season"]), ganhador["Driver"]["givenName"] + " " + ganhador["Driver"]["familyName"], ganhador["Constructor"]["name"]))
        pos += 100
        if pos >= int(r["MRData"]["total"]):
            break
        time.sleep(1.2)
    time.sleep(1.2)
    por_piloto = {}
    por_equipe = {}
    for _, p, e in vitorias:
        por_piloto[p] = por_piloto.get(p, 0) + 1
        por_equipe[e] = por_equipe.get(e, 0) + 1
    vitorias.sort()
    circ[cid] = {
        "nome": corrida["Circuit"]["circuitName"],
        "cidade": corrida["Circuit"]["Location"]["locality"],
        "pais": corrida["Circuit"]["Location"]["country"],
        "rodada": int(corrida["round"]),
        "ate": ano_atual if ja_correu else ano_atual - 1,
        "corridas": len(vitorias),
        "primeira": vitorias[0][0] if vitorias else None,
        "pilotos": sorted(por_piloto.items(), key=lambda x: -x[1])[:5],
        "equipes": sorted(por_equipe.items(), key=lambda x: -x[1])[:3],
        "recentes": [[a, p, e] for a, p, e in vitorias[-5:]][::-1],
    }
    print("ok: circuito", cid)
    arq4.write_text(json.dumps(circ, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
arq4.write_text(json.dumps(circ, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


arq5 = PASTA / "equipes_stats.json"
est_eq = json.loads(arq5.read_text(encoding="utf-8")) if arq5.exists() else {}
tab = json.loads((PASTA / "equipes.json").read_text(encoding="utf-8"))["MRData"]["StandingsTable"]["StandingsLists"][0]
for t in tab["ConstructorStandings"]:
    cid = t["Constructor"]["constructorId"]
    if est_eq.get(cid, {}).get("rodada") == tab["round"]:
        continue
    corridas_eq = {}
    pos = 0
    while True:
        r = buscar("/constructors/" + cid + "/results.json?limit=100&offset=" + str(pos))
        for c in r["MRData"]["RaceTable"]["Races"]:
            d = corridas_eq.setdefault(c["season"] + "-" + c["round"], {"circ": c["Circuit"]["circuitName"], "vit": 0, "pod": 0})
            for res in c["Results"]:
                if res["positionText"] == "1":
                    d["vit"] = 1
                if res["positionText"] in ("1", "2", "3"):
                    d["pod"] += 1
        pos += 100
        if pos >= int(r["MRData"]["total"]):
            break
        time.sleep(1.2)
    time.sleep(1.2)
    por_pista = {}
    for d in corridas_eq.values():
        x = por_pista.setdefault(d["circ"], [0, 0, 0])
        x[0] += 1
        x[1] += d["vit"]
        x[2] += d["pod"]
    melhores = sorted(([n] + v for n, v in por_pista.items() if v[0] >= 3), key=lambda x: (-x[2], -x[3], -x[1]))[:5]
    temp = json.loads((PASTA / "temporadas.json").read_text(encoding="utf-8"))
    anos_titulo = sorted(int(a) for a, v in temp.items() if int(a) < ano_atual and v["equipes"] and v["equipes"][0][1] == t["Constructor"]["name"])
    poles = total_opcional("/constructors/" + cid + "/qualifying/1.json")
    time.sleep(1.2)
    voltas = total_opcional("/constructors/" + cid + "/fastest/1/results.json")
    time.sleep(1.2)
    est_eq[cid] = {
        "rodada": tab["round"],
        "nome": t["Constructor"]["name"],
        "nac": t["Constructor"].get("nationality", ""),
        "pos": t["position"],
        "pontos": t["points"],
        "vit26": t["wins"],
        "titulos": len(anos_titulo),
        "anos": anos_titulo,
        "corridas": len(corridas_eq),
        "vitorias": sum(d["vit"] for d in corridas_eq.values()),
        "podios": sum(d["pod"] for d in corridas_eq.values()),
        "poles": poles,
        "voltas": voltas,
        "melhores": melhores,
        "pilotos": [d["Driver"]["givenName"] + " " + d["Driver"]["familyName"] for d in atual["DriverStandings"] if any(c["constructorId"] == cid for c in d["Constructors"])],
    }
    print("ok: equipe", cid)
    arq5.write_text(json.dumps(est_eq, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def buscar_seguro(caminho):
    try:
        return buscar(caminho)
    except urllib.error.HTTPError:
        return None


arq6 = PASTA / "detalhes.json"
det = json.loads(arq6.read_text(encoding="utf-8")) if arq6.exists() else {}
res_atual = json.loads((PASTA / "resultados.json").read_text(encoding="utf-8"))
for rodada in res_atual:
    if rodada in det and det[rodada]["quali"]:
        continue
    q = buscar_seguro("/current/" + rodada + "/qualifying.json")
    time.sleep(1.2)
    p = buscar_seguro("/current/" + rodada + "/pitstops.json?limit=100")
    time.sleep(1.2)
    quali = []
    if q and q["MRData"]["RaceTable"]["Races"]:
        for x in q["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"]:
            quali.append([x["position"], x["Driver"]["givenName"] + " " + x["Driver"]["familyName"], x["Constructor"]["name"], x.get("Q1", ""), x.get("Q2", ""), x.get("Q3", "")])
    pits = []
    if p and p["MRData"]["RaceTable"]["Races"]:
        for x in p["MRData"]["RaceTable"]["Races"][0]["PitStops"]:
            pits.append([x["driverId"], x["stop"], x["lap"], x["duration"]])
    det[rodada] = {"quali": quali, "pits": pits}
    print("ok: detalhes rodada", rodada)
    arq6.write_text(json.dumps(det, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def contar(caminho, chave):
    pil, eq = {}, {}
    pos = 0
    while True:
        r = buscar(caminho + "?limit=100&offset=" + str(pos))
        for c in r["MRData"]["RaceTable"]["Races"]:
            for x in c.get(chave, []):
                n = x["Driver"]["givenName"] + " " + x["Driver"]["familyName"]
                pil[n] = pil.get(n, 0) + 1
                e = x["Constructor"]["name"]
                eq[e] = eq.get(e, 0) + 1
        pos += 100
        if pos >= int(r["MRData"]["total"]):
            break
        time.sleep(1.2)
    return pil, eq


arq7 = PASTA / "recordes.json"
rec = json.loads(arq7.read_text(encoding="utf-8")) if arq7.exists() else {}
if rec.get("rodada") != atual["round"]:
    v_p, v_e = contar("/results/1.json", "Results")
    p2, _ = contar("/results/2.json", "Results")
    p3, _ = contar("/results/3.json", "Results")
    try:
        pol, _ = contar("/grid/1/results.json", "Results")
    except urllib.error.HTTPError:
        pol = {}
    pod = dict(v_p)
    for d in (p2, p3):
        for n, v in d.items():
            pod[n] = pod.get(n, 0) + v
    def top(d):
        return sorted(d.items(), key=lambda x: -x[1])[:10]
    rec = {"rodada": atual["round"], "vit_pilotos": top(v_p), "vit_equipes": top(v_e), "podios": top(pod), "poles": top(pol)}
    arq7.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("ok: recordes")


arq8 = PASTA / "historico.json"
H = json.loads(arq8.read_text(encoding="utf-8")) if arq8.exists() else {"pilotos": [], "equipes": [], "circuitos": [], "corridas": []}
ip = {p[0]: i for i, p in enumerate(H["pilotos"])}
ie = {e[0]: i for i, e in enumerate(H["equipes"])}
ic = {c[0]: i for i, c in enumerate(H["circuitos"])}
anos_prontos = {c[0] for c in H["corridas"]}


def indice(lista, mapa, chave, item):
    if chave not in mapa:
        mapa[chave] = len(lista)
        lista.append(item)
    return mapa[chave]


def numero(texto):
    v = float(texto)
    return int(v) if v == int(v) else v


for ano in range(1950, ano_atual + 1):
    if ano in anos_prontos and ano != ano_atual:
        continue
    H["corridas"] = [c for c in H["corridas"] if c[0] != ano]
    corr = {}
    desloc = 0
    while True:
        r = buscar("/" + str(ano) + "/results.json?limit=100&offset=" + str(desloc))
        for c in r["MRData"]["RaceTable"]["Races"]:
            ci = c["Circuit"]
            idx_c = indice(H["circuitos"], ic, ci["circuitId"], [ci["circuitId"], ci["circuitName"]])
            linhas = corr.setdefault(int(c["round"]), [idx_c, []])[1]
            for x in c["Results"]:
                d = x["Driver"]
                e = x["Constructor"]
                i_p = indice(H["pilotos"], ip, d["driverId"], [d["driverId"], d["givenName"] + " " + d["familyName"], d.get("nationality", "")])
                i_e = indice(H["equipes"], ie, e["constructorId"], [e["constructorId"], e["name"]])
                colocacao = int(x["position"]) if x["positionText"].isdigit() else 0
                linhas.append([i_p, i_e, int(x["grid"]), colocacao, numero(x["points"])])
        desloc += 100
        if desloc >= int(r["MRData"]["total"]):
            break
        time.sleep(1.2)
    for rod in sorted(corr):
        H["corridas"].append([ano, rod, corr[rod][0], corr[rod][1]])
    arq8.write_text(json.dumps(H, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("ok: historico", ano)
    time.sleep(1.2)
