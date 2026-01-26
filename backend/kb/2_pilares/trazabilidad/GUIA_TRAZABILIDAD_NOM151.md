# Guia: Trazabilidad y Fecha Cierta (Pilar 4)

## Definicion

Capacidad de demostrar QUE se hizo, CUANDO, POR QUIEN, y que la informacion NO ha sido alterada.

## Base normativa

@NOM151 - NOM-151-SCFI-2016

## Que debe tener sello de tiempo

Por fase del flujo F0-F9:

| Fase | Documento | Timestamp |
|------|-----------|-----------|
| F1 | SIB completado | SI |
| F2 | Contrato firmado | SI |
| F3 | CFDI recibido | SI (UUID tiene fecha) |
| F5 | Entregables clave | SI |
| F6 | Acta de aceptacion | SI |
| F8 | Pago realizado | SI (estado de cuenta) |

## Elementos de trazabilidad

### 1. Fecha cierta
- Timestamp al momento de creacion
- Registro en zona horaria definida (UTC)
- Inmutable despues de registro

### 2. Integridad
- Hash SHA-256 del documento
- Cadena de hashes para detectar alteraciones
- Verificacion de no modificacion

### 3. Autoria
- Quien creo el documento
- Quien lo subio al sistema
- Quien lo aprobo

### 4. Versionamiento
- Version 1, 2, ... Final
- Historial de cambios
- Razon del cambio

## Como se registra en la plataforma

### Registro automatico:
- Cada accion genera registro con timestamp UTC
- Hash SHA-256 de documentos subidos
- Versiones inmutables (V1, V2... VF)
- Log de usuario que subio/modifico

### Formato de registro:
```json
{
  "documento_id": "uuid",
  "hash_sha256": "abc123...",
  "fecha_hora_utc": "2026-01-23T10:30:00Z",
  "usuario": "email@empresa.com",
  "accion": "upload | modify | approve",
  "version": "V1",
  "hash_anterior": "xyz789..." // para cadena
}
```

## Timeline para Defense File

La plataforma genera automaticamente:

### 1. Cronologia completa
```
2026-01-10 09:00 - SIB iniciado por usuario@empresa.com
2026-01-15 14:30 - Contrato V1 subido
2026-01-15 16:00 - Contrato V2 (revision legal)
2026-01-16 10:00 - Contrato VF firmado
2026-01-20 11:00 - CFDI recibido (UUID xxx)
2026-02-15 09:00 - Entregable V1 subido
2026-02-20 15:00 - Entregable VF aprobado
2026-02-25 10:00 - Acta de aceptacion firmada
2026-02-28 16:00 - Pago registrado
```

### 2. Certificacion de integridad
- Hash de cada documento
- Verificacion de no alteracion
- Cadena de custodia digital

### 3. Valor probatorio
Los documentos con:
- Fecha cierta
- Integridad verificable
- Cadena de custodia

Tienen mayor peso probatorio ante:
- SAT
- TFJA
- SCJN

## Buenas practicas

### DO:
- Subir documentos conforme se generan
- Usar formatos no editables (PDF)
- Mantener originales (XML de CFDI)
- Documentar aprobaciones

### DON'T:
- Subir documentos con fechas retroactivas
- Modificar documentos despues de subir
- Perder correos o comunicaciones
- Usar versiones editables como finales

## Vinculacion normativa

- @NOM151 (conservacion de mensajes)
- @CFF_29_29A (requisitos CFDI)
- @TESIS_IA (uso de tecnologia)

## Agentes que consumen esta guia

- **A2 (PMO):** Gestion de documentos y fases
- **A7 (Defensa):** Construccion de timeline
- **ARCHIVO:** Ingestion y versionamiento
