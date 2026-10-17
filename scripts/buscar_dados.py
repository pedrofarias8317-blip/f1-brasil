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
