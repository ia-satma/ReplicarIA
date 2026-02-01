"""
============================================================
REVISAR.IA - Servicio de Modo Defensa
============================================================
Gestiona el flujo cuando existe un acto de autoridad fiscal.
Reorganiza la información del expediente para defensa.

Basado en:
- LFPCA (Ley Federal de Procedimiento Contencioso Administrativo)
- CFF (Código Fiscal de la Federación) - Parte procesal
- Criterios TFJA y SCJN sobre carga probatoria
============================================================
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from services.legal_validation_service import (
    LegalValidationService,
    TipoServicio,
    TipoActoAutoridad,
    EvaluacionCompleta,
    NivelRiesgo,
    MATRICES_NHP,
    PLANTILLAS_ARGUMENTACION
)

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS ESPECÍFICOS DE MODO DEFENSA
# ============================================================

class EstadoExpedienteDefensa(str, Enum):
    """Estados del expediente en modo defensa"""
    RECIBIDO = "recibido"  # Se recibió notificación
    EN_ANALISIS = "en_analisis"  # Analizando alcance
    RECOPILANDO = "recopilando"  # Recopilando documentos
    ELABORANDO_RESPUESTA = "elaborando_respuesta"  # Preparando escrito
    LISTO_PARA_PRESENTAR = "listo_para_presentar"  # Expediente completo
    PRESENTADO = "presentado"  # Respuesta entregada
    EN_ESPERA_RESOLUCION = "en_espera_resolucion"  # Esperando resolución
    RESUELTO_FAVORABLE = "resuelto_favorable"
    RESUELTO_PARCIAL = "resuelto_parcial"
    RESUELTO_DESFAVORABLE = "resuelto_desfavorable"
    EN_IMPUGNACION = "en_impugnacion"  # Recurso/juicio en curso


class TipoMedioDefensa(str, Enum):
    """Tipos de medios de defensa disponibles"""
    RESPUESTA_REQUERIMIENTO = "respuesta_requerimiento"
    RECURSO_REVOCACION = "recurso_revocacion"
    JUICIO_NULIDAD = "juicio_nulidad"
    ACUERDO_CONCLUSIVO = "acuerdo_conclusivo"
    AUTOCORRECCION = "autocorreccion"


class PrioridadDocumento(str, Enum):
    """Prioridad de documentos en el expediente"""
    CRITICA = "critica"  # Sin esto, defensa falla
    ALTA = "alta"  # Muy importante
    MEDIA = "media"  # Fortalece defensa
    BAJA = "baja"  # Nice to have


# ============================================================
# MODELOS DE DATOS PARA MODO DEFENSA
# ============================================================

@dataclass
class DocumentoExpediente:
    """Documento del expediente de defensa"""
    id: str
    nombre: str
    tipo: str
    prioridad: PrioridadDocumento
    descripcion: str
    fundamento_legal: str
    disponible: bool = False
    fecha_obtencion: Optional[datetime] = None
    ruta_archivo: Optional[str] = None
    notas: str = ""


@dataclass
class OperacionCuestionada:
    """Operación individual cuestionada por la autoridad"""
    operacion_id: str
    proveedor_rfc: str
    proveedor_nombre: str
    monto: float
    tipo_servicio: TipoServicio
    cfdi_folio: str
    fecha_operacion: datetime
    motivo_cuestionamiento: str
    evaluacion: Optional[EvaluacionCompleta] = None
    argumentacion_generada: Optional[str] = None
    documentos_soporte: List[DocumentoExpediente] = field(default_factory=list)


@dataclass
class ExpedienteDefensaCompleto:
    """Expediente completo en modo defensa"""
    id: str
    empresa_id: str
    estado: EstadoExpedienteDefensa

    # Datos del acto de autoridad
    tipo_acto: TipoActoAutoridad
    numero_oficio: str
    fecha_notificacion: datetime
    autoridad_emisora: str
    ejercicio_revisado: int

    # Plazos
    plazo_dias_habiles: int
    fecha_limite: datetime

    # Operaciones
    operaciones_cuestionadas: List[OperacionCuestionada]
    monto_total_cuestionado: float

    # Documentos
    documentos_requeridos: List[DocumentoExpediente]

    # Contenido del Defense File
    narrativa_hechos: str = ""
    argumentacion_juridica: Dict[str, str] = field(default_factory=dict)
    conclusion_operativa: str = ""

    # Estrategia
    medio_defensa_recomendado: TipoMedioDefensa = TipoMedioDefensa.RESPUESTA_REQUERIMIENTO
    probabilidad_exito_estimada: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ============================================================
# PLAZOS PROCESALES POR TIPO DE ACTO
# ============================================================

PLAZOS_PROCESALES: Dict[TipoActoAutoridad, Dict[str, Any]] = {
    TipoActoAutoridad.REVISION_ELECTRONICA: {
        "plazo_respuesta": 15,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 53-B",
        "prorroga_posible": True,
        "dias_prorroga": 10,
        "notas": "Se puede solicitar prórroga por una sola vez"
    },
    TipoActoAutoridad.VISITA_DOMICILIARIA: {
        "plazo_respuesta": 20,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 46",
        "prorroga_posible": True,
        "dias_prorroga": 15,
        "notas": "Plazo para desvirtuar última acta parcial"
    },
    TipoActoAutoridad.REVISION_GABINETE: {
        "plazo_respuesta": 20,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 48",
        "prorroga_posible": True,
        "dias_prorroga": 15,
        "notas": "Mismo tratamiento que visita domiciliaria"
    },
    TipoActoAutoridad.NEGATIVA_DEVOLUCION: {
        "plazo_respuesta": 30,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 22",
        "prorroga_posible": False,
        "dias_prorroga": 0,
        "notas": "Plazo para recurso de revocación"
    },
    TipoActoAutoridad.OFICIO_OBSERVACIONES: {
        "plazo_respuesta": 20,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 48 Frac. VI",
        "prorroga_posible": True,
        "dias_prorroga": 15,
        "notas": "Momento crítico para desvirtuar"
    },
    TipoActoAutoridad.CARTA_INVITACION: {
        "plazo_respuesta": 15,
        "unidad": "dias_habiles",
        "fundamento": "No vinculante legalmente",
        "prorroga_posible": False,
        "dias_prorroga": 0,
        "notas": "Aunque no es obligatoria, conviene atender para evitar escalamiento"
    },
    TipoActoAutoridad.RESOLUCION_PROVISIONAL: {
        "plazo_respuesta": 45,
        "unidad": "dias_habiles",
        "fundamento": "CFF Art. 117",
        "prorroga_posible": False,
        "dias_prorroga": 0,
        "notas": "Plazo para interponer recurso de revocación"
    }
}


# ============================================================
# SERVICIO DE MODO DEFENSA
# ============================================================

class DefenseModeService:
    """
    Servicio especializado para gestionar expedientes en modo defensa.
    Se activa cuando hay un acto de autoridad fiscal.
    """

    def __init__(self):
        self.legal_service = LegalValidationService()

    def crear_expediente_defensa(
        self,
        empresa_id: str,
        tipo_acto: TipoActoAutoridad,
        numero_oficio: str,
        fecha_notificacion: datetime,
        autoridad_emisora: str,
        ejercicio_revisado: int,
        operaciones: List[Dict[str, Any]]
    ) -> ExpedienteDefensaCompleto:
        """
        Crea un nuevo expediente de defensa a partir de un acto de autoridad.
        """
        import uuid

        # Obtener plazos
        plazo_info = PLAZOS_PROCESALES.get(tipo_acto, {
            "plazo_respuesta": 15,
            "unidad": "dias_habiles"
        })
        plazo_dias = plazo_info["plazo_respuesta"]

        # Calcular fecha límite (simplificado - sin días inhábiles)
        fecha_limite = fecha_notificacion + timedelta(days=int(plazo_dias * 1.4))  # Factor para días naturales

        # Convertir operaciones
        operaciones_cuestionadas = []
        monto_total = 0

        for op in operaciones:
            try:
                tipo_servicio = TipoServicio(op.get("tipo_servicio", "servicios_generales"))
            except ValueError:
                tipo_servicio = TipoServicio.SERVICIOS_GENERALES

            monto = float(op.get("monto", 0))
            monto_total += monto

            operacion = OperacionCuestionada(
                operacion_id=op.get("operacion_id", str(uuid.uuid4())),
                proveedor_rfc=op.get("proveedor_rfc", ""),
                proveedor_nombre=op.get("proveedor_nombre", ""),
                monto=monto,
                tipo_servicio=tipo_servicio,
                cfdi_folio=op.get("cfdi_folio", ""),
                fecha_operacion=op.get("fecha_operacion", datetime.now()),
                motivo_cuestionamiento=op.get("motivo_cuestionamiento", "No especificado")
            )
            operaciones_cuestionadas.append(operacion)

        # Generar lista de documentos requeridos
        documentos_requeridos = self._generar_lista_documentos(operaciones_cuestionadas)

        expediente = ExpedienteDefensaCompleto(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            estado=EstadoExpedienteDefensa.RECIBIDO,
            tipo_acto=tipo_acto,
            numero_oficio=numero_oficio,
            fecha_notificacion=fecha_notificacion,
            autoridad_emisora=autoridad_emisora,
            ejercicio_revisado=ejercicio_revisado,
            plazo_dias_habiles=plazo_dias,
            fecha_limite=fecha_limite,
            operaciones_cuestionadas=operaciones_cuestionadas,
            monto_total_cuestionado=monto_total,
            documentos_requeridos=documentos_requeridos
        )

        return expediente

    def _generar_lista_documentos(
        self,
        operaciones: List[OperacionCuestionada]
    ) -> List[DocumentoExpediente]:
        """
        Genera la lista de documentos requeridos basado en las operaciones cuestionadas.
        """
        documentos = []
        tipos_servicio_vistos = set()

        # Documentos base siempre requeridos
        documentos_base = [
            DocumentoExpediente(
                id="DOC_001",
                nombre="Acuse de notificación del acto",
                tipo="acto_autoridad",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion="Acuse de recibo de la notificación del acto de autoridad",
                fundamento_legal="CFF Art. 134-137"
            ),
            DocumentoExpediente(
                id="DOC_002",
                nombre="Poder del representante legal",
                tipo="legitimacion",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion="Poder notarial del representante legal vigente",
                fundamento_legal="CFF Art. 19"
            ),
            DocumentoExpediente(
                id="DOC_003",
                nombre="Identificación oficial del representante",
                tipo="legitimacion",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion="INE vigente del representante legal",
                fundamento_legal="CFF Art. 19"
            ),
            DocumentoExpediente(
                id="DOC_004",
                nombre="Constancia de situación fiscal de la empresa",
                tipo="identificacion",
                prioridad=PrioridadDocumento.ALTA,
                descripcion="CSF actualizada de la contribuyente",
                fundamento_legal="CFF Art. 27"
            ),
        ]
        documentos.extend(documentos_base)

        doc_counter = len(documentos_base) + 1

        # Documentos por cada operación
        for op in operaciones:
            ts = op.tipo_servicio
            if ts not in tipos_servicio_vistos:
                tipos_servicio_vistos.add(ts)

                # Obtener matriz NHP si existe
                matriz = MATRICES_NHP.get(ts)
                if matriz:
                    for elem in matriz.elementos:
                        for prueba in elem.pruebas_primarias:
                            doc = DocumentoExpediente(
                                id=f"DOC_{doc_counter:03d}",
                                nombre=f"{prueba} ({ts.value})",
                                tipo="materialidad",
                                prioridad=PrioridadDocumento.ALTA if "CRÍTICO" in elem.riesgo_si_falta else PrioridadDocumento.MEDIA,
                                descripcion=prueba,
                                fundamento_legal=elem.fundamento_legal
                            )
                            documentos.append(doc)
                            doc_counter += 1

            # Documentos específicos de la operación
            documentos.append(DocumentoExpediente(
                id=f"DOC_{doc_counter:03d}",
                nombre=f"CFDI {op.cfdi_folio}",
                tipo="cfdi",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion=f"CFDI de la operación con {op.proveedor_nombre}",
                fundamento_legal="CFF Art. 29-29A"
            ))
            doc_counter += 1

            documentos.append(DocumentoExpediente(
                id=f"DOC_{doc_counter:03d}",
                nombre=f"Contrato con {op.proveedor_nombre}",
                tipo="contrato",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion=f"Contrato de servicios de {op.tipo_servicio.value}",
                fundamento_legal="LISR Art. 27 Frac. I"
            ))
            doc_counter += 1

            documentos.append(DocumentoExpediente(
                id=f"DOC_{doc_counter:03d}",
                nombre=f"Estado de cuenta - pago a {op.proveedor_nombre}",
                tipo="pago",
                prioridad=PrioridadDocumento.CRITICA,
                descripcion="Estado de cuenta bancario mostrando el pago",
                fundamento_legal="LISR Art. 27 Frac. III"
            ))
            doc_counter += 1

            documentos.append(DocumentoExpediente(
                id=f"DOC_{doc_counter:03d}",
                nombre=f"Consulta 69-B para {op.proveedor_rfc}",
                tipo="due_diligence",
                prioridad=PrioridadDocumento.ALTA,
                descripcion="Consulta de lista 69-B a fecha de operación",
                fundamento_legal="CFF Art. 69-B"
            ))
            doc_counter += 1

        return documentos

    def evaluar_operaciones(
        self,
        expediente: ExpedienteDefensaCompleto
    ) -> ExpedienteDefensaCompleto:
        """
        Evalúa todas las operaciones cuestionadas con el servicio de validación legal.
        Actualiza el expediente con las evaluaciones.
        """
        for operacion in expediente.operaciones_cuestionadas:
            # Simular evidencias presentadas (en producción, vendría de la BD)
            evidencias_presentadas = []

            evaluacion = self.legal_service.validar_operacion(
                operacion_id=operacion.operacion_id,
                proveedor_rfc=operacion.proveedor_rfc,
                monto=operacion.monto,
                tipo_servicio=operacion.tipo_servicio,
                evidencias_presentadas=evidencias_presentadas,
                es_parte_relacionada=False,
                proveedor_en_69b=False,
                cfdi_validado=True,
                tiene_opinion_32d=False
            )

            operacion.evaluacion = evaluacion

        # Calcular probabilidad de éxito
        evaluaciones = [op.evaluacion for op in expediente.operaciones_cuestionadas if op.evaluacion]
        docs_disponibles = [d.nombre for d in expediente.documentos_requeridos if d.disponible]

        prob_result = self.legal_service.calcular_probabilidad_exito(evaluaciones, docs_disponibles)
        expediente.probabilidad_exito_estimada = prob_result["probabilidad_estimada"]

        # Recomendar medio de defensa
        expediente.medio_defensa_recomendado = self._recomendar_medio_defensa(
            expediente.probabilidad_exito_estimada,
            expediente.monto_total_cuestionado,
            expediente.tipo_acto
        )

        expediente.updated_at = datetime.now()
        return expediente

    def _recomendar_medio_defensa(
        self,
        probabilidad_exito: float,
        monto_cuestionado: float,
        tipo_acto: TipoActoAutoridad
    ) -> TipoMedioDefensa:
        """
        Recomienda el medio de defensa más adecuado según las circunstancias.
        """
        # Si es carta invitación, siempre responder
        if tipo_acto == TipoActoAutoridad.CARTA_INVITACION:
            return TipoMedioDefensa.RESPUESTA_REQUERIMIENTO

        # Si probabilidad es muy baja y monto alto, considerar autocorrección
        if probabilidad_exito < 30 and monto_cuestionado > 500000:
            return TipoMedioDefensa.AUTOCORRECCION

        # Si probabilidad es baja pero monto medio, considerar acuerdo conclusivo
        if probabilidad_exito < 50 and monto_cuestionado > 100000:
            return TipoMedioDefensa.ACUERDO_CONCLUSIVO

        # Si es resolución provisional, toca recurso
        if tipo_acto == TipoActoAutoridad.RESOLUCION_PROVISIONAL:
            if probabilidad_exito > 50:
                return TipoMedioDefensa.RECURSO_REVOCACION
            else:
                return TipoMedioDefensa.ACUERDO_CONCLUSIVO

        # Default: responder al requerimiento
        return TipoMedioDefensa.RESPUESTA_REQUERIMIENTO

    def generar_narrativa_hechos(
        self,
        expediente: ExpedienteDefensaCompleto
    ) -> str:
        """
        Genera la narrativa de hechos cronológica para el expediente.
        """
        narrativa_partes = []

        narrativa_partes.append(f"""ANTECEDENTES

