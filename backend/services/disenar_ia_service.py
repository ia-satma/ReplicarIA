"""
DISEÑAR.IA - Guardián Autónomo de Diseño UI
Sistema de auditoría de interfaz de usuario con detección de inconsistencias
y sugerencias de mejora basadas en mejores prácticas de UX/UI.
"""

import os
import re
import json
import base64
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
from anthropic import Anthropic

from config.design_system import (
    COLORES, COLORES_PROHIBIDOS, TIPOGRAFIAS, 
    BREAKPOINTS, REGLAS_RESPONSIVE, COMPONENTES,
    ACCESIBILIDAD, ESPACIADO, TAMANOS_TEXTO
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
FRONTEND_SRC = ROOT_DIR.parent / "frontend" / "src"


class NivelSeveridad(str, Enum):
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"


class CategoriaAuditoria(str, Enum):
    ACCESIBILIDAD = "accesibilidad"
    CONSISTENCIA_VISUAL = "consistencia_visual"
    RESPONSIVE_DESIGN = "responsive_design"
    USABILIDAD = "usabilidad"
    PERFORMANCE_VISUAL = "performance_visual"
    BRANDING = "branding"


class ProblemaUI:
    """Representa un problema de diseño detectado."""
    
    def __init__(
        self,
        titulo: str,
        descripcion: str,
        categoria: CategoriaAuditoria,
        severidad: NivelSeveridad,
        archivo: str = None,
        linea: int = None,
        codigo_ejemplo: str = None,
        sugerencia: str = None
    ):
        self.id = f"UI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(titulo) % 10000:04d}"
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = categoria
        self.severidad = severidad
        self.archivo = archivo
        self.linea = linea
        self.codigo_ejemplo = codigo_ejemplo
        self.sugerencia = sugerencia
        self.detectado_en = datetime.now()
        self.resuelto = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria.value,
            "severidad": self.severidad.value,
            "archivo": self.archivo,
            "linea": self.linea,
            "codigo_ejemplo": self.codigo_ejemplo,
            "sugerencia": self.sugerencia,
            "detectado_en": self.detectado_en.isoformat(),
            "resuelto": self.resuelto
        }


class ReporteAuditoria:
    """Representa un reporte de auditoría completo."""
    
    def __init__(self, tipo: str, componente: str = None, pagina: str = None):
        self.id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.tipo = tipo
        self.componente = componente
        self.pagina = pagina
        self.problemas: List[ProblemaUI] = []
        self.metricas: Dict[str, Any] = {}
        self.score_general: int = 100
        self.creado_en = datetime.now()
        self.estado = "pendiente"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "componente": self.componente,
            "pagina": self.pagina,
            "problemas": [p.to_dict() for p in self.problemas],
            "metricas": self.metricas,
            "score_general": self.score_general,
            "creado_en": self.creado_en.isoformat(),
            "estado": self.estado,
            "total_problemas": len(self.problemas),
            "por_severidad": self._contar_por_severidad()
        }
    
    def _contar_por_severidad(self) -> Dict[str, int]:
        conteo = {s.value: 0 for s in NivelSeveridad}
        for p in self.problemas:
            conteo[p.severidad.value] += 1
        return conteo


