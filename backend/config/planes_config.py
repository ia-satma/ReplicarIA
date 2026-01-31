"""
Configuración centralizada de planes de suscripción.
Define características, límites y precios de cada plan.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class PlanTipo(str, Enum):
    BASICO = "basico"
    PROFESIONAL = "profesional"
    ENTERPRISE = "enterprise"


@dataclass
class PlanConfig:
    """Configuración de un plan de suscripción."""
    id: str
    nombre: str
    descripcion: str
    precio_mensual_mxn: int

    # Límites de uso
    requests_por_dia: int
    tokens_por_dia: int
    documentos_max: int
    usuarios_max: int
    proyectos_max: int

    # Features habilitados
    features: List[str]

    # Características adicionales
    soporte_prioritario: bool = False
    api_acceso: bool = False
    custom_branding: bool = False
    integraciones_externas: bool = False
    reportes_avanzados: bool = False
    agentes_personalizados: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio_mensual_mxn": self.precio_mensual_mxn,
            "limites": {
                "requests_por_dia": self.requests_por_dia,
                "tokens_por_dia": self.tokens_por_dia,
                "documentos_max": self.documentos_max,
                "usuarios_max": self.usuarios_max,
                "proyectos_max": self.proyectos_max
            },
            "features": self.features,
            "caracteristicas": {
                "soporte_prioritario": self.soporte_prioritario,
                "api_acceso": self.api_acceso,
                "custom_branding": self.custom_branding,
                "integraciones_externas": self.integraciones_externas,
                "reportes_avanzados": self.reportes_avanzados,
                "agentes_personalizados": self.agentes_personalizados
            }
        }


# Definición de planes
PLANES: Dict[str, PlanConfig] = {
    "basico": PlanConfig(
        id="basico",
        nombre="Plan Básico",
        descripcion="Ideal para pequeñas empresas que inician con compliance fiscal",
        precio_mensual_mxn=2990,
        requests_por_dia=50,
        tokens_por_dia=100000,
        documentos_max=50,
        usuarios_max=3,
        proyectos_max=10,
        features=[
            "Análisis de documentos fiscales",
            "Validación RFC automática",
            "Clasificación de tipología de servicios",
            "Checklist de documentos requeridos",
            "Dashboard básico",
            "Historial de análisis (30 días)",
            "Soporte por email"
        ],
        soporte_prioritario=False,
        api_acceso=False,
        custom_branding=False,
        integraciones_externas=False,
        reportes_avanzados=False,
        agentes_personalizados=False
    ),

    "profesional": PlanConfig(
        id="profesional",
        nombre="Plan Profesional",
        descripcion="Para empresas medianas con necesidades de compliance avanzado",
        precio_mensual_mxn=7990,
        requests_por_dia=200,
        tokens_por_dia=500000,
        documentos_max=500,
        usuarios_max=10,
        proyectos_max=50,
        features=[
            "Todo lo del Plan Básico",
            "Análisis multi-agente avanzado",
            "Scoring de riesgo fiscal",
            "Generación de expediente de defensa",
            "Deliberación de agentes especializados",
            "Base de conocimiento personalizable",
            "Reportes de cumplimiento",
            "Historial de análisis (1 año)",
            "Soporte prioritario por chat",
            "Capacitación inicial incluida"
        ],
        soporte_prioritario=True,
        api_acceso=False,
        custom_branding=False,
        integraciones_externas=True,
        reportes_avanzados=True,
        agentes_personalizados=False
    ),

    "enterprise": PlanConfig(
        id="enterprise",
        nombre="Plan Enterprise",
        descripcion="Solución completa para grandes corporativos y despachos",
        precio_mensual_mxn=19990,
        requests_por_dia=1000,
        tokens_por_dia=2000000,
        documentos_max=5000,
        usuarios_max=50,
        proyectos_max=500,
        features=[
            "Todo lo del Plan Profesional",
            "API acceso completo",
            "Agentes personalizados por empresa",
            "Integraciones con ERP/SAT",
            "White-label / branding personalizado",
            "Ambiente dedicado",
            "Retención de datos ilimitada",
            "SLA garantizado 99.9%",
            "Gerente de cuenta dedicado",
            "Capacitación continua",
            "Consultoría de implementación"
        ],
        soporte_prioritario=True,
        api_acceso=True,
        custom_branding=True,
        integraciones_externas=True,
        reportes_avanzados=True,
        agentes_personalizados=True
    )
}


def get_plan(plan_id: str) -> PlanConfig:
    """Obtiene la configuración de un plan por su ID."""
    return PLANES.get(plan_id.lower(), PLANES["basico"])


def get_all_planes() -> List[Dict[str, Any]]:
    """Obtiene todos los planes disponibles."""
    return [plan.to_dict() for plan in PLANES.values()]


def check_feature_access(plan_id: str, feature: str) -> bool:
    """Verifica si un plan tiene acceso a una característica."""
    plan = get_plan(plan_id)
    return feature in plan.features or getattr(plan, feature, False)


def get_plan_limits(plan_id: str) -> Dict[str, int]:
    """Obtiene los límites de un plan."""
    plan = get_plan(plan_id)
    return {
        "requests_por_dia": plan.requests_por_dia,
        "tokens_por_dia": plan.tokens_por_dia,
        "documentos_max": plan.documentos_max,
        "usuarios_max": plan.usuarios_max,
        "proyectos_max": plan.proyectos_max
    }


# Comparación de planes para UI
COMPARACION_PLANES = [
    {
        "categoria": "Límites de uso",
        "items": [
            {"nombre": "Requests por día", "basico": "50", "profesional": "200", "enterprise": "1,000"},
            {"nombre": "Tokens por día", "basico": "100K", "profesional": "500K", "enterprise": "2M"},
            {"nombre": "Documentos máximos", "basico": "50", "profesional": "500", "enterprise": "5,000"},
            {"nombre": "Usuarios", "basico": "3", "profesional": "10", "enterprise": "50"},
            {"nombre": "Proyectos", "basico": "10", "profesional": "50", "enterprise": "500"}
        ]
    },
    {
        "categoria": "Análisis y Compliance",
        "items": [
            {"nombre": "Análisis de documentos", "basico": True, "profesional": True, "enterprise": True},
            {"nombre": "Validación RFC", "basico": True, "profesional": True, "enterprise": True},
            {"nombre": "Clasificación tipología", "basico": True, "profesional": True, "enterprise": True},
            {"nombre": "Scoring de riesgo fiscal", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Expediente de defensa", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Deliberación multi-agente", "basico": False, "profesional": True, "enterprise": True}
        ]
    },
    {
        "categoria": "Base de Conocimiento",
        "items": [
            {"nombre": "Documentos de referencia", "basico": True, "profesional": True, "enterprise": True},
            {"nombre": "Base personalizable", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Agentes personalizados", "basico": False, "profesional": False, "enterprise": True}
        ]
    },
    {
        "categoria": "Reportes e Historial",
        "items": [
            {"nombre": "Dashboard", "basico": "Básico", "profesional": "Avanzado", "enterprise": "Completo"},
            {"nombre": "Historial de análisis", "basico": "30 días", "profesional": "1 año", "enterprise": "Ilimitado"},
            {"nombre": "Reportes de cumplimiento", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Exportación a PDF/Excel", "basico": False, "profesional": True, "enterprise": True}
        ]
    },
    {
        "categoria": "Integraciones",
        "items": [
            {"nombre": "API acceso", "basico": False, "profesional": False, "enterprise": True},
            {"nombre": "Integración ERP", "basico": False, "profesional": False, "enterprise": True},
            {"nombre": "Integración SAT", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Webhooks", "basico": False, "profesional": False, "enterprise": True}
        ]
    },
    {
        "categoria": "Soporte",
        "items": [
            {"nombre": "Soporte email", "basico": True, "profesional": True, "enterprise": True},
            {"nombre": "Soporte chat prioritario", "basico": False, "profesional": True, "enterprise": True},
            {"nombre": "Gerente de cuenta", "basico": False, "profesional": False, "enterprise": True},
            {"nombre": "Capacitación", "basico": False, "profesional": "Inicial", "enterprise": "Continua"},
            {"nombre": "SLA garantizado", "basico": False, "profesional": False, "enterprise": "99.9%"}
        ]
    }
]