Con fecha {expediente.fecha_notificacion.strftime('%d de %B de %Y')}, la {expediente.autoridad_emisora}
notificó a la contribuyente el oficio número {expediente.numero_oficio}, mediante el cual da inicio
a {self._describir_acto(expediente.tipo_acto)} respecto del ejercicio fiscal {expediente.ejercicio_revisado}.

En dicho acto, la autoridad fiscal cuestiona un total de {len(expediente.operaciones_cuestionadas)}
operaciones por un monto agregado de ${expediente.monto_total_cuestionado:,.2f} MXN.
""")

        narrativa_partes.append("\nOPERACIONES CUESTIONADAS\n")

        for i, op in enumerate(expediente.operaciones_cuestionadas, 1):
            narrativa_partes.append(f"""
{i}. Operación con {op.proveedor_nombre} (RFC: {op.proveedor_rfc})
   - Tipo de servicio: {op.tipo_servicio.value}
   - Monto: ${op.monto:,.2f} MXN
   - CFDI: {op.cfdi_folio}
   - Fecha: {op.fecha_operacion.strftime('%d/%m/%Y') if isinstance(op.fecha_operacion, datetime) else 'No especificada'}
   - Motivo de cuestionamiento: {op.motivo_cuestionamiento}
""")

        narrativa_partes.append(f"""