class DisenarIAService:
    """
    Diseñar.IA - Guardián Autónomo de Diseño UI
    
    Misión: Auditar interfaces de usuario, detectar inconsistencias de diseño
    y sugerir mejoras basándose en mejores prácticas de UX/UI y WCAG 2.1.
    """
    
    def __init__(self, ruta_frontend: str = None):
        self.ruta_frontend = ruta_frontend or str(FRONTEND_SRC)
        self.problemas: List[ProblemaUI] = []
        self.reportes: List[ReporteAuditoria] = []
        self.recomendaciones: List[Dict] = []
        self.estadisticas: Dict[str, Any] = {}
        self.metricas_ui: Dict[str, Any] = {
            "total_auditorias": 0,
            "problemas_detectados": 0,
            "problemas_resueltos": 0,
            "score_promedio": 0,
            "ultima_auditoria": None
        }
        
        api_key = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_API_KEY')
        base_url = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_BASE_URL')
        
        if api_key and base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
            logger.info("🎨 Diseñar.IA: Anthropic API configurada correctamente")
        else:
            logger.warning("⚠️ Diseñar.IA: Replit AI Integrations no configurado - análisis con IA no disponible")
            self.client = None
        
        self.model = "claude-sonnet-4-5"
        logger.info("🎨 Diseñar.IA: Servicio inicializado")
    
    def obtener_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del servicio Diseñar.IA."""
        return {
            "servicio": "Diseñar.IA",
            "version": "1.0.0",
            "estado": "activo" if self.client else "degradado",
            "ia_disponible": self.client is not None,
            "modelo": self.model,
            "ruta_frontend": self.ruta_frontend,
            "frontend_existe": os.path.exists(self.ruta_frontend),
            "total_reportes": len(self.reportes),
            "problemas_activos": len([p for p in self.problemas if not p.resuelto]),
            "recomendaciones_pendientes": len([r for r in self.recomendaciones if not r.get('aplicada', False)]),
            "metricas": self.metricas_ui,
            "categorias_auditoria": [c.value for c in CategoriaAuditoria],
            "niveles_severidad": [s.value for s in NivelSeveridad],
            "timestamp": datetime.now().isoformat()
        }
    
    def obtener_metricas_ui(self) -> Dict[str, Any]:
        """Retorna métricas detalladas de calidad UI."""
        scores = [r.score_general for r in self.reportes[-20:]] if self.reportes else [100]
        
        problemas_por_categoria = {c.value: 0 for c in CategoriaAuditoria}
        problemas_por_severidad = {s.value: 0 for s in NivelSeveridad}
        
        for p in self.problemas:
            problemas_por_categoria[p.categoria.value] += 1
            problemas_por_severidad[p.severidad.value] += 1
        
        return {
            "resumen": {
                "total_auditorias": self.metricas_ui["total_auditorias"],
                "problemas_detectados": len(self.problemas),
                "problemas_activos": len([p for p in self.problemas if not p.resuelto]),
                "problemas_resueltos": len([p for p in self.problemas if p.resuelto]),
                "score_promedio": round(sum(scores) / len(scores), 1),
                "ultima_auditoria": self.metricas_ui["ultima_auditoria"]
            },
            "por_categoria": problemas_por_categoria,
            "por_severidad": problemas_por_severidad,
            "tendencia": {
                "ultimos_5_scores": scores[-5:],
                "mejorando": len(scores) > 1 and scores[-1] > scores[0]
            },
            "areas_criticas": self._identificar_areas_criticas(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _identificar_areas_criticas(self) -> List[Dict]:
        """Identifica las áreas con más problemas."""
        conteo = {}
        for p in self.problemas:
            if not p.resuelto:
                key = p.categoria.value
                if key not in conteo:
                    conteo[key] = {"categoria": key, "total": 0, "criticos": 0}
                conteo[key]["total"] += 1
                if p.severidad == NivelSeveridad.CRITICO:
                    conteo[key]["criticos"] += 1
        
        areas = sorted(conteo.values(), key=lambda x: (x["criticos"], x["total"]), reverse=True)
        return areas[:5]
    
    def obtener_reportes(self, limite: int = 20) -> List[Dict]:
        """Retorna el historial de reportes de auditoría."""
        reportes_ordenados = sorted(self.reportes, key=lambda r: r.creado_en, reverse=True)
        return [r.to_dict() for r in reportes_ordenados[:limite]]
    
    def obtener_recomendaciones(self, solo_pendientes: bool = True) -> List[Dict]:
        """Retorna las recomendaciones activas de mejora."""
        if solo_pendientes:
            return [r for r in self.recomendaciones if not r.get('aplicada', False)]
        return self.recomendaciones
    
    async def auditar_componente(self, ruta_componente: str, contenido: str = None) -> Dict[str, Any]:
        """Audita un componente específico de la UI."""
        logger.info(f"🎨 Diseñar.IA: Auditando componente {ruta_componente}")
        
        reporte = ReporteAuditoria(tipo="componente", componente=ruta_componente)
        
        if contenido is None:
            ruta_completa = os.path.join(self.ruta_frontend, ruta_componente)
            if os.path.exists(ruta_completa):
                with open(ruta_completa, 'r', encoding='utf-8') as f:
                    contenido = f.read()
            else:
                reporte.estado = "error"
                reporte.metricas = {"error": f"Archivo no encontrado: {ruta_componente}"}
                self.reportes.append(reporte)
                return reporte.to_dict()
        
        problemas = await self._analizar_codigo_componente(contenido, ruta_componente)
        reporte.problemas = problemas
        
        reporte.score_general = self._calcular_score(problemas)
        reporte.metricas = {
            "lineas_codigo": len(contenido.split('\n')),
            "colores_usados": len(re.findall(r'#[0-9A-Fa-f]{3,6}', contenido)),
            "usa_tailwind": 'className' in contenido,
            "tiene_media_queries": bool(re.search(r'@media|sm:|md:|lg:|xl:', contenido)),
            "tiene_aria": bool(re.search(r'aria-|role=', contenido))
        }
        reporte.estado = "completado"
        
        self.reportes.append(reporte)
        self.problemas.extend(problemas)
        self._actualizar_metricas(reporte)
        self._generar_recomendaciones(problemas)
        
        logger.info(f"🎨 Diseñar.IA: Auditoría de componente completada - Score: {reporte.score_general}")
        return reporte.to_dict()
    
    async def auditar_pagina(self, ruta_pagina: str, incluir_componentes: bool = True) -> Dict[str, Any]:
        """Audita una página completa incluyendo sus componentes."""
        logger.info(f"🎨 Diseñar.IA: Auditando página {ruta_pagina}")
        
        reporte = ReporteAuditoria(tipo="pagina", pagina=ruta_pagina)
        
        ruta_completa = os.path.join(self.ruta_frontend, ruta_pagina)
        if not os.path.exists(ruta_completa):
            if os.path.exists(os.path.join(self.ruta_frontend, "pages", ruta_pagina)):
                ruta_completa = os.path.join(self.ruta_frontend, "pages", ruta_pagina)
            else:
                reporte.estado = "error"
                reporte.metricas = {"error": f"Página no encontrada: {ruta_pagina}"}
                self.reportes.append(reporte)
                return reporte.to_dict()
        
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        problemas = await self._analizar_codigo_componente(contenido, ruta_pagina)
        
        if incluir_componentes:
            imports = re.findall(r"from ['\"]\.\.?/components/([^'\"]+)['\"]", contenido)
            for imp in imports:
                comp_path = os.path.join(self.ruta_frontend, "components", f"{imp}.jsx")
                if os.path.exists(comp_path):
                    with open(comp_path, 'r', encoding='utf-8') as f:
                        comp_contenido = f.read()
                    comp_problemas = await self._analizar_codigo_componente(comp_contenido, imp)
                    problemas.extend(comp_problemas)
        
        reporte.problemas = problemas
        reporte.score_general = self._calcular_score(problemas)
        reporte.metricas = {
            "lineas_codigo": len(contenido.split('\n')),
            "componentes_importados": len(re.findall(r'import .+ from', contenido)),
            "hooks_usados": len(re.findall(r'use[A-Z][a-zA-Z]+', contenido)),
            "usa_context": 'useContext' in contenido,
            "tiene_loading_states": bool(re.search(r'loading|isLoading|Loading', contenido)),
            "tiene_error_handling": bool(re.search(r'error|Error|catch', contenido))
        }
        reporte.estado = "completado"
        
        self.reportes.append(reporte)
        self.problemas.extend(problemas)
        self._actualizar_metricas(reporte)
        self._generar_recomendaciones(problemas)
        
        logger.info(f"🎨 Diseñar.IA: Auditoría de página completada - Score: {reporte.score_general}")
        return reporte.to_dict()
    
    async def analizar_screenshot(self, imagen_base64: str, contexto: str = None) -> Dict[str, Any]:
        """Analiza un screenshot de la UI usando visión de IA."""
        logger.info("🎨 Diseñar.IA: Analizando screenshot con IA")
        
        if not self.client:
            return {
                "success": False,
                "error": "Servicio de IA no configurado. Contacte al administrador."
            }
        
        try:
            system_prompt = """Eres Diseñar.IA, un experto en auditoría de diseño UI/UX.
