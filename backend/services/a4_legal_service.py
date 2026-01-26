from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class TipoContrato(str, Enum):
    PRESTACION_SERVICIOS = "PRESTACION_SERVICIOS"
    CONSULTORÍA = "CONSULTORIA"
    LICENCIAMIENTO = "LICENCIAMIENTO"
    DESARROLLO_SOFTWARE = "DESARROLLO_SOFTWARE"
    MARKETING = "MARKETING"
    INTRAGRUPO = "INTRAGRUPO"
    OTRO = "OTRO"

class RecomendacionA4(str, Enum):
    APROBAR = "APROBAR"
    APROBAR_CON_MODIFICACIONES = "APROBAR_CON_MODIFICACIONES"
    NO_APROBAR = "NO_APROBAR"

class ClausulaRequerida(BaseModel):
    id: str
    nombre: str
    descripcion: str
    criticidad: str  # OBLIGATORIA, RECOMENDADA, OPCIONAL
    presente: bool = False
    observaciones: Optional[str] = None

class ScoreDetalleA4(BaseModel):
    objeto_alcance: int = Field(ge=0, le=5)         # Claridad del objeto
    entregables_aceptacion: int = Field(ge=0, le=5) # Criterios de aceptación
    cooperacion_evidencia: int = Field(ge=0, le=5)  # Cláusula de cooperación
    pi_confidencialidad: int = Field(ge=0, le=5)    # Propiedad intelectual
    cumplimiento_regulatorio: int = Field(ge=0, le=5) # REPSE, fiscal, laboral
    total: int = Field(ge=0, le=25)

class ObservacionLegal(BaseModel):
    codigo: str
    descripcion: str
    severidad: str  # BLOQUEANTE, ALTA, MEDIA, BAJA
    recomendacion: str

class DictamenA4(BaseModel):
    proyecto_id: str
    
    # Contract info
    tipo_contrato: TipoContrato
    tiene_contrato: bool
    tiene_sow: bool
    
    # Clause analysis
    clausulas: List[ClausulaRequerida] = []
    clausulas_presentes: int = 0
    clausulas_faltantes: int = 0
    
    # Score
    score: ScoreDetalleA4
    
    # Observations
    observaciones: List[ObservacionLegal] = []
    
    # Recommendations
    recomendacion_f2: RecomendacionA4  # SOW/borrador review
    recomendacion_f6: RecomendacionA4  # Final contract review
    
    # Justification
    dictamen: str
    areas_mejora: List[str] = []
    
    # Metadata
    fase_evaluacion: str = "F2"  # F2 or F6
    fecha_dictamen: datetime = Field(default_factory=datetime.utcnow)


