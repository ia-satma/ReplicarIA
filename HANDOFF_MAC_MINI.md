# HANDOFF: Migración a Mac Mini M4

> **Última actualización:** 2026-02-06
> **Estado:** En progreso
> **Autor:** Claude + INTELIGENCIA

---

## 1. CONTEXTO DEL PROYECTO

### ¿Qué es ReplicarIA?
Sistema multi-agente para gestión de proyectos de consultoría con cumplimiento fiscal mexicano. Incluye 18 agentes de IA especializados que deliberan sobre proyectos.

### ¿Por qué la migración?
- **Problema:** Los agentes NO funcionan en Railway (ambiente stateless)
- **Causa:** Railway corre cada request en proceso aislado, sin memoria compartida
- **Solución:** Mac Mini M4 corre todo en UN proceso con memoria compartida

### Decisión tomada
- ❌ NO arreglar Railway (arquitectura incompatible)
- ❌ NO usar una Mac Mini por agente (innecesario)
- ✅ UNA Mac Mini M4 para todo (backend + agentes + Claude Code)

---

## 2. ARQUITECTURA ACTUAL vs NUEVA

### Actual (NO funciona bien)
```
Vercel (frontend) → Railway (backend stateless) → Supabase (BD)
                         ↓
                    Agentes NO deliberan correctamente
```

### Nueva (Mac Mini M4)
```
Vercel (frontend) → Cloudflare Tunnel → Mac Mini M4 → Supabase (BD)
                                              ↓
                                    UN proceso Python
                                    18 agentes en memoria
                                    Deliberación funciona
```

---

## 3. ESTADO DE LOS COMPONENTES

| Componente | Ubicación | Estado | Acción |
|------------|-----------|--------|--------|
| Frontend | Vercel | ✅ Funciona | Mantener |
| Backend | Railway | ⚠️ Parcial | → Migrar a Mac Mini |
| Base de datos | Supabase | ✅ Funciona | Mantener |
| Oráculo | Cloudflare Workers | ✅ Funciona | Mantener |
| Agentes | Railway | ❌ No funcionan | → Mac Mini |

---

## 4. CONFIGURACIÓN DE LA MAC MINI M4

### 4.1 Software a instalar

```bash
# 1. Homebrew (gestor de paquetes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python 3.11+
brew install python@3.11

# 3. Node.js (para Claude Code)
brew install node

# 4. Git
brew install git

# 5. Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 6. Cloudflare Tunnel
brew install cloudflare/cloudflare/cloudflared
```

### 4.2 Clonar el proyecto

```bash
# Crear directorio de trabajo
mkdir -p ~/Proyectos
cd ~/Proyectos

# Clonar desde GitHub
git clone https://github.com/ia-satma/ReplicarIA.git
cd ReplicarIA

# Crear entorno virtual Python
cd backend
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4.3 Configurar variables de entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar con tus credenciales REALES
nano .env
```

**Variables críticas a configurar:**
```env
# Base de datos (usar la misma de Supabase/Railway)
DATABASE_URL=postgresql://...

# APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email
DREAMHOST_EMAIL_PASSWORD=...

# URLs (CAMBIAR a Mac Mini)
APP_URL=https://api.tudominio.com
BACKEND_URL=https://api.tudominio.com
FRONTEND_URL=https://replicar-ia.vercel.app

# Seguridad
SECRET_KEY=...
JWT_SECRET_KEY=...
```

### 4.4 Probar que funcione localmente

```bash
# Activar entorno virtual
cd ~/Proyectos/ReplicarIA/backend
source venv/bin/activate

# Correr el servidor
uvicorn server:app --host 0.0.0.0 --port 5000 --reload

# Deberías ver:
# ✅ PostgreSQL Connection Pool Established
# ✅ Health V4 routes loaded successfully
# Uvicorn running on http://0.0.0.0:5000
```

### 4.5 Configurar Cloudflare Tunnel

```bash
# 1. Autenticarse en Cloudflare
cloudflared tunnel login

# 2. Crear el tunnel
cloudflared tunnel create replicaria-backend

# 3. Configurar DNS (en dashboard de Cloudflare)
# Crear CNAME: api.tudominio.com → <tunnel-id>.cfargotunnel.com

# 4. Crear config
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Contenido de `config.yml`:
```yaml
tunnel: <tu-tunnel-id>
credentials-file: /Users/<tu-usuario>/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: api.tudominio.com
    service: http://localhost:5000
  - service: http_status:404
```

```bash
# 5. Correr el tunnel
cloudflared tunnel run replicaria-backend
```

### 4.6 Hacer que corra al iniciar (servicio)

```bash
# Crear archivo de servicio para el backend
sudo nano /Library/LaunchDaemons/com.replicaria.backend.plist
```

---

## 5. CÓMO ACTUALIZAR LA MAC MINI

### Cuando hagamos cambios aquí (en desarrollo):

```bash
# Aquí (donde programamos con Claude):
git add .
git commit -m "feat: mejora en agente X"
git push origin main
```

### En la Mac Mini M4 (producción):

```bash
# Actualizar código
cd ~/Proyectos/ReplicarIA
git pull origin main

# Reiniciar el servidor (si es necesario)
# Opción 1: Manual
pkill -f uvicorn
source backend/venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 5000 &

# Opción 2: Si tienes servicio systemd/launchd
sudo launchctl stop com.replicaria.backend
sudo launchctl start com.replicaria.backend
```

### Script de actualización automática (opcional):

Crear `~/Proyectos/actualizar.sh`:
```bash
#!/bin/bash
cd ~/Proyectos/ReplicarIA
git pull origin main
pkill -f uvicorn
cd backend
source venv/bin/activate
nohup uvicorn server:app --host 0.0.0.0 --port 5000 &
echo "✅ Actualizado y reiniciado"
```

---

## 6. INSTRUCCIONES PARA CLAUDE (en Mac Mini)

Si estás leyendo esto en la Mac Mini M4, aquí está el contexto:

### Tu misión:
1. Verificar que el backend corra correctamente
2. Probar que los agentes deliberen en proceso único
3. Configurar Cloudflare Tunnel
4. Actualizar el frontend en Vercel para apuntar a la nueva URL

### Archivos importantes:
- `/backend/server.py` - Punto de entrada
- `/backend/config/agents_registry.py` - Registro de 18 agentes
- `/backend/services/agent_prompts.py` - Prompts de agentes
- `/PRD_Agentes_ReplicarIA.docx` - Documentación completa de agentes

### Para continuar el trabajo:
```
Lee este archivo y luego pregúntale al usuario:
"Ya tengo el contexto de HANDOFF. ¿Qué quieres que haga primero?"
```

---

## 7. CHECKLIST DE MIGRACIÓN

- [ ] Instalar software en Mac Mini M4
- [ ] Clonar repositorio
- [ ] Configurar .env con credenciales
- [ ] Probar backend localmente (localhost:5000)
- [ ] Verificar que agentes deliberen correctamente
- [ ] Configurar Cloudflare Tunnel
- [ ] Actualizar frontend para apuntar a nueva URL
- [ ] Desactivar Railway
- [ ] Monitorear estabilidad por 1 semana

---

## 8. CONTACTO Y SOPORTE

- **Repositorio:** https://github.com/ia-satma/ReplicarIA
- **Frontend:** https://replicar-ia.vercel.app
- **Documentación de agentes:** Ver `PRD_Agentes_ReplicarIA.docx`

---

*Este archivo se actualiza conforme avanzamos. Haz `git pull` para obtener la última versión.*
