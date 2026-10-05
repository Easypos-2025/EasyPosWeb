"""
Construye el instalador único del agente: instalador_agente/salida/EasyPosAgente-Setup.exe

  1. Compila la mini-app de toma de pedidos (npm run build:tomapedido).
  2. Empaqueta el agente con PyInstaller (EasyPosAgente.exe, no requiere Python instalado).
  3. Junta agente + mini-app + ícono en carga.zip.
  4. Empaqueta el asistente con la carga en un solo .exe que pide permisos de administrador.

Uso (desde la raíz del repositorio):
  venv\\Scripts\\python instalador_agente\\construir.py              solo construye
  venv\\Scripts\\python instalador_agente\\construir.py --publicar   construye y publica la versión en el
      servidor: las sedes la descargan y se actualizan (botón del panel o al abrir turno).
      Solo publica código ya comiteado (versión = AA.MM.DD-commit).
Requiere: pip install -r backend/requirements-dev.txt (pyinstaller) y Node para la mini-app.
"""
import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AQUI = RAIZ / "instalador_agente"
TRABAJO = AQUI / "construccion"
SALIDA = AQUI / "salida"
ICONO = RAIZ / "frontend" / "src" / "assets" / "favicon.ico"
PY = sys.executable
VERSION_PY = RAIZ / "backend" / "agente_local" / "_version.py"
RUTAS_AGENTE = ["backend/agente_local", "frontend/src/apps/tomapedido", "frontend/vite.tomapedido.config.js", "instalador_agente"]

# Servidor de despliegue (los mismos datos del flujo de commit del proyecto)
SERVIDOR = os.getenv("EASYPOS_SERVIDOR", "root@209.38.152.254")
LLAVE_SSH = os.getenv("EASYPOS_LLAVE_SSH", str(Path.home() / ".ssh" / "id_ed25519"))
DIR_REMOTO = "/var/www/easyposweb/descargas_agente"


def correr(args, cwd=None):
    print("»", " ".join(map(str, args)))
    subprocess.run(args, cwd=cwd, check=True, shell=(sys.platform == "win32" and args[0] == "npm"))


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def version_actual(publicar: bool) -> str:
    """AA.MM.DD-commit. Para publicar exige que el código del agente esté comiteado."""
    pendientes = git("status", "--porcelain", "--", *RUTAS_AGENTE)
    if publicar and pendientes:
        sys.exit("Hay cambios sin commit en el agente o la mini-app; haga commit antes de publicar:\n" + pendientes)
    v = f"{date.today():%y.%m.%d}-{git('rev-parse', '--short', 'HEAD')}"
    return v + ("-local" if pendientes else "")


def pyinstaller(*args):
    correr([PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
            "--workpath", str(TRABAJO / "build"), "--specpath", str(TRABAJO / "spec"), *args])


def publicar(carga: Path, version: str) -> None:
    """Sube el paquete al servidor (carpeta privada) y lo deja como versión vigente."""
    archivo = f"agente-{version}.zip"
    paquete = SALIDA / archivo
    shutil.copy(carga, paquete)
    sha = hashlib.sha256(paquete.read_bytes()).hexdigest()
    notas = git("log", "-1", "--pretty=%s")[:300]
    ssh = ["ssh", "-i", LLAVE_SSH, "-o", "ConnectTimeout=20", SERVIDOR]
    correr(ssh + [f"mkdir -p {DIR_REMOTO} && chmod 750 {DIR_REMOTO}"])
    correr(["scp", "-i", LLAVE_SSH, str(paquete), f"{SERVIDOR}:{DIR_REMOTO}/{archivo}"])
    correr(ssh + ["cd /var/www/easyposweb/backend && venv/bin/python -m app.scripts.publicar_agente "
                  f"--version {shlex.quote(version)} --archivo {shlex.quote(archivo)} --sha256 {sha} --notas {shlex.quote(notas)}"])
    paquete.unlink(missing_ok=True)
    print(f"\nPublicada la versión {version}: las sedes la descargan en su próximo latido.")


def main():
    publicar_version = "--publicar" in sys.argv
    version = version_actual(publicar_version)
    print(f"Versión del agente: {version}")
    VERSION_PY.write_text(f'VERSION = "{version}"\n', encoding="utf-8")
    try:
        construir()
    finally:
        VERSION_PY.unlink(missing_ok=True)          # en desarrollo la versión vuelve a ser "dev"
    print(f"\nListo: {SALIDA / 'EasyPosAgente-Setup.exe'} (versión {version})")
    if publicar_version:
        publicar(TRABAJO / "carga.zip", version)


def construir():
    shutil.rmtree(TRABAJO, ignore_errors=True)
    TRABAJO.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(exist_ok=True)

    # 1. Mini-app
    correr(["npm", "run", "build:tomapedido"], cwd=RAIZ / "frontend")
    app = RAIZ / "frontend" / "dist_tomapedido"

    # 2. Agente
    pyinstaller("--name", "EasyPosAgente", "--onedir", "--console", "--icon", str(ICONO),
                "--distpath", str(TRABAJO / "dist"), "--paths", str(RAIZ / "backend"),
                "--collect-submodules", "agente_local", "--collect-submodules", "uvicorn",
                "--collect-submodules", "sqlalchemy.dialects.mysql", "--collect-submodules", "jose",
                "--collect-submodules", "qrcode", "--hidden-import", "aiomysql", "--hidden-import", "pymysql",
                str(AQUI / "lanzador_agente.py"))
    agente = TRABAJO / "dist" / "EasyPosAgente"

    # 3. Carga: agente + mini-app (carpeta app/) + ícono
    carga = TRABAJO / "carga.zip"
    with zipfile.ZipFile(carga, "w", zipfile.ZIP_DEFLATED) as z:
        for f in agente.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(agente))
        for f in app.rglob("*"):
            if f.is_file():
                z.write(f, Path("app") / f.relative_to(app))
        z.write(ICONO, "easypos.ico")

    # 4. Instalador de un solo archivo (el asistente busca el ícono como easypos.ico)
    icono = TRABAJO / "easypos.ico"
    shutil.copy(ICONO, icono)
    pyinstaller("--name", "EasyPosAgente-Setup", "--onefile", "--windowed", "--uac-admin", "--icon", str(ICONO),
                "--distpath", str(SALIDA), "--add-data", f"{carga};.", "--add-data", f"{icono};.",
                "--hidden-import", "pymysql", "--collect-submodules", "qrcode", str(AQUI / "instalador.py"))


if __name__ == "__main__":
    main()
