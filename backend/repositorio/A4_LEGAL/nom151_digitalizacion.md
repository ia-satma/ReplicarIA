# NOM-151-SCFI-2016 - Conservación de Mensajes de Datos

## Requisitos para Documentos Digitales con Valor Legal

---

## 1. Objetivo y Campo de Aplicación

### Objetivo
Establecer los requisitos que deben observarse para la conservación del contenido de mensajes de datos que consignen contratos, convenios o compromisos que den nacimiento a derechos y obligaciones.

### Campo de Aplicación
- Documentos digitales con efectos jurídicos
- Archivos electrónicos que sustituyen documentos físicos
- Registros electrónicos de operaciones

---

## 2. Requisitos de Conservación

### 2.1 Integridad
El mensaje de datos debe permanecer completo e inalterado desde que se generó por primera vez en su forma definitiva.

**Verificación:**
- Hash criptográfico del documento
- Sello de tiempo
- Cadena de custodia documentada

### 2.2 Accesibilidad
La información debe ser accesible para su posterior consulta.

**Requisitos:**
- Formato legible
- Metadatos preservados
- Índice de documentos

### 2.3 Identificación del Origen
Debe poder identificarse el origen y destino del mensaje de datos.

**Elementos:**
- Emisor identificado
- Receptor identificado
- Fecha y hora de generación

---

## 3. Constancia de Conservación

### Elementos de la Constancia
1. Nombre del archivo original
2. Hash SHA-256 del documento
3. Fecha y hora de la constancia
4. Firma electrónica del PSC
5. Sello digital de tiempo

### Prestadores de Servicios de Certificación (PSC)
Solo PSC autorizados por la Secretaría de Economía pueden emitir constancias válidas.

---

## 4. Requisitos Técnicos

### Formatos Aceptados
| Formato | Uso Recomendado |
|---------|-----------------|
| PDF/A | Documentos de texto |
| TIFF | Imágenes escaneadas |
| XML | Datos estructurados |
| PNG | Imágenes con transparencia |

### Metadatos Mínimos
```xml
<metadata>
  <titulo>{{TITULO_DOCUMENTO}}</titulo>
  <autor>{{AUTOR}}</autor>
  <fecha_creacion>{{FECHA}}</fecha_creacion>
  <hash_sha256>{{HASH}}</hash_sha256>
  <clasificacion>{{TIPO}}</clasificacion>
</metadata>
```

---

## 5. Procedimiento de Digitalización

### Paso 1: Preparación
- Verificar legibilidad del documento físico
- Remover grapas y dobleces
- Ordenar páginas secuencialmente

### Paso 2: Escaneo
- Resolución mínima: 200 DPI
- Color o escala de grises según contenido
- Verificar nitidez y completitud

### Paso 3: Indización
- Asignar nombre único al archivo
- Completar metadatos
- Clasificar por tipo y fecha

### Paso 4: Certificación
- Generar hash del documento
- Obtener sello de tiempo
- Emitir constancia NOM-151

### Paso 5: Almacenamiento
- Guardar en sistema seguro
- Respaldo redundante
- Control de acceso

---

## 6. Plazo de Conservación

### Documentos Fiscales
**5 años** a partir de la fecha en que se presentó o debió presentarse la declaración relacionada.

### Documentos Contables
**10 años** para sociedades mercantiles (Art. 46 Código de Comercio).

### Documentos Laborales
**5 años** después de terminada la relación laboral.

---

## 7. Aplicación en DUREZZA 4.0

### Documentos a Certificar
| Documento | Prioridad | Agente |
|-----------|-----------|--------|
| Contratos | Alta | A4 |
| CFDI | Alta | A3 |
| Entregables | Media | A2 |
| Comunicaciones | Media | A7 |
| Bitácoras | Baja | A2 |

### Flujo de Certificación
```
Documento → Hash SHA-256 → Sello de Tiempo → Constancia NOM-151 → Almacenamiento
```

### Integración con Defense File
Cada expediente de defensa debe incluir:
- Constancias NOM-151 de documentos clave
- Cadena de hashes verificable
- Timeline de certificaciones

---

## 8. Checklist de Cumplimiento NOM-151

### Para Cada Documento Digital
- [ ] Formato compatible (PDF/A, TIFF, XML)
- [ ] Resolución mínima 200 DPI (si es escaneo)
- [ ] Metadatos completos
- [ ] Hash SHA-256 generado
- [ ] Sello de tiempo aplicado
- [ ] Constancia de conservación emitida
- [ ] Respaldo en sistema seguro

---
*NOM-151-SCFI-2016 - Consultar texto oficial en DOF.*
