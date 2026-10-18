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
        except urllib.error.HTTPError as erro:
            if erro.code == 429:
                espera = 90 * (tentativa + 1)
                print("limite atingido, esperando", espera, "segundos...")
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
