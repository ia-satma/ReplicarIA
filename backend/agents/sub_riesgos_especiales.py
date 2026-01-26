"""
SUB_RIESGOS_ESPECIALES - Subagente de Detección de Riesgos Especiales

Detecta alertas de riesgo que requieren atención especial: operaciones con 
EFOS potenciales, partes relacionadas sin documentación de TP, posibles 
esquemas reportables, y otras señales de simulación o planeación fiscal agresiva.
"""

from typing import Dict, Any, List

SUB_RIESGOS_ESPECIALES_CONFIG = {
    "id": "SUB_RIESGOS_ESPECIALES",
    "nombre": "Subagente de Detección de Riesgos Especiales",
    
    "rol": """Detectar alertas de riesgo que requieren atención especial: 
    operaciones con EFOS potenciales, partes relacionadas sin documentación de TP, 
    posibles esquemas reportables, y otras señales de simulación o planeación 
    fiscal agresiva.""",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.descripcion",
            "proyecto.monto",
            "proyecto.tipologia",
            "proveedor.rfc",
            "proveedor.tipo_relacion",
            "proveedor.alerta_efos",
            "proveedor.historial_riesgo_score"
        ],
        "deseable": [
            "lista_69b_sat",
            "proyectos_similares_proveedor"
        ]
    },
    
    "fases_participacion": ["F0", "F6"],
    "puede_bloquear_avance": True,
    
    "reglas_deteccion": """
REGLAS PARA DETECTAR RIESGOS ESPECIALES:

RIESGO EFOS:
- Proveedor con alerta_efos = true → ALERTA CRÍTICA
- Proveedor sin empleados visibles + monto alto → ALERTA ALTA
- CFDI genérico + sin entregables → ALERTA ALTA
- RFC en lista 69-B del SAT → RECHAZAR

RIESGO PARTE RELACIONADA:
- tipo_relacion != TERCERO_INDEPENDIENTE → ALERTA
- Sin estudio de TP vigente → BLOQUEO
- Sin análisis de no duplicidad → ALERTA ALTA

RIESGO ESQUEMA REPORTABLE:
- Transferencia de valor a jurisdicción de baja imposición → ALERTA
- Operación que genera beneficio fiscal sin sustancia económica → ALERTA
- Estructuras complejas con múltiples entidades relacionadas → ALERTA

RIESGO TP PENDIENTE:
- Operación intra-grupo > $1M sin estudio de TP → BLOQUEO
- Estudio de TP vencido (> 1 año) → ALERTA ALTA

RIESGO MONTO ALTO:
- Monto > $5M → Revisión humana obligatoria
- Monto > 3% de ingresos anuales → ALERTA MEDIA
    """
}

UMBRAL_MONTO_ALTO = 5000000
UMBRAL_TP_REQUERIDO = 1000000


