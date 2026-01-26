# [NORMA] CFF - Articulos 29 y 29-A: Comprobantes Fiscales Digitales (CFDI)

## Texto Normativo (Extracto Art. 29)

Cuando las leyes fiscales establezcan la obligacion de expedir comprobantes fiscales por los actos o actividades que realicen, por los ingresos que se perciban o por las retenciones de contribuciones que efectuen, los contribuyentes deberan emitirlos mediante documentos digitales a traves de la pagina de Internet del Servicio de Administracion Tributaria.

Los comprobantes fiscales digitales por Internet deberan contener los requisitos establecidos en el articulo 29-A de este Codigo.

## Texto Normativo (Extracto Art. 29-A)

Los comprobantes fiscales digitales a que se refiere el articulo 29 de este Codigo, deberan contener los siguientes requisitos:

I. La clave del RFC de quien lo expida y el regimen fiscal
II. El numero de folio y el sello digital del SAT (UUID)
III. El lugar y fecha de expedicion
IV. La clave del RFC de la persona a favor de quien se expida
V. La cantidad, unidad de medida y clase de los bienes o mercancia o descripcion del servicio
VI. El valor unitario consignado en numero
VII. El importe total consignado en numero o letra
VIII. Tratandose de retencion de contribuciones, deberan contener los datos relativos a las retenciones efectuadas

**Referencia oficial:**  
https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf

---

# [INTERPRETACION EN REVISAR-IA]

## Ambito de uso

- **A3 (Fiscal):** Validacion de CFDIs para deducibilidad
- **A6 (Proveedor):** Verificacion de comprobantes recibidos
- **A7 (Defensa):** Documentacion de operaciones en Defense File

## Validaciones obligatorias por CFDI

### Requisitos formales (automaticos):
- UUID valido y registrado en SAT
- RFC emisor activo
- RFC receptor correcto
- Sello digital vigente
- Cadena original verificable

### Requisitos sustanciales (revision A3):
- Descripcion del servicio clara y especifica
- Congruencia con contrato/orden de compra
- Monto correcto vs cotizacion/contrato
- Metodo de pago correcto (PUE/PPD)

## Red flags en CFDI

- Descripcion generica ("servicios varios", "asesoria")
- Incongruencia entre clave de producto/servicio y descripcion
- Fecha de emision fuera de periodo de la operacion
- Cancelacion posterior sin complemento

## Documentar para Defense File

1. CFDI en XML original
2. Representacion impresa (PDF)
3. Acuse de recepcion
4. Verificacion en portal SAT (fecha)
5. Relacion con contrato y entregables

## Tags relacionados

@CFF_29 @CFF_29A @CFDI @UUID @COMPROBANTES @DEDUCIBILIDAD
