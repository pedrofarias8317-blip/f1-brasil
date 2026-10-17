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
