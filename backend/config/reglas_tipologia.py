"""
REGLAS DURAS POR TIPOLOGÍA
Checklist obligatorio específico que bloquea avance si no se cumple.
"""

from typing import Dict, List

REGLAS_POR_TIPOLOGIA: Dict[str, Dict] = {
    
    "CONSULTORIA_MACRO_ESTRATEGIA": {
        "id": "TYPE_CONSULTORIA_MACRO_ESTRATEGIA",
        "nombre": "Consultoría Macro / Estratégica",
        
        "checklist_obligatorio": {
            "F0": [
                {
                    "documento": "Ficha SIB con BEE",
                    "obligatorio": True,
                    "criterio_validacion": "Debe declarar ROI estimado o impacto en decisión estratégica",
                    "ejemplo_valido": "SIB declara ROI de 15% en proyecto de inversión NL",
                    "ejemplo_invalido": "SIB sin mención de beneficio cuantificable"
                }
            ],
            "F1": [
                {
                    "documento": "SOW / Propuesta",
                    "obligatorio": True,
                    "criterio_validacion": "Debe listar entregables con nombre propio. NO acepta 'Servicios Profesionales'",
                    "ejemplo_valido": "SOW con: Informe de Mercado, Modelo Paramétrico, Manual Metodológico",
                    "ejemplo_invalido": "SOW con 'Servicios profesionales de consultoría'"
                }
            ],
            "F3": [
                {
                    "documento": "Minutas (Kick-off/Avance)",
                    "obligatorio": True,
                    "cantidad_minima": 2,
                    "criterio_validacion": "Mínimo 2 documentos con fecha, asistentes y acuerdos",
                    "ejemplo_valido": "Minuta kick-off 15/ene + Minuta avance 30/ene con lista de asistentes",
                    "ejemplo_invalido": "Solo 1 minuta o minutas sin fecha/asistentes"
                }
            ],
            "F4": [
                {
                    "documento": "Borradores (V0/V1)",
                    "obligatorio": True,
                    "criterio_validacion": "Evidencia de versión preliminar distinta a la final",
                    "ejemplo_valido": "Informe_V1.pdf con marca de agua 'BORRADOR'",
                    "ejemplo_invalido": "Solo versión final sin evidencia de iteración"
                }
            ],
            "F5": [
                {
                    "documento": "Informe Final Integrado",
                    "obligatorio": True,
                    "criterio_validacion": "PDF extenso. Se valida índice, fuentes y fecha",
                    "ejemplo_valido": "Informe 80+ páginas con índice, metodología, fuentes citadas",
                    "ejemplo_invalido": "PDF de 5 páginas sin estructura ni fuentes"
                },
                {
                    "documento": "Herramienta/Modelo",
                    "obligatorio": True,
                    "criticidad": "MAXIMA",
                    "criterio_validacion": "CRÍTICO: Archivo Excel (Modelo Paramétrico) o acceso a Dashboard. Sin esto es riesgo de simulación.",
                    "ejemplo_valido": "Modelo_Parametrico.xlsx con fórmulas activas o Dashboard en Power BI",
                    "ejemplo_invalido": "Solo PDF sin herramienta de trabajo"
                },
                {
                    "documento": "Manual Metodológico",
                    "obligatorio": True,
                    "criterio_validacion": "Explicación técnica de cómo se construyó el análisis",
                    "ejemplo_valido": "Manual con fuentes de datos, metodología de proyección, supuestos",
                    "ejemplo_invalido": "Sin documentación de metodología"
                }
            ],
            "F6": [
                {
                    "documento": "VBC Fiscal",
                    "obligatorio": True,
                    "criterio_validacion": "Dictamen positivo de A3_FISCAL"
                },
                {
                    "documento": "VBC Legal",
                    "obligatorio": True,
                    "criterio_validacion": "Dictamen positivo de A4_LEGAL"
                }
            ],
            "F8": [
                {
                    "documento": "CFDI",
                    "obligatorio": True,
                    "criterio_validacion": "Descripción del CFDI debe coincidir con título del Estudio en SOW",
                    "ejemplo_valido": "CFDI: 'Estudio de Mercado Inmobiliario Nayarit 2026'",
                    "ejemplo_invalido": "CFDI: 'Servicios profesionales varios'"
                },
                {
                    "documento": "Comprobante de pago",
                    "obligatorio": True,
                    "criterio_validacion": "Transferencia bancaria identificable"
                }
            ]
        },
        
        "reglas_auditoria_fiscal": [
            {
                "regla": "REGLA_MODELO_OBLIGATORIO",
                "descripcion": "Si solo hay PDF y monto > $500k, exigir Modelo/Excel fuente",
                "condicion": "monto > 500000 AND NOT existe_modelo_excel",
                "accion": "RECHAZAR",
                "mensaje": "Falta Modelo Paramétrico o herramienta de trabajo. Alto riesgo de simulación."
            },
            {
                "regla": "REGLA_SOW_ESPECIFICO",
                "descripcion": "Si SOW dice 'Asesoría General', RECHAZAR",
                "condicion": "sow_descripcion CONTAINS 'asesoría general' OR 'servicios profesionales'",
                "accion": "RECHAZAR",
                "mensaje": "SOW con descripción genérica. Debe especificar entregables concretos."
            },
            {
                "regla": "REGLA_BEE_VINCULADO",
                "descripcion": "BEE no puede ser genérico",
                "condicion": "bee_descripcion NOT CONTAINS decisión OR inversión OR proyecto",
                "accion": "SOLICITAR_AJUSTES",
                "mensaje": "BEE debe ligarse a una decisión de inversión o proyecto específico."
            }
        ],
        
        "contexto_inyeccion_agentes": {
            "A3_FISCAL": {
                "contexto_rol": "Auditor Fiscal SAT (Enfoque 69-B y 5-A)",
                "tarea_actual": "Validar Materialidad y Razón de Negocios",
                "alertas_tipologia": [
                    "Esta tipología es vulnerable a 69-B si solo hay PDF",
                    "Exigir Modelo/Excel como prueba de know-how",
                    "Verificar que BEE genere decisión de negocio real"
                ]
            },
            "A4_LEGAL": {
                "contexto_rol": "Validador de cumplimiento contractual",
                "tarea_actual": "Verificar que entregables del contrato coincidan con lo recibido",
                "alertas_tipologia": [
                    "Contrato debe listar entregables específicos",
                    "Verificar cláusula de propiedad intelectual del Modelo"
                ]
            }
        }
    },
    
    "INTRAGRUPO_MANAGEMENT_FEE": {
        "id": "TYPE_INTRAGRUPO_MANAGEMENT_FEE",
        "nombre": "Servicios Intragrupo / Management Fee",
        
        "checklist_obligatorio": {
            "F0": [
                {
                    "documento": "Análisis de no duplicidad",
                    "obligatorio": True,
                    "criterio_validacion": "Demostrar que el servicio no se presta internamente"
                }
            ],
            "F1": [
                {
                    "documento": "Estudio de Precios de Transferencia",
                    "obligatorio": True,
                    "criterio_validacion": "Estudio vigente (menos de 1 año) con método arm's length"
                }
            ],
            "F6": [
                {
                    "documento": "Análisis de beneficio real",
                    "obligatorio": True,
                    "criterio_validacion": "Evidencia de que el receptor obtuvo beneficio medible"
                }
            ]
        },
        
        "reglas_auditoria_fiscal": [
            {
                "regla": "REGLA_TP_VIGENTE",
                "descripcion": "Estudio de TP obligatorio y vigente",
                "condicion": "NOT existe_estudio_tp OR estudio_tp_antiguedad > 365",
                "accion": "BLOQUEAR",
                "mensaje": "Operación intragrupo sin estudio de TP vigente. BLOQUEO TOTAL."
            }
        ],
        
        "contexto_inyeccion_agentes": {
            "A3_FISCAL": {
                "contexto_rol": "Auditor de Precios de Transferencia",
                "tarea_actual": "Validar arm's length y beneficio real",
                "alertas_tipologia": [
                    "CRÍTICO: Operación intragrupo requiere escrutinio máximo",
                    "Verificar estudio de TP vigente",
                    "Analizar no duplicidad de servicios"
                ]
            }
        },
        
        "revision_humana_obligatoria": True
    },
    
    "SOFTWARE_SAAS_DESARROLLO": {
        "id": "TYPE_SOFTWARE_SAAS_DESARROLLO",
        "nombre": "Software / SaaS / Desarrollo",
        
        "checklist_obligatorio": {
            "F1": [
                {
                    "documento": "Especificación Técnica",
                    "obligatorio": True,
                    "criterio_validacion": "Documento con funcionalidades, arquitectura, tecnologías"
                }
            ],
            "F4": [
                {
                    "documento": "Evidencia de Desarrollo",
                    "obligatorio": True,
                    "criterio_validacion": "Commits, tickets, sprints o UAT documentado"
                }
            ],
            "F5": [
                {
                    "documento": "Sistema en Producción o Licencias",
                    "obligatorio": True,
                    "criterio_validacion": "Acceso a sistema, licencias SaaS activas, o código fuente"
                },
                {
                    "documento": "Manual de Usuario",
                    "obligatorio": True,
                    "criterio_validacion": "Documentación de uso del sistema"
                }
            ]
        },
        
        "reglas_auditoria_fiscal": [
            {
                "regla": "REGLA_EVIDENCIA_DESARROLLO",
                "descripcion": "Software debe tener evidencia de desarrollo real",
                "condicion": "NOT existe_evidencia_desarrollo",
                "accion": "SOLICITAR_AJUSTES",
                "mensaje": "Falta evidencia de desarrollo (commits, tickets, UAT)."
            }
        ],
        
        "contexto_inyeccion_agentes": {
            "A3_FISCAL": {
                "contexto_rol": "Auditor de Activos Intangibles",
                "tarea_actual": "Validar desarrollo real y uso efectivo",
                "alertas_tipologia": [
                    "Verificar que el software se esté utilizando",
                    "Confirmar que el desarrollo fue real (no solo licencias)"
                ]
            }
        }
    },
    
    "CAPACITACION_FORMACION": {
        "id": "TYPE_CAPACITACION_FORMACION",
        "nombre": "Capacitación / Formación",
        
        "checklist_obligatorio": {
            "F3": [
                {
                    "documento": "Lista de Asistencia",
                    "obligatorio": True,
                    "criterio_validacion": "Lista firmada con nombres y fechas"
                }
            ],
            "F5": [
                {
                    "documento": "Evidencia de Capacitación",
                    "obligatorio": True,
                    "criterio_validacion": "Fotos, evaluaciones, constancias de participación"
                },
                {
                    "documento": "Material Didáctico",
                    "obligatorio": True,
                    "criterio_validacion": "Presentaciones, manuales, o material de apoyo"
                }
            ]
        },
        
        "reglas_auditoria_fiscal": [
            {
                "regla": "REGLA_ASISTENCIA_VERIFICABLE",
                "descripcion": "Capacitación debe tener asistencia verificable",
                "condicion": "NOT existe_lista_asistencia",
                "accion": "RECHAZAR",
                "mensaje": "Falta lista de asistencia firmada."
            }
        ],
        
        "contexto_inyeccion_agentes": {
            "A3_FISCAL": {
                "contexto_rol": "Auditor de Gastos de Capacitación",
                "tarea_actual": "Validar que la capacitación fue real y benefició al personal",
                "alertas_tipologia": [
                    "Verificar que los asistentes sean empleados reales",
                    "Confirmar que el tema de capacitación es relevante al giro"
                ]
            }
        }
    }
}


