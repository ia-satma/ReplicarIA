
import sys
import os
import asyncio
import logging

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services.email_service import email_service, get_email_provider, is_configured

async def manual_test():
    print("\n--- DIAGNÓSTICO MANUAL DE EMAIL ---")
    print("Este script probará el envío real usando credenciales que ingreses ahora.")
    print("Las credenciales NO se guardarán, solo se usan para esta ejecución.\n")

    print(f"Estado Actual Configurado: {get_email_provider().upper()}")
    
    print("\n1. SendGrid Check")
    sg_key = input("Ingresa SENDGRID_API_KEY (Enter para saltar): ").strip()
    
    print("\n2. DreamHost Check")
    dh_pass = input("Ingresa DREAMHOST_EMAIL_PASSWORD (Enter para saltar): ").strip()

    # Set ephemeral env vars
    if sg_key:
        os.environ['SENDGRID_API_KEY'] = sg_key
    if dh_pass:
        os.environ['DREAMHOST_EMAIL_PASSWORD'] = dh_pass

    # Re-initialize service to pick up new vars involves re-instantiating or just relying on the methods checking os.environ
    # services/email_service.py checks os.environ in is_configured() and get_email_provider() called by methods.
    # However, 'email_service' instance was already created at module level.
    # We need to manually check the methods or re-create the instance logic.
    
    # Reloading config logic
    provider = get_email_provider()
    configured = is_configured()
    
    print(f"\nConfiguración para esta prueba: {provider.upper()}")
    if not configured:
        print("❌ No se ingresaron credenciales. Se usará MODO DEMO (no enviará email real).")
    
    target_email = "ia@satma.mx"
    print(f"Intentando enviar a: {target_email}...")

    # Force re-evaluation of provider in the instance if needed, 
    # but email_service writes self._provider in __init__. 
    # We must patch the instance or create a new one.
    email_service._configured = configured
    email_service._provider = provider

    try:
        result = await email_service.send_email(
            to=target_email,
            subject="PRUEBA MANUAL - Diagnóstico de Incidente",
            body_html="<h1>Prueba de Diagnóstico</h1><p>Este correo confirma que las credenciales funcionan.</p>",
            body_text="Prueba de Diagnóstico. Credenciales funcionan."
        )

        print("\n--- RESULTADO ---")
        if result.get("success"):
            print("✅ ENVÍO EXITOSO")
            print(f"Proveedor: {result.get('provider', 'demo').upper()}")
            print(f"Message ID: {result.get('message_id')}")
            if result.get("simulado"):
                print("⚠️  ADVERTENCIA: Fue un envío SIMULADO (Demo Mode).")
            else:
                print("🎉 El correo debería llegar en breve.")
        else:
            print("❌ FALLÓ EL ENVÍO")
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"❌ Excepción Crítica: {e}")

if __name__ == "__main__":
    asyncio.run(manual_test())
