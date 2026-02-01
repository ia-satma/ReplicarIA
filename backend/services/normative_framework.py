"""
============================================================
REVISAR.IA - Marco Normativo con Fundamentación Oficial
============================================================
Catálogo de normas aplicables con URLs oficiales para
trazabilidad en Defense Files y validación legal.

Fuentes oficiales:
- Cámara de Diputados (leyes federales)
- SAT (documentos técnicos, listas, validadores)
- DOF (normas oficiales mexicanas)
- SCJN (jurisprudencia y tesis)
============================================================
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


# ============================================================
# ENUMS
# ============================================================

class TipoNorma(str, Enum):
    """Tipos de normas jurídicas"""
    LEY_FEDERAL = "ley_federal"
    CODIGO = "codigo"
    REGLAMENTO = "reglamento"
    RESOLUCION_MISCELANEA = "rmf"
    NORMA_OFICIAL = "nom"
    JURISPRUDENCIA = "jurisprudencia"
    TESIS_AISLADA = "tesis_aislada"
    CRITERIO_TFJA = "criterio_tfja"


class RamaJuridica(str, Enum):
    """Rama jurídica de la norma"""
    FISCAL = "fiscal"
    COMERCIAL = "comercial"
    LABORAL = "laboral"
    ADMINISTRATIVA = "administrativa"
    PROCESAL = "procesal"


# ============================================================
# MODELOS DE DATOS
# ============================================================

@dataclass
class FundamentoNormativo:
    """Fundamento normativo con URL oficial"""
    id: str
    nombre_corto: str
    nombre_completo: str
    tipo: TipoNorma
    rama: RamaJuridica
    articulos_relevantes: List[str]
    url_oficial: str
    fuente: str
    descripcion: str
    aplicacion_practica: str
    notas_interpretacion: str = ""
    vigente: bool = True
    ultima_reforma: str = ""


@dataclass
class BloqueNormativo:
    """Bloque temático de normas relacionadas"""
    id: str
    nombre: str
    descripcion: str
    fundamentos: List[FundamentoNormativo]
    aplicable_a: List[str]  # tipos de servicio
    notas_sistema: str = ""


# ============================================================
# CATÁLOGO DE FUNDAMENTOS NORMATIVOS
# ============================================================

# --- LISR ---
LISR_27 = FundamentoNormativo(
    id="LISR_27",
    nombre_corto="LISR 27",
    nombre_completo="Ley del Impuesto Sobre la Renta - Artículo 27",
    tipo=TipoNorma.LEY_FEDERAL,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["27", "25", "28", "76"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf",
    fuente="Cámara de Diputados",
    descripcion="Requisitos generales de las deducciones autorizadas para personas morales",
    aplicacion_practica="""
    Las deducciones deben ser:
    - Estrictamente indispensables para la actividad del contribuyente
    - Debidamente registradas en contabilidad
    - Comprobadas con CFDI que reúnan requisitos del CFF
    - Efectivamente erogadas
    """,
    notas_interpretacion="""
    Para marketing: mapear 'estricta indispensabilidad' a vínculo directo con
    generación de ingresos/posicionamiento comercial demostrable.
    Para outsourcing: mapear a necesidad operativa real, no simulación laboral.
    SAT y TFJA exigen conexión funcional demostrable; CFDI y contrato solos son insuficientes.
    """,
    ultima_reforma="2024"
)

LISR_76 = FundamentoNormativo(
    id="LISR_76",
    nombre_corto="LISR 76",
    nombre_completo="Ley del Impuesto Sobre la Renta - Artículo 76",
    tipo=TipoNorma.LEY_FEDERAL,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["76", "179", "180"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf",
    fuente="Cámara de Diputados",
    descripcion="Obligaciones en operaciones con partes relacionadas y precios de transferencia",
    aplicacion_practica="""
    Operaciones entre partes relacionadas requieren:
    - Determinación de precios conforme a métodos establecidos
    - Documentación comprobatoria (estudio de precios de transferencia)
    - Declaraciones informativas adicionales
    """,
    notas_interpretacion="""
    Para servicios intragrupo: exigir siempre estudio de PT o análisis soporte.
    La carga probatoria de mercado recae en el contribuyente.
    """,
    ultima_reforma="2024"
)

# --- CFF ---
CFF_5A = FundamentoNormativo(
    id="CFF_5A",
    nombre_corto="CFF 5-A",
    nombre_completo="Código Fiscal de la Federación - Artículo 5-A",
    tipo=TipoNorma.CODIGO,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["5-A"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
    fuente="Cámara de Diputados",
    descripcion="Razón de negocios como criterio de recaracterización",
    aplicacion_practica="""
    Permite recaracterizar actos jurídicos cuando:
    - El beneficio fiscal es desproporcionado vs el económico
    - No existe razón de negocios válida más allá del ahorro fiscal
    - La operación carece de sustancia económica real
    """,
    notas_interpretacion="""
    Para marketing y outsourcing: exigir análisis costo-beneficio y escenario alternativo.
    El contribuyente debe demostrar que la operación tendría sentido económico
    incluso sin el beneficio fiscal.
    """,
    ultima_reforma="2020"
)

CFF_28_30 = FundamentoNormativo(
    id="CFF_28_30",
    nombre_corto="CFF 28 y 30",
    nombre_completo="Código Fiscal de la Federación - Artículos 28 y 30",
    tipo=TipoNorma.CODIGO,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["28", "30"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
    fuente="Cámara de Diputados",
    descripcion="Obligaciones de contabilidad y conservación de documentación",
    aplicacion_practica="""
    Obligación de:
    - Llevar contabilidad conforme a las disposiciones aplicables
    - Conservar contabilidad y documentación comprobatoria por 5 años
    - Mantener documentación que acredite operaciones
    """,
    notas_interpretacion="""
    La documentación de materialidad (contratos, entregables, comunicaciones)
    debe formar parte de la contabilidad, no ser archivos sueltos.
    """
)

CFF_29_29A = FundamentoNormativo(
    id="CFF_29_29A",
    nombre_corto="CFF 29 y 29-A",
    nombre_completo="Código Fiscal de la Federación - Artículos 29 y 29-A",
    tipo=TipoNorma.CODIGO,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["29", "29-A"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
    fuente="Cámara de Diputados",
    descripcion="Expedición y requisitos de CFDI",
    aplicacion_practica="""
    Establece:
    - Obligación de expedir CFDI por actos o actividades
    - Requisitos esenciales del CFDI (RFC, descripción, importe, impuestos)
    - Efectos de CFDIs que no cumplan requisitos
    """,
    notas_interpretacion="""
    Base legal para las reglas LISR_27_CFDI y ANEXO20_ESTRUCTURA.
    La descripción debe ser específica, no genérica.
    """
)

CFF_69B = FundamentoNormativo(
    id="CFF_69B",
    nombre_corto="CFF 69-B",
    nombre_completo="Código Fiscal de la Federación - Artículo 69-B",
    tipo=TipoNorma.CODIGO,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["69-B", "69-B Bis"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
    fuente="Cámara de Diputados",
    descripcion="Operaciones inexistentes (EFOS/EDOS)",
    aplicacion_practica="""
    Prevé el procedimiento para:
    - Declarar inexistencia de operaciones (EFOS)
    - Tratamiento de quien deduce de EFOS (EDOS)
    - Publicación de listas en portal SAT y DOF
    - Plazos y medios de defensa del contribuyente presunto
    """,
    notas_interpretacion="""
    La ausencia en lista 69-B NO prueba materialidad, pero la presencia
    genera riesgo extremo. El semáforo rojo absoluto está jurídicamente justificado.
    El contribuyente puede acreditar que la operación SÍ existió incluso
    si el proveedor está listado, pero la carga probatoria es muy alta.
    """
)

# --- LIVA ---
LIVA_5 = FundamentoNormativo(
    id="LIVA_5",
    nombre_corto="LIVA 5",
    nombre_completo="Ley del Impuesto al Valor Agregado - Artículo 5",
    tipo=TipoNorma.LEY_FEDERAL,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["5", "5-D"],
    url_oficial="https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf",
    fuente="Cámara de Diputados",
    descripcion="Requisitos para acreditamiento de IVA",
    aplicacion_practica="""
    El acreditamiento requiere:
    - IVA trasladado expresamente y por separado en CFDI
    - IVA efectivamente pagado
    - Gasto estrictamente relacionado con actividades gravadas
    """,
    notas_interpretacion="""
    Un gasto puede ser deducible para ISR pero NO dar acreditamiento de IVA
    si se vincula con actividades exentas. Considerar flag de 'mezcla de actividades'.
    """
)

# --- ANEXO 20 ---
ANEXO_20 = FundamentoNormativo(
    id="ANEXO_20",
    nombre_corto="Anexo 20 RMF",
    nombre_completo="Anexo 20 de la Resolución Miscelánea Fiscal",
    tipo=TipoNorma.RESOLUCION_MISCELANEA,
    rama=RamaJuridica.FISCAL,
    articulos_relevantes=["Anexo 20"],
    url_oficial="https://www.sat.gob.mx/consulta/70515/consulta-los-documentos-tecnicos-del-cfdi",
    fuente="SAT",
    descripcion="Estándar técnico del CFDI",
    aplicacion_practica="""
    Define:
    - Campos obligatorios y opcionales del CFDI
    - Estructura de nodos (emisor, receptor, conceptos, impuestos)
    - Catálogos (claves producto/servicio, unidad, uso CFDI)
    - Complementos aplicables según tipo de operación
    """,
    notas_interpretacion="""
    En marketing: clave de producto/servicio y descripción deben corresponder
    a actividades reales, no genéricas.
    En outsourcing: reflejar si son servicios especializados.
    Marcar inconsistencia cuando la narrativa contractual y la descripción CFDI no coinciden.
    """
)

# --- NOM-151 ---
NOM_151 = FundamentoNormativo(
    id="NOM_151",
    nombre_corto="NOM-151-SCFI-2016",
    nombre_completo="Norma Oficial Mexicana NOM-151-SCFI-2016",
    tipo=TipoNorma.NORMA_OFICIAL,
    rama=RamaJuridica.COMERCIAL,
    articulos_relevantes=["Capítulos 4-8"],
    url_oficial="https://www.dof.gob.mx/nota_detalle.php?codigo=5476969&fecha=30/03/2017",
    fuente="Diario Oficial de la Federación",
    descripcion="Conservación de mensajes de datos y digitalización de documentos",
    aplicacion_practica="""
    Establece requisitos para:
    - Conservación de mensajes de datos
    - Digitalización de documentos
    - Sellos de tiempo y mecanismos de integridad
    - Validez probatoria de documentos electrónicos
    """,
    notas_interpretacion="""
    Refuerza la fuerza probatoria de evidencia electrónica en Defense File.
    Aplicar a: reportes de campañas, logs de sistemas, minutas, entregables digitales.
    No convierte automáticamente cualquier archivo en prueba plena, pero mejora
    significativamente la posición del contribuyente ante cuestionamientos de autenticidad.
    """
)

# --- JURISPRUDENCIA ---
TESIS_2031639 = FundamentoNormativo(
    id="TESIS_2031639",
    nombre_corto="Tesis 2031639",
    nombre_completo="Tesis II.2o.C. J/1 K (12a.) - Registro 2031639",
    tipo=TipoNorma.JURISPRUDENCIA,
    rama=RamaJuridica.PROCESAL,
    articulos_relevantes=["N/A"],
    url_oficial="https://sjf2.scjn.gob.mx/detalle/tesis/2031639",
    fuente="Semanario Judicial de la Federación (SCJN)",
    descripcion="Uso de IA como herramienta auxiliar en procedimientos jurídicos",
    aplicacion_practica="""
    Reconoce que:
    - La IA puede usarse como herramienta auxiliar para organización
    - La decisión final y valoración jurídica debe ser humana
    - El uso de IA no sustituye el juicio profesional
    """,
    notas_interpretacion="""
    Útil para blindar el uso de REVISAR.IA en juicios.
    Documentar que el sistema es auxiliar, no decisor.
    La valoración final la hace el contribuyente/abogado.
    Es argumento de contexto probatorio, no de fondo fiscal.
    """
)


# ============================================================
# RECURSOS SAT PARA VALIDACIÓN
# ============================================================

RECURSOS_SAT = {
    "lista_69b": {
        "nombre": "Lista de contribuyentes Art. 69-B (EFOS)",
        "url": "https://www.sat.gob.mx/consultas/45288/consulta-la-relacion-de-contribuyentes-con-operaciones-presuntamente-inexistentes",
        "fuente": "SAT",
        "descripcion": "Consulta de proveedores en lista de operaciones presuntamente inexistentes",
        "uso_revisar_ia": "Validación obligatoria en regla CFF_69B_PROVEEDOR"
    },
    "validador_cfdi": {
        "nombre": "Validador de CFDI",
        "url": "https://verificacfdi.facturaelectronica.sat.gob.mx/",
        "fuente": "SAT",
        "descripcion": "Verificación de autenticidad y vigencia de CFDI por UUID",
        "uso_revisar_ia": "Validación en reglas LISR_27_CFDI y ANEXO20_ESTRUCTURA"
    },
    "opinion_32d": {
        "nombre": "Opinión de cumplimiento (32-D)",
        "url": "https://www.sat.gob.mx/consultas/20777/consulta-tu-opinion-de-cumplimiento-de-obligaciones-fiscales",
        "fuente": "SAT",
        "descripcion": "Consulta de opinión positiva de cumplimiento fiscal",
        "uso_revisar_ia": "Refuerzo de due diligence en proveedores de alto riesgo"
    },
    "constancia_situacion": {
        "nombre": "Constancia de situación fiscal",
        "url": "https://www.sat.gob.mx/aplicacion/login/53027/genera-tu-constancia-de-situacion-fiscal",
        "fuente": "SAT",
        "descripcion": "Verificación de RFC activo y régimen fiscal del proveedor",
        "uso_revisar_ia": "Validación en CFF_69B_INFRAESTRUCTURA"
    },
    "repse": {
        "nombre": "Registro de Prestadoras de Servicios Especializados",
        "url": "https://repse.stps.gob.mx/",
        "fuente": "STPS",
        "descripcion": "Verificación de registro REPSE para servicios especializados",
        "uso_revisar_ia": "Obligatorio para outsourcing post-reforma 2021"
    }
}


# ============================================================
# BLOQUES NORMATIVOS POR TEMA
# ============================================================

BLOQUES_NORMATIVOS: Dict[str, BloqueNormativo] = {
    "deducibilidad_general": BloqueNormativo(
        id="deducibilidad_general",
        nombre="Deducibilidad General LISR 27",
        descripcion="Requisitos generales para deducciones autorizadas",
        fundamentos=[LISR_27],
        aplicable_a=["todos"],
        notas_sistema="Base para reglas LISR_27_I, LISR_27_III"
    ),
    "contabilidad_cfdi": BloqueNormativo(
        id="contabilidad_cfdi",
        nombre="Contabilidad, CFDI y Requisitos Formales",
        descripcion="Obligaciones de contabilidad y comprobación fiscal",
        fundamentos=[CFF_28_30, CFF_29_29A, ANEXO_20],
        aplicable_a=["todos"],
        notas_sistema="Base para reglas LISR_27_CFDI, ANEXO20_ESTRUCTURA, ANEXO20_DESCRIPCION"
    ),
    "materialidad_efos": BloqueNormativo(
        id="materialidad_efos",
        nombre="Materialidad y Operaciones Inexistentes",
        descripcion="Régimen de EFOS/EDOS y acreditación de materialidad",
        fundamentos=[CFF_69B],
        aplicable_a=["todos", "marketing", "outsourcing"],
        notas_sistema="Base para reglas CFF_69B_PROVEEDOR, CFF_69B_MATERIALIDAD, CFF_69B_INFRAESTRUCTURA"
    ),
    "razon_negocios": BloqueNormativo(
        id="razon_negocios",
        nombre="Razón de Negocios",
        descripcion="Criterio de recaracterización por falta de sustancia económica",
        fundamentos=[CFF_5A],
        aplicable_a=["todos", "marketing", "consultoria", "outsourcing"],
        notas_sistema="Base para regla CFF_5A_RAZON"
    ),
    "acreditamiento_iva": BloqueNormativo(
        id="acreditamiento_iva",
        nombre="Acreditamiento de IVA",
        descripcion="Requisitos para acreditar IVA trasladado",
        fundamentos=[LIVA_5],
        aplicable_a=["todos"],
        notas_sistema="Base para regla LIVA_5_ACREDITAMIENTO"
    ),
    "partes_relacionadas": BloqueNormativo(
        id="partes_relacionadas",
        nombre="Operaciones con Partes Relacionadas",
        descripcion="Precios de transferencia y documentación intragrupo",
        fundamentos=[LISR_76],
        aplicable_a=["partes_relacionadas"],
        notas_sistema="Base para regla LISR_27_PARTES_REL"
    ),
    "evidencia_digital": BloqueNormativo(
        id="evidencia_digital",
        nombre="Evidencia Digital y Conservación",
        descripcion="Valor probatorio de documentos electrónicos",
        fundamentos=[NOM_151],
        aplicable_a=["todos"],
        notas_sistema="Refuerzo probatorio para Defense File"
    ),
    "uso_ia": BloqueNormativo(
        id="uso_ia",
        nombre="Uso de IA como Auxiliar",
        descripcion="Marco jurisprudencial para herramientas de IA",
        fundamentos=[TESIS_2031639],
        aplicable_a=["todos"],
        notas_sistema="Blindaje del uso de REVISAR.IA en contexto procesal"
    )
}


# ============================================================
# FUNCIONES DE CONSULTA
# ============================================================

def obtener_fundamento(id_fundamento: str) -> Optional[FundamentoNormativo]:
    """Obtiene un fundamento normativo por su ID"""
    fundamentos = {
        "LISR_27": LISR_27,
        "LISR_76": LISR_76,
        "CFF_5A": CFF_5A,
        "CFF_28_30": CFF_28_30,
        "CFF_29_29A": CFF_29_29A,
        "CFF_69B": CFF_69B,
        "LIVA_5": LIVA_5,
        "ANEXO_20": ANEXO_20,
        "NOM_151": NOM_151,
        "TESIS_2031639": TESIS_2031639,
    }
    return fundamentos.get(id_fundamento)


def obtener_bloque(id_bloque: str) -> Optional[BloqueNormativo]:
    """Obtiene un bloque normativo por su ID"""
    return BLOQUES_NORMATIVOS.get(id_bloque)


def obtener_fundamentos_por_tipo_servicio(tipo_servicio: str) -> List[FundamentoNormativo]:
    """
    Obtiene los fundamentos normativos aplicables a un tipo de servicio.
    """
    fundamentos = []
    for bloque in BLOQUES_NORMATIVOS.values():
        if "todos" in bloque.aplicable_a or tipo_servicio in bloque.aplicable_a:
            fundamentos.extend(bloque.fundamentos)

    # Eliminar duplicados manteniendo orden
    vistos = set()
    resultado = []
    for f in fundamentos:
        if f.id not in vistos:
            vistos.add(f.id)
            resultado.append(f)

    return resultado


def obtener_url_recurso_sat(recurso: str) -> Optional[Dict[str, str]]:
    """Obtiene información de un recurso SAT"""
    return RECURSOS_SAT.get(recurso)


def generar_fundamentacion_para_regla(regla_id: str) -> Dict[str, Any]:
    """
    Genera la fundamentación normativa completa para una regla del sistema.
    """
    # Mapeo de reglas a fundamentos
    mapeo = {
        "LISR_27_I": ["LISR_27"],
        "LISR_27_III": ["LISR_27", "CFF_28_30"],
        "LISR_27_CFDI": ["LISR_27", "CFF_29_29A", "ANEXO_20"],
        "LISR_27_PARTES_REL": ["LISR_27", "LISR_76"],
        "CFF_69B_PROVEEDOR": ["CFF_69B"],
        "CFF_69B_MATERIALIDAD": ["CFF_69B", "CFF_28_30"],
        "CFF_69B_INFRAESTRUCTURA": ["CFF_69B"],
        "CFF_5A_RAZON": ["CFF_5A"],
        "LIVA_5_ACREDITAMIENTO": ["LIVA_5"],
        "ANEXO20_ESTRUCTURA": ["CFF_29_29A", "ANEXO_20"],
        "ANEXO20_DESCRIPCION": ["ANEXO_20"],
    }

    ids_fundamentos = mapeo.get(regla_id, [])
    fundamentos = [obtener_fundamento(f) for f in ids_fundamentos if obtener_fundamento(f)]

    return {
        "regla_id": regla_id,
        "fundamentos": [
            {
                "id": f.id,
                "nombre": f.nombre_corto,
                "url": f.url_oficial,
                "fuente": f.fuente,
                "articulos": f.articulos_relevantes,
                "descripcion": f.descripcion
            }
            for f in fundamentos
        ],
        "recursos_sat_relacionados": [
            RECURSOS_SAT.get("lista_69b") if "69B" in regla_id else None,
            RECURSOS_SAT.get("validador_cfdi") if "CFDI" in regla_id or "ANEXO" in regla_id else None,
        ]
    }


def generar_disclaimer_legal() -> str:
    """
    Genera el disclaimer legal para Defense Files generados con REVISAR.IA.
    """
    return """
