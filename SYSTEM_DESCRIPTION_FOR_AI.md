# REVISAR.IA - Descripción Técnica Completa para Revisión por IA

## Propósito de este Documento
Este documento describe el sistema REVISAR.IA para que otra inteligencia artificial especializada pueda analizarlo y proporcionar recomendaciones de mejora para la red de agentes y sus funcionalidades.

---

## 1. VISIÓN GENERAL

**REVISAR.IA** es un sistema multi-agente de IA para la trazabilidad de servicios intangibles y consultoría especializada en el contexto regulatorio mexicano. Su objetivo principal es:

1. **Prevenir** deducciones fiscales cuestionables antes de que el SAT las rechace
2. **Documentar** la materialidad de servicios contratados
3. **Generar** expedientes de defensa fiscal (Defense Files) estructurados
4. **Automatizar** el flujo de validación de servicios en 10 fases (F0-F9)

### Contexto Legal Mexicano
- **LISR Art. 27**: Requisitos de deducibilidad
- **CFF Art. 5-A**: Razón de negocios
- **CFF Art. 69-B**: Operaciones inexistentes (EFOS)
- **LIVA Art. 5**: Acreditamiento de IVA
- **Anexo 20**: Estructura de CFDI

---

## 2. ARQUITECTURA DE AGENTES

### 2.1 Agentes Principales (A1-A7)

| ID | Nombre | Rol | Responsabilidad Principal |
|----|--------|-----|---------------------------|
| **A1** | María Rodríguez | Directora Estrategia | Validar razón de negocios (Art. 5-A CFF) y BEE |
| **A2** | Carlos Mendoza | Director PMO | Coordinar fases F0-F9, gestionar candados |
| **A3** | Laura Sánchez | Especialista Fiscal | Dictamen de deducibilidad (LISR 27) |
| **A4** | Ana García | Directora Legal | Validación contractual y materialidad |
| **A5** | Roberto Sánchez | Director Finanzas | Análisis ROI/NPV, 3-Way Match |
| **A6** | DD Proveedor | Validación Proveedores | Due diligence, verificación 69-B |
| **A7** | Laura Vázquez | Defensa Fiscal | Generación de Defense Files |

### 2.2 Agentes de Soporte

| ID | Nombre | Responsabilidad |
|----|--------|-----------------|
| **A8** | Diego Ramírez | Auditoría documental |
| **KB** | Dra. Elena Vázquez | Knowledge Base / Curator |
| **Guardian** | Sistema | Monitoreo de salud del sistema |

### 2.3 Subagentes Especializados

| ID | Función |
|----|---------|
| **S1** | Tipificación de servicios |
| **S2** | Evaluación de materialidad |
| **S3** | Cálculo de riesgos fiscales |

---

## 3. FLUJO DE TRABAJO F0-F9

```
F0 (INTAKE)     → Captura SIB/BEE, dictamen A1 preliminar
    ↓
F1 (PROVEEDOR)  → Datos proveedor, SOW preliminar
    ↓
F2 (CANDADO)    → ⛔ Validación A1+A6, autorización de inicio
    ↓
F3 (EJECUCIÓN)  → Kick-off, plan de trabajo
    ↓
F4 (REVISIÓN)   → Entregables iterativos, observaciones
    ↓
F5 (ENTREGA)    → Acta de aceptación técnica
    ↓
F6 (VBC)        → ⛔ Candado Fiscal/Legal (A3+A4)
    ↓
F7 (AUDITORÍA)  → QA interno del expediente
    ↓
F8 (PAGO)       → ⛔ 3-Way Match (PO=Acta=CFDI)
    ↓
F9 (CIERRE)     → Seguimiento BEE, Defense File final
```

### Candados de Control
- **F2**: No avanzar sin razón de negocios (A1) y proveedor validado (A6)
- **F6**: No avanzar sin dictamen fiscal (A3) y legal (A4)
- **F8**: No pagar sin 3-Way Match completo

---

## 4. SISTEMA DE VALIDACIÓN LEGAL

### 4.1 Tres Capas de Validación

| Capa | Peso | Reglas Principales |
|------|------|-------------------|
| **Formal-Fiscal** | 35% | CFDI válido, LISR 27, pago bancarizado |
| **Materialidad** | 40% | CFF 69-B, evidencia de prestación real |
| **Razón de Negocios** | 25% | CFF 5-A, justificación económica |

### 4.2 Reglas Implementadas

