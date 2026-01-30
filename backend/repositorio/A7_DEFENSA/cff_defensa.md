# CFF - Artículos para Defensa Fiscal

## Extracto de Código Fiscal de la Federación

---

## 1. Medios de Defensa

### Artículo 117 - Recurso de Revocación
Los contribuyentes podrán interponer el recurso de revocación contra:
- Resoluciones definitivas de autoridades fiscales
- Actos administrativos dictados en materia fiscal federal

**Plazo:** 30 días hábiles siguientes a la notificación

### Artículo 121 - Requisitos del Recurso
El escrito de interposición deberá contener:
1. Nombre y domicilio del recurrente
2. Resolución o acto que se impugna
3. Agravios que causa la resolución
4. Pruebas y hechos controvertidos
5. Firma del interesado

### Artículo 123 - Pruebas Admisibles
Se admitirán toda clase de pruebas, excepto:
- La testimonial
- La confesión de las autoridades

**Nota:** Los documentos deben exhibirse en original o copia certificada.

---

## 2. Derechos del Contribuyente

### Artículo 2 - Principios
Los contribuyentes tienen derecho a:
- Recibir asistencia gratuita del SAT
- Conocer el estado de sus trámites
- Obtener certificación de documentos
- Formular consultas y obtener respuesta

### Artículo 22 - Devolución de Saldos
Los contribuyentes tienen derecho a la devolución de cantidades pagadas indebidamente.

**Plazo SAT para resolver:** 40 días hábiles

### Artículo 34 - Consultas
Los contribuyentes pueden formular consultas a las autoridades fiscales sobre situaciones reales y concretas.

**Plazo SAT para responder:** 3 meses

---

## 3. Defensa contra 69-B

### Artículo 69-B - Procedimiento de Defensa

**Paso 1:** Notificación al contribuyente
- Se publica en DOF y portal SAT
- Se notifica personalmente

**Paso 2:** Plazo de defensa
- **15 días hábiles** para manifestar lo que convenga
- Aportar documentación comprobatoria

**Paso 3:** Resolución
- SAT tiene 50 días para resolver
- Notificación de resolución definitiva

### Documentación para Desvirtuar
Según el propio artículo 69-B:
- Contratos de prestación de servicios
- Evidencia de entrega del servicio
- Comprobantes de pago
- Registros contables
- Cualquier otro medio de prueba

---

## 4. Prescripción y Caducidad

### Artículo 67 - Caducidad de Facultades
Las facultades de las autoridades fiscales para determinar contribuciones omitidas se extinguen en:
- **5 años** contados desde la fecha de presentación de declaración
- **10 años** si no se presentó declaración

### Artículo 146 - Prescripción de Créditos
Los créditos fiscales se extinguen por prescripción en **5 años**.

---

## 5. Garantía de Audiencia

### Artículo 75 - Procedimiento de Audiencia
Las autoridades fiscales:
1. Deben notificar el inicio del procedimiento
2. Otorgar plazo para ofrecer pruebas
3. Desahogar las pruebas ofrecidas
4. Emitir resolución fundada y motivada

### Artículo 38 - Requisitos de Notificación
Los actos administrativos deben ser notificados:
- Personalmente
- Por correo certificado con acuse de recibo
- Por estrados
- Por buzón tributario

---

## 6. Argumentos de Defensa Comunes

### Vicios de Procedimiento
| Vicio | Fundamento | Efecto |
|-------|------------|--------|
| Falta de fundamentación | Art. 38, fracc. IV | Nulidad |
| Falta de motivación | Art. 38, fracc. V | Nulidad |
| Notificación ilegal | Art. 134 | Nulidad |
| Incompetencia | Art. 13 | Nulidad |
| Violación de plazo | Varios | Nulidad |

### Vicios de Fondo
| Vicio | Fundamento | Efecto |
|-------|------------|--------|
| Materialidad acreditada | Art. 69-B | Archivo |
| Pago indebido | Art. 22 | Devolución |
| Prescripción | Art. 146 | Extinción |
| Caducidad | Art. 67 | Archivo |

---

## 7. Plazos Clave para Defensa

| Acto | Plazo | Fundamento |
|------|-------|------------|
| Recurso de revocación | 30 días hábiles | Art. 121 |
| Juicio contencioso | 30 días hábiles | LFPCA |
| Amparo indirecto | 15 días | Ley de Amparo |
| Manifestación 69-B | 15 días hábiles | Art. 69-B |
| Solicitud de condonación | Variable | RMF |

---

## 8. Aplicación en DUREZZA 4.0

### Automatización de Defensa
| Escenario | Acción | Agente |
|-----------|--------|--------|
| Notificación 69-B | Generar expediente defensa | A7 |
| Requerimiento SAT | Compilar documentación | A7 |
| Auditoría fiscal | Preparar respuesta | A7, A3 |
| Crédito fiscal | Analizar viabilidad defensa | A7 |

### Estructura del Expediente de Defensa
```
/defensa_{{PROYECTO_ID}}/
├── argumentos_legales/
│   ├── fundamentos_cff.pdf
│   └── agravios.docx
├── pruebas/
│   ├── contrato.pdf
│   ├── evidencias_materialidad/
│   └── pagos_bancarios/
├── timeline/
│   └── cronologia_operacion.pdf
└── escritos/
    └── recurso_revocacion.docx
```

---
*Extracto del CFF vigente - Verificar versión actualizada en DOF.*
