# Oráculo Estratégico - Integración con ReplicarIA

## Resumen

El **Oráculo Estratégico** es un sistema de investigación empresarial profunda desplegado como Cloudflare Worker que proporciona análisis exhaustivo en 14 fases para documentar materialidad de servicios intangibles.

## Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────────────┐
│                        ReplicarIA Backend                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌───────────────────────────────────┐  │
│  │  Tool Registry   │◄───│  research_tools.py                │  │
│  │  (registry.py)   │    │  - investigar_empresa_profunda    │  │
│  └────────┬─────────┘    │  - due_diligence_proveedor        │  │
│           │              │  - documentar_materialidad_sat     │  │
│           │              │  - analisis_pestel                 │  │
│           │              │  - analisis_porter                 │  │
│           │              │  - analisis_esg                    │  │
│           │              │  - validar_razon_negocios          │  │
│           │              └───────────────┬───────────────────┘  │
│           │                              │                       │
│           │              ┌───────────────▼───────────────────┐  │
│           │              │  oraculo_estrategico_service.py   │  │
│           │              │  (HTTP Client → Worker)            │  │
│           │              └───────────────┬───────────────────┘  │
│           │                              │                       │
│  ┌────────▼─────────┐                    │ HTTP/REST            │
│  │     Agentes      │                    │                       │
│  │  ┌────────────┐  │                    │                       │
│  │  │A6_PROVEEDOR│◄─┼────────────────────┘                       │
│  │  │Due Diligence│ │                                            │
│  │  └────────────┘  │                                            │
│  │  ┌────────────┐  │                                            │
│  │  │S2_MATERIAL │◄─┼────────────────────┘                       │
│  │  │  IDAD      │  │                                            │
│  │  └────────────┘  │                                            │
│  │  ┌────────────┐  │                                            │
│  │  │ A3_FISCAL  │◄─┼────────────────────┘                       │
│  │  └────────────┘  │                                            │
│  │  ┌────────────┐  │                                            │
│  │  │ A1_SPONSOR │◄─┼────────────────────┘                       │
│  │  └────────────┘  │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Cloudflare Workers                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             oraculo-estrategico.workers.dev               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Scraping  │  │   Claude    │  │  Perplexity │       │   │
│  │  │  (Firecrawl)│  │  (14 fases) │  │ (sonar-pro) │       │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │   │
│  │         │                │                │               │   │
│  │         └────────────────┼────────────────┘               │   │
│  │                          ▼                                │   │
│  │              ┌───────────────────────┐                    │   │
│  │              │    Consolidador       │                    │   │
│  │              │  (14 tipos análisis)  │                    │   │
│  │              └───────────────────────┘                    │   │
│  │                                                           │   │
│  │  Tipos de Análisis:                                       │   │
│  │  • empresa, industria, economia, competidores             │   │
│  │  • oportunidades, pestel, porter, tendencias              │   │
│  │  • esg, ecosistema, digital, materialidad                 │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Herramientas Disponibles

### 1. `investigar_empresa_profunda`
Investigación exhaustiva de empresa con análisis en 14 fases.

**Uso típico:** Inicio de Due Diligence, evaluación de nuevo proveedor.

```python
resultado = await registry.invoke("investigar_empresa_profunda", {
    "empresa": "Acme Consulting S.A. de C.V.",
    "sitio_web": "https://acme-consulting.mx",
    "sector": "Consultoría empresarial",
    "contexto": "Evaluación para contrato de marketing digital"
})
```

### 2. `due_diligence_proveedor`
Due Diligence completo para agente A6_PROVEEDOR.

**Fases de uso:** F3-F5

```python
resultado = await registry.invoke("due_diligence_proveedor", {
    "empresa": "Digital Solutions MX",
    "rfc": "DSM180115ABC",
    "sitio_web": "https://digitalsolutions.mx",
    "monto_operacion": 500000.00,
    "tipo_servicio": "Desarrollo de software"
})

# Respuesta incluye:
# - evaluacion_riesgo: {"score": 85, "nivel": "BAJO", "factores": [...]}
# - banderas_rojas: ["Sin presencia web verificable"]
# - apto_para_operacion: {"apto": True, "nivel_confianza": 85}
# - recomendaciones: ["Verificar RFC en Lista 69-B", ...]
```

### 3. `documentar_materialidad_sat`
Genera documentación de materialidad para S2_MATERIALIDAD.

**Cumple con:** Art. 69-B CFF

**Fases de uso:** F5-F6

```python
resultado = await registry.invoke("documentar_materialidad_sat", {
    "empresa": "Marketing Pro",
    "rfc": "MPR200520XYZ",
    "servicio_contratado": "Campaña de marketing digital Q1 2026",
    "monto": 1200000.00,
    "sitio_web": "https://marketingpro.mx",
    "documentos_existentes": ["Contrato", "Factura CFDI", "Brief creativo"]
})

# Respuesta incluye:
# - score_materialidad: 75
# - pilares_documentados: {
#     "razon_de_negocios": {...},
#     "capacidad_operativa": {...},
#     "proporcionalidad": {...},
#     "evidencia_ejecucion": {...},
#     "consistencia_documental": {...}
#   }
# - documentos_sugeridos: ["Acta de recepción", "Opinión 32-D", ...]
# - conclusion: "La operación requiere documentación adicional..."
```

