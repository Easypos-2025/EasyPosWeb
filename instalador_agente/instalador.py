"""
Instalador del EasyPos Agente Local (EasyPosAgente-Setup.exe).

Un solo paso en el PC de caja (se ejecuta como administrador):
  1. Copia el agente y la mini-app de toma de pedidos a C:\\EasyPos\\AgenteLocal.
  2. Crea el usuario MySQL "easypos_agente" con permisos solo en lo que usa el agente.
  3. Genera el .env (protegido: solo SYSTEM y Administradores lo pueden leer).
  4. Fija la clave del panel de administración (cifrada).
  5. Registra el agente para que arranque con Windows y se reinicie si falla (Programador de tareas).
  6. Regla del firewall para el puerto (los celulares entran por la red local).
  7. Accesos directos en el escritorio con el ícono de EasyPosWeb.
  8. Muestra la dirección y el código QR para los celulares.

Los celulares, tablets y otros PC no instalan nada: abren la dirección en el navegador.
"""
import ctypes
import io
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from tkinter import messagebox, ttk

import pymysql

TITULO = "EasyPos Agente Local"
DESTINO = Path(r"C:\EasyPos\AgenteLocal")
TAREA = "EasyPos Agente Local"
REGLA_FW = "EasyPos Agente Local"
USUARIO_BD = "easypos_agente"
EXE = "EasyPosAgente.exe"
ESCRITORIO = Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop"
RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
RESPALDO = re.compile(r"_\d{2}_\d{2}_\d{4}$")          # copias de seguridad del escritorio (maduritos_02_10_2026)
SIN_VENTANA = 0x08000000


# ═════════════════════════════ lógica de instalación ═════════════════════════════

def es_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ip_local() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def ejecutar(args, entrada: str | None = None, cwd=None, revisar: bool = True) -> str:
    r = subprocess.run(args, input=entrada, capture_output=True, text=True, cwd=cwd, creationflags=SIN_VENTANA,
                       encoding="utf-8", errors="replace")
    if revisar and r.returncode != 0:
        salida = (r.stderr or r.stdout or "").strip()
        registrar_log(f"FALLÓ: {' '.join(map(str, args))}\n{salida}")
        # La causa real está al final del mensaje
        raise RuntimeError(f"{Path(str(args[0])).name} {' '.join(map(str, args[1:]))[:80]}\n\n…{salida[-700:]}")
    return r.stdout


def registrar_log(texto: str) -> None:
    """Detalle completo de la instalación en C:\\EasyPos\\AgenteLocal\\instalacion.log."""
    try:
        DESTINO.mkdir(parents=True, exist_ok=True)
        with open(DESTINO / "instalacion.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {texto}\n")
    except OSError:
        pass


def conectar(d: dict, base: str | None = None):
    return pymysql.connect(host=d["host"], port=int(d["puerto"]), user=d["usuario"], password=d["clave"],
                           database=base, connect_timeout=8, autocommit=True, charset="utf8mb4")