class A4LegalService:
    """Service for A4_LEGAL contract analysis"""
    
    CLAUSULAS_MINIMAS = [
        ClausulaRequerida(
            id="CL01",
            nombre="Objeto y Alcance",
            descripcion="Definición clara del servicio contratado",
            criticidad="OBLIGATORIA"
        ),
        ClausulaRequerida(
            id="CL02",
            nombre="Entregables",
            descripcion="Lista específica de entregables con criterios de aceptación",
            criticidad="OBLIGATORIA"
        ),
        ClausulaRequerida(
            id="CL03",
            nombre="Contraprestación",
            descripcion="Monto, forma y calendario de pagos",
            criticidad="OBLIGATORIA"
        ),
        ClausulaRequerida(
            id="CL04",
            nombre="Vigencia",
            descripcion="Plazo de ejecución del servicio",
            criticidad="OBLIGATORIA"
        ),
        ClausulaRequerida(
            id="CL05",
            nombre="Cooperación y Evidencia",
            descripcion="Obligación de documentar y colaborar en auditorías",
            criticidad="RECOMENDADA"
        ),
        ClausulaRequerida(
            id="CL06",
            nombre="Propiedad Intelectual",
            descripcion="Titularidad de entregables y contenidos",
            criticidad="RECOMENDADA"
        ),
        ClausulaRequerida(
            id="CL07",
            nombre="Confidencialidad",
            descripcion="Protección de información sensible",
            criticidad="RECOMENDADA"
        ),
        ClausulaRequerida(
            id="CL08",
            nombre="Cumplimiento Fiscal",
            descripcion="Manifestación de estar al corriente con SAT",
            criticidad="RECOMENDADA"
        ),
        ClausulaRequerida(
            id="CL09",
            nombre="REPSE (si aplica)",
            descripcion="Cumplimiento de subcontratación especializada",
            criticidad="OBLIGATORIA"
        ),
        ClausulaRequerida(
            id="CL10",
            nombre="Terminación",
            descripcion="Causales y procedimiento de terminación",
            criticidad="OPCIONAL"
        ),
    ]
    
    def evaluar_contrato(
        self,
        proyecto_id: str,
        tipo_servicio: str,
        tiene_contrato: bool,
        tiene_sow: bool,
        clausulas_presentes: List[str],  # IDs of clauses present
        requiere_repse: bool = False,
        fase: str = "F2"
    ) -> DictamenA4:
        """Evaluate contract/SOW"""
        
        # Map tipo_servicio to TipoContrato
        tipo_contrato = self._mapear_tipo_contrato(tipo_servicio)
        
        # Check clauses
        clausulas = self._verificar_clausulas(clausulas_presentes, requiere_repse)
        presentes = sum(1 for c in clausulas if c.presente)
        faltantes = sum(1 for c in clausulas if not c.presente and c.criticidad == "OBLIGATORIA")
        
        # Calculate score
        score = self._calcular_score(clausulas, tiene_contrato, tiene_sow)
        
        # Generate observations
        observaciones = self._generar_observaciones(clausulas, tiene_contrato, tiene_sow, requiere_repse)
        
        # Determine recommendations
        recomendacion_f2 = self._determinar_recomendacion_f2(score.total, observaciones, tiene_sow)
        recomendacion_f6 = self._determinar_recomendacion_f6(score.total, observaciones, tiene_contrato)
        
        # Generate dictamen and improvement areas
        dictamen = self._generar_dictamen(score, observaciones, fase)
        areas = self._generar_areas_mejora(clausulas, observaciones)
        
        return DictamenA4(
            proyecto_id=proyecto_id,
            tipo_contrato=tipo_contrato,
            tiene_contrato=tiene_contrato,
            tiene_sow=tiene_sow,
            clausulas=clausulas,
            clausulas_presentes=presentes,
            clausulas_faltantes=faltantes,
            score=score,
            observaciones=observaciones,
            recomendacion_f2=recomendacion_f2,
            recomendacion_f6=recomendacion_f6,
            dictamen=dictamen,
            areas_mejora=areas,
            fase_evaluacion=fase
        )
    
    def _mapear_tipo_contrato(self, tipo_servicio: str) -> TipoContrato:
        """Map service type to contract type"""
        mapping = {
            "CONSULTORIA": TipoContrato.CONSULTORÍA,
            "MARKETING": TipoContrato.MARKETING,
            "SOFTWARE": TipoContrato.DESARROLLO_SOFTWARE,
            "INTRAGRUPO": TipoContrato.INTRAGRUPO,
            "LICENCIA": TipoContrato.LICENCIAMIENTO,
        }
        return mapping.get(tipo_servicio.upper(), TipoContrato.PRESTACION_SERVICIOS)
    
    def _verificar_clausulas(self, presentes: List[str], requiere_repse: bool) -> List[ClausulaRequerida]:
        """Verify which clauses are present"""
        resultado = []
        for clausula in self.CLAUSULAS_MINIMAS:
            c = clausula.model_copy()
            c.presente = c.id in presentes
            
            # Adjust REPSE criticality
            if c.id == "CL09":
                if requiere_repse:
                    c.criticidad = "OBLIGATORIA"
                else:
                    c.criticidad = "OPCIONAL"
                    c.presente = True  # N/A counts as present
            
            resultado.append(c)
        return resultado
    
    def _calcular_score(
        self, 
        clausulas: List[ClausulaRequerida],
        tiene_contrato: bool,
        tiene_sow: bool
    ) -> ScoreDetalleA4:
        """Calculate legal score"""
        
        def get_clause_score(clause_id: str) -> int:
            for c in clausulas:
                if c.id == clause_id:
                    return 5 if c.presente else 0
            return 0
        
        # Objeto y alcance (CL01)
        objeto = get_clause_score("CL01")
        
        # Entregables y aceptación (CL02)
        entregables = get_clause_score("CL02")
        
        # Cooperación (CL05)
        cooperacion = get_clause_score("CL05")
        
        # PI y confidencialidad (CL06 + CL07)
        pi = 0
        if any(c.presente for c in clausulas if c.id in ["CL06", "CL07"]):
            pi = 5 if all(c.presente for c in clausulas if c.id in ["CL06", "CL07"]) else 3
        
        # Cumplimiento (CL08 + CL09)
        cumplimiento = 0
        if any(c.presente for c in clausulas if c.id in ["CL08", "CL09"]):
            cumplimiento = 5 if all(c.presente for c in clausulas if c.id in ["CL08", "CL09"]) else 3
        
        total = objeto + entregables + cooperacion + pi + cumplimiento
        
        return ScoreDetalleA4(
            objeto_alcance=objeto,
            entregables_aceptacion=entregables,
            cooperacion_evidencia=cooperacion,
            pi_confidencialidad=pi,
            cumplimiento_regulatorio=cumplimiento,
            total=min(total, 25)
        )
    
    def _generar_observaciones(
        self,
        clausulas: List[ClausulaRequerida],
        tiene_contrato: bool,
        tiene_sow: bool,
        requiere_repse: bool
    ) -> List[ObservacionLegal]:
        """Generate legal observations"""
        obs = []
        
        # Check for missing obligatory clauses
        faltantes_obligatorias = [c for c in clausulas if c.criticidad == "OBLIGATORIA" and not c.presente]
        if faltantes_obligatorias:
            for c in faltantes_obligatorias:
                obs.append(ObservacionLegal(
                    codigo=f"FALTA_{c.id}",
                    descripcion=f"Falta cláusula obligatoria: {c.nombre}",
                    severidad="ALTA" if c.id in ["CL01", "CL02"] else "MEDIA",
                    recomendacion=f"Incluir cláusula de {c.nombre.lower()} en el contrato"
                ))
        
        # Check REPSE specifically
        if requiere_repse:
            repse_clause = next((c for c in clausulas if c.id == "CL09"), None)
            if repse_clause and not repse_clause.presente:
                obs.append(ObservacionLegal(
                    codigo="REPSE_REQUERIDO",
                    descripcion="Servicio requiere REPSE y no hay cláusula de cumplimiento",
                    severidad="BLOQUEANTE",
                    recomendacion="Verificar registro REPSE del proveedor e incluir en contrato"
                ))
        
        # Check if no contract
        if not tiene_contrato and not tiene_sow:
            obs.append(ObservacionLegal(
                codigo="SIN_DOCUMENTO",
                descripcion="No existe contrato ni SOW",
                severidad="BLOQUEANTE",
                recomendacion="Formalizar relación con contrato o SOW mínimo"
            ))
        
        return obs
    
    def _determinar_recomendacion_f2(
        self, 
        score: int, 
        observaciones: List[ObservacionLegal],
        tiene_sow: bool
    ) -> RecomendacionA4:
        """Determine F2 recommendation (SOW review)"""
        bloqueantes = [o for o in observaciones if o.severidad == "BLOQUEANTE"]
        
        if bloqueantes:
            return RecomendacionA4.NO_APROBAR
        elif not tiene_sow:
            return RecomendacionA4.APROBAR_CON_MODIFICACIONES
        elif score >= 15:
            return RecomendacionA4.APROBAR
        else:
            return RecomendacionA4.APROBAR_CON_MODIFICACIONES
    
    def _determinar_recomendacion_f6(
        self, 
        score: int, 
        observaciones: List[ObservacionLegal],
        tiene_contrato: bool
    ) -> RecomendacionA4:
        """Determine F6 recommendation (final contract)"""
        bloqueantes = [o for o in observaciones if o.severidad == "BLOQUEANTE"]
        
        if bloqueantes:
            return RecomendacionA4.NO_APROBAR
        elif not tiene_contrato:
            return RecomendacionA4.APROBAR_CON_MODIFICACIONES
        elif score >= 20:
            return RecomendacionA4.APROBAR
        elif score >= 12:
            return RecomendacionA4.APROBAR_CON_MODIFICACIONES
        else:
            return RecomendacionA4.NO_APROBAR
    
    def _generar_dictamen(
        self, 
        score: ScoreDetalleA4, 
        observaciones: List[ObservacionLegal],
        fase: str
    ) -> str:
        """Generate dictamen text"""
        obs_count = len(observaciones)
        bloqueantes = sum(1 for o in observaciones if o.severidad == "BLOQUEANTE")
        
        if bloqueantes > 0:
            return f"Dictamen {fase}: NO APROBADO. Score {score.total}/25. {bloqueantes} observaciones bloqueantes."
        elif obs_count > 0:
            return f"Dictamen {fase}: APROBADO CON MODIFICACIONES. Score {score.total}/25. {obs_count} observaciones a atender."
        else:
            return f"Dictamen {fase}: APROBADO. Score {score.total}/25. Contrato conforme."
    
    def _generar_areas_mejora(
        self, 
        clausulas: List[ClausulaRequerida],
        observaciones: List[ObservacionLegal]
    ) -> List[str]:
        """Generate improvement areas"""
        areas = []
        
        faltantes = [c for c in clausulas if not c.presente and c.criticidad in ["OBLIGATORIA", "RECOMENDADA"]]
        for c in faltantes:
            areas.append(f"Agregar cláusula de {c.nombre.lower()}")
        
        return areas
