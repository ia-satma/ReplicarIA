# Models package

from .durezza_enums import (
    TipologiaProyecto, FaseProyecto, EstadoGlobal, TipoRelacionProveedor,
    EstadoFase, TipoAgente, DecisionAgente, TipoDocumento, AccionAuditLog,
    StatusPilar, EstadoEvidencia, ResponsableChecklist, EstadoMaterialidad
)

from .durezza_models import (
    Project, Supplier, ProjectPhase, AgentDeliberation, DefenseFile,
    ChecklistTemplate, AgentConfig, Document, AuditLog,
    ConclusionPilar, ChecklistEvidenciaItem, AnalisisEstructurado,
    DocumentoDefenseFile, MatrizMaterialidadItem, ResumenAprobacionGlobal,
    ChecklistTemplateItem, DecisionAprobacion
)

from .versioning import (
    TipoCambio,
    Severidad,
    EntradaBitacora,
    VersionExpediente,
    ProyectoVersionado,
    generar_folio_base,
    generar_hash_contenido,
    crear_entrada_bitacora
)
