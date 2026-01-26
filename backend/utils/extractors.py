"""
Extractores de entidades para Defense Files
Extrae RFCs, artículos legales, montos, fechas, etc. de textos
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime


def extraer_entidades(datos: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extrae entidades mencionadas de los datos de un evento.
    
    Returns:
        Dict con listas de: rfcs, articulos, montos, fechas, uuids
    """
    entidades = {
        'rfcs': [],
        'articulos': [],
        'montos': [],
        'fechas': [],
        'uuids': [],
        'leyes': []
    }
    
    texto = _datos_a_texto(datos)
    
    entidades['rfcs'] = extraer_rfcs(texto)
    entidades['articulos'] = extraer_articulos(texto)
    entidades['montos'] = extraer_montos(texto)
    entidades['uuids'] = extraer_uuids(texto)
    entidades['leyes'] = extraer_leyes(texto)
    
    entidades = {k: v for k, v in entidades.items() if v}
    
    return entidades


def _datos_a_texto(datos: Any, nivel: int = 0) -> str:
    """Convierte datos anidados a texto plano para búsqueda"""
    if nivel > 5:
        return ""
    
    if isinstance(datos, str):
        return datos
    elif isinstance(datos, (int, float)):
        return str(datos)
    elif isinstance(datos, dict):
        partes = []
        for k, v in datos.items():
            partes.append(f"{k}: {_datos_a_texto(v, nivel + 1)}")
        return " ".join(partes)
    elif isinstance(datos, (list, tuple)):
        return " ".join(_datos_a_texto(item, nivel + 1) for item in datos)
    else:
        return str(datos) if datos else ""


def extraer_rfcs(texto: str) -> List[str]:
    """
    Extrae RFCs válidos (personas físicas y morales) del texto.
    
    Formatos:
    - Persona Moral: 3 letras + 6 dígitos + 3 alfanuméricos (12 caracteres)
    - Persona Física: 4 letras + 6 dígitos + 3 alfanuméricos (13 caracteres)
    """
    patron_rfc = r'\b([A-ZÑ&]{3,4})(\d{6})([A-Z0-9]{3})\b'
    
    matches = re.findall(patron_rfc, texto.upper())
    
    rfcs = []
    for match in matches:
        rfc = ''.join(match)
        if len(rfc) in [12, 13] and rfc not in rfcs:
            rfcs.append(rfc)
    
    return rfcs


def extraer_articulos(texto: str) -> List[str]:
    """
    Extrae referencias a artículos legales del texto.
    
    Ejemplos:
    - "artículo 27"
    - "Art. 27 LISR"
    - "artículo 5-A CFF"
    """
    patrones = [
        r'[Aa]rt[íi]culo\s+(\d+(?:-[A-Z])?)',
        r'[Aa]rt\.?\s*(\d+(?:-[A-Z])?)',
        r'[Aa]rtículos?\s+(\d+(?:-[A-Z])?(?:\s*(?:,|y)\s*\d+(?:-[A-Z])?)*)',
    ]
    
    articulos = []
    for patron in patrones:
        matches = re.findall(patron, texto)
        for match in matches:
            art = f"Art. {match}" if not match.startswith('Art') else match
            if art not in articulos:
                articulos.append(art)
    
    return articulos


def extraer_leyes(texto: str) -> List[str]:
    """
    Extrae referencias a leyes fiscales mexicanas.
    """
    leyes_conocidas = [
        ('LISR', r'\bLISR\b'),
        ('LIVA', r'\bLIVA\b'),
        ('CFF', r'\bCFF\b'),
        ('CPEUM', r'\bCPEUM\b'),
        ('LGSM', r'\bLGSM\b'),
        ('Ley del Impuesto Sobre la Renta', r'[Ll]ey\s+del\s+[Ii]mpuesto\s+[Ss]obre\s+la\s+[Rr]enta'),
        ('Ley del IVA', r'[Ll]ey\s+del\s+IVA'),
        ('Código Fiscal de la Federación', r'[Cc]ódigo\s+[Ff]iscal\s+de\s+la\s+[Ff]ederación'),
    ]
    
    leyes_encontradas = []
    texto_upper = texto.upper()
    
    for nombre, patron in leyes_conocidas:
        if re.search(patron, texto, re.IGNORECASE):
            if nombre not in leyes_encontradas:
                leyes_encontradas.append(nombre)
    
    return leyes_encontradas


