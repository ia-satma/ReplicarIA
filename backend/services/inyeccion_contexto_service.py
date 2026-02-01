"""
Servicio que inyecta el contexto completo a los agentes:
1. Contexto Global (normativo, corporativo, POE)
2. Contexto de Tipología (reglas duras, alertas)
3. Contexto Específico del Agente
4. Documentos RAG del Agente (con fallback tenant → template)
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

from services.rag_agente_service import RAGAgenteService
from config.agentes_config import get_agente_config, get_contexto_obligatorio, TipoContexto

logger = logging.getLogger(__name__)


class InyeccionContextoService:
    """Servicio para construir e inyectar contexto completo a agentes"""
    
    def __init__(self):
        self.rag_service = RAGAgenteService()
    
    async def construir_contexto_completo_para_agente(
        self,
        proyecto_id: str,
        agente_id: str,
        fase_actual: str,
        proyecto: Optional[Dict] = None,
        empresa: Optional[Dict] = None
    ) -> dict:
        """
        Construye contexto COMPLETO para un agente específico.
        
        Incluye:
        1. Marco normativo UNIVERSAL
        2. Contexto corporativo del TENANT
        3. Contexto del PROYECTO
        4. Documentos RAG del AGENTE
        5. Configuración específica del agente
        """
        config_agente = get_agente_config(agente_id)
        
        empresa_id = None
        if proyecto:
            empresa_id = proyecto.get("empresa_id")
        if empresa:
            empresa_id = empresa.get("id") or empresa.get("_id")
        
        contexto_normativo = self._get_marco_normativo_universal()
        
        contexto_corporativo = self._construir_contexto_corporativo(empresa)
        
        contexto_proyecto = self._construir_contexto_proyecto(
            proyecto or {},
            config_agente.contexto_requerido
        )
        
        documentos_rag = await self.rag_service.cargar_documentos_para_agente(
            agente_id=agente_id,
            empresa_id=empresa_id
        )
        
        contexto_poe = self._get_contexto_poe(fase_actual)
        
        contexto_obligatorio = get_contexto_obligatorio(agente_id)
        faltantes = self._validar_contexto_obligatorio(
            contexto_obligatorio,
            contexto_corporativo,
            contexto_proyecto
        )
        
        return {
            "agente": {
                "id": agente_id,
                "nombre": config_agente.nombre,
                "rol": config_agente.rol,
                "descripcion": config_agente.descripcion,
                "output_esperado": config_agente.output_fields,
                "puede_bloquear": config_agente.puede_bloquear,
                "fases_bloqueo": config_agente.fases_bloqueo
            },
            "normativo": contexto_normativo,
            "corporativo": contexto_corporativo,
            "proyecto": contexto_proyecto,
            "documentos_referencia": documentos_rag,
            "poe": contexto_poe,
            "fase_actual": fase_actual,
            "contexto_faltante": faltantes,
            "_meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "proyecto_id": proyecto_id,
                "empresa_id": empresa_id
            }
        }
    
    def _get_marco_normativo_universal(self) -> Dict:
        """Retorna el marco normativo universal aplicable a todos los agentes"""
        return {
            "cff_5a": {
                "titulo": "Artículo 5-A CFF - Razón de Negocios",
                "resumen": "Los actos jurídicos sin razón de negocios que generen beneficio fiscal tendrán efectos fiscales de los actos que sí hubieran tenido razón de negocios.",
                "aplicacion": "Evaluar si existe beneficio económico esperado más allá del ahorro fiscal"
            },
            "cff_69b": {
                "titulo": "Artículo 69-B CFF - Operaciones Inexistentes",
                "resumen": "Procedimiento para determinar que un contribuyente emitió comprobantes sin sustento real.",
                "aplicacion": "Verificar materialidad: evidencia de que el servicio realmente se prestó"
            },
            "lisr_27": {
                "titulo": "Artículo 27 LISR - Requisitos de Deducciones",
                "resumen": "Las deducciones deben ser estrictamente indispensables para la actividad del contribuyente.",
                "aplicacion": "Demostrar que el gasto es necesario y proporcional al negocio"
            }
        }
    
    def _construir_contexto_corporativo(self, empresa: Optional[Dict]) -> Dict:
        """Construye contexto corporativo del tenant"""
        if not empresa:
            return {
                "grupo": "Sin configurar",
                "giro_principal": "Sin configurar",
                "mercados_clave": [],
                "vision": None,
                "pilares_estrategicos": [],
                "okrs_vigentes": []
            }
        
        return {
            "grupo": empresa.get("nombre", empresa.get("razon_social", "Sin configurar")),
            "giro_principal": empresa.get("industria", empresa.get("giro", "Sin configurar")),
            "mercados_clave": empresa.get("mercados_clave", []),
            "vision": empresa.get("vision"),
            "mision": empresa.get("mision"),
            "pilares_estrategicos": empresa.get("pilares_estrategicos", []),
            "okrs_vigentes": empresa.get("okrs", []),
            "tipologias_servicio": empresa.get("tipologias_servicio", [])
        }
    
    def _construir_contexto_proyecto(
        self,
        proyecto: Dict,
        contexto_requerido: List
    ) -> Dict:
        """Construye contexto del proyecto según lo que requiere el agente"""
        contexto = {
            "id": proyecto.get("_id") or proyecto.get("id"),
            "nombre": proyecto.get("nombre"),
            "tipologia": proyecto.get("tipologia"),
            "fase_actual": proyecto.get("fase_actual", "F0"),
            "monto": proyecto.get("monto"),
            "proveedor": proyecto.get("proveedor", {}),
            "bee_propuesto": proyecto.get("bee_esperado") or proyecto.get("beneficio_economico"),
            "documentos_cargados": proyecto.get("documentos", []),
            "deliberaciones_previas": proyecto.get("deliberaciones", [])
        }
        
        for req in contexto_requerido:
            campo = req.nombre
            if campo not in contexto:
                valor = proyecto.get(campo)
                if valor is not None:
                    contexto[campo] = valor
        
        return contexto
    
    def _get_contexto_poe(self, fase: str) -> Dict:
        """Retorna el contexto POE para la fase actual"""
        poe_por_fase = {
            "F0": {
                "nombre": "Intake y Clasificación",
                "objetivo": "Recibir proyecto, tipificar servicio, evaluar razón de negocios inicial",
                "agentes_activos": ["A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "S1_TIPIFICACION"],
                "entregables": ["Tipología asignada", "Risk score inicial", "Dictamen F0"]
            },
            "F1": {
                "nombre": "Revisión Contractual",
                "objetivo": "Validar contrato y SOW con cláusulas de materialidad",
                "agentes_activos": ["A2_PMO", "A4_LEGAL"],
                "entregables": ["VBC Legal", "Contrato revisado", "SOW validado"]
            },
            "F2": {
                "nombre": "Evaluación Financiera",
                "objetivo": "Validar presupuesto, ROI y proporcionalidad",
                "agentes_activos": ["A2_PMO", "A5_FINANZAS"],
                "entregables": ["Autorización presupuestal", "Análisis ROI"]
            },
            "F3": {
                "nombre": "Kick-off y Ejecución",
                "objetivo": "Iniciar ejecución y monitorear entregables",
                "agentes_activos": ["A2_PMO", "A6_PROVEEDOR"],
                "entregables": ["Acta de kick-off", "Plan de trabajo"]
            },
            "F4": {
                "nombre": "Seguimiento",
                "objetivo": "Monitorear avance, documentar evidencias",
                "agentes_activos": ["A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A5_FINANZAS", "A6_PROVEEDOR"],
                "entregables": ["Reportes de avance", "Evidencias de ejecución"]
            },
            "F5": {
                "nombre": "Validación de Materialidad",
                "objetivo": "Construir matriz de materialidad hecho-evidencia",
                "agentes_activos": ["A1_ESTRATEGIA", "A2_PMO", "A6_PROVEEDOR", "S2_MATERIALIDAD"],
                "entregables": ["Matriz de materialidad", "Acta de aceptación"]
            },
            "F6": {
                "nombre": "Cierre y VBC",
                "objetivo": "Emitir VBC Fiscal y Legal, consolidar Defense File",
                "agentes_activos": ["A2_PMO", "A3_FISCAL", "A4_LEGAL", "A7_DEFENSA", "S2_MATERIALIDAD", "S3_RIESGOS"],
                "entregables": ["VBC Fiscal", "VBC Legal", "Defense File preliminar"]
            },
            "F7": {
                "nombre": "Refuerzo Probatorio",
                "objetivo": "Fortalecer expediente si hay brechas",
                "agentes_activos": ["A2_PMO", "A7_DEFENSA"],
                "entregables": ["Documentación adicional", "Argumentos reforzados"]
            },
            "F8": {
                "nombre": "Pago y 3-Way Match",
                "objetivo": "Validar conciliación PO-Recepción-Factura",
                "agentes_activos": ["A2_PMO", "A5_FINANZAS"],
                "entregables": ["3-Way Match validado", "Autorización de pago"]
            },
            "F9": {
                "nombre": "Cierre Final",
                "objetivo": "Archivar Defense File completo, lecciones aprendidas",
                "agentes_activos": ["A1_ESTRATEGIA", "A2_PMO", "A7_DEFENSA"],
                "entregables": ["Defense File final", "Índice de defendibilidad"]
            }
        }
        
        return poe_por_fase.get(fase, {
            "nombre": "Fase no definida",
            "objetivo": "",
            "agentes_activos": [],
            "entregables": []
        })
    
    def _validar_contexto_obligatorio(
        self,
        requeridos: List[str],
        corporativo: dict,
        proyecto: dict
    ) -> List[str]:
        """Valida que todo el contexto obligatorio esté presente"""
        contexto_completo = {**corporativo, **proyecto}
        faltantes = []
        
        for req in requeridos:
            if req not in contexto_completo or contexto_completo[req] is None:
                faltantes.append(req)
        
        if faltantes:
            logger.warning(f"Contexto obligatorio faltante: {', '.join(faltantes)}")
        
        return faltantes


def construir_contexto_completo_para_agente(
    agente_id: str,
    proyecto: Dict,
    proveedor: Optional[Dict] = None,
    documentos: Optional[list] = None,
    deliberaciones_previas: Optional[list] = None
) -> Dict:
    """
    Construye el contexto completo que se inyecta al agente.
    Combina: Global + Tipología + Específico del Agente + Datos del Proyecto
    
    NOTA: Esta es la función legacy. Para nuevos usos, usar InyeccionContextoService.
    """
    from context.contexto_global import ContextoGlobalService
    from config.reglas_tipologia import get_reglas_tipologia, get_checklist_obligatorio
    from config.contexto_requerido import get_contexto_requerido
    
    tipologia = proyecto.get("tipologia", "")
    fase_actual = proyecto.get("fase_actual", "F0")
    
    ctx_global = ContextoGlobalService.get_contexto_completo()
    
    ctx_tipologia = get_reglas_tipologia(tipologia)
    
    ctx_agente = get_contexto_requerido(agente_id)
    
    ctx_inyeccion = {}
    if ctx_tipologia:
        ctx_inyeccion = ctx_tipologia.get("contexto_inyeccion_agentes", {}).get(agente_id, {})
    
    contexto_completo = {
        "_meta": {
            "agente_id": agente_id,
            "tipologia": tipologia,
            "fase_actual": fase_actual,
            "timestamp": datetime.utcnow().isoformat()
        },
        
        "contexto_normativo": {
            "cff_5a": _extraer_contenido_normativo(ctx_global, "normativo", "CFF", "articulo_5A"),
            "cff_69b": _extraer_contenido_normativo(ctx_global, "normativo", "CFF", "articulo_69B"),
            "lisr_27": _extraer_contenido_normativo(ctx_global, "normativo", "LISR", "articulo_27")
        },
        
        "contexto_corporativo": {
            "grupo": "Grupo Revisar.IA / Fortezza",
            "giro_principal": "Desarrollo inmobiliario y construcción",
            "mercados_clave": ["Nuevo León", "Nayarit", "Jalisco"],
            "plan_estrategico": "Plan Estratégico 2026 - Revisar.IA"
        },
        
        "tipologia": {
            "id": tipologia,
            "info": ctx_global.get("tipologias", {}).get(tipologia, {}),
            "reglas_auditoria": ctx_tipologia.get("reglas_auditoria_fiscal", []) if ctx_tipologia else [],
            "alertas": ctx_inyeccion.get("alertas_tipologia", [])
        },
        
        "rol_agente": {
            "descripcion": ctx_agente.get("descripcion", ""),
            "contexto_rol": ctx_inyeccion.get("contexto_rol", ""),
            "tarea_actual": ctx_inyeccion.get("tarea_actual", ""),
            "output_esperado": ctx_agente.get("output_esperado", [])
        },
        
        "proyecto": proyecto,
        "proveedor": proveedor or {},
        "documentos_cargados": documentos or [],
        "deliberaciones_previas": deliberaciones_previas or [],
        
        "checklist_fase_actual": get_checklist_obligatorio(tipologia, fase_actual)
    }
    
    logger.info(
        f"Contexto construido para {agente_id} - "
        f"Tipología: {tipologia} - "
        f"Fase: {fase_actual}"
    )
    
    return contexto_completo


def _extraer_contenido_normativo(ctx_global: Dict, categoria: str, ley: str, articulo: str) -> str:
    """Extrae contenido normativo del contexto global"""
    try:
        normativo = ctx_global.get(categoria, {})
        if isinstance(normativo, dict):
            ley_data = normativo.get(ley, {})
            if isinstance(ley_data, dict):
                articulo_data = ley_data.get(articulo, {})
                if isinstance(articulo_data, dict):
                    return articulo_data.get("texto", articulo_data.get("contenido", ""))
        return ""
    except Exception as e:
        logger.warning(f"Error extrayendo contenido normativo {categoria}.{ley}.{articulo}: {e}")
        return ""


def _get_normativo_texto(normativo: Dict, key: str) -> str:
    """Extrae texto normativo manejando tanto formato dict como string"""
    valor = normativo.get(key, 'Ver documentación normativa')
    if isinstance(valor, dict):
        return valor.get('resumen', valor.get('texto', str(valor)))
    return str(valor) if valor else 'Ver documentación normativa'


def generar_system_prompt_con_contexto(agente_id: str, contexto: Dict) -> str:
    """
    Genera el system prompt completo para el agente incluyendo todo el contexto.
    """
    
    rol = contexto.get('rol_agente', contexto.get('agente', {}))
    normativo = contexto.get('contexto_normativo', contexto.get('normativo', {}))
    corporativo = contexto.get('contexto_corporativo', contexto.get('corporativo', {}))
    tipologia = contexto.get('tipologia', {})
    documentos_ref = contexto.get('documentos_referencia', {})
    
    if not isinstance(normativo, dict):
        normativo = {}
    if not isinstance(corporativo, dict):
        corporativo = {}
    if not isinstance(tipologia, dict):
        tipologia = {}
    
    docs_texto = ""
    if documentos_ref and isinstance(documentos_ref, dict):
        docs_texto = "\n\n# DOCUMENTOS DE REFERENCIA\n"
        for doc_id, contenido in documentos_ref.items():
            preview = contenido[:500] + "..." if len(contenido) > 500 else contenido
            docs_texto += f"\n## {doc_id}\n{preview}\n"
    
    prompt = f"""