def bases_disponibles(d: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """BD de empresa (tienen platos y registro_dispositivos) con su nombre de sede, y BD temporales."""
    with conectar(d) as con, con.cursor() as c:
        c.execute("""
            SELECT table_schema, SUM(table_name = 'platos') AS p, SUM(table_name = 'registro_dispositivos') AS r,
                   SUM(table_name = 'temp_comanda') AS t
            FROM information_schema.tables
            WHERE table_name IN ('platos', 'registro_dispositivos', 'temp_comanda')
            GROUP BY table_schema
        """)
        filas = c.fetchall()
        empresas, temporales = [], []
        for esquema, p, r, t in filas:
            if t:
                temporales.append(esquema)
            elif p and r and not RESPALDO.search(esquema):
                nombre = ""
                try:
                    c.execute(f"SELECT Nombre_Almacen FROM `{esquema}`.configuracion_sede LIMIT 1")
                    nombre = ((c.fetchone() or [""])[0] or "").strip()
                except Exception:
                    pass
                empresas.append((esquema, nombre))
    return sorted(empresas), sorted(temporales)


def _bd_grant(nombre: str) -> str:
    """Nombre de BD para GRANT a nivel de base: "_" y "%" son comodines y se escapan."""
    return "`" + nombre.replace("`", "").replace("_", r"\_").replace("%", r"\%") + "`"


def crear_usuario_bd(d: dict, bd_empresa: str, bd_temp: str) -> str:
    clave = secrets.token_urlsafe(24)
    with conectar(d) as con, con.cursor() as c:
        for host in ("localhost", "127.0.0.1"):
            usuario = f"'{USUARIO_BD}'@'{host}'"
            c.execute(f"CREATE USER IF NOT EXISTS {usuario} IDENTIFIED BY %s", (clave,))
            c.execute(f"ALTER USER {usuario} IDENTIFIED BY %s", (clave,))
            # Empresa: solo lectura, salvo asignar fotos de la web a platos sin foto
            c.execute(f"GRANT SELECT ON {_bd_grant(bd_empresa)}.* TO {usuario}")
            c.execute(f"GRANT UPDATE (Ruta_Foto) ON `{bd_empresa}`.`platos` TO {usuario}")
            # Temporales: pedidos y tablas propias del agente (ag_*)
            c.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX ON {_bd_grant(bd_temp)}.* TO {usuario}")
        c.execute("FLUSH PRIVILEGES")
    return clave


def escribir_env(d: dict, clave_bd: str, bd_empresa: str, bd_temp: str, puerto: int, clave_nube: str) -> None:
    usuario = urllib.parse.quote(USUARIO_BD, safe="")
    clave = urllib.parse.quote(clave_bd, safe="")
    host = "127.0.0.1" if d["host"] in ("localhost", "127.0.0.1") else d["host"]
    lineas = [
        "# Generado por el instalador del EasyPos Agente Local. No compartir este archivo.",
        f"AG_DB_EMPRESA_URL=mysql+aiomysql://{usuario}:{clave}@{host}:{int(d['puerto'])}/{bd_empresa}",
        f"AG_DB_TEMP_URL=mysql+aiomysql://{usuario}:{clave}@{host}:{int(d['puerto'])}/{bd_temp}",
        f"AG_PUERTO={puerto}",
    ]
    if clave_nube:
        lineas.append(f"AG_NUBE_CLAVE={clave_nube}")
    env = DESTINO / ".env"
    env.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    # Solo SYSTEM (el agente) y Administradores pueden leerlo: tiene la clave de la BD
    ejecutar(["icacls", str(env), "/inheritance:r", "/grant:r", "*S-1-5-18:F", "*S-1-5-32-544:F"], revisar=False)


def detener_agente() -> None:
    ejecutar(["schtasks", "/End", "/TN", TAREA], revisar=False)
    ejecutar(["taskkill", "/F", "/IM", EXE], revisar=False)
    time.sleep(1.5)


def copiar_archivos() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    # Se reemplaza el programa; se conservan .env, secreto.key, logs y caché de fotos
    for viejo in ("_internal", "app"):
        shutil.rmtree(DESTINO / viejo, ignore_errors=True)
    with zipfile.ZipFile(RECURSOS / "carga.zip") as z:
        z.extractall(DESTINO)


def fijar_clave_admin(clave: str) -> None:
    ejecutar([str(DESTINO / EXE), "--clave-admin-stdin"], entrada=clave + "\n", cwd=str(DESTINO))


def regla_firewall(puerto: int) -> None:
    ejecutar(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={REGLA_FW}"], revisar=False)
    ejecutar(["netsh", "advfirewall", "firewall", "add", "rule", f"name={REGLA_FW}", "dir=in", "action=allow",
              "protocol=TCP", f"localport={puerto}"])


def registrar_tarea() -> None:
    """Arranca con Windows (cuenta SYSTEM, sin sesión iniciada) y se reinicia si falla."""
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>EasyPos Agente Local: toma de pedidos de la red local</Description></RegistrationInfo>
  <Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>S-1-5-18</UserId><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure><Interval>PT1M</Interval><Count>999</Count></RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>"{DESTINO / EXE}"</Command><WorkingDirectory>{DESTINO}</WorkingDirectory></Exec>
  </Actions>
</Task>"""
    archivo = DESTINO / "tarea.xml"
    archivo.write_text(xml, encoding="utf-16")
    ejecutar(["schtasks", "/Create", "/TN", TAREA, "/XML", str(archivo), "/F"])
    ejecutar(["schtasks", "/Run", "/TN", TAREA])


def accesos_directos(puerto: int) -> None:
    icono = DESTINO / "easypos.ico"
    for nombre, url in (("EasyPos Toma de Pedidos", f"http://localhost:{puerto}/"),
                        ("EasyPos Panel del Agente", f"http://localhost:{puerto}/#/admin")):
        (ESCRITORIO / f"{nombre}.url").write_text(
            f"[InternetShortcut]\r\nURL={url}\r\nIconFile={icono}\r\nIconIndex=0\r\n", encoding="utf-8")


def esperar_agente(puerto: int, segundos: int = 60) -> bool:
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/ag/salud", timeout=3)
            return True
        except Exception:
            time.sleep(2)
    return False


def puerto_libre(puerto: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def desinstalar() -> None:
    detener_agente()
    ejecutar(["schtasks", "/Delete", "/TN", TAREA, "/F"], revisar=False)
    ejecutar(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={REGLA_FW}"], revisar=False)
    for nombre in ("EasyPos Toma de Pedidos", "EasyPos Panel del Agente"):
        (ESCRITORIO / f"{nombre}.url").unlink(missing_ok=True)
    shutil.rmtree(DESTINO, ignore_errors=True)


# ═════════════════════════════ asistente (ventanas) ═════════════════════════════

class Asistente(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Instalar {TITULO}")
        self.geometry("660x560")
        self.minsize(600, 520)
        try:
            self.iconbitmap(str(RECURSOS / "easypos.ico"))
        except Exception:
            pass
        estilo = ttk.Style(self)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 15, "bold"))
        estilo.configure("Sub.TLabel", foreground="#475569")
        estilo.configure("Accion.TButton", font=("Segoe UI", 10, "bold"))
        self.datos = {"host": tk.StringVar(value="localhost"), "puerto": tk.StringVar(value="3306"),
                      "usuario": tk.StringVar(value="root"), "clave": tk.StringVar()}
        self.bd_empresa = tk.StringVar()
        self.bd_temp = tk.StringVar(value="datatemppos")
        self.puerto_agente = tk.StringVar(value="8090")
        self.clave_nube = tk.StringVar()
        self.clave_admin = tk.StringVar()
        self.clave_admin2 = tk.StringVar()
        self.empresas: list[tuple[str, str]] = []
        self.marco = ttk.Frame(self, padding=22)
        self.marco.pack(fill="both", expand=True)
        self.paso_bienvenida()

    def limpiar(self, titulo: str, sub: str = ""):
        for w in self.marco.winfo_children():
            w.destroy()
        ttk.Label(self.marco, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        if sub:
            ttk.Label(self.marco, text=sub, style="Sub.TLabel", wraplength=600, justify="left").pack(anchor="w", pady=(4, 14))

    def botones(self, siguiente=None, texto="Siguiente", atras=None):
        barra = ttk.Frame(self.marco)
        barra.pack(side="bottom", fill="x", pady=(14, 0))
        if siguiente:
            ttk.Button(barra, text=texto, style="Accion.TButton", command=siguiente).pack(side="right")
        if atras:
            ttk.Button(barra, text="Atrás", command=atras).pack(side="right", padx=8)
        return barra

    def campo(self, padre, etiqueta, var, oculto=False, ancho=34):
        f = ttk.Frame(padre)
        f.pack(fill="x", pady=4)
        ttk.Label(f, text=etiqueta, width=26).pack(side="left")
        e = ttk.Entry(f, textvariable=var, show="•" if oculto else "", width=ancho)
        e.pack(side="left", fill="x", expand=True)
        return e

    # ── 1. Bienvenida
    def paso_bienvenida(self):
        self.limpiar(f"Instalar {TITULO}",
                     "Instala en este PC de caja el servicio de toma de pedidos para celulares, tablets y otros PC "
                     "de la red del negocio. Se hace todo en este asistente; los dispositivos no instalan nada.")
        texto = ("Se instalará en: C:\\EasyPos\\AgenteLocal\n\n"
                 "• Arranca solo con Windows y se reinicia si falla.\n"
                 "• Abre el puerto del agente en el firewall (solo red local).\n"
                 "• Crea un usuario de base de datos con permisos mínimos.\n"
                 "• Crea accesos directos en el escritorio.")
        ttk.Label(self.marco, text=texto, justify="left").pack(anchor="w")
        barra = self.botones(self.paso_mysql, "Comenzar")
        if (DESTINO / EXE).exists():
            ttk.Label(self.marco, text="\nYa hay un agente instalado: se actualizará conservando su configuración.",
                      foreground="#b45309").pack(anchor="w")
            ttk.Button(barra, text="Desinstalar", command=self.desinstalar).pack(side="left")

    def desinstalar(self):
        if messagebox.askyesno(TITULO, "¿Desinstalar el agente de este PC?\n\nLas tablas del agente en la base de "
                                       "datos se conservan."):
            desinstalar()
            messagebox.showinfo(TITULO, "Agente desinstalado.")
            self.destroy()

    # ── 2. MySQL
    def paso_mysql(self):
        self.limpiar("Base de datos del programa de escritorio",
                     "Datos de MySQL / MariaDB de este PC. Se usan una sola vez para crear el usuario del agente; "
                     "la clave no se guarda.")
        for etiqueta, clave, oculto in (("Servidor", "host", False), ("Puerto", "puerto", False),
                                        ("Usuario administrador", "usuario", False), ("Clave", "clave", True)):
            e = self.campo(self.marco, etiqueta, self.datos[clave], oculto)
        e.focus_set()
        self.botones(self.probar_mysql, "Conectar", atras=self.paso_bienvenida)

    def valores_mysql(self) -> dict:
        return {k: v.get().strip() for k, v in self.datos.items()}

    def probar_mysql(self):
        try:
            self.empresas, temporales = bases_disponibles(self.valores_mysql())
        except Exception as e:
            messagebox.showerror(TITULO, f"No fue posible conectar:\n{e}")
            return
        if not self.empresas or not temporales:
            messagebox.showerror(TITULO, "No se encontró la base de datos del escritorio o la de temporales.")
            return
        self.temporales = temporales
        if self.bd_temp.get() not in temporales:
            self.bd_temp.set(temporales[0])
        if len(self.empresas) == 1:
            self.bd_empresa.set(self.empresas[0][0])
        self.paso_bases()

    # ── 3. Bases de datos
    def paso_bases(self):
        self.limpiar("Empresa", "Escoja la base de datos de la empresa de este PC y la de temporales.")
        f = ttk.Frame(self.marco)
        f.pack(fill="x", pady=4)
        ttk.Label(f, text="Base de datos de la empresa", width=26).pack(side="left")
        opciones = [f"{bd}  —  {nombre}" if nombre else bd for bd, nombre in self.empresas]
        combo = ttk.Combobox(f, values=opciones, state="readonly", width=40)
        combo.pack(side="left", fill="x", expand=True)
        actual = self.bd_empresa.get()
        for i, (bd, _) in enumerate(self.empresas):
            if bd == actual:
                combo.current(i)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.bd_empresa.set(self.empresas[combo.current()][0]))
        f2 = ttk.Frame(self.marco)
        f2.pack(fill="x", pady=4)
        ttk.Label(f2, text="Base de datos de temporales", width=26).pack(side="left")
        ttk.Combobox(f2, values=self.temporales, textvariable=self.bd_temp, state="readonly", width=40).pack(
            side="left", fill="x", expand=True)
        self.campo(self.marco, "Puerto del agente", self.puerto_agente, ancho=10)
        self.botones(self.validar_bases, atras=self.paso_mysql)

    def validar_bases(self):
        if not self.bd_empresa.get():
            messagebox.showwarning(TITULO, "Escoja la base de datos de la empresa.")
            return
        if not self.puerto_agente.get().isdigit() or not (1024 < int(self.puerto_agente.get()) < 65535):
            messagebox.showwarning(TITULO, "Puerto no válido.")
            return
        self.paso_claves()

    # ── 4. Claves
    def paso_claves(self):
        self.limpiar("Claves",
                     "Clave del administrador: para entrar al panel del agente en este PC (errores, dispositivos…). "
                     "Guárdela; no se puede ver después.\n\nClave de la nube: la que asignó EasyPosWeb para este "
                     "negocio en \"Agentes Locales\" (opcional; sin ella el agente funciona igual en la red local).")
        e = self.campo(self.marco, "Clave del administrador", self.clave_admin, oculto=True)
        self.campo(self.marco, "Repita la clave", self.clave_admin2, oculto=True)
        ttk.Separator(self.marco).pack(fill="x", pady=12)
        self.campo(self.marco, "Clave de la nube (opcional)", self.clave_nube)
        e.focus_set()
        self.botones(self.validar_claves, "Instalar", atras=self.paso_bases)

    def validar_claves(self):
        if len(self.clave_admin.get()) < 6:
            messagebox.showwarning(TITULO, "La clave del administrador debe tener mínimo 6 caracteres.")
            return
        if self.clave_admin.get() != self.clave_admin2.get():
            messagebox.showwarning(TITULO, "Las claves del administrador no coinciden.")
            return
        nube = self.clave_nube.get().strip()
        if nube and not re.match(r"^ag_[A-Za-z0-9_\-]{20,}$", nube):
            messagebox.showwarning(TITULO, "La clave de la nube no tiene el formato correcto (empieza por ag_).")
            return
        self.paso_instalando()

    # ── 5. Instalación
    def paso_instalando(self):
        self.limpiar("Instalando…", "No cierre esta ventana.")
        self.lista = tk.Listbox(self.marco, height=12, font=("Segoe UI", 10), activestyle="none")
        self.lista.pack(fill="both", expand=True)
        self.barra = ttk.Progressbar(self.marco, mode="determinate", maximum=8)
        self.barra.pack(fill="x", pady=(10, 0))
        threading.Thread(target=self.instalar, daemon=True).start()

    def avance(self, texto: str):
        self.after(0, lambda: (self.lista.insert("end", texto), self.lista.see("end"), self.barra.step(1)))

    def instalar(self):
        puerto = int(self.puerto_agente.get())
        d = self.valores_mysql()
        try:
            self.avance("Deteniendo el agente anterior (si existe)…"); detener_agente()
            if not puerto_libre(puerto):
                raise RuntimeError(f"El puerto {puerto} está en uso por otro programa. Escoja otro puerto.")
            self.avance("Copiando archivos…"); copiar_archivos()
            self.avance("Creando el usuario de base de datos…")
            clave_bd = crear_usuario_bd(d, self.bd_empresa.get(), self.bd_temp.get())
            self.avance("Guardando la configuración…")
            escribir_env(d, clave_bd, self.bd_empresa.get(), self.bd_temp.get(), puerto, self.clave_nube.get().strip())
            self.avance("Guardando la clave del administrador…"); fijar_clave_admin(self.clave_admin.get())
            self.avance("Abriendo el puerto en el firewall…"); regla_firewall(puerto)
            self.avance("Registrando el arranque con Windows…"); registrar_tarea()
            self.avance("Creando accesos directos…"); accesos_directos(puerto)
            self.avance("Esperando que el agente responda…")
            if not esperar_agente(puerto):
                raise RuntimeError("El agente no respondió. Revise C:\\EasyPos\\AgenteLocal\\logs\\agente.log")
            self.after(0, lambda: self.paso_listo(puerto))
        except Exception as e:
            registrar_log(f"Instalación incompleta: {e}")
            mensaje = (f"No se completó la instalación:\n\n{e}\n\n"         # la variable e no existe fuera del except
                       f"Detalle completo en {DESTINO}\\instalacion.log")
            self.after(0, lambda: messagebox.showerror(TITULO, mensaje))
            self.after(0, lambda: self.botones(self.paso_claves, "Volver"))

    # ── 6. Listo
    def paso_listo(self, puerto: int):
        direccion = f"http://{ip_local()}:{puerto}"
        self.limpiar("¡Listo!", "El agente quedó instalado y arranca solo con Windows. En los celulares, tablets u otros "
                                "PC (conectados al wifi del negocio) abra esta dirección o escanee el código:")
        try:
            import qrcode
            from PIL import ImageTk
            img = qrcode.make(direccion + "/", box_size=6, border=2)
            self.qr = ImageTk.PhotoImage(img)
            ttk.Label(self.marco, image=self.qr).pack(pady=6)
        except Exception:
            pass
        ttk.Label(self.marco, text=direccion, font=("Consolas", 16, "bold"), foreground="#1e3a5f").pack()
        ttk.Label(self.marco, text="En el escritorio quedaron los accesos \"EasyPos Toma de Pedidos\" y "
                                   "\"EasyPos Panel del Agente\".", style="Sub.TLabel", wraplength=600).pack(pady=8)
        self.botones(self.destroy, "Terminar")


def main():
    if not es_admin():
        # Se vuelve a abrir pidiendo permisos de administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)
        return
    Asistente().mainloop()


if __name__ == "__main__":
    main()
