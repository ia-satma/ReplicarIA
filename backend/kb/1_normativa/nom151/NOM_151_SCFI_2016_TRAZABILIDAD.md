# [NORMA] NOM-151-SCFI-2016: Conservacion de Mensajes de Datos

## Texto Normativo (Extracto)

Esta Norma Oficial Mexicana establece los requisitos que deben observarse para la conservacion de mensajes de datos y digitalizacion de documentos.

### Requisitos de conservacion:
1. Mantener la integridad del mensaje de datos
2. Que el mensaje de datos permanezca accesible para su consulta posterior
3. Que se conserve el mensaje de datos en el formato en que se haya generado, enviado o recibido, o en algun formato que demuestre que reproduce con exactitud la informacion generada, enviada o recibida
4. Que se conserve, de haber alguna, toda informacion que permita determinar el origen y destino del mensaje de datos, asi como la fecha y hora en que fue enviado o recibido

### Constancia de conservacion:
Los prestadores de servicios de certificacion podran emitir constancias de conservacion de mensajes de datos que incluyan:
- Fecha y hora cierta
- Firma electronica del prestador
- Hash del documento original

**Referencia oficial:**  
https://www.dof.gob.mx/nota_detalle.php?codigo=5436568

---

# [INTERPRETACION EN REVISAR-IA]

## Ambito de uso

- **A2 (PMO):** Gestion de documentos y evidencias
- **A7 (Defensa):** Validez legal de evidencias
- **Defense File:** Trazabilidad de operaciones

## Pilares de trazabilidad

### 1. Integridad
- Hash SHA-256 de cada documento
- Cadena de hashes para detectar alteraciones
- Sin modificaciones posteriores

### 2. Accesibilidad
- Documentos disponibles para consulta
- Formatos estandar (PDF, XML)
- Almacenamiento seguro (pCloud)

### 3. Fecha cierta
- Timestamp al momento de creacion
- Registro UTC
- Sello de tiempo certificado (opcional)

### 4. Trazabilidad
- Quien creo/modifico
- Cuando (fecha/hora)
- Historial de versiones

## Documentos con timestamp obligatorio

| Fase | Documento | Timestamp |
|------|-----------|-----------|
| F1 | SIB completado | SI |
| F2 | Contrato firmado | SI |
| F3 | CFDI recibido | SI (UUID) |
| F5 | Entregables clave | SI |
| F6 | Acta de aceptacion | SI |
| F8 | Pago realizado | SI (estado cuenta) |

## Implementacion en la plataforma

### Registro automatico:
- Cada accion genera registro con timestamp UTC
- Hash SHA-256 de documentos subidos
- Versiones inmutables (V1, V2... VF)
- Log de usuario que subio/modifico

### Para Defense File:
- Timeline cronologico de toda la operacion
- Certificacion de integridad de documentos
- Cadena de custodia digital

## Valor probatorio

Los documentos con:
- Fecha cierta
- Integridad verificable
- Cadena de custodia

Tienen mayor peso probatorio ante autoridades fiscales y tribunales.

## Tags relacionados

@NOM151 @TRAZABILIDAD @FECHA_CIERTA @INTEGRIDAD @HASH @TIMESTAMP