# ROL
Eres {rol.get('nombre', rol.get('descripcion', 'un agente del sistema')) if isinstance(rol, dict) else 'un agente del sistema'}.
{rol.get('rol', rol.get('contexto_rol', '')) if isinstance(rol, dict) else ''}

# TAREA ACTUAL
{rol.get('descripcion', rol.get('tarea_actual', 'Analizar el proyecto asignado')) if isinstance(rol, dict) else 'Analizar el proyecto asignado'}

# MARCO NORMATIVO APLICABLE
## Artículo 5-A CFF (Razón de Negocios)
{_get_normativo_texto(normativo, 'cff_5a')}

## Artículo 69-B CFF (Operaciones Inexistentes)
{_get_normativo_texto(normativo, 'cff_69b')}

## Artículo 27 LISR (Deducibilidad)
{_get_normativo_texto(normativo, 'lisr_27')}

# CONTEXTO DE LA EMPRESA
- Grupo: {corporativo.get('grupo', 'N/A')}
- Giro: {corporativo.get('giro_principal', 'N/A')}
- Visión: {corporativo.get('vision', 'N/A')}
- Pilares Estratégicos: {', '.join(corporativo.get('pilares_estrategicos', [])) or 'N/A'}

# TIPOLOGÍA DEL PROYECTO: {tipologia.get('id', 'No especificada')}
{tipologia.get('info', {}).get('definicion', '')}

