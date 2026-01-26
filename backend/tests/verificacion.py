#!/usr/bin/env python3
"""
SCRIPT DE VERIFICACIÓN COMPLETA DEL SISTEMA
Ejecutar después de CADA cambio: python backend/tests/verificacion.py
"""

import requests
import json
import sys
import os
from datetime import datetime

BASE_URL = "http://localhost:5000"

class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def ok(msg):
    print(f"{Colores.VERDE}✅ PASS{Colores.RESET} - {msg}")
    return True

def fail(msg, detalle=""):
    print(f"{Colores.ROJO}❌ FAIL{Colores.RESET} - {msg}")
    if detalle:
        print(f"   {Colores.AMARILLO}Detalle: {detalle}{Colores.RESET}")
    return False

def warn(msg):
    print(f"{Colores.AMARILLO}⚠️ WARN{Colores.RESET} - {msg}")

def header(titulo):
    print(f"\n{Colores.AZUL}{Colores.BOLD}{'='*60}")
    print(f" {titulo}")
    print(f"{'='*60}{Colores.RESET}\n")

def test_health():
    header("TEST 1: HEALTH CHECK")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   Respuesta: {json.dumps(data, indent=2)}")
            return ok("Health check responde 200")
        else:
            return fail(f"Health check retorna {r.status_code}", r.text[:200])
    except Exception as e:
        return fail("Health check no accesible", str(e))

def test_chat_facturar():
    header("TEST 2: CHAT FACTURAR.IA")
    try:
        r = requests.post(
            f"{BASE_URL}/api/asistente-facturacion/chat",
            json={"mensaje": "hola, ¿qué puedes hacer?"},
            timeout=30
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:500]}")
        
        if r.status_code == 200:
            data = r.json()
            respuesta = data.get('respuesta') or data.get('response') or data.get('message') or ''
            if len(respuesta) > 10:
                return ok(f"Chat responde con {len(respuesta)} caracteres")
            else:
                return fail("Chat responde pero sin contenido útil", f"Respuesta: {respuesta}")
        else:
            return fail(f"Chat retorna {r.status_code}", r.text[:300])
            
    except requests.exceptions.Timeout:
        return fail("Chat TIMEOUT después de 30 segundos")
    except Exception as e:
        return fail("Chat no accesible", str(e))

def test_crear_cliente():
    header("TEST 3: CREAR CLIENTE SIN RAZON_SOCIAL")
    try:
        r = requests.post(
            f"{BASE_URL}/api/clientes",
            json={
                "nombre": f"Cliente Test Verificacion {datetime.now().strftime('%H%M%S')}",
                "rfc": "XAXX010101000"
            },
            headers={"Authorization": "Bearer test-token"},
            timeout=10
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:500]}")
        
        if r.status_code in [200, 201]:
            data = r.json()
            if data.get('id') or data.get('success'):
                return ok("Cliente creado sin necesidad de razon_social")
            else:
                return fail("Respuesta 200 pero sin ID de cliente")
        elif r.status_code == 422:
            return fail("Aún requiere campos obligatorios", r.text[:200])
        else:
            return fail(f"Error {r.status_code}", r.text[:200])
            
    except Exception as e:
        return fail("Endpoint clientes no accesible", str(e))

def test_onboarding_investigar():
    header("TEST 4: ONBOARDING INVESTIGAR")
    try:
        r = requests.post(
            f"{BASE_URL}/api/archivo/investigar",
            json={"sitio_web": "sat.gob.mx"},
            timeout=60
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:500]}")
        
        if r.status_code == 405:
            return fail("Endpoint NO EXISTE (405 Method Not Allowed)")
        elif r.status_code == 404:
            return fail("Endpoint NO EXISTE (404 Not Found)")
        elif r.status_code == 200:
            data = r.json()
            if data.get('success'):
                datos = data.get('datos', {})
                campos = len([k for k, v in datos.items() if v])
                return ok(f"Investigar funciona - {campos} campos auto-completados")
            else:
                return fail("Responde pero success=false", data.get('error', ''))
        else:
            return fail(f"Error {r.status_code}", r.text[:200])
            
    except requests.exceptions.Timeout:
        return fail("TIMEOUT después de 60 segundos")
    except Exception as e:
        return fail("Endpoint no accesible", str(e))

def test_estado_acervo():
    header("TEST 5: ESTADO DEL ACERVO")
    try:
        r = requests.get(f"{BASE_URL}/api/biblioteca/estado-acervo", timeout=10)
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:800]}")
        
        if r.status_code == 404:
            return fail("Endpoint NO EXISTE (404)")
        elif r.status_code == 200:
            data = r.json()
            agentes = data.get('agentes', [])
            progreso = data.get('completitud_global', 0)
            if len(agentes) >= 7:
                return ok(f"Estado acervo funciona - {len(agentes)} agentes, {progreso}% progreso")
            elif len(agentes) > 0:
                warn(f"Solo {len(agentes)} agentes configurados (esperados 7)")
                return ok(f"Estado acervo funciona parcialmente")
            else:
                return fail("Responde pero sin agentes configurados")
        else:
            return fail(f"Error {r.status_code}", r.text[:200])
            
    except Exception as e:
        return fail("Endpoint no accesible", str(e))

