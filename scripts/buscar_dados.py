import json
import time
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
    req = urllib.request.Request(BASE + caminho, headers={"User-Agent": "f1-brasil"})
    with urllib.request.urlopen(req, timeout=30) as resposta:
        return json.load(resposta)


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
