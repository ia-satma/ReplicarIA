"""
Script para medir métricas baseline del sistema Revisar.IA.
Ejecutar: python backend/scripts/baseline_metrics.py
"""

import asyncio
import time
import statistics
import asyncpg
import httpx
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE = "http://localhost:5000"

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MetricsCollector:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_latencies": [],
            "db_latencies": {},
            "system_resources": {},
        }
    
    async def measure_api_latency(self, endpoint: str, n: int = 10):
        """Mide latencia de un endpoint."""
        latencies = []
        
        async with httpx.AsyncClient() as client:
            for _ in range(n):
                start = time.perf_counter()
                try:
                    resp = await client.get(f"{API_BASE}{endpoint}", timeout=10)
                    latency = (time.perf_counter() - start) * 1000
                    latencies.append(latency)
                except Exception as e:
                    print(f"  Error en {endpoint}: {e}")
                await asyncio.sleep(0.05)
        
        return latencies
    
    async def measure_db_latency(self, n: int = 20):
        """Mide latencia de queries a la base de datos."""
        latencies = []
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        queries = [
            "SELECT 1",
            "SELECT COUNT(*) FROM empresas",
            "SELECT COUNT(*) FROM knowledge_chunks",
            "SELECT * FROM planes LIMIT 5",
        ]
        
        for query in queries:
            for _ in range(n // len(queries)):
                start = time.perf_counter()
                try:
                    await conn.fetch(query)
                    latency = (time.perf_counter() - start) * 1000
                    latencies.append(latency)
                except:
                    pass
        
        await conn.close()
        return latencies
    
    def measure_system_resources(self):
        """Mide uso de CPU y memoria."""
        if not HAS_PSUTIL:
            return {"note": "psutil not installed"}
        
        process = psutil.Process()
        
        return {
            "cpu_percent": process.cpu_percent(interval=1),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "threads": process.num_threads(),
        }
    
    def calculate_percentiles(self, data: list) -> dict:
        """Calcula percentiles de una lista de datos."""
        if not data:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "min": 0, "max": 0}
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        return {
            "p50": round(sorted_data[int(n * 0.50)], 2),
            "p95": round(sorted_data[int(n * 0.95)] if n > 1 else sorted_data[0], 2),
            "p99": round(sorted_data[int(n * 0.99)] if n > 1 else sorted_data[0], 2),
            "avg": round(statistics.mean(data), 2),
            "min": round(min(data), 2),
            "max": round(max(data), 2),
        }
    
    async def run_full_baseline(self):
        """Ejecuta todas las mediciones."""
        print("=" * 60)
        print("🔍 MEDICIÓN DE MÉTRICAS BASELINE - REVISAR.IA")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        
        print("\n📡 Midiendo latencia de API...")
        endpoints = ["/api/health", "/docs", "/api/usage/plans"]
        
        for endpoint in endpoints:
            print(f"  Testing {endpoint}...")
            latencies = await self.measure_api_latency(endpoint, 10)
            if latencies:
                stats = self.calculate_percentiles(latencies)
                status = "✅" if stats['p50'] < 100 else "⚠️" if stats['p50'] < 300 else "❌"
                print(f"    {status} P50: {stats['p50']}ms | P95: {stats['p95']}ms | P99: {stats['p99']}ms")
                self.results["api_latencies"].append({"endpoint": endpoint, **stats})
        
        print("\n💾 Midiendo latencia de base de datos...")
        try:
            db_latencies = await self.measure_db_latency(20)
            db_stats = self.calculate_percentiles(db_latencies)
            status = "✅" if db_stats['p50'] < 50 else "⚠️" if db_stats['p50'] < 100 else "❌"
            print(f"  {status} P50: {db_stats['p50']}ms | P95: {db_stats['p95']}ms | P99: {db_stats['p99']}ms")
            self.results["db_latencies"] = db_stats
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print("\n🖥️ Midiendo recursos del sistema...")
        resources = self.measure_system_resources()
        if "note" not in resources:
            cpu_status = "✅" if resources['cpu_percent'] < 70 else "⚠️"
            mem_status = "✅" if resources['memory_percent'] < 80 else "⚠️"
            print(f"  {cpu_status} CPU: {resources['cpu_percent']:.1f}%")
            print(f"  {mem_status} Memoria: {resources['memory_mb']:.1f} MB ({resources['memory_percent']:.1f}%)")
            print(f"  ℹ️ Threads: {resources['threads']}")
        else:
            print("  ⚠️ psutil no instalado - métricas de sistema no disponibles")
        self.results["system_resources"] = resources
        
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE BASELINE")
        print("=" * 60)
        
        api_avg = sum(r.get('p50', 0) for r in self.results['api_latencies']) / max(len(self.results['api_latencies']), 1)
        db_p50 = self.results['db_latencies'].get('p50', 0)
        
        print(f"  API Latencia Promedio P50: {api_avg:.2f}ms {'✅' if api_avg < 100 else '⚠️'}")
        print(f"  DB Latencia P50: {db_p50}ms {'✅' if db_p50 < 50 else '⚠️'}")
        
        if "note" not in resources:
            print(f"  CPU: {resources.get('cpu_percent', 0):.1f}%")
            print(f"  Memoria: {resources.get('memory_mb', 0):.1f} MB")
        
        return self.results


async def main():
    collector = MetricsCollector()
    results = await collector.run_full_baseline()
    
    import json
    output_file = "backend/baseline_metrics.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Resultados guardados en {output_file}")
    return results


if __name__ == "__main__":
    asyncio.run(main())