Riesgo Fiscal Inherente: {tipologia.get('info', {}).get('riesgo_fiscal_inherente', 'N/A')}
Foco SAT: {tipologia.get('info', {}).get('foco_5a', '')}

# ALERTAS ESPECÍFICAS PARA ESTA TIPOLOGÍA
{chr(10).join('- ' + a for a in tipologia.get('alertas', [])) or 'Sin alertas específicas'}

# REGLAS DE AUDITORÍA A APLICAR
{_formatear_reglas(tipologia.get('reglas_auditoria', []))}

# CHECKLIST OBLIGATORIO FASE {contexto.get('fase_actual', contexto.get('_meta', {}).get('fase_actual', 'F0'))}
{_formatear_checklist(contexto.get('checklist_fase_actual', contexto.get('poe', {}).get('entregables', [])))}
{docs_texto}

# OUTPUT ESPERADO
Tu respuesta debe incluir: {', '.join(rol.get('output_esperado', []))}
"""
    
    return prompt.strip()


def _formatear_reglas(reglas: list) -> str:
    if not reglas:
        return "Sin reglas específicas adicionales."
    
    lines = []
    for r in reglas:
        if isinstance(r, dict):
            lines.append(f"- {r.get('regla', 'REGLA')}: {r.get('descripcion', '')}")
            lines.append(f"  Acción si incumple: {r.get('accion', 'N/A')}")
        else:
            lines.append(f"- {r}")
    return "\n".join(lines)


def _formatear_checklist(checklist: list) -> str:
    if not checklist:
        return "Sin checklist específico para esta fase."
    
    lines = []
    for item in checklist:
        if isinstance(item, dict):
            obligatorio = "OBLIGATORIO" if item.get("obligatorio") else "Deseable"
            lines.append(f"- [{obligatorio}] {item.get('documento', 'Documento')}")
            lines.append(f"  Criterio: {item.get('criterio_validacion', 'N/A')}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def obtener_contexto_minimo_agente(agente_id: str) -> Dict:
    """Retorna el contexto mínimo requerido para un agente"""
    from config.contexto_requerido import get_contexto_requerido
    
    return get_contexto_requerido(agente_id)


inyeccion_contexto_service = InyeccionContextoService()
