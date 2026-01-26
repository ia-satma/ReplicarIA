"""
Script para ingestar el listado 69-B del SAT en la base de datos.
Uso: python ingestar_lista_69b.py /ruta/al/Listado_Completo_69-B.xls
"""

import pandas as pd
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/revisar_ia')


def normalizar_situacion(situacion):
    """Normaliza el campo situación"""
    if pd.isna(situacion):
        return 'Desconocido'
    
    situacion = str(situacion).strip()
    
    if 'definitivo' in situacion.lower():
        return 'Definitivo'
    elif 'presunto' in situacion.lower():
        return 'Presunto'
    elif 'desvirtuado' in situacion.lower():
        return 'Desvirtuado'
    elif 'sentencia' in situacion.lower() or 'favorable' in situacion.lower():
        return 'Sentencia Favorable'
    
    return situacion


def ingestar_lista_69b(archivo_excel: str):
    """
    Ingesta el archivo Excel del listado 69-B en la base de datos.
    """
    print(f"📋 Iniciando ingesta de {archivo_excel}")
    
    df = pd.read_excel(archivo_excel)
    print(f"   Registros encontrados: {len(df):,}")
    print(f"   Columnas: {list(df.columns)}")
    
    cols = df.columns.tolist()
    rfc_col = None
    nombre_col = None
    situacion_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'rfc' in c_lower and rfc_col is None:
            rfc_col = c
        elif 'nombre' in c_lower and nombre_col is None:
            nombre_col = c
        elif 'situac' in c_lower and situacion_col is None:
            situacion_col = c
    
    if rfc_col is None:
        rfc_col = cols[1] if len(cols) > 1 else cols[0]
    if nombre_col is None:
        nombre_col = cols[2] if len(cols) > 2 else cols[1]
    if situacion_col is None:
        situacion_col = cols[3] if len(cols) > 3 else cols[2]
    
    print(f"   Columna RFC: {rfc_col}")
    print(f"   Columna Nombre: {nombre_col}")
    print(f"   Columna Situación: {situacion_col}")
    
    df['_rfc'] = df[rfc_col].astype(str).str.strip().str.upper()
    df['_nombre'] = df[nombre_col].astype(str).fillna('')
    df['_situacion'] = df[situacion_col].apply(normalizar_situacion)
    
    df = df[df['_rfc'].str.len() >= 12]
    df = df.drop_duplicates(subset=['_rfc'], keep='last')
    
    print(f"   Registros únicos por RFC: {len(df):,}")
    print(f"   Distribución por situación:")
    print(df['_situacion'].value_counts().to_string())
    
    engine = create_engine(DATABASE_URL)
    
    print("\n📥 Insertando en base de datos...")
    
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE sat_lista_69b RESTART IDENTITY"))
        conn.commit()
        
        data_to_insert = []
        for idx, row in df.iterrows():
            data_to_insert.append({
                'rfc': row['_rfc'],
                'nombre': row['_nombre'][:500],
                'situacion': row['_situacion']
            })
        
        batch_size = 500
        total = len(data_to_insert)
        insertados = 0
        errores = 0
        
        for i in range(0, total, batch_size):
            batch = data_to_insert[i:i+batch_size]
            
            for item in batch:
                try:
                    conn.execute(text("""
                        INSERT INTO sat_lista_69b (rfc, nombre_contribuyente, situacion)
                        VALUES (:rfc, :nombre, :situacion)
                        ON CONFLICT (rfc) DO UPDATE SET
                            nombre_contribuyente = EXCLUDED.nombre_contribuyente,
                            situacion = EXCLUDED.situacion,
                            fecha_actualizacion = NOW()
                    """), item)
                    insertados += 1
                except Exception as e:
                    errores += 1
                    if errores < 5:
                        print(f"   ⚠️ Error en RFC {item['rfc']}: {e}")
            
            conn.commit()
            print(f"   Progreso: {min(i+batch_size, total):,}/{total:,} ({(min(i+batch_size, total)/total*100):.1f}%)")
    
    print(f"\n✅ Ingesta completada:")
    print(f"   Insertados: {insertados:,}")
    print(f"   Errores: {errores:,}")
    
    return insertados, errores


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ingestar_lista_69b.py /ruta/al/archivo.xls")
        sys.exit(1)
    
    archivo = sys.argv[1]
    ingestar_lista_69b(archivo)
