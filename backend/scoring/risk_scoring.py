"""
Risk Scoring Matrix para Revisar.IA
Matriz de 12 criterios observables para calcular risk_score objetivo (0-100)
"""

from typing import Dict, Any, Optional, Tuple

RISK_SCORING_MATRIX: Dict[str, Any] = {
    
    "descripcion": "Matriz de 12 criterios observables para calcular risk_score objetivo (0-100). Cada pilar tiene 3 criterios que suman máximo 25 puntos. Más puntos = más riesgo.",
    
    "RAZON_NEGOCIOS": {
        "nombre": "Razón de Negocios (Art. 5-A CFF)",
        "max_puntos": 25,
        "criterios": {
            
            "vinculacion_giro": {
                "nombre": "Vinculación del servicio con el giro del contribuyente",
                "max_puntos": 5,
                "escala": {
                    0: {
                        "descripcion": "Servicio plenamente alineado al giro",
                        "ejemplo": "Desarrollo de software para empresa de TI, estudio de mercado inmobiliario para desarrolladora"
                    },
                    3: {
                        "descripcion": "Alineado de forma genérica",
                        "ejemplo": "Consultoría genérica de gestión, capacitación general"
                    },
                    5: {
                        "descripcion": "Débilmente vinculado o no vinculado",
                        "ejemplo": "Coaching personal, 'estrategias holísticas', servicios sin relación clara con el negocio"
                    }
                }
            },
            
            "objetivo_economico": {
                "nombre": "Existencia de objetivo económico concreto y medible",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Objetivo cuantificable definido",
                        "ejemplo": "Reducir costo logístico 15%, aumentar conversión web 20%, optimizar inventario $X"
                    },
                    5: {
                        "descripcion": "Objetivo descrito pero sin métricas",
                        "ejemplo": "'Mejorar eficiencia', 'optimizar procesos' sin números concretos"
                    },
                    10: {
                        "descripcion": "Objetivo vago o inexistente",
                        "ejemplo": "'Potenciar la marca', 'mejor visibilidad', 'asesoría general'"
                    }
                }
            },
            
            "coherencia_monto": {
                "nombre": "Coherencia del monto vs escala del negocio y beneficio esperado",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Monto razonable",
                        "ejemplo": "Estudio de $1M para empresa de $500M (0.2%), consultoría $500K para problema de $5M"
                    },
                    5: {
                        "descripcion": "Monto alto pero defendible",
                        "ejemplo": "Proyecto representa 2-3% de ventas pero con justificación clara"
                    },
                    10: {
                        "descripcion": "Monto claramente desproporcionado",
                        "ejemplo": "Consultoría de $8M para 'asesoría general', monto > 5% de ventas sin justificación"
                    }
                }
            }
        }
    },
    
    "BENEFICIO_ECONOMICO": {
        "nombre": "Beneficio Económico Esperado (Art. 5-A CFF)",
        "max_puntos": 25,
        "criterios": {
            
            "identificacion_beneficios": {
                "nombre": "Identificación de beneficios económicos específicos",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Beneficios económicos concretos descritos",
                        "ejemplo": "Mayor producción X%, ahorro de costos $Y, acceso a nuevos mercados con proyección $Z"
                    },
                    5: {
                        "descripcion": "Beneficios genéricos",
                        "ejemplo": "'Mejora competitiva', 'eficiencias operativas' sin cuantificar"
                    },
                    10: {
                        "descripcion": "Beneficio económico prácticamente inexistente",
                        "ejemplo": "Solo ahorro fiscal, o ni siquiera eso identificable"
                    }
                }
            },
            
            "modelo_roi": {
                "nombre": "Existencia de modelo de ROI o análisis costo-beneficio",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Hay proyecciones, supuestos y metodología documentada",
                        "ejemplo": "ROI 2.5x basado en: ahorro logístico $X + incremento ventas $Y, con supuestos explícitos"
                    },
                    5: {
                        "descripcion": "Solo narrativa sin cifras",
                        "ejemplo": "'Esperamos recuperar la inversión' sin números"
                    },
                    10: {
                        "descripcion": "Ninguna reflexión explícita del ROI",
                        "ejemplo": "No se menciona retorno ni justificación económica"
                    }
                }
            },
            
            "horizonte_temporal": {
                "nombre": "Horizonte temporal razonable del beneficio",
                "max_puntos": 5,
                "escala": {
                    0: {
                        "descripcion": "Plazo congruente con naturaleza del intangible",
                        "ejemplo": "Estudio de mercado → decisiones en 6-12 meses, implementación ERP → beneficios en 18-24 meses"
                    },
                    3: {
                        "descripcion": "Plazo optimista pero defendible",
                        "ejemplo": "ROI en 6 meses para proyecto que típicamente toma 12"
                    },
                    5: {
                        "descripcion": "Expectativas temporales irreales",
                        "ejemplo": "Beneficios inmediatos para proyectos de largo plazo, o viceversa"
                    }
                }
            }
        }
    },
    
    "MATERIALIDAD": {
        "nombre": "Materialidad (Art. 69-B CFF)",
        "max_puntos": 25,
        "criterios": {
            
            "formalizacion": {
                "nombre": "Contratos/formalización adecuada",
                "max_puntos": 5,
                "escala": {
                    0: {
                        "descripcion": "Contrato firmado con objeto, alcance, entregables, precio y plazos claros",
                        "ejemplo": "Contrato de 15 páginas con anexo técnico detallando entregables específicos"
                    },
                    3: {
                        "descripcion": "Solo orden de servicio o correos formales",
                        "ejemplo": "Correo de aceptación de propuesta, sin contrato formal"
                    },
                    5: {
                        "descripcion": "Ausencia de cualquier formalización",
                        "ejemplo": "Solo existe factura, no hay propuesta ni contrato previo"
                    }
                }
            },
            
            "evidencias_ejecucion": {
                "nombre": "Evidencias de ejecución del servicio",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Entregables claros",
                        "ejemplo": "Reportes, códigos, diseños, estrategias, actas de reuniones, logs de trabajo"
                    },
                    5: {
                        "descripcion": "Evidencias parciales o genéricas",
                        "ejemplo": "Solo presentación final, sin borradores ni registros intermedios"
                    },
                    10: {
                        "descripcion": "Prácticamente sin evidencia material",
                        "ejemplo": "Solo existe la factura, no hay ningún entregable identificable"
                    }
                }
            },
            
            "coherencia_documentos": {
                "nombre": "Coherencia entre CFDI, contrato y entregables",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Conceptos, montos y fechas coinciden razonablemente",
                        "ejemplo": "CFDI dice 'Estudio de mercado NL', contrato dice lo mismo, entregable es eso"
                    },
                    5: {
                        "descripcion": "Inconsistencias menores",
                        "ejemplo": "Fechas desfasadas por días, descripción ligeramente diferente"
                    },
                    10: {
                        "descripcion": "Discrepancias serias",
                        "ejemplo": "CFDI genérico 'servicios profesionales varios' sin correspondencia con contrato"
                    }
                }
            }
        }
    },
    
    "TRAZABILIDAD": {
        "nombre": "Trazabilidad (NOM-151)",
        "max_puntos": 25,
        "criterios": {
            
            "conservacion": {
                "nombre": "Conservación de documentos fuente y respaldos electrónicos",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Expediente digital estructurado con fechas",
                        "ejemplo": "Defense File organizado por fase, todos los docs con versión y fecha"
                    },
                    5: {
                        "descripcion": "Archivos dispersos sin orden",
                        "ejemplo": "Documentos en diferentes carpetas sin nomenclatura consistente"
                    },
                    10: {
                        "descripcion": "Dependencia de correos sueltos sin orden mínimo",
                        "ejemplo": "Solo existen correos con adjuntos, sin expediente consolidado"
                    }
                }
            },
            
            "integridad": {
                "nombre": "Pruebas de integridad y autenticidad",
                "max_puntos": 10,
                "escala": {
                    0: {
                        "descripcion": "Documentos con mecanismos robustos",
                        "ejemplo": "Hash SHA-256 calculado, timestamps verificables, firmas electrónicas"
                    },
                    5: {
                        "descripcion": "Algunos elementos pero no sistemáticos",
                        "ejemplo": "Algunos PDFs con firma, otros sin nada"
                    },
                    10: {
                        "descripcion": "Sin rastro de integridad/autenticidad",
                        "ejemplo": "Solo PDFs editables sin ningún mecanismo de verificación"
                    }
                }
            },
            
            "timeline": {
                "nombre": "Relacionamiento lógico entre documentos (timeline claro)",
                "max_puntos": 5,
                "escala": {
                    0: {
                        "descripcion": "Secuencia reconstruible fácilmente",
                        "ejemplo": "Propuesta → contrato → ejecución → entregables → factura → pago, todo con fechas lógicas"
                    },
                    3: {
                        "descripcion": "Secuencia existe pero con huecos",
                        "ejemplo": "Falta fecha de kick-off, o hay salto de 2 meses sin explicación"
                    },
                    5: {
                        "descripcion": "Secuencia confusa o contradictoria",
                        "ejemplo": "Factura antes de contrato, entregables con fecha posterior al pago"
                    }
                }
            }
        }
    }
}