```python
# LISR 27
LISR_27_I      # Estricta indispensabilidad (peso: 1.5)
LISR_27_III    # Efectivamente erogado (peso: 1.2)
LISR_27_CFDI   # CFDI válido (peso: 1.3)
LISR_27_PARTES_REL  # Partes relacionadas

# CFF 69-B / 5-A
CFF_69B_PROVEEDOR      # Lista 69-B (peso: 2.0 - CRÍTICO)
CFF_69B_MATERIALIDAD   # Acreditación de materialidad (peso: 1.8)
CFF_5A_RAZON          # Razón de negocios (peso: 1.5)

# LIVA / Anexo 20
LIVA_5_ACREDITAMIENTO  # IVA trasladado y pagado
ANEXO20_ESTRUCTURA     # Estructura CFDI correcta
```

### 4.3 Sistema de Semáforo

| Color | Score | Significado |
|-------|-------|-------------|
| 🟢 VERDE | ≥80% | Operación segura |
| 🟡 AMARILLO | 50-79% | Revisar documentación |
| 🔴 ROJO | <50% o 69-B | Alto riesgo |

---

## 5. TIPOS DE SERVICIO SOPORTADOS

| ID | Tipo | Riesgo Inherente |
|----|------|------------------|
| consultoria | Consultoría | Medio |
| tecnologia | Tecnología/Software | Medio |
| marketing | Marketing/Publicidad | Alto |
| legal | Servicios Legales | Bajo |
| contable | Contabilidad/Auditoría | Bajo |
| outsourcing | Tercerización | Alto |
| capacitacion | Capacitación | Medio |
| transporte | Logística | Bajo |
| mantenimiento | Mantenimiento | Bajo |
| honorarios | Honorarios Profesionales | Medio |
| arrendamiento | Arrendamiento | Bajo |
| servicios_generales | Servicios Generales | Medio |

---

## 6. DEFENSE FILE (EXPEDIENTE DE DEFENSA)

### Estructura del Defense File

1. **Carátula** - Datos generales
2. **Índice** - Secciones y anexos
3. **Resumen Ejecutivo** - Qué, por qué, cuánto
4. **Razón de Negocios** - Dictamen A1 + Art. 5-A
5. **Beneficio Económico** - ROI/NPV de A5
6. **Matriz de Materialidad** - Evidencia por pilar
7. **Análisis Fiscal** - Dictamen A3
8. **Análisis Legal** - Dictamen A4
9. **Due Diligence Proveedor** - Reporte A6
10. **Cronología F0-F9** - Timeline de eventos
11. **Matriz de Riesgos** - Probabilidad × Impacto
12. **Argumentación** - Hechos → Pruebas → Norma → Conclusión
13. **Anexos** - Documentos soporte

### Niveles de Defensa
- **FUERTE**: Score ≥80, todos los pilares cubiertos
- **MODERADA**: Score 60-79, algunos gaps menores
- **DÉBIL**: Score <60, gaps críticos

---

## 7. INTEGRACIONES

### Bases de Datos
- **PostgreSQL**: Base de datos principal con connection pooling (min=2, max=20)
- **Redis**: Cache distribuido para configuraciones y agentes (opcional, graceful fallback)

### APIs Externas
- **OpenAI**: GPT-4 para agentes principales
- **Anthropic**: Claude para agentes especializados
- **SAT Oficial**: 
  - Lista 69-B (Definitivos.csv) - 11,000+ registros reales
  - Validación CFDI vía SOAP (ConsultaCFDIService)

### Almacenamiento
- **pCloud**: Documentos estructurados por agente
- **Local Cache**: SAT blacklist con TTL de 7 días

### Arquitectura de Herramientas (Tools)
Los agentes pueden invocar herramientas especializadas mediante function calling:

| Herramienta | Archivo | Descripción |
|-------------|---------|-------------|
| `query_sat_lista_69b` | `tools/compliance_tools.py` | Consulta lista negra SAT (11k+ registros) |
| `check_compliance_obligations` | `tools/compliance_tools.py` | Verificación de obligaciones fiscales |
| `calculate_roi` | `tools/financial_tools.py` | Cálculo de ROI/NPV |
| `validate_cfdi` | `tools/financial_tools.py` | Validación oficial de CFDI via SOAP |

---

## 8. MÉTRICAS Y KPIs

### Por Agente
- Decisiones tomadas
- Precisión (vs resultado final)
- Tiempo promedio de respuesta
- Escalamientos a humano

