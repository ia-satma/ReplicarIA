from datetime import datetime
from typing import Optional, Dict, Any, List
from backend.models.defense_file import (
    DefenseFileJson, SeccionContenido, SeccionDefenseFile,
    DocumentoEvidencia, HitoTimeline, MatrizMaterialidad,
    ResumenDictamenes
)
import uuid

class A7DefenseService:
    """Service for A7_DEFENSA - Defense File generation"""
    
    SECCIONES_TEMPLATE = [
        (SeccionDefenseFile.CARATULA, "Carátula"),
        (SeccionDefenseFile.RESUMEN_EJECUTIVO, "Resumen Ejecutivo"),
        (SeccionDefenseFile.INDICE, "Índice de Contenido"),
        (SeccionDefenseFile.ANTECEDENTES, "Antecedentes y Contexto"),
        (SeccionDefenseFile.RAZON_NEGOCIOS, "Razón de Negocios (Art. 5-A CFF)"),
        (SeccionDefenseFile.BENEFICIO_ECONOMICO, "Beneficio Económico Esperado"),
        (SeccionDefenseFile.MATERIALIDAD, "Materialidad del Servicio"),
        (SeccionDefenseFile.FISCAL, "Análisis Fiscal y Deducibilidad"),
        (SeccionDefenseFile.PROVEEDOR, "Due Diligence del Proveedor"),
        (SeccionDefenseFile.LEGAL, "Marco Contractual"),
        (SeccionDefenseFile.EVIDENCIAS, "Catálogo de Evidencias"),
        (SeccionDefenseFile.TIMELINE, "Cronología del Proyecto"),
        (SeccionDefenseFile.CONCLUSIONES, "Conclusiones"),
        (SeccionDefenseFile.ANEXOS, "Anexos"),
        (SeccionDefenseFile.METODOLOGIA, "Metodología y Disclaimer"),
    ]
    
    def crear_defense_file(
        self,
        proyecto_id: str,
        empresa_id: str,
        nombre_proyecto: str,
        descripcion: str,
        tipo_servicio: str,
        monto: float,
        proveedor_nombre: str,
        proveedor_rfc: str
    ) -> DefenseFileJson:
        """Create initial Defense File structure"""
        
        # Create empty sections
        secciones = [
            SeccionContenido(
                seccion_id=sec_id,
                titulo=titulo,
                contenido="",
                estado="PENDIENTE"
            )
            for sec_id, titulo in self.SECCIONES_TEMPLATE
        ]
        
        return DefenseFileJson(
            id=str(uuid.uuid4()),
            proyecto_id=proyecto_id,
            empresa_id=empresa_id,
            nombre_proyecto=nombre_proyecto,
            descripcion_proyecto=descripcion,
            tipo_servicio=tipo_servicio,
            monto_total=monto,
            proveedor_nombre=proveedor_nombre,
            proveedor_rfc=proveedor_rfc,
            secciones=secciones,
            dictamenes=ResumenDictamenes()
        )
    
    def incorporar_dictamen_a1(self, df: DefenseFileJson, dictamen: Dict[str, Any]) -> None:
        """Incorporate A1 dictamen into Defense File"""
        df.dictamenes.a1_estrategia = dictamen
        
        # Update section 05 - Razón de Negocios
        seccion = self._get_seccion(df, SeccionDefenseFile.RAZON_NEGOCIOS)
        if seccion:
            seccion.contenido = self._generar_contenido_razon_negocios(dictamen)
            seccion.dictamen_agente = "A1_ESTRATEGIA"
            seccion.fuentes_normativas = ["CFF Art. 5-A"]
            seccion.estado = "COMPLETO"
    
    def incorporar_dictamen_a3(self, df: DefenseFileJson, dictamen: Dict[str, Any]) -> None:
        """Incorporate A3 dictamen into Defense File"""
        df.dictamenes.a3_fiscal = dictamen
        
        # Update section 08 - Fiscal
        seccion = self._get_seccion(df, SeccionDefenseFile.FISCAL)
        if seccion:
            seccion.contenido = self._generar_contenido_fiscal(dictamen)
            seccion.dictamen_agente = "A3_FISCAL"
            seccion.fuentes_normativas = ["LISR Art. 27", "CFF Art. 29/29-A", "CFF Art. 69-B"]
            seccion.estado = "COMPLETO"
    
    def incorporar_dictamen_a5(self, df: DefenseFileJson, dictamen: Dict[str, Any]) -> None:
        """Incorporate A5 dictamen into Defense File"""
        df.dictamenes.a5_finanzas = dictamen
        
        # Update section 06 - Beneficio Económico
        seccion = self._get_seccion(df, SeccionDefenseFile.BENEFICIO_ECONOMICO)
        if seccion:
            seccion.contenido = self._generar_contenido_bee(dictamen)
            seccion.dictamen_agente = "A5_FINANZAS"
            seccion.estado = "COMPLETO"
    
    def incorporar_dictamen_a6(self, df: DefenseFileJson, dictamen: Dict[str, Any]) -> None:
        """Incorporate A6 dictamen into Defense File"""
        df.dictamenes.a6_proveedor = dictamen
        
        # Update section 09 - Proveedor
        seccion = self._get_seccion(df, SeccionDefenseFile.PROVEEDOR)
        if seccion:
            seccion.contenido = self._generar_contenido_proveedor(dictamen)
            seccion.dictamen_agente = "A6_PROVEEDOR"
            seccion.fuentes_normativas = ["CFF Art. 69-B"]
            seccion.estado = "COMPLETO"
    
    def incorporar_dictamen_a4(self, df: DefenseFileJson, dictamen: Dict[str, Any]) -> None:
        """Incorporate A4 dictamen into Defense File"""
        df.dictamenes.a4_legal = dictamen
        
        # Update section 10 - Legal
        seccion = self._get_seccion(df, SeccionDefenseFile.LEGAL)
        if seccion:
            seccion.contenido = self._generar_contenido_legal(dictamen)
            seccion.dictamen_agente = "A4_LEGAL"
            seccion.estado = "COMPLETO"
    
    def agregar_documento(self, df: DefenseFileJson, doc: DocumentoEvidencia) -> None:
        """Add document to Defense File"""
        df.documentos.append(doc)
    
    def agregar_hito_timeline(self, df: DefenseFileJson, hito: HitoTimeline) -> None:
        """Add timeline milestone"""
        df.timeline.append(hito)
        df.timeline.sort(key=lambda x: x.fecha)
    
    def calcular_scores(self, df: DefenseFileJson) -> None:
        """Calculate materiality, traceability and defense scores"""
        # Materialidad score
        if df.matriz_materialidad:
            presentes = sum(1 for m in df.matriz_materialidad if m.evidencia_presente)
            df.score_materialidad = int((presentes / len(df.matriz_materialidad)) * 100)
        
        # Trazabilidad score
        fases_cubiertas = set(h.fase for h in df.timeline)
        df.score_trazabilidad = int((len(fases_cubiertas) / 10) * 100)  # F0-F9 = 10 fases
        
        # Defense score (weighted average)
        secciones_completas = sum(1 for s in df.secciones if s.estado == "COMPLETO")
        score_secciones = int((secciones_completas / len(df.secciones)) * 100)
        
        df.score_defensa = int(
            (df.score_materialidad * 0.4) +
            (df.score_trazabilidad * 0.3) +
            (score_secciones * 0.3)
        )
    
    def generar_metodologia(self) -> str:
        """Generate methodology section with disclaimer"""
        return """
## Metodología

Este Defense File fue elaborado utilizando la plataforma Revisar.ia, que emplea 
herramientas de inteligencia artificial como auxiliares en el análisis y 
sistematización de información.

Conforme a la Tesis II.2o.C. J/1 K (12a.) del Poder Judicial de la Federación, 
el uso de IA como herramienta auxiliar es válido cuando el control intelectual 
y la responsabilidad de las conclusiones corresponden a los profesionales 
responsables del expediente.

### Proceso de elaboración:
1. Recopilación de información del proyecto (SIB, contratos, evidencias)
2. Análisis por agentes especializados (A1-A6)
3. Consolidación por A7_DEFENSA
4. Validación por responsable fiscal del cliente

### Fuentes normativas consultadas:
- Código Fiscal de la Federación (CFF) - Arts. 5-A, 27, 29, 29-A, 69-B
- Ley del Impuesto Sobre la Renta (LISR) - Arts. 25, 27, 28
- NOM-151-SCFI-2016 (Conservación de mensajes de datos)
- Resolución Miscelánea Fiscal vigente

### Disclaimer:
Este documento es un auxiliar de análisis y documentación. No constituye 
asesoría fiscal ni legal vinculante. Las conclusiones deben ser validadas 
por el asesor fiscal del contribuyente antes de su uso ante autoridades.
"""
    
    def _get_seccion(self, df: DefenseFileJson, seccion_id: SeccionDefenseFile) -> Optional[SeccionContenido]:
        """Get section by ID"""
        for s in df.secciones:
            if s.seccion_id == seccion_id:
                return s
        return None
    
    def _generar_contenido_razon_negocios(self, dictamen: Dict[str, Any]) -> str:
        return f"""
## Razón de Negocios

### Objetivo del proyecto
{dictamen.get('razon_negocios_identificada', 'No especificado')}

### Solidez de la razón de negocios
{dictamen.get('razon_negocios_solidez', 'No evaluado')}

### Análisis conforme al Art. 5-A CFF
El proyecto presenta una razón de negocios {dictamen.get('razon_negocios_solidez', '').lower()}, 
con un propósito económico identificable más allá del beneficio fiscal.

### Score A1: {dictamen.get('score', {}).get('total', 0)}/25
- Sustancia económica: {dictamen.get('score', {}).get('sustancia_economica', 0)}/5
- Propósito concreto: {dictamen.get('score', {}).get('proposito_concreto', 0)}/5
- Coherencia estratégica: {dictamen.get('score', {}).get('coherencia_estrategica', 0)}/5
- BEE describible: {dictamen.get('score', {}).get('bee_describible', 0)}/5
- Documentación contemporánea: {dictamen.get('score', {}).get('documentacion_contemporanea', 0)}/5

### Estado: {dictamen.get('estado', 'NO_EVALUADO')}
### Recomendación F2: {dictamen.get('recomendacion_f2', 'NO_EVALUADO')}
"""
    
    def _generar_contenido_fiscal(self, dictamen: Dict[str, Any]) -> str:
        return f"""
## Análisis Fiscal

### Cumplimiento LISR Art. 27
{dictamen.get('cumplimiento_lisr27', 'Pendiente de evaluación')}

### Riesgo EFOS (Art. 69-B CFF)
{dictamen.get('riesgo_efos', 'No evaluado')}

### CFDI y documentación
{dictamen.get('analisis_cfdi', 'Pendiente')}

### Dictamen de deducibilidad
{dictamen.get('dictamen_deducibilidad', 'Pendiente')}
"""
    
    def _generar_contenido_bee(self, dictamen: Dict[str, Any]) -> str:
        return f"""
## Beneficio Económico Esperado

### Tipo de beneficio
{dictamen.get('tipo_beneficio', 'No especificado')}

### ROI Esperado
{dictamen.get('roi_esperado', 'No calculado')}

### NPV
{dictamen.get('npv', 'No calculado')}

### Payback
{dictamen.get('payback_meses', 'No calculado')} meses

### Score A5: {dictamen.get('score', {}).get('total', 0)}/25
"""
    
    def _generar_contenido_proveedor(self, dictamen: Dict[str, Any]) -> str:
        return f"""
## Due Diligence del Proveedor

### Score A6: {dictamen.get('score', {}).get('total', 0)}/100
- Capacidad jurídica: {dictamen.get('score', {}).get('capacidad_juridica', 0)}/20
- Capacidad material: {dictamen.get('score', {}).get('capacidad_material', 0)}/35
- Cumplimiento fiscal: {dictamen.get('score', {}).get('cumplimiento_fiscal', 0)}/35
- Historial comercial: {dictamen.get('score', {}).get('historial_comercial', 0)}/10

### Nivel de riesgo
{dictamen.get('nivel_riesgo', 'No evaluado')}

### Estatus 69-B
{dictamen.get('estatus_69b', 'No consultado')}

### Recomendación A6
{dictamen.get('recomendacion', 'Pendiente')}
"""
    
    def _generar_contenido_legal(self, dictamen: Dict[str, Any]) -> str:
        return f"""
## Marco Contractual

### Tipo de contrato
{dictamen.get('tipo_contrato', 'No especificado')}

### Score A4: {dictamen.get('score', {}).get('total', 0)}/25

### Cláusulas verificadas
{dictamen.get('clausulas_verificadas', 'Pendiente de revisión')}

### Recomendación A4
{dictamen.get('recomendacion', 'Pendiente')}
"""
