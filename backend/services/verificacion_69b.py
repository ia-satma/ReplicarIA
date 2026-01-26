"""
Servicio para verificar proveedores contra la lista 69-B del SAT.
"""

from sqlalchemy import text
from typing import Dict, Optional, List
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL')

RIESGO_POR_SITUACION = {
    'Definitivo': {
        'nivel': 'CRITICO',
        'score': 100,
        'color': 'red',
        'accion': 'NO OPERAR - EFOS confirmado',
        'descripcion': 'El contribuyente está en la lista DEFINITIVA del Art. 69-B. Las operaciones con este proveedor NO SON DEDUCIBLES.'
    },
    'Presunto': {
        'nivel': 'ALTO',
        'score': 80,
        'color': 'orange',
        'accion': 'PRECAUCIÓN - En proceso de presunción',
        'descripcion': 'El contribuyente está en la lista de PRESUNTOS del Art. 69-B. Tiene 15 días para desvirtuar. Alto riesgo de pasar a definitivo.'
    },
    'Desvirtuado': {
        'nivel': 'BAJO',
        'score': 10,
        'color': 'green',
        'accion': 'PROCEDER con precaución',
        'descripcion': 'El contribuyente DESVIRTUÓ la presunción. Documentar materialidad de operaciones.'
    },
    'Sentencia Favorable': {
        'nivel': 'BAJO',
        'score': 5,
        'color': 'green',
        'accion': 'PROCEDER - Sentencia favorable',
        'descripcion': 'El contribuyente obtuvo SENTENCIA FAVORABLE. Conservar copia de la sentencia como respaldo.'
    },
    'No encontrado': {
        'nivel': 'OK',
        'score': 0,
        'color': 'green',
        'accion': 'PROCEDER - No en lista 69-B',
        'descripcion': 'El contribuyente NO aparece en la lista 69-B del SAT.'
    }
}


def get_db_connection():
    """Obtiene conexión a la base de datos"""
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL)
    return engine.connect()


def verificar_rfc(rfc: str, registrar_consulta: bool = True, 
                  contexto: str = None, empresa_id: int = None,
                  usuario_id: int = None, proveedor_id: int = None) -> Dict:
    """
    Verifica un RFC contra la lista 69-B.
    
    Args:
        rfc: RFC a verificar (12 o 13 caracteres)
        registrar_consulta: Si True, registra la consulta en historial
        contexto: Contexto de la consulta (alta_proveedor, verificacion_cfdi, etc)
        empresa_id, usuario_id, proveedor_id: IDs para trazabilidad
        
    Returns:
        Dict con resultado de la verificación
    """
    
    rfc = rfc.strip().upper()
    
    with get_db_connection() as conn:
        resultado = conn.execute(text("""
            SELECT 
                rfc,
                nombre_contribuyente,
                situacion,
                fecha_publicacion_sat_presuntos,
                fecha_publicacion_sat_definitivos,
                fecha_publicacion_sat_desvirtuados,
                fecha_publicacion_sat_sentencia,
                oficio_definitivos_sat,
                fecha_actualizacion
            FROM sat_lista_69b
            WHERE rfc = :rfc
        """), {'rfc': rfc}).fetchone()
        
        if resultado:
            situacion = resultado.situacion
            config_riesgo = RIESGO_POR_SITUACION.get(
                situacion, 
                RIESGO_POR_SITUACION['Presunto']
            )
            
            respuesta = {
                'encontrado': True,
                'rfc': resultado.rfc,
                'nombre': resultado.nombre_contribuyente,
                'situacion': situacion,
                'nivel_riesgo': config_riesgo['nivel'],
                'score_riesgo': config_riesgo['score'],
                'color': config_riesgo['color'],
                'accion_recomendada': config_riesgo['accion'],
                'descripcion': config_riesgo['descripcion'],
                'fecha_presuncion': str(resultado.fecha_publicacion_sat_presuntos) if resultado.fecha_publicacion_sat_presuntos else None,
                'fecha_definitivo': str(resultado.fecha_publicacion_sat_definitivos) if resultado.fecha_publicacion_sat_definitivos else None,
                'fecha_desvirtuacion': str(resultado.fecha_publicacion_sat_desvirtuados) if resultado.fecha_publicacion_sat_desvirtuados else None,
                'fecha_sentencia': str(resultado.fecha_publicacion_sat_sentencia) if resultado.fecha_publicacion_sat_sentencia else None,
                'oficio_referencia': resultado.oficio_definitivos_sat,
                'ultima_actualizacion': str(resultado.fecha_actualizacion) if resultado.fecha_actualizacion else None,
                'consultado_at': datetime.now().isoformat()
            }
        else:
            config_riesgo = RIESGO_POR_SITUACION['No encontrado']
            respuesta = {
                'encontrado': False,
                'rfc': rfc,
                'nombre': None,
                'situacion': 'No encontrado',
                'nivel_riesgo': config_riesgo['nivel'],
                'score_riesgo': config_riesgo['score'],
                'color': config_riesgo['color'],
                'accion_recomendada': config_riesgo['accion'],
                'descripcion': config_riesgo['descripcion'],
                'consultado_at': datetime.now().isoformat()
            }
        
        if registrar_consulta:
            try:
                conn.execute(text("""
                    INSERT INTO sat_69b_consultas 
                    (rfc_consultado, encontrado, situacion_encontrada, 
                     empresa_id, usuario_id, proveedor_id, contexto)
                    VALUES 
                    (:rfc, :encontrado, :situacion, :empresa, :usuario, :proveedor, :contexto)
                """), {
                    'rfc': rfc,
                    'encontrado': respuesta['encontrado'],
                    'situacion': respuesta['situacion'],
                    'empresa': empresa_id,
                    'usuario': usuario_id,
                    'proveedor': proveedor_id,
                    'contexto': contexto
                })
                conn.commit()
            except Exception as e:
                print(f"Error registrando consulta 69-B: {e}")
        
        return respuesta