Analiza el screenshot proporcionado y detecta:

1. **ACCESIBILIDAD (WCAG 2.1)**:
   - Contraste de colores (mínimo 4.5:1 para texto normal, 3:1 para texto grande)
   - Tamaños de fuente legibles (mínimo 14px)
   - Espaciado táctil adecuado (mínimo 44x44px)
   - Indicadores de foco visibles

2. **CONSISTENCIA VISUAL**:
   - Uso consistente de colores
   - Tipografía uniforme
   - Espaciado coherente
   - Alineación de elementos

3. **RESPONSIVE DESIGN**:
   - Elementos que podrían causar overflow
   - Tamaños fijos problemáticos
   - Uso de espacio en pantalla

4. **USABILIDAD**:
   - Jerarquía visual clara
   - CTAs visibles y accesibles
   - Feedback visual para estados
   - Navegación intuitiva

5. **BRANDING**:
   - Consistencia con identidad de marca
   - Uso apropiado del logo
   - Paleta de colores corporativa

Responde en español con formato estructurado:
- Lista los problemas encontrados con severidad (CRITICO/ALTO/MEDIO/BAJO)
- Incluye sugerencias concretas de mejora
- Proporciona ejemplos de código CSS/React cuando sea útil
- Da un score general de 0-100"""

            prompt_usuario = "Analiza esta captura de pantalla de la interfaz de usuario:"
            if contexto:
                prompt_usuario += f"\n\nContexto adicional: {contexto}"

            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": imagen_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_usuario
                        }
                    ]
                }]
            )
            
            analisis = response.content[0].text
            
            reporte = ReporteAuditoria(tipo="screenshot")
            reporte.metricas = {
                "analizado_con_ia": True,
                "modelo": self.model,
                "contexto": contexto
            }
            reporte.estado = "completado"
            self.reportes.append(reporte)
            self._actualizar_metricas(reporte)
            
            logger.info("🎨 Diseñar.IA: Análisis de screenshot completado")
            
            return {
                "success": True,
                "analisis": analisis,
                "reporte_id": reporte.id,
                "agente": "Diseñar.IA",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Diseñar.IA: Error analizando screenshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analizar_codigo_componente(self, contenido: str, nombre: str) -> List[ProblemaUI]:
        """Analiza el código de un componente y detecta problemas."""
        problemas = []
        lineas = contenido.split('\n')
        
        colores_raw = re.findall(r'#[0-9A-Fa-f]{3,6}', contenido)
        colores_oficiales = self._extraer_colores_oficiales()
        for color in colores_raw:
            color_upper = color.upper()
            if color_upper not in colores_oficiales and color_upper not in ['#FFF', '#000', '#FFFFFF', '#000000']:
                problemas.append(ProblemaUI(
                    titulo=f"Color no oficial: {color}",
                    descripcion=f"Se encontró el color {color} que no está en el design system oficial.",
                    categoria=CategoriaAuditoria.BRANDING,
                    severidad=NivelSeveridad.MEDIO,
                    archivo=nombre,
                    sugerencia=self._sugerir_color_alternativo(color)
                ))
        
        for color_prohibido in COLORES_PROHIBIDOS:
            if isinstance(color_prohibido, str) and color_prohibido.startswith('#'):
                if color_prohibido.upper() in contenido.upper():
                    problemas.append(ProblemaUI(
                        titulo=f"Color prohibido: {color_prohibido}",
                        descripcion=f"El color {color_prohibido} está en la lista de colores prohibidos del design system.",
                        categoria=CategoriaAuditoria.BRANDING,
                        severidad=NivelSeveridad.ALTO,
                        archivo=nombre,
                        sugerencia=f"Reemplazar con color oficial: {self._sugerir_color_alternativo(color_prohibido)}"
                    ))
        
        imgs_sin_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', contenido)
        if imgs_sin_alt:
            problemas.append(ProblemaUI(
                titulo=f"{len(imgs_sin_alt)} imágenes sin atributo alt",
                descripcion="Las imágenes sin atributo alt afectan la accesibilidad para usuarios con lectores de pantalla.",
                categoria=CategoriaAuditoria.ACCESIBILIDAD,
                severidad=NivelSeveridad.CRITICO,
                archivo=nombre,
                codigo_ejemplo='<img src="..." alt="Descripción de la imagen" />',
                sugerencia="Agregar atributos alt descriptivos a todas las imágenes."
            ))
        
        inputs_sin_label = re.findall(r'<input(?![^>]*aria-label)[^>]*(?!.*<label)', contenido)
        if len(inputs_sin_label) > 0:
            problemas.append(ProblemaUI(
                titulo="Inputs sin etiquetas accesibles",
                descripcion="Los campos de entrada deben tener labels asociados o aria-label para accesibilidad.",
                categoria=CategoriaAuditoria.ACCESIBILIDAD,
                severidad=NivelSeveridad.ALTO,
                archivo=nombre,
                codigo_ejemplo='<label htmlFor="email">Email</label>\n<input id="email" type="email" />',
                sugerencia="Asociar cada input con un label usando htmlFor/id o aria-label."
            ))
        
        tamaños_pequenos = re.findall(r'font-size:\s*(\d+)px', contenido)
        for match in tamaños_pequenos:
            if int(match) < 14:
                problemas.append(ProblemaUI(
                    titulo=f"Tamaño de fuente muy pequeño: {match}px",
                    descripcion=f"El tamaño de fuente {match}px es menor al mínimo recomendado de 14px para legibilidad.",
                    categoria=CategoriaAuditoria.ACCESIBILIDAD,
                    severidad=NivelSeveridad.MEDIO,
                    archivo=nombre,
                    sugerencia="Usar tamaños de fuente de al menos 14px (0.875rem) para texto normal."
                ))
        
        anchos_fijos = re.findall(r'width:\s*(\d{4,})px', contenido)
        for ancho in anchos_fijos:
            problemas.append(ProblemaUI(
                titulo=f"Ancho fijo muy grande: {ancho}px",
                descripcion=f"El ancho fijo de {ancho}px puede causar problemas en pantallas pequeñas.",
                categoria=CategoriaAuditoria.RESPONSIVE_DESIGN,
                severidad=NivelSeveridad.ALTO,
                archivo=nombre,
                codigo_ejemplo='max-width: 100%;\nwidth: min(1200px, 90vw);',
                sugerencia="Usar anchos relativos (%, vw) o max-width con min() para responsive."
            ))
        
        usa_breakpoints = bool(re.search(r'@media|sm:|md:|lg:|xl:|2xl:', contenido))
        if not usa_breakpoints and len(contenido) > 500:
            problemas.append(ProblemaUI(
                titulo="Componente sin breakpoints responsive",
                descripcion="El componente no utiliza breakpoints de Tailwind ni media queries.",
                categoria=CategoriaAuditoria.RESPONSIVE_DESIGN,
                severidad=NivelSeveridad.MEDIO,
                archivo=nombre,
                codigo_ejemplo='<div className="p-4 md:p-6 lg:p-8">...</div>',
                sugerencia="Agregar clases responsive (sm:, md:, lg:) para mejor adaptación móvil."
            ))
        
        inline_styles = len(re.findall(r'style=\{\{', contenido))
        if inline_styles > 10:
            problemas.append(ProblemaUI(
                titulo=f"Exceso de estilos inline: {inline_styles}",
                descripcion="Muchos estilos inline dificultan el mantenimiento y afectan el rendimiento.",
                categoria=CategoriaAuditoria.PERFORMANCE_VISUAL,
                severidad=NivelSeveridad.BAJO,
                archivo=nombre,
                sugerencia="Migrar estilos inline a clases de Tailwind o archivos CSS."
            ))
        
        if not re.search(r'loading|isLoading|skeleton|Skeleton|spinner|Spinner', contenido, re.IGNORECASE):
            if 'fetch' in contenido or 'axios' in contenido or 'useQuery' in contenido:
                problemas.append(ProblemaUI(
                    titulo="Falta indicador de carga",
                    descripcion="El componente hace llamadas de datos pero no muestra estado de carga.",
                    categoria=CategoriaAuditoria.USABILIDAD,
                    severidad=NivelSeveridad.MEDIO,
                    archivo=nombre,
                    codigo_ejemplo='if (isLoading) return <Skeleton />;',
                    sugerencia="Agregar skeletons o spinners para mejorar la percepción de velocidad."
                ))
        
        return problemas
    
    def _calcular_score(self, problemas: List[ProblemaUI]) -> int:
        """Calcula el score de calidad basado en los problemas encontrados."""
        score = 100
        penalizaciones = {
            NivelSeveridad.CRITICO: 20,
            NivelSeveridad.ALTO: 10,
            NivelSeveridad.MEDIO: 5,
            NivelSeveridad.BAJO: 2
        }
        
        for problema in problemas:
            score -= penalizaciones.get(problema.severidad, 2)
        
        return max(0, score)
    
    def _actualizar_metricas(self, reporte: ReporteAuditoria):
        """Actualiza las métricas globales del servicio."""
        self.metricas_ui["total_auditorias"] += 1
        self.metricas_ui["problemas_detectados"] += len(reporte.problemas)
        self.metricas_ui["ultima_auditoria"] = reporte.creado_en.isoformat()
        
        scores = [r.score_general for r in self.reportes]
        self.metricas_ui["score_promedio"] = round(sum(scores) / len(scores), 1) if scores else 0
    
    def _generar_recomendaciones(self, problemas: List[ProblemaUI]):
        """Genera recomendaciones basadas en los problemas detectados."""
        for problema in problemas:
            if problema.severidad in [NivelSeveridad.CRITICO, NivelSeveridad.ALTO]:
                rec = {
                    "id": f"REC-{len(self.recomendaciones)+1:04d}",
                    "problema_id": problema.id,
                    "titulo": f"Corregir: {problema.titulo}",
                    "descripcion": problema.sugerencia or problema.descripcion,
                    "categoria": problema.categoria.value,
                    "prioridad": "alta" if problema.severidad == NivelSeveridad.CRITICO else "media",
                    "codigo_ejemplo": problema.codigo_ejemplo,
                    "aplicada": False,
                    "creada_en": datetime.now().isoformat()
                }
                if not any(r["titulo"] == rec["titulo"] for r in self.recomendaciones):
                    self.recomendaciones.append(rec)
    
    def auditar_todo(self) -> Dict[str, Any]:
        """Ejecuta auditoría completa del frontend."""
        logger.info("🎨 Diseñar.IA: Iniciando auditoría completa")
        
        inicio = datetime.now()
        self.problemas = []
        
        resultados = {
            'timestamp': inicio.isoformat(),
            'colorimetria': self.auditar_colores(),
            'tipografia': self.auditar_tipografias(),
            'responsive': self.auditar_responsive(),
            'componentes': self.auditar_componentes(),
            'accesibilidad': self.auditar_accesibilidad(),
            'rendimiento': self.auditar_rendimiento(),
        }
        
        scores = [r.get('score', 0) for r in resultados.values() if isinstance(r, dict)]
        resultados['score_general'] = round(sum(scores) / len(scores)) if scores else 0
        
        if resultados['score_general'] >= 90:
            resultados['estado'] = 'excelente'
            resultados['mensaje'] = '✨ Diseño consistente y optimizado'
        elif resultados['score_general'] >= 75:
            resultados['estado'] = 'bueno'
            resultados['mensaje'] = '👍 Algunas mejoras recomendadas'
        elif resultados['score_general'] >= 50:
            resultados['estado'] = 'regular'
            resultados['mensaje'] = '⚠️ Requiere atención'
        else:
            resultados['estado'] = 'critico'
            resultados['mensaje'] = '🚨 Múltiples problemas de diseño'
        
        resultados['problemas'] = self.problemas
        resultados['tiempo_auditoria_ms'] = (datetime.now() - inicio).total_seconds() * 1000
        
        reporte = ReporteAuditoria(tipo="completa")
        reporte.score_general = resultados['score_general']
        reporte.metricas = {k: v for k, v in resultados.items() if k not in ['problemas', 'timestamp']}
        reporte.estado = "completado"
        self.reportes.append(reporte)
        self._actualizar_metricas(reporte)
        
        logger.info(f"🎨 Diseñar.IA: Auditoría completa finalizada - Score: {resultados['score_general']}")
        
        return resultados
    
    def auditar_colores(self) -> Dict[str, Any]:
        """Analiza uso de colores en el código."""
        colores_encontrados = {}
        colores_prohibidos_usados = []
        archivos_analizados = 0
        
        patrones = [
            r'#[0-9A-Fa-f]{6}\b',
            r'#[0-9A-Fa-f]{3}\b',
            r'rgb\([^)]+\)',
            r'rgba\([^)]+\)',
            r'(?:bg|text|border|fill|stroke)-(?:red|green|blue|yellow|purple|pink|orange)-\d+',
        ]
        
        colores_oficiales = self._extraer_colores_oficiales()
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 100, 'total_colores': 0, 'mensaje': 'Ruta frontend no encontrada'}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx', '.js', '.ts', '.css', '.scss')):
                    archivos_analizados += 1
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            for patron in patrones:
                                matches = re.findall(patron, contenido, re.IGNORECASE)
                                for color in matches:
                                    color_normalizado = color.upper() if color.startswith('#') else color
                                    
                                    if color_normalizado not in colores_encontrados:
                                        colores_encontrados[color_normalizado] = {
                                            'usos': 0,
                                            'archivos': []
                                        }
                                    
                                    colores_encontrados[color_normalizado]['usos'] += 1
                                    if file not in colores_encontrados[color_normalizado]['archivos']:
                                        colores_encontrados[color_normalizado]['archivos'].append(file)
                                    
                                    if color_normalizado in [c.upper() for c in COLORES_PROHIBIDOS if isinstance(c, str) and c.startswith('#')]:
                                        if not any(c['color'] == color_normalizado for c in colores_prohibidos_usados):
                                            colores_prohibidos_usados.append({
                                                'color': color_normalizado,
                                                'archivo': file,
                                                'sugerencia': self._sugerir_color_alternativo(color_normalizado)
                                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        total_colores = len(colores_encontrados)
        score = max(0, 100 - len(colores_prohibidos_usados) * 10)
        
        return {
            'score': score,
            'total_colores': total_colores,
            'colores_oficiales_usados': len([c for c in colores_encontrados if c in colores_oficiales]),
            'colores_prohibidos': colores_prohibidos_usados,
            'archivos_analizados': archivos_analizados,
            'detalle': {k: v for k, v in list(colores_encontrados.items())[:20]}
        }
    
    def _extraer_colores_oficiales(self) -> List[str]:
        """Extrae lista de colores oficiales del design system."""
        colores = []
        
        def extraer_recursivo(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and v.startswith('#'):
                        colores.append(v.upper())
                    else:
                        extraer_recursivo(v)
        
        extraer_recursivo(COLORES)
        return colores
    
    def _sugerir_color_alternativo(self, color: str) -> str:
        """Sugiere un color de la paleta oficial como alternativa."""
        sugerencias = {
            '#FF0000': '#EF4444 (red-500)',
            '#00FF00': '#10B981 (green-500)',
            '#0000FF': '#0891B2 (cyan-600)',
            '#FFFF00': '#F59E0B (yellow-500)',
            '#FF00FF': '#A855F7 (purple-500)',
            '#00FFFF': '#22D3EE (cyan-400)',
            'RED': '#EF4444',
            'GREEN': '#10B981',
            'BLUE': '#0891B2',
        }
        return sugerencias.get(color.upper(), '#0891B2 (primary - cyan-600)')
    
    def auditar_tipografias(self) -> Dict[str, Any]:
        """Analiza uso de tipografías."""
        fuentes_encontradas = {}
        problemas_fuentes = []
        
        patrones_fuentes = [
            r'font-family:\s*["\']?([^"\';\n]+)',
            r'fontFamily:\s*["\']([^"\']+)',
            r'font-(?:sans|serif|mono)',
        ]
        
        fuentes_oficiales = [t['familia'] for t in TIPOGRAFIAS.values()]
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 100, 'fuentes_oficiales': fuentes_oficiales}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx', '.css', '.scss')):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            for patron in patrones_fuentes:
                                matches = re.findall(patron, contenido)
                                for fuente in matches:
                                    fuente_limpia = fuente.strip().split(',')[0].strip('"\'')
                                    
                                    if fuente_limpia not in fuentes_encontradas:
                                        fuentes_encontradas[fuente_limpia] = 0
                                    fuentes_encontradas[fuente_limpia] += 1
                                    
                                    if fuente_limpia not in fuentes_oficiales and fuente_limpia not in ['inherit', 'sans-serif', 'monospace', 'system-ui']:
                                        if fuente_limpia not in [p['fuente'] for p in problemas_fuentes]:
                                            problemas_fuentes.append({
                                                'fuente': fuente_limpia,
                                                'archivo': filepath.replace(self.ruta_frontend + '/', '')
                                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        score = 100 if len(problemas_fuentes) == 0 else max(0, 100 - len(problemas_fuentes) * 15)
        
        return {
            'score': score,
            'fuentes_oficiales': fuentes_oficiales,
            'fuentes_encontradas': fuentes_encontradas,
            'fuentes_no_oficiales': problemas_fuentes
        }
    
    def auditar_responsive(self) -> Dict[str, Any]:
        """Analiza optimización móvil."""
        componentes_analizados = 0
        problemas_responsive = []
        
        patrones_problematicos = [
            (r'width:\s*\d{4,}px', 'Ancho fijo muy grande'),
            (r'height:\s*\d{3,}px', 'Alto fijo puede causar overflow'),
            (r'font-size:\s*\d{1,2}px', 'Tamaño de fuente fijo pequeño'),
        ]
        
        patrones_buenos = [
            r'@media',
            r'sm:|md:|lg:|xl:',
            r'flex|grid',
            r'max-w-|min-w-',
            r'responsive',
        ]
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 100, 'componentes_analizados': 0}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx')):
                    componentes_analizados += 1
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            for patron, descripcion in patrones_problematicos:
                                if re.search(patron, contenido):
                                    problemas_responsive.append({
                                        'archivo': file,
                                        'problema': descripcion,
                                        'severidad': 'media'
                                    })
                            
                            usa_responsive = any(re.search(p, contenido) for p in patrones_buenos)
                            
                            if not usa_responsive and len(contenido) > 1000:
                                problemas_responsive.append({
                                    'archivo': file,
                                    'problema': 'No usa breakpoints responsive',
                                    'severidad': 'baja'
                                })
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        score = max(0, 100 - len(problemas_responsive) * 3)
        
        return {
            'score': score,
            'componentes_analizados': componentes_analizados,
            'problemas': problemas_responsive[:15],
            'total_problemas': len(problemas_responsive)
        }
    
    def auditar_componentes(self) -> Dict[str, Any]:
        """Analiza consistencia de componentes UI."""
        componentes = {
            'buttons': [],
            'inputs': [],
            'cards': [],
            'modals': []
        }
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 90, 'total_componentes': 0}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx')):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            buttons = len(re.findall(r'<button|<Button', contenido))
                            if buttons > 0:
                                componentes['buttons'].append({'archivo': file, 'cantidad': buttons})
                            
                            inputs = len(re.findall(r'<input|<Input|<textarea|<TextArea', contenido))
                            if inputs > 0:
                                componentes['inputs'].append({'archivo': file, 'cantidad': inputs})
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        total_componentes = sum(len(v) for v in componentes.values())
        
        return {
            'score': 90,
            'total_componentes': total_componentes,
            'detalle': componentes
        }
    
    def auditar_accesibilidad(self) -> Dict[str, Any]:
        """Analiza accesibilidad básica (WCAG 2.1)."""
        problemas_a11y = []
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 100, 'total_problemas': 0}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx')):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            imgs_sin_alt = len(re.findall(r'<img(?![^>]*alt=)[^>]*>', contenido))
                            if imgs_sin_alt > 0:
                                problemas_a11y.append({
                                    'archivo': file,
                                    'problema': f'{imgs_sin_alt} imágenes sin atributo alt',
                                    'severidad': 'alta',
                                    'wcag': '1.1.1 Non-text Content'
                                })
                            
                            btns_icon_only = len(re.findall(r'<button[^>]*>\s*<(?:svg|Icon|img)[^>]*>\s*</button>', contenido))
                            if btns_icon_only > 0:
                                problemas_a11y.append({
                                    'archivo': file,
                                    'problema': f'{btns_icon_only} botones solo con icono sin aria-label',
                                    'severidad': 'media',
                                    'wcag': '4.1.2 Name, Role, Value'
                                })
                            
                            divs_click = len(re.findall(r'<div[^>]*onClick', contenido))
                            if divs_click > 0:
                                problemas_a11y.append({
                                    'archivo': file,
                                    'problema': f'{divs_click} divs con onClick (deberían ser buttons)',
                                    'severidad': 'media',
                                    'wcag': '2.1.1 Keyboard'
                                })
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        score = max(0, 100 - len(problemas_a11y) * 10)
        
        return {
            'score': score,
            'problemas': problemas_a11y[:10],
            'total_problemas': len(problemas_a11y),
            'wcag_version': '2.1'
        }
    
    def auditar_rendimiento(self) -> Dict[str, Any]:
        """Analiza potenciales problemas de rendimiento en UI."""
        problemas_perf = []
        
        if not os.path.exists(self.ruta_frontend):
            return {'score': 100, 'total_problemas': 0}
        
        for root, dirs, files in os.walk(self.ruta_frontend):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            
            for file in files:
                if file.endswith(('.jsx', '.tsx')):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            
                            inline_styles = len(re.findall(r'style=\{\{', contenido))
                            if inline_styles > 15:
                                problemas_perf.append({
                                    'archivo': file,
                                    'problema': f'{inline_styles} inline styles (causan re-renders)',
                                    'severidad': 'baja'
                                })
                            
                            if 'useState' in contenido and contenido.count('useState') > 15:
                                problemas_perf.append({
                                    'archivo': file,
                                    'problema': 'Muchos useState pueden causar re-renders excesivos',
                                    'severidad': 'media'
                                })
                            
                            if not re.search(r'useMemo|useCallback|React\.memo', contenido):
                                if contenido.count('map(') > 5:
                                    problemas_perf.append({
                                        'archivo': file,
                                        'problema': 'Múltiples maps sin memoización',
                                        'severidad': 'baja'
                                    })
                    except Exception as e:
                        logger.warning(f"⚠️ Error leyendo {filepath}: {e}")
        
        score = max(0, 100 - len(problemas_perf) * 5)
        
        return {
            'score': score,
            'problemas': problemas_perf[:10],
            'total_problemas': len(problemas_perf)
        }
    
    def generar_sugerencias_tecnologias(self) -> List[Dict[str, Any]]:
        """Genera sugerencias de nuevas tecnologías a implementar."""
        return [
            {
                'tecnologia': 'Framer Motion',
                'descripcion': 'Librería de animaciones fluidas para React',
                'impacto': 'Mejora percepción de calidad en +15%',
                'dificultad': 'media',
                'ejemplo': '''<motion.div 
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  className="card"
>...</motion.div>'''
            },
            {
                'tecnologia': 'CSS Container Queries',
                'descripcion': 'Componentes que se adaptan a su contenedor',
                'impacto': 'Componentes verdaderamente reutilizables',
                'dificultad': 'baja',
                'ejemplo': '''@container (min-width: 400px) {
  .card { flex-direction: row; }
}'''
            },
            {
                'tecnologia': 'View Transitions API',
                'descripcion': 'Transiciones nativas entre páginas/estados',
                'impacto': 'UX tipo app nativa',
                'dificultad': 'media',
                'ejemplo': '''document.startViewTransition(() => {
  navigate('/nueva-pagina');
});'''
            },
            {
                'tecnologia': 'Skeleton Loading',
                'descripcion': 'Placeholders animados durante la carga',
                'impacto': 'Mejor percepción de velocidad',
                'dificultad': 'baja',
                'ejemplo': '''<div className="animate-pulse bg-gray-700 h-4 w-full rounded" />'''
            },
            {
                'tecnologia': 'React Aria',
                'descripcion': 'Hooks de accesibilidad de Adobe',
                'impacto': 'Accesibilidad WCAG 2.1 automática',
                'dificultad': 'media',
            }
        ]
    
    async def chat(self, mensaje: str, history: List[dict] = None) -> Dict[str, Any]:
        """Chat con el agente Diseñar.IA."""
        if not self.client:
            return {
                'success': False,
                'error': 'Servicio de IA no configurado. Contacte al administrador.'
            }
        
        try:
            auditoria_rapida = {
                'colores': self.auditar_colores(),
                'responsive': self.auditar_responsive()
            }
            
            system_prompt = f"""Eres Diseñar.IA, el agente guardián del diseño de la plataforma Revisar.IA/Durezza.

