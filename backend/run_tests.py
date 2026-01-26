#!/usr/bin/env python3
"""
Script para ejecutar todas las pruebas unitarias - Revisar.IA
"""

import subprocess
import sys
import os

def run_tests():
    """Ejecuta pytest con cobertura"""
    print("=" * 60)
    print("EJECUTANDO PRUEBAS UNITARIAS - REVISAR.IA")
    print("=" * 60)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-x"
        ]
    )
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
