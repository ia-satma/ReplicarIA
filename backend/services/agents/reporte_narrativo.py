"""
GENERADOR DE REPORTES NARRATIVOS HUMANIZADOS

Transforma datos crudos de los agentes en reportes profesionales
con narrativa, contexto y recomendaciones accionables.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .personas import (
    PersonaProfesional, 
    obtener_persona,
    TonoComunicacion,
    PERSONA_VALIDADOR_DOCUMENTAL,
    PERSONA_AUDITOR_SAT,
    PERSONA_ANALISTA_RIESGO,
    PERSONA_ESPECIALISTA_MATERIALIDAD,
    PERSONA_DEFENSOR_FISCAL
)


class NivelSeveridad(Enum):
    CRITICO = "crítico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"
    INFORMATIVO = "informativo"


@dataclass
class SeccionReporte:
    """Una sección del reporte narrativo"""
    titulo: str
    contenido: str
    nivel_importancia: int = 1
    icono: str = "📋"


class ReporteNarrativo:
    """Genera reportes narrativos humanizados"""
    
    def __init__(self, persona: PersonaProfesional):
        self.persona = persona
        self.secciones: List[SeccionReporte] = []
        self.fecha = datetime.now()
    
    def agregar_seccion(self, seccion: SeccionReporte):
        self.secciones.append(seccion)
    
    def _humanizar_severidad(self, severidad: str) -> str:
        """Convierte severidad técnica a lenguaje profesional"""
        mapeo = {
            'CRITICAL': 'requiere atención inmediata',
            'HIGH': 'representa un riesgo significativo',
            'MEDIUM': 'merece consideración',
            'LOW': 'es un punto menor a monitorear',
            'INFO': 'se documenta para referencia',
        }
        return mapeo.get(severidad.upper(), 'ha sido identificado')
    
    def _humanizar_porcentaje(self, valor: float, contexto: str = "confianza") -> str:
        """Convierte porcentajes a descripciones narrativas"""
        if valor >= 0.95:
            return f"un nivel de {contexto} muy alto ({valor*100:.0f}%)"
        elif valor >= 0.85:
            return f"un nivel de {contexto} alto ({valor*100:.0f}%)"
        elif valor >= 0.70:
            return f"un nivel de {contexto} aceptable ({valor*100:.0f}%)"
        elif valor >= 0.50:
            return f"un nivel de {contexto} que requiere atención ({valor*100:.0f}%)"
        else:
            return f"un nivel de {contexto} insuficiente ({valor*100:.0f}%)"
    
    def _formatear_lista_narrativa(self, items: List[str], max_items: int = 5) -> str:
        """Convierte lista a texto narrativo"""
        if not items:
            return "ninguno identificado"
        
        items = items[:max_items]
        
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} y {items[1]}"
        else:
            return ", ".join(items[:-1]) + f", y {items[-1]}"
    
    def generar_markdown(self) -> str:
        """Genera el reporte completo en formato Markdown"""
        partes = []
        
        partes.append(f"# Reporte de {self.persona.titulo}")
        partes.append(f"**Fecha:** {self.fecha.strftime('%d de %B de %Y, %H:%M hrs')}")
        partes.append(f"**Elaborado por:** {self.persona.nombre}")
        partes.append("")
        partes.append("---")
        partes.append("")
        
        partes.append(self.persona.saludo_formal)
        partes.append("")
        
        secciones_ordenadas = sorted(
            self.secciones, 
            key=lambda s: s.nivel_importancia, 
            reverse=True
        )
        
        for seccion in secciones_ordenadas:
            partes.append(f"## {seccion.icono} {seccion.titulo}")
            partes.append("")
            partes.append(seccion.contenido)
            partes.append("")
        
        partes.append("---")
        partes.append("")
        partes.append(self.persona.generar_cierre())
        
        return "\n".join(partes)
    
    def generar_html(self) -> str:
        """Genera el reporte en formato HTML estilizado"""
        import re
        
        md = self.generar_markdown()
        
        html = md
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'---', r'<hr>', html)
        html = re.sub(r'\n\n', r'</p><p>', html)
        
        return f"""
        <div class="reporte-narrativo" style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6;">
            <style>
                .reporte-narrativo h1 {{ color: #1a365d; border-bottom: 2px solid #3182ce; padding-bottom: 10px; }}
                .reporte-narrativo h2 {{ color: #2c5282; margin-top: 25px; }}
                .reporte-narrativo h3 {{ color: #4a5568; }}
                .reporte-narrativo hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }}
                .reporte-narrativo li {{ margin: 5px 0; }}
                .reporte-narrativo strong {{ color: #2d3748; }}
            </style>
            <p>{html}</p>
        </div>
        """


def generar_reporte_ocr(resultados: Dict[str, Any], proyecto: str) -> str:
    """Genera reporte narrativo para validación OCR"""
    persona = PERSONA_VALIDADOR_DOCUMENTAL
    reporte = ReporteNarrativo(persona)
    
    docs_validados = resultados.get('documentos_validados', [])
    total_docs = resultados.get('total_documentos', len(docs_validados))
    confianza_promedio = resultados.get('confianza_promedio', 0.85)
    
    intro = f"""
{persona.frases_caracteristicas[0]} para el proyecto "{proyecto}", 
he procedido a verificar la integridad y consistencia de {total_docs} documentos 
mediante técnicas de reconocimiento óptico de caracteres (OCR).

El análisis arroja {reporte._humanizar_porcentaje(confianza_promedio, 'confianza')} 
en la extracción de datos clave.
    """.strip()
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Resumen Ejecutivo",
        contenido=intro,
        nivel_importancia=5,
        icono="📊"
    ))
    
    hallazgos = []
    for doc in docs_validados[:5]:
        nombre = doc.get('nombre', 'Documento')
        status = doc.get('status', 'PENDING')
        confianza = doc.get('confianza', 0.8)
        
        if status == 'VALIDATED':
            hallazgos.append(f"- **{nombre}**: Validado satisfactoriamente con {reporte._humanizar_porcentaje(confianza)}")
        else:
            hallazgos.append(f"- **{nombre}**: Requiere revisión adicional")
    
    if hallazgos:
        reporte.agregar_seccion(SeccionReporte(
            titulo="Hallazgos por Documento",
            contenido="\n".join(hallazgos),
            nivel_importancia=4,
            icono="🔍"
        ))
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Recomendaciones",
        contenido=f"""
{persona.frases_caracteristicas[4]} revisar los documentos con nivel de confianza 
inferior al 85% para asegurar la precisión de los datos extraídos.

{persona.frases_caracteristicas[5]} la consistencia entre los montos declarados 
en facturas y los registrados en comprobantes de pago.
        """.strip(),
        nivel_importancia=3,
        icono="💡"
    ))
    
    return reporte.generar_markdown()


def generar_reporte_red_team(resultados: Dict[str, Any], proyecto: str) -> str:
    """Genera reporte narrativo para simulación Red Team"""
    persona = PERSONA_AUDITOR_SAT
    reporte = ReporteNarrativo(persona)
    
    vulnerabilidades = resultados.get('vulnerabilidades', [])
    score = resultados.get('score', 50)
    nivel_riesgo = resultados.get('nivel_riesgo', 'MEDIUM')
    conclusion = resultados.get('conclusion', 'DEFENDIBLE')
    
    intro = f"""
{persona.frases_caracteristicas[0]} he sometido el proyecto "{proyecto}" a una 
simulación exhaustiva de auditoría fiscal, aplicando los criterios y vectores 
de ataque que típicamente emplea la autoridad en sus revisiones.

{persona.frases_caracteristicas[1]} las operaciones con servicios intangibles, 
por lo que este análisis cobra especial relevancia.

**Score de Defensa: {score}/100** - Nivel de riesgo: {nivel_riesgo}
    """.strip()
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Resumen de Simulación",
        contenido=intro,
        nivel_importancia=5,
        icono="🎯"
    ))
    
    if vulnerabilidades:
        vuln_texto = []
        for i, vuln in enumerate(vulnerabilidades[:5], 1):
            severidad = vuln.get('severity', 'MEDIUM')
            mensaje = vuln.get('message', vuln.get('description', 'Vulnerabilidad detectada'))
            recomendacion = vuln.get('recommendation', 'Documentar adecuadamente')
            
            vuln_texto.append(f"""
**{i}. {mensaje}**
- Severidad: {severidad} - {reporte._humanizar_severidad(severidad)}
- {persona.frases_caracteristicas[5]} {recomendacion}
            """.strip())
        
        reporte.agregar_seccion(SeccionReporte(
            titulo="Vulnerabilidades Identificadas",
            contenido="\n\n".join(vuln_texto),
            nivel_importancia=5,
            icono="⚠️"
        ))
    else:
        reporte.agregar_seccion(SeccionReporte(
            titulo="Estado del Expediente",
            contenido=f"""
{persona.frases_caracteristicas[4]} no se identificaron vulnerabilidades críticas 
en la documentación analizada. El expediente presenta una posición defendible 
ante una eventual revisión de la autoridad fiscal.
            """.strip(),
            nivel_importancia=4,
            icono="✅"
        ))
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Conclusión",
        contenido=f"""
**Dictamen: {conclusion}**

{persona.cierre_formal}
        """.strip(),
        nivel_importancia=5,
        icono="📋"
    ))
    
    return reporte.generar_markdown()


def generar_reporte_riesgo(resultados: Dict[str, Any], proyecto: str) -> str:
    """Genera reporte narrativo para análisis de riesgo"""
    persona = PERSONA_ANALISTA_RIESGO
    reporte = ReporteNarrativo(persona)
    
    risk_score = resultados.get('risk_score', 50)
    nivel = resultados.get('nivel', 'MEDIUM')
    factores = resultados.get('factores', [])
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Perfil de Riesgo",
        contenido=f"""
{persona.frases_caracteristicas[0]} un score de **{risk_score}/100**, 
clasificándose como riesgo **{nivel}**.

{persona.frases_caracteristicas[2]}:
- Probabilidad de controversia fiscal: {'Alta' if risk_score > 50 else 'Moderada' if risk_score > 30 else 'Baja'}
- Impacto potencial en caso de rechazo: Significativo
- Tiempo estimado de resolución: {'6-12 meses' if risk_score > 50 else '3-6 meses'}
        """.strip(),
        nivel_importancia=5,
        icono="📈"
    ))
    
    if factores:
        factores_texto = "\n".join([f"- {f}" for f in factores[:5]])
        reporte.agregar_seccion(SeccionReporte(
            titulo="Factores de Riesgo",
            contenido=factores_texto,
            nivel_importancia=4,
            icono="⚡"
        ))
    
    return reporte.generar_markdown()


def generar_reporte_defensa(resultados: Dict[str, Any], proyecto: str) -> str:
    """Genera reporte narrativo para estrategia de defensa"""
    persona = PERSONA_DEFENSOR_FISCAL
    reporte = ReporteNarrativo(persona)
    
    fortalezas = resultados.get('fortalezas', [])
    debilidades = resultados.get('debilidades', [])
    estrategia = resultados.get('estrategia', '')
    
    reporte.agregar_seccion(SeccionReporte(
        titulo="Análisis de Posición",
        contenido=f"""
{persona.frases_caracteristicas[0]} he evaluado la documentación del proyecto 
"{proyecto}" para determinar su solidez ante una eventual controversia fiscal.

{persona.frases_caracteristicas[2]} documentar exhaustivamente la razón de 
negocios y el beneficio económico obtenido.
        """.strip(),
        nivel_importancia=5,
        icono="⚖️"
    ))
    
    if fortalezas:
        reporte.agregar_seccion(SeccionReporte(
            titulo="Fortalezas del Expediente",
            contenido=reporte._formatear_lista_narrativa(fortalezas),
            nivel_importancia=4,
            icono="💪"
        ))
    
    if debilidades:
        reporte.agregar_seccion(SeccionReporte(
            titulo="Áreas de Oportunidad",
            contenido=reporte._formatear_lista_narrativa(debilidades),
            nivel_importancia=4,
            icono="🔧"
        ))
    
    if estrategia:
        reporte.agregar_seccion(SeccionReporte(
            titulo="Estrategia Recomendada",
            contenido=f"{persona.frases_caracteristicas[5]}\n\n{estrategia}",
            nivel_importancia=5,
            icono="🎯"
        ))
    
    return reporte.generar_markdown()