SITUACIÓN ACTUAL

A la fecha del presente escrito, el plazo para dar respuesta vence el
{expediente.fecha_limite.strftime('%d de %B de %Y')} ({expediente.plazo_dias_habiles} días hábiles
desde la notificación).

La contribuyente ha recopilado la documentación soporte de las operaciones cuestionadas y
procede a desvirtuar las observaciones de la autoridad fiscal conforme a los argumentos que
se desarrollan en el presente escrito.
""")

        return "\n".join(narrativa_partes)

    def _describir_acto(self, tipo_acto: TipoActoAutoridad) -> str:
        """Describe el tipo de acto en lenguaje natural"""
        descripciones = {
            TipoActoAutoridad.REVISION_ELECTRONICA: "una revisión electrónica",
            TipoActoAutoridad.VISITA_DOMICILIARIA: "una visita domiciliaria",
            TipoActoAutoridad.REVISION_GABINETE: "una revisión de gabinete",
            TipoActoAutoridad.NEGATIVA_DEVOLUCION: "la negativa de devolución",
            TipoActoAutoridad.OFICIO_OBSERVACIONES: "un oficio de observaciones",
            TipoActoAutoridad.CARTA_INVITACION: "una carta invitación",
            TipoActoAutoridad.RESOLUCION_PROVISIONAL: "una resolución provisional",
        }
        return descripciones.get(tipo_acto, "un procedimiento de fiscalización")

    def generar_argumentacion_completa(
        self,
        expediente: ExpedienteDefensaCompleto,
        datos_adicionales: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Genera toda la argumentación jurídica para el expediente usando las plantillas.
        """
        # Preparar variables base para las plantillas
        variables_base = {
            "año": expediente.ejercicio_revisado,
            "nombre_contribuyente": datos_adicionales.get("nombre_contribuyente", "[NOMBRE EMPRESA]"),
            "rfc_contribuyente": datos_adicionales.get("rfc_contribuyente", "[RFC]"),
        }

        argumentacion = {}

        # Generar argumentación por cada operación
        for i, op in enumerate(expediente.operaciones_cuestionadas, 1):
            variables_op = variables_base.copy()
            variables_op.update({
                "nombre_proveedor": op.proveedor_nombre,
                "rfc_proveedor": op.proveedor_rfc,
                "tipo_servicio": op.tipo_servicio.value,
                "descripcion_servicio": datos_adicionales.get(f"descripcion_{op.operacion_id}", "[DESCRIPCIÓN DEL SERVICIO]"),
                "objetivo_negocio": datos_adicionales.get(f"objetivo_{op.operacion_id}", "[OBJETIVO DE NEGOCIO]"),
                "contexto_estrategico": datos_adicionales.get(f"contexto_{op.operacion_id}", "[CONTEXTO ESTRATÉGICO]"),
                "monto_total": op.monto,
                "monto_iva": op.monto * 0.16,
                "forma_pago": datos_adicionales.get("forma_pago", "transferencia electrónica"),
                "numero_pagos": datos_adicionales.get("numero_pagos", "una"),
                "folios_cfdi": op.cfdi_folio,
            })

            # Generar secciones para esta operación
            for plantilla in PLANTILLAS_ARGUMENTACION:
                seccion_key = f"{plantilla.seccion}_op_{i}"
                texto = self.legal_service.generar_argumentacion(plantilla.seccion, variables_op)
                if texto:
                    argumentacion[seccion_key] = texto
                else:
                    argumentacion[seccion_key] = f"[PENDIENTE: {plantilla.titulo} para operación {i}]"

        expediente.argumentacion_juridica = argumentacion
        return argumentacion

    def generar_conclusion_operativa(
        self,
        expediente: ExpedienteDefensaCompleto
    ) -> str:
        """
        Genera la conclusión operativa con recomendación de acción.
        """
        # Análisis de situación
        evaluaciones = [op.evaluacion for op in expediente.operaciones_cuestionadas if op.evaluacion]

        if not evaluaciones:
            return "No hay evaluaciones disponibles para generar conclusión."

        verdes = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.VERDE)
        amarillas = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.AMARILLO)
        rojas = sum(1 for e in evaluaciones if e.nivel_riesgo == NivelRiesgo.ROJO)
        total = len(evaluaciones)

        conclusion_partes = []

        conclusion_partes.append("CONCLUSIÓN OPERATIVA\n")
        conclusion_partes.append("=" * 50)

        conclusion_partes.append(f"""
ANÁLISIS DE SITUACIÓN:
- Operaciones evaluadas: {total}
- Riesgo bajo (verde): {verdes} ({verdes/total*100:.0f}%)
- Riesgo medio (amarillo): {amarillas} ({amarillas/total*100:.0f}%)
- Riesgo alto (rojo): {rojas} ({rojas/total*100:.0f}%)

Probabilidad de éxito estimada: {expediente.probabilidad_exito_estimada:.0f}%
""")

        # Recomendación
        recomendaciones = {
            TipoMedioDefensa.RESPUESTA_REQUERIMIENTO:
                "Proceder con respuesta al requerimiento, anexando toda la documentación de soporte.",
            TipoMedioDefensa.RECURSO_REVOCACION:
                "Interponer recurso de revocación dentro del plazo legal.",
            TipoMedioDefensa.JUICIO_NULIDAD:
                "Preparar demanda de nulidad ante el TFJA.",
            TipoMedioDefensa.ACUERDO_CONCLUSIVO:
                "Considerar solicitar acuerdo conclusivo ante PRODECON para reducir contingencia.",
            TipoMedioDefensa.AUTOCORRECCION:
                "Evaluar seriamente la autocorrección para minimizar multas y recargos."
        }

        conclusion_partes.append(f"""
MEDIO DE DEFENSA RECOMENDADO: {expediente.medio_defensa_recomendado.value.upper()}

{recomendaciones.get(expediente.medio_defensa_recomendado, "Consultar con abogado fiscalista.")}
""")

        # Acciones inmediatas
        conclusion_partes.append("""
ACCIONES INMEDIATAS:
1. Verificar que todos los documentos del checklist estén disponibles
2. Revisar que los CFDIs estén validados ante SAT
3. Confirmar consultas 69-B de todos los proveedores
4. Preparar el escrito de respuesta/recurso según la plantilla
5. Coordinar con abogado fiscalista para revisión final

ADVERTENCIA: Esta conclusión es un indicador de gestión de riesgo interno.
Consulte siempre con un abogado fiscalista antes de tomar decisiones procesales.
""")

        expediente.conclusion_operativa = "\n".join(conclusion_partes)
        return expediente.conclusion_operativa

    def obtener_resumen_expediente(
        self,
        expediente: ExpedienteDefensaCompleto
    ) -> Dict[str, Any]:
        """
        Genera un resumen ejecutivo del expediente para dashboard.
        """
        docs_listos = sum(1 for d in expediente.documentos_requeridos if d.disponible)
        docs_total = len(expediente.documentos_requeridos)

        dias_restantes = (expediente.fecha_limite - datetime.now()).days

        return {
            "id": expediente.id,
            "estado": expediente.estado.value,
            "tipo_acto": expediente.tipo_acto.value,
            "numero_oficio": expediente.numero_oficio,
            "autoridad": expediente.autoridad_emisora,
            "ejercicio": expediente.ejercicio_revisado,
            "plazos": {
                "fecha_limite": expediente.fecha_limite.isoformat(),
                "dias_restantes": max(0, dias_restantes),
                "urgencia": "CRITICA" if dias_restantes <= 3 else "ALTA" if dias_restantes <= 7 else "MEDIA" if dias_restantes <= 15 else "NORMAL"
            },
            "operaciones": {
                "total": len(expediente.operaciones_cuestionadas),
                "monto_total": expediente.monto_total_cuestionado
            },
            "documentos": {
                "listos": docs_listos,
                "total": docs_total,
                "porcentaje": (docs_listos / docs_total * 100) if docs_total > 0 else 0
            },
            "evaluacion": {
                "probabilidad_exito": expediente.probabilidad_exito_estimada,
                "medio_recomendado": expediente.medio_defensa_recomendado.value
            }
        }


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

defense_mode_service = DefenseModeService()


def get_defense_mode_service() -> DefenseModeService:
    """Obtiene la instancia del servicio de modo defensa"""
    return defense_mode_service