### Por Proyecto
- Índice de defendibilidad (0-100)
- Completitud documental (%)
- Risk score final
- Tiempo en cada fase

### Rendimiento del Sistema
- **Cache Redis**: Hit rate, keys activas, latencia
- **PDF Generation**: ~0.1s (non-blocking via thread pool)
- **SAT 69-B Lookup**: ~0.00s warm, ~0.04s cold (in-memory cache)

---

## 9. ÁREAS DE MEJORA IDENTIFICADAS

### 9.1 Red de Agentes
- [ ] Implementar memoria conversacional entre agentes
- [ ] Mejorar resolución de conflictos inter-agentes
- [ ] Añadir agente de "segundo opinión" para casos críticos

### 9.2 Validación Legal
- [x] ~~Integración directa con API de SAT (69-B)~~ ✅ Implementado (11k+ registros reales)
- [x] ~~Validación de CFDI en tiempo real~~ ✅ SOAP endpoint oficial
- [ ] Detección de patrones EFOS por machine learning

### 9.3 Defense Files
- [x] ~~Generación automática de PDF~~ ✅ Non-blocking export service
- [ ] Templates por tipo de controversia SAT
- [ ] Integración con TFJA (sentencias y criterios)

### 9.4 Experiencia de Usuario
- [ ] Dashboard de riesgo consolidado
- [ ] Alertas proactivas de vencimientos
- [ ] Modo "simulación de auditoría SAT"

### 9.5 Performance (COMPLETADO ✅)
- [x] Connection pooling PostgreSQL
- [x] Redis caching para configuraciones
- [x] Parallel agent execution (asyncio.gather)
- [x] Non-blocking PDF generation
- [x] In-memory SAT blacklist cache

---

## 10. PREGUNTAS PARA LA IA REVISORA

1. **Arquitectura de Agentes**:
   - ¿La división de responsabilidades es óptima?
   - ¿Faltan agentes especializados para algún caso de uso?
   - ¿Cómo mejorar la coordinación entre agentes?

2. **Validación Legal**:
   - ¿Las reglas implementadas cubren los escenarios principales?
   - ¿Qué reglas adicionales de LISR/CFF deberían implementarse?
   - ¿Cómo mejorar la detección de riesgo EFOS?

3. **Defense Files**:
   - ¿La estructura cumple con mejores prácticas de defensa fiscal?
   - ¿Qué secciones adicionales serían valiosas?
   - ¿Cómo automatizar más la argumentación?

4. **Flujo de Trabajo**:
   - ¿El modelo F0-F9 es adecuado?
   - ¿Los candados de control están bien ubicados?
   - ¿Qué excepciones adicionales deberían contemplarse?

5. **Escalabilidad**:
   - ¿Cómo manejar 1000+ proyectos simultáneos?
   - ¿Qué optimizaciones de performance son prioritarias?

---

## APÉNDICE: ARCHIVOS CLAVE DEL CÓDIGO

### Servicios Core
| Archivo | Descripción |
|---------|-------------|
| `backend/services/agent_orchestrator.py` | Orquestación de agentes con parallel execution |
| `backend/services/legal_validation_service.py` | Reglas de validación LISR/CFF (83KB) |
| `backend/services/defense_file_pg_service.py` | Defense File CRUD (PostgreSQL) |
| `backend/services/defense_file_export_service.py` | PDF export non-blocking |
| `backend/services/subagent_executor.py` | Ejecución de S1/S2/S3 |

### Herramientas de Agentes
| Archivo | Descripción |
|---------|-------------|
| `backend/services/tools/registry.py` | ToolRegistry y decorador @tool |
| `backend/services/tools/compliance_tools.py` | SAT 69-B real, obligaciones |
| `backend/services/tools/financial_tools.py` | ROI, CFDI SOAP validation |

### Infraestructura
| Archivo | Descripción |
|---------|-------------|
| `backend/services/database_pg.py` | PostgreSQL connection pool |
| `backend/services/cache_service.py` | Redis cache with TTL decorators |

### Configuración
| Archivo | Descripción |
|---------|-------------|
| `backend/config/agents_config.py` | Configuración de 10 agentes |
| `backend/services/specialized_agent_prompts.py` | Prompts con "superpoderes" |

---

*Documento generado para revisión por IA especializada*
*REVISAR.IA v2.0 - Enero 2026*
*Última auditoría: Enero 31, 2026 - Sistema verificado y optimizado*