def get_reglas_tipologia(tipologia_id: str) -> dict:
    """Obtiene las reglas duras para una tipología"""
    return REGLAS_POR_TIPOLOGIA.get(tipologia_id, {})


def get_checklist_obligatorio(tipologia_id: str, fase: str) -> list:
    """Obtiene el checklist obligatorio para una tipología y fase"""
    reglas = get_reglas_tipologia(tipologia_id)
    checklist = reglas.get("checklist_obligatorio", {})
    return checklist.get(fase, [])


def get_reglas_auditoria(tipologia_id: str) -> list:
    """Obtiene las reglas de auditoría fiscal para una tipología"""
    reglas = get_reglas_tipologia(tipologia_id)
    return reglas.get("reglas_auditoria_fiscal", [])


def get_contexto_inyeccion(tipologia_id: str, agente_id: str) -> dict:
    """Obtiene el contexto de inyección para un agente en una tipología"""
    reglas = get_reglas_tipologia(tipologia_id)
    return reglas.get("contexto_inyeccion_agentes", {}).get(agente_id, {})


def validar_checklist_fase(tipologia_id: str, fase: str, documentos_cargados: list) -> dict:
    """
    Valida si se cumplen los documentos obligatorios de una fase.
    
    Returns:
        {
            "cumple": bool,
            "faltantes": list,
            "puede_avanzar": bool
        }
    """
    checklist = get_checklist_obligatorio(tipologia_id, fase)
    
    faltantes = []
    for item in checklist:
        if item.get("obligatorio", False):
            doc_nombre = item["documento"].lower()
            encontrado = any(
                doc_nombre in doc.get("tipo", "").lower() or
                doc_nombre in doc.get("descripcion", "").lower() or
                doc_nombre in doc.get("nombre", "").lower()
                for doc in documentos_cargados
            )
            if not encontrado:
                faltantes.append({
                    "documento": item["documento"],
                    "criterio": item.get("criterio_validacion", ""),
                    "criticidad": item.get("criticidad", "ALTA")
                })
    
    return {
        "cumple": len(faltantes) == 0,
        "faltantes": faltantes,
        "puede_avanzar": len(faltantes) == 0
    }


def listar_tipologias() -> list:
    """Lista todas las tipologías configuradas"""
    return list(REGLAS_POR_TIPOLOGIA.keys())


def requiere_revision_humana(tipologia_id: str) -> bool:
    """Verifica si una tipología requiere revisión humana obligatoria"""
    reglas = get_reglas_tipologia(tipologia_id)
    return reglas.get("revision_humana_obligatoria", False)
