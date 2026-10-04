"""
Agente Local EasyPos
====================
Servicio que corre en el PC del negocio (donde están la BD de la empresa y `datatemppos`)
y atiende la toma de pedidos desde celulares, tablets o PC de la red local.

Reemplaza la API PHP `/easypos/public/api`. Es independiente del backend de la nube
(no importa nada de `app/`): las tablas del escritorio no tienen `company_id`.
"""

VERSION = "0.1.0"
