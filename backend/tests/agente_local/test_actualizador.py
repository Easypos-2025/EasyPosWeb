"""Actualización del agente instalado (A: botón del panel · B: al abrir turno)."""
import hashlib
import io

import pytest

PAQUETE = b"PK-paquete-de-prueba"
VIG = {"version": "26.10.05-abc1234", "sha256": hashlib.sha256(PAQUETE).hexdigest(), "tamano": len(PAQUETE), "notas": "Mejoras"}


@pytest.fixture
def act(monkeypatch, tmp_path):
    from agente_local import actualizador, config
    monkeypatch.setattr(config, "EMPAQUETADO", True)
    monkeypatch.setattr(actualizador, "DIR", tmp_path)
    for k in ("descargada", "vigente", "ultimo", "reportar", "error"):
        actualizador.estado[k] = None
    actualizador.estado.update(descargando=False, aplicando=False)
    return actualizador


def test_desarrollo_nunca_se_actualiza(monkeypatch):
    from agente_local import actualizador, config
    monkeypatch.setattr(config, "EMPAQUETADO", False)
    actualizador.estado["vigente"] = VIG
    assert actualizador.disponible() is False


def test_misma_version_no_es_actualizacion(act, monkeypatch):
    monkeypatch.setattr(act, "VERSION", VIG["version"])
    act.estado["vigente"] = VIG
    assert act.disponible() is False


def test_descarga_verifica_huella(act, monkeypatch, tmp_path):
    act.estado["vigente"] = VIG
    monkeypatch.setattr(act.urllib.request, "urlopen", lambda req, timeout=60: io.BytesIO(PAQUETE))
    act._descargar(VIG)
    assert (tmp_path / f"agente-{VIG['version']}.zip").read_bytes() == PAQUETE
    # Paquete alterado: se descarta
    malo = {**VIG, "version": "26.10.06-def5678"}
    monkeypatch.setattr(act.urllib.request, "urlopen", lambda req, timeout=60: io.BytesIO(b"PK-alterado-xxxxxx"))
    with pytest.raises(ValueError, match="huella"):
        act._descargar(malo)
    assert not (tmp_path / "agente-26.10.06-def5678.zip").exists()


def test_descarga_mas_grande_de_lo_informado(act, monkeypatch):
    grande = {**VIG, "tamano": 10}
    monkeypatch.setattr(act.urllib.request, "urlopen", lambda req, timeout=60: io.BytesIO(b"x" * (2 * 1024 * 1024)))
    with pytest.raises(ValueError, match="grande"):
        act._descargar(grande)


def test_aplicar_crea_tarea_y_script(act, monkeypatch, tmp_path):
    llamadas = []

    class R:
        returncode, stdout, stderr = 0, "", ""
    monkeypatch.setattr(act.subprocess, "run", lambda args, **k: llamadas.append(args) or R())
    act.estado["vigente"] = VIG
    with pytest.raises(RuntimeError):
        act.aplicar("prueba")                                  # sin descargar: no aplica
    act.estado["descargada"] = VIG["version"]
    act.aplicar("prueba")
    assert llamadas[0][:3] == ["schtasks", "/Create", "/TN"] and llamadas[1][:2] == ["schtasks", "/Run"]
    script = (tmp_path / "actualizar.ps1").read_text(encoding="utf-8-sig")
    assert VIG["version"] in script and "REVERTIDO" in script and "Expand-Archive" in script
    assert "powershell.exe" in (tmp_path / "actualizar.xml").read_text(encoding="utf-16")
    with pytest.raises(RuntimeError):
        act.aplicar("otra vez")                                # ya se está aplicando


def test_abrir_turno(act, monkeypatch):
    aplicadas = []
    monkeypatch.setattr(act, "aplicar", lambda motivo: aplicadas.append(motivo))
    act.estado["vigente"] = VIG
    assert act.al_abrir_turno(0) is False                      # aún no descargada
    act.estado["descargada"] = VIG["version"]
    assert act.al_abrir_turno(3) is False                      # hay pedidos abiertos: espera
    assert act.al_abrir_turno(0) is True and aplicadas == ["apertura de turno"]


def test_resultado_escrito_despues_de_arrancar(act, tmp_path, monkeypatch):
    """El script escribe el resultado cuando el agente nuevo ya arrancó: se detecta en el ciclo."""
    import asyncio
    registrados = []

    async def registrar(**k):
        registrados.append(k)
    from agente_local import errores
    monkeypatch.setattr(errores, "registrar", registrar)
    asyncio.run(act.revisar_resultado())                        # aún no hay resultado
    assert act.estado["reportar"] is None
    (tmp_path / "resultado.json").write_text('{"estado": "OK", "desde": "a", "hacia": "b"}', encoding="utf-8-sig")
    asyncio.run(act.revisar_resultado())
    assert act.estado["reportar"].startswith("OK a → b") and registrados == []
    (tmp_path / "resultado.json").write_text('{"estado": "REVERTIDO", "desde": "b", "hacia": "c"}', encoding="utf-8-sig")
    asyncio.run(act.revisar_resultado())
    assert registrados and registrados[0]["nivel"] == "CRITICO"


def test_resultado_de_la_actualizacion(act, tmp_path):
    (tmp_path / "resultado.json").write_text('{"estado": "REVERTIDO", "desde": "a", "hacia": "b", "mensaje": "no respondió"}',
                                              encoding="utf-8-sig")
    act.leer_resultado()
    assert act.estado["ultimo"]["estado"] == "REVERTIDO" and "REVERTIDO a → b" in act.estado["reportar"]
    assert (tmp_path / "resultado_reportado.json").exists() and not (tmp_path / "resultado.json").exists()


def test_forzada_desde_la_nube(act, monkeypatch):
    """Opción C: la nube pide forzar; se aplica solo con la versión vigente ya descargada y verificada."""
    aplicadas = []
    monkeypatch.setattr(act, "aplicar", lambda motivo: aplicadas.append(motivo))
    act.estado.update(vigente=VIG, forzar=True)
    assert act.forzada() is False and aplicadas == []                # aún no descargada
    act.estado["descargada"] = VIG["version"]
    assert act.forzada() is True and aplicadas == ["forzada desde la nube"]
    act.estado.update(forzar=False, aplicando=False)
    assert act.forzada() is False                                    # sin pedido de la nube no se fuerza


def test_sin_uso_espera_version_lista(act, monkeypatch):
    """Opción D: sin versión lista no consulta nada ni aplica."""
    import asyncio
    aplicadas = []
    monkeypatch.setattr(act, "aplicar", lambda motivo: aplicadas.append(motivo))
    act.estado.update(vigente=VIG, descargada=None, forzar=False)
    assert asyncio.run(act.sin_uso()) is False and aplicadas == []