def calcular_risk_score(evaluacion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula el risk_score objetivo basado en los 12 criterios.
    
    Args:
        evaluacion: Dict con estructura:
            {
                "razon_negocios": {"vinculacion_giro": 0-5, "objetivo_economico": 0-10, "coherencia_monto": 0-10},
                "beneficio_economico": {"identificacion_beneficios": 0-10, "modelo_roi": 0-10, "horizonte_temporal": 0-5},
                "materialidad": {"formalizacion": 0-5, "evidencias_ejecucion": 0-10, "coherencia_documentos": 0-10},
                "trazabilidad": {"conservacion": 0-10, "integridad": 0-10, "timeline": 0-5}
            }
    
    Returns:
        Dict con risk_score_total, desglose por pilar, nivel de riesgo, y explicación
    """
    
    rn = evaluacion.get("razon_negocios", {})
    rn_total = (rn.get("vinculacion_giro", 0) + 
                rn.get("objetivo_economico", 0) + 
                rn.get("coherencia_monto", 0))
    
    be = evaluacion.get("beneficio_economico", {})
    be_total = (be.get("identificacion_beneficios", 0) +
                be.get("modelo_roi", 0) +
                be.get("horizonte_temporal", 0))
    
    mat = evaluacion.get("materialidad", {})
    mat_total = (mat.get("formalizacion", 0) +
                 mat.get("evidencias_ejecucion", 0) +
                 mat.get("coherencia_documentos", 0))
    
    tra = evaluacion.get("trazabilidad", {})
    tra_total = (tra.get("conservacion", 0) +
                 tra.get("integridad", 0) +
                 tra.get("timeline", 0))
    
    def validar_rango(valor: int, max_val: int, nombre: str) -> int:
        if valor < 0 or valor > max_val:
            raise ValueError(f"{nombre} fuera de rango: {valor} (debe ser 0-{max_val})")
        return valor
    
    validar_rango(rn_total, 25, "Razón de negocios")
    validar_rango(be_total, 25, "Beneficio económico")
    validar_rango(mat_total, 25, "Materialidad")
    validar_rango(tra_total, 25, "Trazabilidad")
    
    total = rn_total + be_total + mat_total + tra_total
    
    if total < 40:
        nivel_riesgo = "BAJO"
    elif total < 60:
        nivel_riesgo = "MEDIO"
    elif total < 80:
        nivel_riesgo = "ALTO"
    else:
        nivel_riesgo = "CRITICO"
    
    return {
        "risk_score_total": total,
        "risk_score_razon_negocios": rn_total,
        "risk_score_beneficio_economico": be_total,
        "risk_score_materialidad": mat_total,
        "risk_score_trazabilidad": tra_total,
        "nivel_riesgo": nivel_riesgo,
        "requiere_revision_humana": total >= 60,
        "explicacion": f"""
Risk Score Total: {total}/100 ({nivel_riesgo})

Desglose por pilar:
- Razón de Negocios: {rn_total}/25 {'⚠️' if rn_total > 15 else '✓'}
- Beneficio Económico: {be_total}/25 {'⚠️' if be_total > 15 else '✓'}
- Materialidad: {mat_total}/25 {'⚠️' if mat_total > 15 else '✓'}
- Trazabilidad: {tra_total}/25 {'⚠️' if tra_total > 15 else '✓'}

{'⚠️ REQUIERE REVISIÓN HUMANA OBLIGATORIA' if total >= 60 else '✓ Puede procesarse automáticamente'}
        """.strip()
    }


def get_descripcion_criterio(pilar: str, criterio: str, puntos: int) -> Optional[Dict[str, str]]:
    """
    Obtiene la descripción más cercana al puntaje dado para un criterio.
    
    Args:
        pilar: RAZON_NEGOCIOS, BENEFICIO_ECONOMICO, MATERIALIDAD, TRAZABILIDAD
        criterio: nombre del criterio dentro del pilar
        puntos: puntaje asignado
        
    Returns:
        Dict con descripcion y ejemplo, o None si no se encuentra
    """
    pilar_config = RISK_SCORING_MATRIX.get(pilar)
    if not pilar_config:
        return None
    
    criterio_config = pilar_config.get("criterios", {}).get(criterio)
    if not criterio_config:
        return None
    
    descripcion = None
    puntos_cercanos = -1
    
    for puntos_escala, info in criterio_config.get("escala", {}).items():
        puntos_num = int(puntos_escala)
        if puntos_num <= puntos and puntos_num > puntos_cercanos:
            puntos_cercanos = puntos_num
            descripcion = info
    
    return descripcion


def get_matriz_completa() -> Dict[str, Any]:
    """Retorna la matriz de scoring completa"""
    return RISK_SCORING_MATRIX


def explicar_diferencia_scores(score_alto: int, score_bajo: int, 
                               desglose_alto: Dict[str, int], 
                               desglose_bajo: Dict[str, int]) -> str:
    """
    Explica por qué un proyecto tiene un risk_score mayor que otro.
    
    Args:
        score_alto: Risk score del proyecto con mayor riesgo
        score_bajo: Risk score del proyecto con menor riesgo
        desglose_alto: Desglose por pilar del proyecto de alto riesgo
        desglose_bajo: Desglose por pilar del proyecto de bajo riesgo
        
    Returns:
        Explicación textual de las diferencias
    """
    diferencia_total = score_alto - score_bajo
    
    diferencias = []
    pilares = [
        ("Razón de Negocios", "razon_negocios"),
        ("Beneficio Económico", "beneficio_economico"),
        ("Materialidad", "materialidad"),
        ("Trazabilidad", "trazabilidad")
    ]
    
    for nombre, key in pilares:
        diff = desglose_alto.get(key, 0) - desglose_bajo.get(key, 0)
        if diff > 0:
            diferencias.append(f"- {nombre}: +{diff} puntos de riesgo adicional")
    
    return f"""
El proyecto con score {score_alto} tiene {diferencia_total} puntos más de riesgo que el de score {score_bajo}.

Diferencias por pilar:
{chr(10).join(diferencias) if diferencias else "- Sin diferencias significativas"}

Interpretación:
- Score {score_bajo}: {"BAJO" if score_bajo < 40 else "MEDIO" if score_bajo < 60 else "ALTO" if score_bajo < 80 else "CRÍTICO"} riesgo
- Score {score_alto}: {"BAJO" if score_alto < 40 else "MEDIO" if score_alto < 60 else "ALTO" if score_alto < 80 else "CRÍTICO"} riesgo
    """.strip()