### 4. `analisis_pestel`
Análisis macro-ambiental para A1_SPONSOR.

```python
resultado = await registry.invoke("analisis_pestel", {
    "empresa": "TechStart",
    "sector": "Fintech",
    "pais": "México"
})
```

### 5. `analisis_porter`
5 Fuerzas de Porter para evaluación estratégica.

```python
resultado = await registry.invoke("analisis_porter", {
    "empresa": "PaymentCo",
    "sector": "Procesamiento de pagos"
})
```

### 6. `analisis_esg`
Evaluación Environmental, Social, Governance.

```python
resultado = await registry.invoke("analisis_esg", {
    "empresa": "GreenTech Solutions",
    "sitio_web": "https://greentech.mx"
})
```

### 7. `validar_razon_negocios`
Validación de razón de negocios para A3_FISCAL.

```python
resultado = await registry.invoke("validar_razon_negocios", {
    "empresa_cliente": "Mi Empresa S.A.",
    "empresa_proveedor": "Consultor XYZ",
    "servicio": "Estudio de mercado sector retail",
    "monto": 350000.00,
    "justificacion": "Expandir operaciones a nuevos mercados",
    "sector_cliente": "Retail"
})
```

## Integración por Agente

### A6_PROVEEDOR (Due Diligence)

El agente A6 debe usar las herramientas en este orden:

1. **F0/F1 - Alta de proveedor nuevo:**
   ```
   1. query_sat_lista_69b (verificar lista negra)
   2. due_diligence_proveedor (investigación completa)
   ```

2. **F2 - Candado de inicio:**
   ```
   Validar que due_diligence_proveedor.apto_para_operacion.apto == True
   ```

3. **F6 - Candado fiscal:**
   ```
   Re-ejecutar query_sat_lista_69b (verificar cambios)
   ```

### S2_MATERIALIDAD (Subagente Fiscal)

1. **F5 - Entrega del servicio:**
   ```
   documentar_materialidad_sat con servicio completado
   ```

2. **F6 - VBC Fiscal:**
   ```
   Verificar score_materialidad >= 70 para aprobar
   ```

### A3_FISCAL

1. **F0 - Evaluación inicial:**
   ```
   validar_razon_negocios para verificar coherencia
   ```

2. **F6 - Dictamen fiscal:**
   ```
   Consumir resultados de S2_MATERIALIDAD y A6_PROVEEDOR
   ```

### A1_SPONSOR

1. **F0 - Evaluación estratégica:**
   ```
   analisis_pestel + analisis_porter para contexto sectorial
   ```

## Configuración

### Variables de Entorno

```bash
# URL del Worker desplegado
ORACULO_WORKER_URL=https://oraculo-estrategico.tu-cuenta.workers.dev

# Opcional: Timeout personalizado (default: 300s)
ORACULO_REQUEST_TIMEOUT=300
```

### Despliegue del Worker

El Worker se despliega en Cloudflare usando Wrangler:

```bash
cd cloudflare-workers/oraculo-estrategico
npx wrangler deploy
```

Ver `cloudflare-workers/oraculo-estrategico/wrangler.toml` para configuración.

## Flujo de Datos

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Agente LLM    │────▶│  Tool Registry  │────▶│ research_tools  │
│  (A6_PROVEEDOR) │     │   invoke()      │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   JSON Result   │◀────│ OraculoService  │◀────│ Cloudflare      │
│   to Agent      │     │                 │     │ Worker          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Manejo de Errores

El servicio retorna siempre un objeto con `success: bool`:

```python
{
    "success": False,
    "error": "Descripción del error",
    "message": "Mensaje amigable para usuario"
}
```

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "Servicio no configurado" | ORACULO_WORKER_URL no definida | Configurar variable de entorno |
| "Timeout" | Investigación muy larga | Usar tipos específicos en lugar de completa |
| "Worker error: 500" | Error en Worker | Verificar logs de Cloudflare |

## Métricas y Monitoreo

El servicio registra logs en cada invocación:

```
INFO: Tool: due_diligence_proveedor - Digital Solutions MX
INFO: Investigación completa exitosa: Digital Solutions MX
```

Para monitoreo avanzado, integrar con el sistema de métricas de ReplicarIA en `routes/metrics.py`.

## Próximas Mejoras

1. **Cache de resultados** - Evitar re-investigación de proveedores recientes
2. **Investigación incremental** - Actualizar solo cambios desde última investigación
3. **Integración con pCloud** - Almacenar reportes en carpetas de agentes
4. **Alertas automáticas** - Notificar cuando proveedor cae en 69-B
