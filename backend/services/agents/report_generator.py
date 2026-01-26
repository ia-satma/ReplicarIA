"""
GENERADOR DE REPORTES HUMANIZADOS

Función principal para transformar datos crudos de cualquier agente
en reportes narrativos profesionales.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .personas import obtener_persona, PersonaProfesional
from .reporte_narrativo import (
    ReporteNarrativo,
    SeccionReporte,
    generar_reporte_ocr,
    generar_reporte_red_team,
    generar_reporte_riesgo,
    generar_reporte_defensa
)


def humanizar_reporte(
    tipo_agente: str,
    datos_crudos: Dict[str, Any],
    contexto: Dict[str, Any] = None,
    formato: str = 'markdown'
) -> Dict[str, Any]:
    """
    Transforma datos crudos en un reporte narrativo humanizado.
    
    Args:
        tipo_agente: Tipo de agente (ocr_validation, red_team, risk, defense, a1-a8)
        datos_crudos: Datos técnicos a humanizar
        contexto: Contexto adicional del proyecto
        formato: 'markdown', 'html', o 'dict'
    
    Returns:
        Dict con reporte_markdown, reporte_html, resumen, y metadata
    """
    contexto = contexto or {}
    proyecto = contexto.get('proyecto', contexto.get('project_name', 'Proyecto'))
    
    persona = obtener_persona(tipo_agente)
    
    # Generar reporte según tipo de agente
    tipo_lower = tipo_agente.lower()
    
    if 'ocr' in tipo_lower or 'validador' in tipo_lower or 'documental' in tipo_lower:
        reporte_md = _generar_reporte_ocr_humanizado(persona, datos_crudos, proyecto)
    elif 'red_team' in tipo_lower or 'sat' in tipo_lower or 'auditor_sat' in tipo_lower:
        reporte_md = _generar_reporte_red_team_humanizado(persona, datos_crudos, proyecto)
    elif 'risk' in tipo_lower or 'riesgo' in tipo_lower:
        reporte_md = _generar_reporte_riesgo_humanizado(persona, datos_crudos, proyecto)
    elif 'defense' in tipo_lower or 'defensa' in tipo_lower:
        reporte_md = _generar_reporte_defensa_humanizado(persona, datos_crudos, proyecto)
    elif tipo_lower.startswith('a') and len(tipo_lower) <= 3:
        reporte_md = _generar_reporte_agente_principal(persona, datos_crudos, proyecto, tipo_lower)
    else:
        reporte_md = _generar_reporte_generico(persona, datos_crudos, proyecto)
    
    # Generar resumen ejecutivo
    resumen = _generar_resumen_ejecutivo(persona, datos_crudos)
    
    # Convertir a HTML si es necesario
    reporte_html = _markdown_a_html(reporte_md) if formato in ['html', 'dict'] else None
    
    resultado = {
        'reporte_markdown': reporte_md,
        'reporte_html': reporte_html,
        'resumen': resumen,
        'metadata': {
            'agente': tipo_agente,
            'persona': persona.nombre,
            'titulo': persona.titulo,
            'generado': datetime.now().isoformat(),
            'proyecto': proyecto
        }
    }
    
    if formato == 'markdown':
        return {'contenido': reporte_md, **resultado}
    elif formato == 'html':
        return {'contenido': reporte_html, **resultado}
    else:
        return resultado


def _generar_reporte_ocr_humanizado(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str
) -> str:
    """Genera reporte humanizado para validación OCR/documental"""
    
    doc_name = datos.get('document_name', 'Documento')
    doc_type = datos.get('document_type', 'documento')
    status = datos.get('status', 'PENDING')
    confidence = datos.get('confidence', 0)
    iterations = datos.get('iterations', 1)
    keywords_found = datos.get('keywords_found', [])
    keywords_missing = datos.get('keywords_missing', [])
    contradictions = datos.get('contradictions', [])
    
    # Humanizar confianza
    if confidence >= 0.95:
        nivel_confianza = "muy alto"
        emoji_status = "✅"
    elif confidence >= 0.85:
        nivel_confianza = "alto"
        emoji_status = "✅"
    elif confidence >= 0.70:
        nivel_confianza = "aceptable"
        emoji_status = "⚠️"
    elif confidence >= 0.50:
        nivel_confianza = "bajo, requiere revisión"
        emoji_status = "⚠️"
    else:
        nivel_confianza = "insuficiente, requiere atención inmediata"
        emoji_status = "❌"
    
    # Construir reporte
    partes = []
    
    partes.append(f"# Reporte de Validación Documental")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## {emoji_status} Resumen de Validación")
    partes.append("")
    partes.append(f"{persona.frases_caracteristicas[0]} del documento **\"{doc_name}\"** "
                  f"(tipo: {doc_type}) para el proyecto \"{proyecto}\".")
    partes.append("")
    partes.append(f"El análisis arroja un nivel de confianza **{nivel_confianza}** "
                  f"({confidence*100:.0f}%), completado en {iterations} iteración(es).")
    partes.append("")
    
    if keywords_found:
        partes.append("### Elementos Identificados")
        partes.append("")
        for kw in keywords_found[:10]:
            partes.append(f"- ✓ {kw}")
        partes.append("")
    
    if keywords_missing:
        partes.append("### Elementos Faltantes")
        partes.append("")
        partes.append(f"{persona.frases_caracteristicas[5]}")
        partes.append("")
        for kw in keywords_missing[:10]:
            partes.append(f"- ○ {kw}")
        partes.append("")
    
    if contradictions:
        partes.append("### Observaciones de Consistencia")
        partes.append("")
        for c in contradictions[:5]:
            partes.append(f"- ⚠️ {c}")
        partes.append("")
    
    partes.append("## 💡 Recomendaciones")
    partes.append("")
    if status == 'VALIDATED':
        partes.append(f"{persona.frases_caracteristicas[4]} proceder con el documento, "
                      "el cual cumple con los requisitos de validación.")
    else:
        partes.append(f"{persona.frases_caracteristicas[4]} revisar los elementos faltantes "
                      "antes de continuar con el proceso.")
    partes.append("")
    
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_reporte_red_team_humanizado(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str
) -> str:
    """Genera reporte humanizado para simulación Red Team/SAT"""
    
    vulnerabilidades = datos.get('vulnerabilidades', datos.get('vulnerabilities', []))
    score = datos.get('score', datos.get('defense_score', 50))
    nivel_riesgo = datos.get('nivel_riesgo', datos.get('risk_level', 'MEDIUM'))
    conclusion = datos.get('conclusion', 'REQUIERE REVISIÓN')
    vectores_testeados = datos.get('vectores_testeados', len(vulnerabilidades) + 3)
    
    # Determinar estado
    if score >= 80:
        estado = "DEFENDIBLE"
        emoji = "🛡️"
    elif score >= 60:
        estado = "DEFENDIBLE CON OBSERVACIONES"
        emoji = "⚠️"
    else:
        estado = "REQUIERE CORRECCIONES URGENTES"
        emoji = "🚨"
    
    partes = []
    
    partes.append(f"# Reporte de Simulación de Auditoría SAT")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## {emoji} Dictamen: {estado}")
    partes.append("")
    partes.append(f"{persona.frases_caracteristicas[0]} he sometido el proyecto \"{proyecto}\" "
                  "a una simulación exhaustiva de auditoría fiscal.")
    partes.append("")
    partes.append(f"**Score de Defensa:** {score}/100")
    partes.append(f"**Nivel de Riesgo:** {nivel_riesgo}")
    partes.append(f"**Vectores Evaluados:** {vectores_testeados}")
    partes.append("")
    
    if vulnerabilidades:
        partes.append("## ⚠️ Vulnerabilidades Identificadas")
        partes.append("")
        partes.append(f"{persona.frases_caracteristicas[1]} los siguientes puntos:")
        partes.append("")
        
        for i, vuln in enumerate(vulnerabilidades[:7], 1):
            sev = vuln.get('severity', 'MEDIUM')
            msg = vuln.get('message', vuln.get('description', 'Vulnerabilidad detectada'))
            rec = vuln.get('recommendation', 'Documentar adecuadamente')
            
            sev_emoji = "🔴" if sev == 'CRITICAL' else "🟠" if sev == 'HIGH' else "🟡" if sev == 'MEDIUM' else "🟢"
            
            partes.append(f"### {i}. {sev_emoji} {msg}")
            partes.append(f"- **Severidad:** {sev}")
            partes.append(f"- **Recomendación:** {rec}")
            partes.append("")
    else:
        partes.append("## ✅ Sin Vulnerabilidades Críticas")
        partes.append("")
        partes.append(f"{persona.frases_caracteristicas[4]} no se identificaron vulnerabilidades "
                      "significativas en la documentación analizada.")
        partes.append("")
    
    partes.append("## 📋 Conclusión")
    partes.append("")
    partes.append(f"{persona.frases_caracteristicas[5]} el expediente ante una eventual revisión.")
    partes.append("")
    
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_reporte_riesgo_humanizado(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str
) -> str:
    """Genera reporte humanizado para análisis de riesgo"""
    
    risk_score = datos.get('risk_score', datos.get('score', 50))
    nivel = datos.get('nivel', datos.get('level', 'MEDIUM'))
    factores = datos.get('factores', datos.get('factors', []))
    
    partes = []
    
    partes.append(f"# Análisis de Perfil de Riesgo")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## 📊 Perfil de Riesgo: {proyecto}")
    partes.append("")
    partes.append(f"{persona.frases_caracteristicas[0]} un score de **{risk_score}/100**, "
                  f"clasificándose como riesgo **{nivel}**.")
    partes.append("")
    
    if factores:
        partes.append("## ⚡ Factores de Riesgo")
        partes.append("")
        for f in factores[:8]:
            partes.append(f"- {f}")
        partes.append("")
    
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_reporte_defensa_humanizado(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str
) -> str:
    """Genera reporte humanizado para estrategia de defensa"""
    
    fortalezas = datos.get('fortalezas', datos.get('strengths', []))
    debilidades = datos.get('debilidades', datos.get('weaknesses', []))
    estrategia = datos.get('estrategia', datos.get('strategy', ''))
    
    partes = []
    
    partes.append(f"# Estrategia de Defensa Fiscal")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## ⚖️ Análisis de Posición: {proyecto}")
    partes.append("")
    partes.append(f"{persona.frases_caracteristicas[0]} he evaluado la documentación del proyecto.")
    partes.append("")
    
    if fortalezas:
        partes.append("### 💪 Fortalezas del Expediente")
        partes.append("")
        for f in fortalezas[:5]:
            partes.append(f"- ✓ {f}")
        partes.append("")
    
    if debilidades:
        partes.append("### 🔧 Áreas de Oportunidad")
        partes.append("")
        for d in debilidades[:5]:
            partes.append(f"- ○ {d}")
        partes.append("")
    
    if estrategia:
        partes.append("### 🎯 Estrategia Recomendada")
        partes.append("")
        partes.append(estrategia)
        partes.append("")
    
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_reporte_agente_principal(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str,
    agente_id: str
) -> str:
    """Genera reporte para agentes principales A1-A8"""
    
    decision = datos.get('decision', datos.get('status', 'pendiente'))
    analisis = datos.get('analisis', datos.get('analysis', ''))
    recomendaciones = datos.get('recomendaciones', datos.get('recommendations', []))
    
    partes = []
    
    partes.append(f"# Deliberación {agente_id.upper()}")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## 📋 Análisis del Proyecto: {proyecto}")
    partes.append("")
    
    if analisis:
        partes.append(analisis)
        partes.append("")
    else:
        partes.append(f"{persona.frases_caracteristicas[0]}")
        partes.append("")
    
    # Decisión
    decision_emoji = "✅" if 'apro' in decision.lower() else "❌" if 'recha' in decision.lower() else "⚠️"
    partes.append(f"## {decision_emoji} Decisión: {decision.upper()}")
    partes.append("")
    
    if recomendaciones:
        partes.append("## 💡 Recomendaciones")
        partes.append("")
        for r in recomendaciones[:5]:
            partes.append(f"- {r}")
        partes.append("")
    
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_reporte_generico(
    persona: PersonaProfesional,
    datos: Dict[str, Any],
    proyecto: str
) -> str:
    """Genera reporte genérico para tipos no especificados"""
    
    partes = []
    
    partes.append(f"# Reporte de {persona.titulo}")
    partes.append(f"**Elaborado por:** {persona.nombre}")
    partes.append(f"**Fecha:** {datetime.now().strftime('%d de %B de %Y, %H:%M hrs')}")
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.saludo_formal)
    partes.append("")
    
    partes.append(f"## 📋 Análisis: {proyecto}")
    partes.append("")
    
    for key, value in datos.items():
        if isinstance(value, (str, int, float, bool)):
            partes.append(f"- **{key}:** {value}")
        elif isinstance(value, list) and len(value) <= 5:
            partes.append(f"- **{key}:** {', '.join(str(v) for v in value)}")
    
    partes.append("")
    partes.append("---")
    partes.append("")
    partes.append(persona.generar_cierre())
    
    return "\n".join(partes)


def _generar_resumen_ejecutivo(persona: PersonaProfesional, datos: Dict[str, Any]) -> str:
    """Genera resumen ejecutivo breve"""
    
    status = datos.get('status', datos.get('decision', 'pendiente'))
    score = datos.get('score', datos.get('confidence', datos.get('risk_score', None)))
    
    resumen = f"{persona.nombre} ({persona.titulo}): "
    
    if score is not None:
        score_val = score * 100 if score <= 1 else score
        resumen += f"Score {score_val:.0f}/100. "
    
    resumen += f"Estado: {status}."
    
    return resumen


def _markdown_a_html(markdown: str) -> str:
    """Convierte markdown básico a HTML"""
    import re
    
    html = markdown
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'---', r'<hr>', html)
    html = html.replace('\n\n', '</p><p>')
    
    return f'<div class="reporte-humanizado"><p>{html}</p></div>'