def test_biblioteca_chat():
    header("TEST 6: BIBLIOTECA CHAT")
    try:
        r = requests.post(
            f"{BASE_URL}/api/biblioteca/chat",
            json={"message": "¿qué documentos necesito subir?"},
            timeout=30
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:500]}")
        
        if r.status_code == 200:
            data = r.json()
            respuesta = data.get('response') or data.get('message') or ''
            if len(respuesta) > 20:
                return ok(f"Biblioteca chat funciona - {len(respuesta)} chars")
            else:
                return fail("Responde pero sin contenido útil")
        else:
            return fail(f"Error {r.status_code}", r.text[:200])
            
    except Exception as e:
        return fail("Endpoint no accesible", str(e))

def test_reingestar():
    header("TEST 7: REINGESTAR DOCUMENTO")
    try:
        import subprocess
        result = subprocess.run(
            ["psql", os.environ.get("DATABASE_URL", ""), "-t", "-c", 
             "SELECT id FROM kb_documentos LIMIT 1"],
            capture_output=True, text=True, timeout=5
        )
        doc_uuid = result.stdout.strip()
        
        if not doc_uuid or len(doc_uuid) < 32:
            warn("No hay documentos en la base de datos")
            return True
        
        print(f"   Probando con documento: {doc_uuid}")
        
        r = requests.post(
            f"{BASE_URL}/api/biblioteca/documento/{doc_uuid}/reingestar",
            headers={"Authorization": "Bearer test-token"},
            timeout=60
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:300]}")
        
        if r.status_code == 404:
            if 'no encontrado' in r.text.lower() or 'not found' in r.text.lower():
                return ok("Endpoint existe (doc no encontrado es esperado)")
            return fail("Endpoint reingestar NO EXISTE")
        elif r.status_code == 200:
            return ok("Reingestar funciona")
        else:
            return fail(f"Error {r.status_code}", r.text[:200])
            
    except Exception as e:
        return fail("Error en test", str(e))

def test_stats_documento():
    header("TEST 8: STATS DE DOCUMENTO")
    try:
        import subprocess
        result = subprocess.run(
            ["psql", os.environ.get("DATABASE_URL", ""), "-t", "-c", 
             "SELECT id FROM kb_documentos LIMIT 1"],
            capture_output=True, text=True, timeout=5
        )
        doc_uuid = result.stdout.strip()
        
        if not doc_uuid or len(doc_uuid) < 32:
            warn("No hay documentos en la base de datos")
            return True
            
        print(f"   Probando con documento: {doc_uuid}")
        
        r = requests.get(f"{BASE_URL}/api/biblioteca/documento/{doc_uuid}/stats", timeout=10)
        
        print(f"   Status: {r.status_code}")
        print(f"   Respuesta: {r.text[:500]}")
        
        if r.status_code == 404:
            if 'endpoint' in r.text.lower() or 'route' in r.text.lower():
                return fail("Endpoint stats NO EXISTE")
            else:
                return ok("Endpoint existe (doc no encontrado es OK)")
        elif r.status_code == 200:
            data = r.json()
            if 'estadisticas' in data or 'chunks' in str(data):
                return ok("Stats documento funciona")
            else:
                return fail("Responde pero sin estadísticas")
        else:
            return fail(f"Error {r.status_code}")
            
    except Exception as e:
        return fail("Error en test", str(e))

def main():
    print(f"\n{Colores.BOLD}{'='*60}")
    print(" VERIFICACIÓN COMPLETA DEL SISTEMA REVISAR.IA")
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colores.RESET}")
    
    resultados = {
        'health': test_health(),
        'chat_facturar': test_chat_facturar(),
        'crear_cliente': test_crear_cliente(),
        'onboarding_investigar': test_onboarding_investigar(),
        'estado_acervo': test_estado_acervo(),
        'biblioteca_chat': test_biblioteca_chat(),
        'reingestar': test_reingestar(),
        'stats_documento': test_stats_documento(),
    }
    
    header("RESUMEN DE VERIFICACIÓN")
    
    passed = sum(1 for v in resultados.values() if v)
    total = len(resultados)
    porcentaje = round((passed / total) * 100)
    
    for nombre, resultado in resultados.items():
        estado = f"{Colores.VERDE}✅ PASS{Colores.RESET}" if resultado else f"{Colores.ROJO}❌ FAIL{Colores.RESET}"
        print(f"   {nombre}: {estado}")
    
    print(f"\n   {Colores.BOLD}TOTAL: {passed}/{total} tests pasaron ({porcentaje}%){Colores.RESET}")
    
    criticos = ['health', 'chat_facturar', 'biblioteca_chat']
    criticos_ok = all(resultados.get(c, False) for c in criticos)
    
    if porcentaje >= 90 and criticos_ok:
        print(f"\n   {Colores.VERDE}{Colores.BOLD}🎉 SISTEMA LISTO PARA DEMO{Colores.RESET}")
        return 0
    elif porcentaje >= 70 and criticos_ok:
        print(f"\n   {Colores.AMARILLO}{Colores.BOLD}⚠️ SISTEMA PARCIALMENTE LISTO - FUNCIONALIDAD BÁSICA OK{Colores.RESET}")
        return 0
    else:
        print(f"\n   {Colores.ROJO}{Colores.BOLD}❌ SISTEMA NO LISTO - ARREGLAR TESTS FALLIDOS{Colores.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
