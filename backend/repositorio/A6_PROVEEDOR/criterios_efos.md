# Criterios para Identificar EFOS

## Indicadores de Operaciones Simuladas

---

## 1. Definición de EFOS

**EFOS:** Empresas que Facturan Operaciones Simuladas

Son contribuyentes que emiten comprobantes fiscales por operaciones inexistentes, permitiendo a terceros:
- Deducir gastos ficticios
- Acreditar IVA no enterado
- Disminuir artificialmente la base gravable

---

## 2. Red Flags del Proveedor

### 2.1 Perfil Empresarial
| Indicador | Nivel de Riesgo |
|-----------|-----------------|
| Empresa recién constituida (<2 años) | Medio |
| Capital social mínimo ($50,000) | Alto |
| Objeto social muy amplio | Alto |
| Múltiples actividades no relacionadas | Alto |
| Cambios frecuentes de domicilio | Crítico |

### 2.2 Infraestructura
| Indicador | Nivel de Riesgo |
|-----------|-----------------|
| Sin oficinas físicas verificables | Crítico |
| Sin empleados registrados en IMSS | Crítico |
| Sin activos fijos | Alto |
| Domicilio en oficina virtual | Alto |
| Sin página web ni presencia digital | Medio |

### 2.3 Comportamiento Fiscal
| Indicador | Nivel de Riesgo |
|-----------|-----------------|
| Opinión 32-D negativa | Crítico |
| Sin declaraciones presentadas | Crítico |
| Declaraciones en ceros | Alto |
| Facturación muy superior a capacidad | Crítico |
| Clientes concentrados (1-2) | Alto |

---

## 3. Red Flags de la Operación

### 3.1 Características Sospechosas
| Indicador | Descripción | Riesgo |
|-----------|-------------|--------|
| Precio fuera de mercado | >30% arriba o abajo | Alto |
| Pago en efectivo | Sin trazabilidad | Crítico |
| Sin contrato | Informalidad | Alto |
| Descripción genérica en CFDI | "Servicios varios" | Alto |
| Factura al final del período | Ajuste de resultados | Medio |

### 3.2 Falta de Materialidad
| Indicador | Descripción | Riesgo |
|-----------|-------------|--------|
| Sin evidencia de entregables | No hay producto | Crítico |
| Sin comunicaciones | No hay interacción | Alto |
| Sin horas trabajadas | No hay esfuerzo | Alto |
| Fechas inconsistentes | Contrato posterior a CFDI | Crítico |
| Servicio no relacionado con giro | Sin razón de negocio | Alto |

---

## 4. Perfil Típico de EFOS

### Características Comunes
1. **Edad:** Constituida en los últimos 2-3 años
2. **Capital:** Mínimo legal ($50,000)
3. **Socios:** Personas físicas sin historial empresarial
4. **Domicilio:** Virtual o compartido
5. **Empleados:** Cero o mínimos
6. **Facturación:** Alta en relación a infraestructura
7. **Clientes:** Pocos, con montos altos

### Modus Operandi
```
1. Constitución de empresa "limpia"
2. Alta ante SAT con múltiples actividades
3. Operación por 12-24 meses
4. Emisión masiva de CFDI
5. No pago de impuestos
6. Cambio de domicilio / baja
7. Repetir con nueva empresa
```

---

## 5. Matriz de Evaluación de Riesgo

### Scoring de Proveedor
| Factor | Peso | Puntos |
|--------|------|--------|
| Lista 69-B | 30% | 0-100 |
| Opinión 32-D | 25% | 0-100 |
| Antigüedad empresa | 15% | 0-100 |
| Infraestructura | 15% | 0-100 |
| Historial comercial | 15% | 0-100 |

### Interpretación
| Score | Nivel | Acción |
|-------|-------|--------|
| 80-100 | Verde | Operar normalmente |
| 60-79 | Amarillo | Documentación reforzada |
| 40-59 | Naranja | Supervisión cercana |
| 0-39 | Rojo | Rechazar operación |

---

## 6. Due Diligence Recomendado

### Nivel Básico (< $100,000 MXN)
- [ ] Consulta Lista 69-B
- [ ] Consulta Opinión 32-D
- [ ] Verificación de RFC activo
- [ ] CFDI con descripción detallada

### Nivel Estándar ($100,000 - $500,000 MXN)
- [ ] Todo lo anterior +
- [ ] Contrato firmado
- [ ] Verificación de domicilio fiscal
- [ ] Referencias comerciales
- [ ] Evidencia de entregables

### Nivel Reforzado (> $500,000 MXN)
- [ ] Todo lo anterior +
- [ ] Acta constitutiva
- [ ] Poderes del representante
- [ ] Estados financieros auditados
- [ ] Visita a instalaciones
- [ ] Validación de empleados IMSS

---

## 7. Preguntas Clave al Proveedor

### Sobre la Empresa
1. ¿Cuántos empleados tiene?
2. ¿Dónde están sus oficinas?
3. ¿Cuáles son sus principales clientes?
4. ¿Desde cuándo opera?
5. ¿Tiene página web o redes sociales?

### Sobre el Servicio
1. ¿Quién realizará el trabajo?
2. ¿Qué entregables recibiré?
3. ¿Cómo documentan el avance?
4. ¿Pueden proporcionar referencias?
5. ¿Aceptan pago bancario?

---

## 8. Documentación Preventiva

### Expediente por Proveedor
```
/proveedor_{{RFC}}/
├── alta_proveedor/
│   ├── constancia_situacion_fiscal.pdf
│   ├── opinion_32d.pdf
│   ├── acta_constitutiva.pdf
│   └── poder_representante.pdf
├── verificaciones/
│   ├── consulta_69b_{{FECHA}}.pdf
│   ├── verificacion_domicilio.pdf
│   └── referencias_comerciales.pdf
└── operaciones/
    ├── contrato_{{NUM}}.pdf
    ├── orden_{{NUM}}.pdf
    └── entregables_{{NUM}}/
```

---

## 9. Aplicación en DUREZZA 4.0

### Automatización de Verificación
| Paso | Acción | Frecuencia |
|------|--------|------------|
| 1 | Consulta 69-B | Por operación |
| 2 | Consulta 32-D | Mensual |
| 3 | Scoring de riesgo | Por operación |
| 4 | Alerta automática | Cambio de status |

### Umbrales de Alerta
```python
if score < 40:
    return "RECHAZAR"
elif score < 60:
    return "REQUIERE_APROBACION_ESPECIAL"
elif score < 80:
    return "DOCUMENTACION_REFORZADA"
else:
    return "APROBADO"
```

---
*Criterios actualizados según mejores prácticas de prevención.*
