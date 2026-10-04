"""
Construye el instalador único del agente: instalador_agente/salida/EasyPosAgente-Setup.exe

  1. Compila la mini-app de toma de pedidos (npm run build:tomapedido).
  2. Empaqueta el agente con PyInstaller (EasyPosAgente.exe, no requiere Python instalado).
  3. Junta agente + mini-app + ícono en carga.zip.
  4. Empaqueta el asistente con la carga en un solo .exe que pide permisos de administrador.

Uso (desde la raíz del repositorio):  venv\\Scripts\\python instalador_agente\\construir.py
Requiere: pip install -r backend/requirements-dev.txt (pyinstaller) y Node para la mini-app.
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AQUI = RAIZ / "instalador_agente"
TRABAJO = AQUI / "construccion"
SALIDA = AQUI / "salida"
ICONO = RAIZ / "frontend" / "src" / "assets" / "favicon.ico"
PY = sys.executable


def correr(args, cwd=None):
    print("»", " ".join(map(str, args)))
    subprocess.run(args, cwd=cwd, check=True, shell=(sys.platform == "win32" and args[0] == "npm"))


def pyinstaller(*args):
    correr([PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
            "--workpath", str(TRABAJO / "build"), "--specpath", str(TRABAJO / "spec"), *args])


def main():
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
    print(f"\nListo: {SALIDA / 'EasyPosAgente-Setup.exe'}")


if __name__ == "__main__":
    main()