Tu personalidad:
- Nombre: Diseñar.IA
- Rol: Director de Arte Digital
- Obsesión: Consistencia visual, UX perfecta, optimización móvil
- Tono: Profesional pero apasionado por el diseño

Tu conocimiento incluye:
1. Design System oficial de la marca
2. Últimas tendencias en UI/UX
3. Mejores prácticas de responsive design
4. Accesibilidad web (WCAG 2.1)
5. Performance de CSS y animaciones

Estado actual del diseño:
{json.dumps(auditoria_rapida, indent=2, default=str)}

Paleta de colores oficial:
- Primary: #0891B2 (Cyan)
- Success: #10B981 (Green)
- Warning: #F59E0B (Yellow)
- Error: #EF4444 (Red)
- Background: #0F172A (Dark)

Niveles de severidad que usas:
- CRITICO: Bloquea la funcionalidad
- ALTO: Afecta significativamente la UX
- MEDIO: Inconsistencias menores
- BAJO: Sugerencias de mejora

Cuando respondas:
- Sé específico con códigos de color y valores
- Sugiere mejoras concretas con ejemplos de código
- Menciona nuevas tecnologías cuando sea relevante
- Prioriza la experiencia móvil
- Usa emojis relacionados con diseño: 🎨 🖌️ 📱 💡 ✨"""

            messages = []
            if history:
                for msg in history[-10:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": mensaje})
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            
            respuesta = response.content[0].text
            
            return {
                'success': True,
                'response': respuesta,
                'agente': 'Diseñar.IA'
            }
            
        except Exception as e:
            logger.error(f"❌ Diseñar.IA: Error en chat: {e}")
            return {
                'success': False,
                'error': str(e)
            }


disenar_service = DisenarIAService()
