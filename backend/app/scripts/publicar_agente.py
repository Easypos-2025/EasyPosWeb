"""
Registra en la BD una versión del Agente Local ya copiada a la carpeta de descargas y la deja
como vigente (las sedes la descargan en su próximo latido). Lo ejecuta construir.py --publicar
por SSH en el servidor:

  cd /var/www/easyposweb/backend && venv/bin/python -m app.scripts.publicar_agente \\
      --version 26.10.04-abc1234 --archivo agente-26.10.04-abc1234.zip --sha256 <hex> --notas "..."

Se conservan las últimas 5 versiones (más la vigente); las demás se borran del disco y de la BD.
"""
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

DIR_DESCARGAS = Path(os.getenv("AGENTE_DESCARGAS_DIR", "/var/www/easyposweb/descargas_agente"))
CONSERVAR = 5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--archivo", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--notas", default="")
    a = ap.parse_args()

    if not re.match(r"^[0-9A-Za-z.\-]{3,40}$", a.version) or not re.match(r"^[0-9A-Za-z.\-_]{3,200}\.zip$", a.archivo):
        sys.exit("Versión o nombre de archivo no válido.")
    ruta = DIR_DESCARGAS / a.archivo
    if not ruta.is_file():
        sys.exit(f"No existe {ruta}")
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    if sha != a.sha256.lower():
        sys.exit("La huella SHA-256 no coincide: el archivo se dañó al copiarlo.")

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    url = os.getenv("DATABASE_URL", "").replace("+aiomysql", "+pymysql")
    motor = create_engine(url)
    with motor.begin() as c:
        c.execute(text("UPDATE agente_versiones SET vigente = 0"))
        c.execute(text("""
            INSERT INTO agente_versiones (version, archivo, sha256, tamano, notas, vigente)
            VALUES (:v, :a, :s, :t, :n, 1)
            ON DUPLICATE KEY UPDATE archivo = :a, sha256 = :s, tamano = :t, notas = :n, vigente = 1, publicado_en = NOW()
        """), {"v": a.version, "a": a.archivo, "s": sha, "t": ruta.stat().st_size, "n": a.notas[:2000]})
        # Limpieza: últimas CONSERVAR versiones + la vigente
        viejas = c.execute(text("""
            SELECT id, archivo FROM agente_versiones WHERE vigente = 0
            ORDER BY publicado_en DESC LIMIT 1000 OFFSET :n
        """), {"n": CONSERVAR}).all()
        for id_v, archivo in viejas:
            (DIR_DESCARGAS / archivo).unlink(missing_ok=True)
            c.execute(text("DELETE FROM agente_versiones WHERE id = :id"), {"id": id_v})
    print(f"Versión {a.version} publicada como vigente ({ruta.stat().st_size // 1024} KB).")


if __name__ == "__main__":
    main()
