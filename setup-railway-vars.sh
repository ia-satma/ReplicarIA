#!/bin/bash
# Script para configurar variables de Railway
# Ejecutar: ./setup-railway-vars.sh

echo "🚂 Configurando variables de Railway para Revisar.IA..."

# Primero hacer login (esto abrirá el navegador)
echo "📝 Iniciando sesión en Railway..."
npx @railway/cli login

# Linkear al proyecto
echo "🔗 Conectando al proyecto..."
npx @railway/cli link

# Configurar variables una por una
echo "⚙️ Configurando variables de entorno..."

npx @railway/cli variables set OPENAI_API_KEY="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"
npx @railway/cli variables set DREAMHOST_EMAIL_PASSWORD="B859931f#"
npx @railway/cli variables set DREAMHOST_FROM_EMAIL="pmo@revisar-ia.com"
npx @railway/cli variables set SMTP_HOST="smtp.dreamhost.com"
npx @railway/cli variables set SMTP_PORT="587"
npx @railway/cli variables set IMAP_HOST="imap.dreamhost.com"
npx @railway/cli variables set SECRET_KEY="rv1s4r-1a-pr0d-s3cr3t-k3y-2026-x7k9m2p4q8w5"
npx @railway/cli variables set JWT_SECRET_KEY="rv1s4r-1a-jwt-s3cr3t-2026-h8j4n6t2y9u1"
npx @railway/cli variables set SESSION_SECRET="rv1s4r-1a-s3ss10n-2026-p3q8w5r7v2b6"
npx @railway/cli variables set APP_URL="https://backend-production-ceb1.up.railway.app"
npx @railway/cli variables set BACKEND_URL="https://backend-production-ceb1.up.railway.app"
npx @railway/cli variables set FRONTEND_URL="https://replicar-ia.vercel.app"
npx @railway/cli variables set CORS_ORIGINS="https://replicar-ia.vercel.app,http://localhost:3000,http://localhost:5173"
npx @railway/cli variables set ADMIN_EMAIL="admin@revisar-ia.com"
npx @railway/cli variables set ADMIN_PASSWORD="Rv1s4r-Adm1n-Pr0d-2026!"
npx @railway/cli variables set ADMIN_NAME="Administrador"
npx @railway/cli variables set ADMIN_COMPANY="Revisar.IA"
npx @railway/cli variables set ENVIRONMENT="production"
npx @railway/cli variables set PORT="8000"
npx @railway/cli variables set PYTHONUNBUFFERED="1"
npx @railway/cli variables set ENABLE_QUERY_ROUTER="true"
npx @railway/cli variables set ENABLE_RAG="true"
npx @railway/cli variables set ENABLE_EMAIL_NOTIFICATIONS="true"

echo "✅ Variables configuradas!"
echo "🔄 Haciendo redeploy..."
npx @railway/cli redeploy

echo "🎉 ¡Listo! Tu backend se está desplegando."