def verificar_multiples(rfcs: List[str]) -> Dict[str, Dict]:
    """
    Verifica múltiples RFCs a la vez (optimizado).
    """
    rfcs_limpios = [rfc.strip().upper() for rfc in rfcs]
    
    with get_db_connection() as conn:
        resultados = conn.execute(text("""
            SELECT 
                rfc, nombre_contribuyente, situacion,
                fecha_publicacion_sat_definitivos
            FROM sat_lista_69b
            WHERE rfc = ANY(:rfcs)
        """), {'rfcs': rfcs_limpios}).fetchall()
        
        encontrados = {r.rfc: r for r in resultados}
        
        respuestas = {}
        for rfc in rfcs_limpios:
            if rfc in encontrados:
                r = encontrados[rfc]
                config = RIESGO_POR_SITUACION.get(r.situacion, RIESGO_POR_SITUACION['Presunto'])
                respuestas[rfc] = {
                    'encontrado': True,
                    'nombre': r.nombre_contribuyente,
                    'situacion': r.situacion,
                    'nivel_riesgo': config['nivel'],
                    'score_riesgo': config['score'],
                    'color': config['color'],
                    'accion_recomendada': config['accion']
                }
            else:
                config = RIESGO_POR_SITUACION['No encontrado']
                respuestas[rfc] = {
                    'encontrado': False,
                    'situacion': 'No encontrado',
                    'nivel_riesgo': config['nivel'],
                    'score_riesgo': config['score'],
                    'color': config['color'],
                    'accion_recomendada': config['accion']
                }
        
        return respuestas


def obtener_estadisticas() -> Dict:
    """Obtiene estadísticas de la lista 69-B"""
    with get_db_connection() as conn:
        stats = conn.execute(text("""
            SELECT 
                situacion,
                COUNT(*) as cantidad
            FROM sat_lista_69b
            GROUP BY situacion
            ORDER BY cantidad DESC
        """)).fetchall()
        
        total = conn.execute(text("SELECT COUNT(*) FROM sat_lista_69b")).scalar()
        ultima_actualizacion = conn.execute(text(
            "SELECT MAX(fecha_actualizacion) FROM sat_lista_69b"
        )).scalar()
        
        return {
            'total_registros': total or 0,
            'distribucion': {s.situacion: s.cantidad for s in stats},
            'ultima_actualizacion': str(ultima_actualizacion) if ultima_actualizacion else None
        }


def buscar_por_nombre(nombre: str, limite: int = 20) -> List[Dict]:
    """Busca contribuyentes por nombre (búsqueda parcial)"""
    with get_db_connection() as conn:
        resultados = conn.execute(text("""
            SELECT rfc, nombre_contribuyente, situacion
            FROM sat_lista_69b
            WHERE LOWER(nombre_contribuyente) LIKE LOWER(:nombre)
            ORDER BY situacion, nombre_contribuyente
            LIMIT :limite
        """), {'nombre': f'%{nombre}%', 'limite': limite}).fetchall()
        
        return [
            {
                'rfc': r.rfc,
                'nombre': r.nombre_contribuyente,
                'situacion': r.situacion,
                'nivel_riesgo': RIESGO_POR_SITUACION.get(r.situacion, {}).get('nivel', 'DESCONOCIDO')
            }
            for r in resultados
        ]