def extraer_montos(texto: str) -> List[str]:
    """
    Extrae montos en pesos mexicanos del texto.
    
    Formatos:
    - $1,234.56
    - MXN 1234.56
    - 1,234.56 pesos
    """
    patrones = [
        r'\$[\d,]+(?:\.\d{2})?',
        r'MXN\s*[\d,]+(?:\.\d{2})?',
        r'[\d,]+(?:\.\d{2})?\s*(?:pesos|MXN)',
    ]
    
    montos = []
    for patron in patrones:
        matches = re.findall(patron, texto, re.IGNORECASE)
        for match in matches:
            monto_limpio = re.sub(r'[^\d.,]', '', match)
            if monto_limpio and monto_limpio not in montos:
                montos.append(f"${monto_limpio}")
    
    return montos


def extraer_uuids(texto: str) -> List[str]:
    """
    Extrae UUIDs de CFDIs del texto.
    Formato: 8-4-4-4-12 caracteres hexadecimales
    """
    patron_uuid = r'\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b'
    
    matches = re.findall(patron_uuid, texto)
    
    return list(set(match.upper() for match in matches))


def extraer_fechas(texto: str) -> List[str]:
    """
    Extrae fechas del texto en formatos comunes.
    """
    patrones = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}/\d{2}/\d{4}',
        r'\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}',
    ]
    
    fechas = []
    for patron in patrones:
        matches = re.findall(patron, texto, re.IGNORECASE)
        for match in matches:
            if match not in fechas:
                fechas.append(match)
    
    return fechas


def validar_rfc(rfc: str) -> Dict[str, Any]:
    """
    Valida formato de RFC y determina tipo.
    
    Returns:
        Dict con: valido, tipo (moral/fisica), errores
    """
    rfc = rfc.upper().strip()
    resultado = {
        'valido': False,
        'tipo': None,
        'rfc': rfc,
        'errores': []
    }
    
    if len(rfc) == 12:
        resultado['tipo'] = 'moral'
        patron = r'^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$'
    elif len(rfc) == 13:
        resultado['tipo'] = 'fisica'
        patron = r'^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$'
    else:
        resultado['errores'].append(f'Longitud inválida: {len(rfc)} (debe ser 12 o 13)')
        return resultado
    
    if not re.match(patron, rfc):
        resultado['errores'].append('Formato inválido')
        return resultado
    
    fecha_str = rfc[4:10] if len(rfc) == 13 else rfc[3:9]
    try:
        año = int(fecha_str[0:2])
        mes = int(fecha_str[2:4])
        dia = int(fecha_str[4:6])
        
        if not (1 <= mes <= 12):
            resultado['errores'].append(f'Mes inválido: {mes}')
        if not (1 <= dia <= 31):
            resultado['errores'].append(f'Día inválido: {dia}')
    except ValueError:
        resultado['errores'].append('Fecha de nacimiento inválida')
    
    if not resultado['errores']:
        resultado['valido'] = True
    
    return resultado


def generar_codigo_defense_file(anio: int, secuencia: int) -> str:
    """
    Genera código único para Defense File.
    Formato: DF-YYYY-NNNN
    
    Args:
        anio: Año fiscal
        secuencia: Número secuencial
    
    Returns:
        str: Código como "DF-2025-0001"
    """
    return f"DF-{anio}-{secuencia:04d}"


def generar_codigo_evento() -> str:
    """
    Genera ID único para evento.
    Formato: EVT-YYYYMMDD-HHMMSS-XXXX
    """
    import random
    import string
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"EVT-{timestamp}-{sufijo}"
