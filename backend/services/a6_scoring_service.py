from datetime import datetime
from typing import List
from models.proveedor import (
    ProveedorJson, ScoreDetalleA6, RiesgoProveedorA6, 
    NivelRiesgoProveedor, RecomendacionA6, FlagRiesgo
)


class A6ScoringService:
    """Service for A6_PROVEEDOR scoring logic"""
    
    FLAGS_CRITICOS = [
        ("DEFINITIVO_EFOS_69B", "Proveedor en lista definitiva 69-B"),
        ("SIN_RFC_ACTIVO", "RFC no activo en SAT"),
    ]
    
    FLAGS_ALTOS = [
        ("PRESUNTO_EFOS_69B", "Proveedor en lista de presuntos 69-B"),
        ("SIN_OPINION_32D", "Sin opinión de cumplimiento positiva"),
        ("SIN_REPSE_SI_APLICA", "Requiere REPSE y no lo tiene"),
        ("SIN_EMPLEADOS_IMSS", "Sin empleados registrados en IMSS"),
    ]
    
    FLAGS_MEDIOS = [
        ("CAPITAL_MINIMO", "Capital social menor a $100,000"),
        ("ANTIGUEDAD_MENOR_2_ANIOS", "Antigüedad menor a 2 años"),
        ("SIN_SITIO_WEB", "Sin presencia web verificable"),
        ("DOMICILIO_NO_VERIFICABLE", "Domicilio fiscal no verificable"),
    ]
    
    def calcular_score(self, proveedor: ProveedorJson) -> ScoreDetalleA6:
        """Calculate detailed score for supplier"""
        cap_juridica = self._score_capacidad_juridica(proveedor)
        cap_material = self._score_capacidad_material(proveedor)
        cumplimiento = self._score_cumplimiento_fiscal(proveedor)
        historial = self._score_historial_comercial(proveedor)
        
        total = cap_juridica + cap_material + cumplimiento + historial
        
        return ScoreDetalleA6(
            capacidad_juridica=cap_juridica,
            capacidad_material=cap_material,
            cumplimiento_fiscal=cumplimiento,
            historial_comercial=historial,
            total=total
        )
    
    def detectar_flags(self, proveedor: ProveedorJson) -> List[FlagRiesgo]:
        """Detect risk flags for supplier"""
        flags = []
        now = datetime.utcnow()
        
        if proveedor.estatus_lista_69b == "DEFINITIVO":
            flags.append(FlagRiesgo(
                codigo="DEFINITIVO_EFOS_69B",
                descripcion="Proveedor en lista definitiva 69-B",
                severidad="CRITICO",
                detectado=True,
                fecha_deteccion=now
            ))
        elif proveedor.estatus_lista_69b == "PRESUNTO":
            flags.append(FlagRiesgo(
                codigo="PRESUNTO_EFOS_69B",
                descripcion="Proveedor en lista de presuntos 69-B",
                severidad="ALTO",
                detectado=True,
                fecha_deteccion=now
            ))
        
        tiene_32d = any(d.tipo == "OPINION_32D" and d.verificado for d in proveedor.documentos)
        if not tiene_32d:
            flags.append(FlagRiesgo(
                codigo="SIN_OPINION_32D",
                descripcion="Sin opinión de cumplimiento positiva",
                severidad="ALTO",
                detectado=True,
                fecha_deteccion=now
            ))
        
        if proveedor.datos_legales_fiscales.capital_social:
            if proveedor.datos_legales_fiscales.capital_social < 100000:
                flags.append(FlagRiesgo(
                    codigo="CAPITAL_MINIMO",
                    descripcion="Capital social menor a $100,000",
                    severidad="MEDIO",
                    detectado=True,
                    fecha_deteccion=now
                ))
        
        if not proveedor.datos_contacto_operativos.sitio_web:
            flags.append(FlagRiesgo(
                codigo="SIN_SITIO_WEB",
                descripcion="Sin presencia web verificable",
                severidad="MEDIO",
                detectado=True,
                fecha_deteccion=now
            ))
        
        return flags
    
    def determinar_nivel_riesgo(self, score: int) -> NivelRiesgoProveedor:
        """Determine risk level from score"""
        if score >= 80:
            return NivelRiesgoProveedor.BAJO
        elif score >= 70:
            return NivelRiesgoProveedor.MEDIO_BAJO
        elif score >= 60:
            return NivelRiesgoProveedor.MEDIO
        elif score >= 50:
            return NivelRiesgoProveedor.MEDIO_ALTO
        elif score >= 40:
            return NivelRiesgoProveedor.ALTO
        else:
            return NivelRiesgoProveedor.CRITICO
    
    def determinar_recomendacion(self, score: int, flags: List[FlagRiesgo]) -> RecomendacionA6:
        """Determine recommendation based on score and flags"""
        if any(f.severidad == "CRITICO" and f.detectado for f in flags):
            return RecomendacionA6.RECHAZAR
        
        high_flags = [f for f in flags if f.severidad == "ALTO" and f.detectado]
        if len(high_flags) >= 2 or score < 40:
            return RecomendacionA6.RECHAZAR
        
        if score >= 80:
            return RecomendacionA6.APROBAR
        elif score >= 60:
            return RecomendacionA6.APROBAR_CON_CONDICIONES
        elif score >= 40:
            return RecomendacionA6.REQUIERE_MAS_INVESTIGACION
        else:
            return RecomendacionA6.RECHAZAR
    
    def evaluar_proveedor(self, proveedor: ProveedorJson) -> RiesgoProveedorA6:
        """Complete evaluation of supplier"""
        score = self.calcular_score(proveedor)
        flags = self.detectar_flags(proveedor)
        nivel = self.determinar_nivel_riesgo(score.total)
        recomendacion = self.determinar_recomendacion(score.total, flags)
        
        justificacion = self._generar_justificacion(score, flags, nivel, recomendacion)
        
        return RiesgoProveedorA6(
            score=score,
            nivel_riesgo=nivel,
            flags=flags,
            recomendacion=recomendacion,
            justificacion=justificacion,
            fecha_evaluacion=datetime.utcnow()
        )
    
    def _score_capacidad_juridica(self, p: ProveedorJson) -> int:
        score = 0
        dl = p.datos_legales_fiscales
        
        if dl.rfc: score += 5
        if dl.razon_social: score += 3
        if dl.representante_legal: score += 4
        if dl.domicilio_fiscal: score += 4
        if dl.objeto_social: score += 4
        
        return min(score, 20)
    
    def _score_capacidad_material(self, p: ProveedorJson) -> int:
        score = 0
        dl = p.datos_legales_fiscales
        dc = p.datos_contacto_operativos
        
        if dc.sitio_web: score += 8
        if dc.direccion_operativa: score += 7
        if dl.capital_social and dl.capital_social >= 100000: score += 10
        if dl.fecha_constitucion:
            years = (datetime.utcnow() - dl.fecha_constitucion).days / 365
            if years >= 2: score += 10
            elif years >= 1: score += 5
        
        return min(score, 35)
    
    def _score_cumplimiento_fiscal(self, p: ProveedorJson) -> int:
        score = 0
        
        if p.estatus_lista_69b == "LIMPIO" or p.estatus_lista_69b == "DESVIRTUADO":
            score += 15
        elif p.estatus_lista_69b == "PRESUNTO":
            score += 0
        elif p.estatus_lista_69b == "DEFINITIVO":
            score -= 35
        else:
            score += 10
        
        for doc in p.documentos:
            if doc.tipo == "OPINION_32D" and doc.verificado:
                score += 10
            if doc.tipo == "CSF" and doc.verificado:
                score += 5
            if doc.tipo == "REPSE" and doc.verificado:
                score += 5
        
        return max(0, min(score, 35))
    
    def _score_historial_comercial(self, p: ProveedorJson) -> int:
        score = 0
        dc = p.datos_contacto_operativos
        
        if dc.sitio_web: score += 5
        if dc.email_principal: score += 2
        if dc.telefono: score += 3
        
        return min(score, 10)
    
    def _generar_justificacion(self, score: ScoreDetalleA6, flags: List[FlagRiesgo], 
                                nivel: NivelRiesgoProveedor, rec: RecomendacionA6) -> str:
        parts = []
        parts.append(f"Score total: {score.total}/100 (Nivel: {nivel.value})")
        parts.append(f"Capacidad jurídica: {score.capacidad_juridica}/20")
        parts.append(f"Capacidad material: {score.capacidad_material}/35")
        parts.append(f"Cumplimiento fiscal: {score.cumplimiento_fiscal}/35")
        parts.append(f"Historial comercial: {score.historial_comercial}/10")
        
        detected_flags = [f for f in flags if f.detectado]
        if detected_flags:
            parts.append(f"Flags detectados: {len(detected_flags)}")
            for f in detected_flags:
                parts.append(f"  - [{f.severidad}] {f.descripcion}")
        
        parts.append(f"Recomendación: {rec.value}")
        
        return "\n".join(parts)