NOTA IMPORTANTE:

Este documento ha sido elaborado con apoyo de REVISAR.IA, un sistema de inteligencia
artificial utilizado como herramienta auxiliar para la organización de hechos, pruebas
y análisis normativo, conforme al criterio establecido en la Tesis II.2o.C. J/1 K (12a.),
Registro 2031639 del Semanario Judicial de la Federación.

La valoración jurídica final, las decisiones estratégicas y la responsabilidad del
contenido corresponden al contribuyente y, en su caso, a su asesor legal.

Los fundamentos normativos citados corresponden a las leyes y disposiciones vigentes
consultadas en fuentes oficiales (Cámara de Diputados, SAT, DOF, SCJN). Se recomienda
verificar la vigencia de las disposiciones a la fecha de presentación del escrito.
"""


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    # Fundamentos individuales
    "LISR_27", "LISR_76", "CFF_5A", "CFF_28_30", "CFF_29_29A",
    "CFF_69B", "LIVA_5", "ANEXO_20", "NOM_151", "TESIS_2031639",
    # Recursos SAT
    "RECURSOS_SAT",
    # Bloques
    "BLOQUES_NORMATIVOS",
    # Funciones
    "obtener_fundamento",
    "obtener_bloque",
    "obtener_fundamentos_por_tipo_servicio",
    "obtener_url_recurso_sat",
    "generar_fundamentacion_para_regla",
    "generar_disclaimer_legal",
]