def detectar_riesgos(
    proyecto: Dict[str, Any],
    proveedor: Dict[str, Any],
    contexto: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Detecta riesgos especiales en un proyecto.
    
    Args:
        proyecto: Datos del proyecto
        proveedor: Datos del proveedor
        contexto: Contexto adicional (estudio_tp, lista_69b, etc.)
    
    Returns:
        Output estructurado con alertas detectadas
    """
    if contexto is None:
        contexto = {}
    
    alertas = []
    condiciones = []
    
    alertas_efos = detectar_riesgo_efos(proveedor, contexto)
    alertas.extend(alertas_efos)
    
    alertas_pr = detectar_riesgo_parte_relacionada(proyecto, proveedor, contexto)
    alertas.extend(alertas_pr)
    
    alertas_er = detectar_riesgo_esquema_reportable(proyecto, proveedor, contexto)
    alertas.extend(alertas_er)
    
    alertas_tp = detectar_riesgo_tp_pendiente(proyecto, proveedor, contexto)
    alertas.extend(alertas_tp)
    
    alertas_monto = detectar_riesgo_monto_alto(proyecto)
    alertas.extend(alertas_monto)
    
    nivel_global = calcular_nivel_global(alertas)
    
    hay_bloqueos = any(a["bloquea_avance"] for a in alertas)
    puede_continuar = not hay_bloqueos
    
    for alerta in alertas:
        if alerta["bloquea_avance"]:
            condiciones.append(alerta["accion_requerida"])
    
    requiere_humano = (
        nivel_global in ["ALTO", "CRITICO"] or
        any(a["severidad"] == "CRITICA" for a in alertas)
    )
    
    recomendacion = generar_recomendacion(alertas, nivel_global, puede_continuar)
    
    return {
        "alertas_detectadas": alertas,
        "nivel_riesgo_global": nivel_global,
        "puede_continuar": puede_continuar,
        "condiciones_para_continuar": condiciones,
        "requiere_revision_humana_inmediata": requiere_humano,
        "recomendacion": recomendacion
    }


def detectar_riesgo_efos(proveedor: Dict[str, Any], contexto: Dict[str, Any]) -> List[Dict]:
    """Detecta riesgos relacionados con EFOS"""
    alertas = []
    
    if proveedor.get("alerta_efos", False):
        alertas.append({
            "tipo_riesgo": "EFOS",
            "severidad": "CRITICA",
            "descripcion": "Proveedor con alerta de EFOS activa",
            "evidencia": f"RFC {proveedor.get('rfc', 'N/A')} marcado en sistema",
            "accion_requerida": "DETENER operación - verificar estatus legal del proveedor",
            "bloquea_avance": True
        })
    
    if proveedor.get("rfc") in contexto.get("lista_69b_sat", []):
        alertas.append({
            "tipo_riesgo": "EFOS",
            "severidad": "CRITICA",
            "descripcion": "RFC en lista 69-B del SAT",
            "evidencia": f"RFC {proveedor.get('rfc')} aparece en lista definitiva",
            "accion_requerida": "RECHAZAR operación - proveedor en lista negra SAT",
            "bloquea_avance": True
        })
    
    if proveedor.get("empleados", 0) == 0 and proveedor.get("historial_riesgo_score", 0) > 50:
        alertas.append({
            "tipo_riesgo": "EFOS",
            "severidad": "ALTA",
            "descripcion": "Proveedor sin empleados visibles y alto riesgo histórico",
            "evidencia": f"0 empleados, risk_score histórico: {proveedor.get('historial_riesgo_score')}",
            "accion_requerida": "Solicitar documentación de capacidad operativa",
            "bloquea_avance": False
        })
    
    return alertas


def detectar_riesgo_parte_relacionada(
    proyecto: Dict[str, Any],
    proveedor: Dict[str, Any],
    contexto: Dict[str, Any]
) -> List[Dict]:
    """Detecta riesgos de partes relacionadas"""
    alertas = []
    tipo_relacion = proveedor.get("tipo_relacion", "TERCERO_INDEPENDIENTE")
    
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        alertas.append({
            "tipo_riesgo": "PARTE_RELACIONADA",
            "severidad": "MEDIA",
            "descripcion": f"Operación con parte relacionada ({tipo_relacion})",
            "evidencia": f"Proveedor clasificado como {tipo_relacion}",
            "accion_requerida": "Verificar estudio de precios de transferencia",
            "bloquea_avance": False
        })
        
        if not contexto.get("estudio_tp_vigente", False):
            monto = proyecto.get("monto", 0)
            if monto >= UMBRAL_TP_REQUERIDO:
                alertas.append({
                    "tipo_riesgo": "PARTE_RELACIONADA",
                    "severidad": "ALTA",
                    "descripcion": "Operación intra-grupo sin estudio de TP vigente",
                    "evidencia": f"Monto ${monto:,} >= ${UMBRAL_TP_REQUERIDO:,} sin TP documentado",
                    "accion_requerida": "Obtener estudio de precios de transferencia antes de continuar",
                    "bloquea_avance": True
                })
        
        if not contexto.get("analisis_no_duplicidad", False):
            alertas.append({
                "tipo_riesgo": "PARTE_RELACIONADA",
                "severidad": "ALTA",
                "descripcion": "Sin análisis de no duplicidad de funciones",
                "evidencia": "No se ha documentado que el servicio no duplica funciones internas",
                "accion_requerida": "Documentar análisis de no duplicidad",
                "bloquea_avance": False
            })
    
    return alertas


def detectar_riesgo_esquema_reportable(
    proyecto: Dict[str, Any],
    proveedor: Dict[str, Any],
    contexto: Dict[str, Any]
) -> List[Dict]:
    """Detecta posibles esquemas reportables"""
    alertas = []
    
    if contexto.get("jurisdiccion_baja_imposicion", False):
        alertas.append({
            "tipo_riesgo": "ESQUEMA_REPORTABLE",
            "severidad": "ALTA",
            "descripcion": "Transferencia de valor a jurisdicción de baja imposición",
            "evidencia": f"Proveedor en jurisdicción: {proveedor.get('jurisdiccion', 'N/A')}",
            "accion_requerida": "Evaluar si constituye esquema reportable ante SAT",
            "bloquea_avance": False
        })
    
    if contexto.get("beneficio_fiscal_sin_sustancia", False):
        alertas.append({
            "tipo_riesgo": "ESQUEMA_REPORTABLE",
            "severidad": "CRITICA",
            "descripcion": "Operación genera beneficio fiscal sin sustancia económica aparente",
            "evidencia": "Análisis indica falta de sustancia económica",
            "accion_requerida": "DETENER - Revisar con área fiscal antes de continuar",
            "bloquea_avance": True
        })
    
    if contexto.get("estructura_compleja_relacionadas", False):
        alertas.append({
            "tipo_riesgo": "ESQUEMA_REPORTABLE",
            "severidad": "MEDIA",
            "descripcion": "Estructura compleja con múltiples entidades relacionadas",
            "evidencia": "Operación involucra más de 2 entidades del grupo",
            "accion_requerida": "Documentar flujo completo y razón de negocios de cada paso",
            "bloquea_avance": False
        })
    
    return alertas


def detectar_riesgo_tp_pendiente(
    proyecto: Dict[str, Any],
    proveedor: Dict[str, Any],
    contexto: Dict[str, Any]
) -> List[Dict]:
    """Detecta riesgos de TP pendiente"""
    alertas = []
    tipo_relacion = proveedor.get("tipo_relacion", "TERCERO_INDEPENDIENTE")
    
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        if contexto.get("estudio_tp_vencido", False):
            alertas.append({
                "tipo_riesgo": "TP_PENDIENTE",
                "severidad": "ALTA",
                "descripcion": "Estudio de precios de transferencia vencido (> 1 año)",
                "evidencia": f"Último estudio: {contexto.get('fecha_ultimo_tp', 'N/A')}",
                "accion_requerida": "Actualizar estudio de TP antes de VBC",
                "bloquea_avance": False
            })
    
    return alertas


def detectar_riesgo_monto_alto(proyecto: Dict[str, Any]) -> List[Dict]:
    """Detecta riesgos por monto alto"""
    alertas = []
    monto = proyecto.get("monto", 0)
    
    if monto >= UMBRAL_MONTO_ALTO:
        alertas.append({
            "tipo_riesgo": "MONTO_ALTO",
            "severidad": "MEDIA",
            "descripcion": f"Monto alto requiere revisión humana",
            "evidencia": f"Monto ${monto:,} >= umbral ${UMBRAL_MONTO_ALTO:,}",
            "accion_requerida": "Obtener aprobación de revisión humana",
            "bloquea_avance": False
        })
    
    return alertas


def calcular_nivel_global(alertas: List[Dict]) -> str:
    """Calcula el nivel de riesgo global basado en las alertas"""
    if not alertas:
        return "BAJO"
    
    severidades = [a["severidad"] for a in alertas]
    
    if "CRITICA" in severidades:
        return "CRITICO"
    elif severidades.count("ALTA") >= 2:
        return "CRITICO"
    elif "ALTA" in severidades:
        return "ALTO"
    elif severidades.count("MEDIA") >= 2:
        return "ALTO"
    elif "MEDIA" in severidades:
        return "MEDIO"
    else:
        return "BAJO"


def generar_recomendacion(alertas: List[Dict], nivel: str, puede_continuar: bool) -> str:
    """Genera recomendación basada en las alertas detectadas"""
    if not alertas:
        return "Sin alertas de riesgo especial. Proyecto puede continuar normalmente."
    
    if nivel == "CRITICO":
        return "RIESGO CRÍTICO: Se requiere intervención inmediata. No proceder hasta resolver bloqueos."
    elif nivel == "ALTO":
        return "RIESGO ALTO: Revisar alertas con área fiscal/legal antes de continuar. Documentar mitigaciones."
    elif nivel == "MEDIO":
        return "RIESGO MEDIO: Monitorear alertas identificadas. Asegurar documentación completa."
    else:
        return "RIESGO BAJO: Continuar con monitoreo estándar."
