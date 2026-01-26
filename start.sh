#!/bin/bash
# ============================================================
# ReplicarIA - Script de Inicio Unificado
# ============================================================
# Uso:
#   ./start.sh              # Inicia todo (DBs + Backend + Frontend)
#   ./start.sh db           # Solo bases de datos
#   ./start.sh backend      # Solo backend (asume DBs corriendo)
#   ./start.sh frontend     # Solo frontend
#   ./start.sh stop         # Detiene todo
# ============================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado. Por favor instala Docker primero."
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose no está instalado."
        exit 1
    fi
}

# Verificar si Python está instalado
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado."
        exit 1
    fi
}

# Verificar si Node está instalado
check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js no está instalado."
        exit 1
    fi
}

# Crear archivo .env si no existe
setup_env() {
    if [ ! -f ".env" ]; then
        log_warning "Archivo .env no encontrado. Creando desde .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Archivo .env creado. Por favor edita las variables antes de continuar."
            log_warning "Especialmente: OPENAI_API_KEY, ANTHROPIC_API_KEY, ADMIN_PASSWORD"
            read -p "Presiona Enter cuando hayas configurado .env, o Ctrl+C para cancelar..."
        else
            log_error "No se encontró .env.example"
            exit 1
        fi
    fi
}

# Cargar variables de entorno
load_env() {
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
}

# Iniciar bases de datos con Docker
start_databases() {
    log_info "Iniciando bases de datos con Docker..."
    check_docker

    # Usar docker-compose o docker compose según disponibilidad
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d mongodb postgres redis
    else
        docker compose up -d mongodb postgres redis
    fi

    log_info "Esperando que las bases de datos estén listas..."
    sleep 5

    # Verificar MongoDB
    if docker exec replicaria-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        log_success "MongoDB está listo"
    else
        log_warning "MongoDB aún iniciando..."
        sleep 5
    fi

    # Verificar PostgreSQL
    if docker exec replicaria-postgres pg_isready -U replicaria &> /dev/null; then
        log_success "PostgreSQL está listo"
    else
        log_warning "PostgreSQL aún iniciando..."
        sleep 5
    fi

    log_success "Bases de datos iniciadas"
}

# Detener bases de datos
stop_databases() {
    log_info "Deteniendo bases de datos..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    log_success "Bases de datos detenidas"
}

# Instalar dependencias del backend
install_backend_deps() {
    log_info "Instalando dependencias del backend..."
    cd "$PROJECT_DIR/backend"

    # Crear virtualenv si no existe
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activar virtualenv e instalar dependencias
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    log_success "Dependencias del backend instaladas"
    cd "$PROJECT_DIR"
}

# Iniciar backend
start_backend() {
    log_info "Iniciando backend..."
    check_python
    cd "$PROJECT_DIR/backend"

    # Activar virtualenv si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Exportar variables para conexión con Docker
    export MONGO_URL="mongodb://admin:replicaria2024@localhost:27017/agent_network?authSource=admin"
    export DATABASE_URL="postgresql://replicaria:replicaria2024@localhost:5432/replicaria"
    export REDIS_URL="redis://localhost:6379"

    # Iniciar uvicorn
    uvicorn server:app --host 0.0.0.0 --port 5000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_DIR/.backend.pid"

    sleep 3
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_success "Backend iniciado en http://localhost:5000"
        log_info "API Docs en http://localhost:5000/docs"
    else
        log_error "Error iniciando backend"
        exit 1
    fi

    cd "$PROJECT_DIR"
}

# Detener backend
stop_backend() {
    if [ -f "$PROJECT_DIR/.backend.pid" ]; then
        PID=$(cat "$PROJECT_DIR/.backend.pid")
        if kill -0 $PID 2>/dev/null; then
            log_info "Deteniendo backend (PID: $PID)..."
            kill $PID
            rm "$PROJECT_DIR/.backend.pid"
            log_success "Backend detenido"
        fi
    fi
}

# Instalar dependencias del frontend
install_frontend_deps() {
    log_info "Instalando dependencias del frontend..."
    cd "$PROJECT_DIR/frontend"
    npm install --legacy-peer-deps
    log_success "Dependencias del frontend instaladas"
    cd "$PROJECT_DIR"
}

# Iniciar frontend
start_frontend() {
    log_info "Iniciando frontend..."
    check_node
    cd "$PROJECT_DIR/frontend"

    export REACT_APP_BACKEND_URL="http://localhost:5000"

    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_DIR/.frontend.pid"

    sleep 5
    log_success "Frontend iniciado en http://localhost:3000"

    cd "$PROJECT_DIR"
}

# Detener frontend
stop_frontend() {
    if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
        PID=$(cat "$PROJECT_DIR/.frontend.pid")
        if kill -0 $PID 2>/dev/null; then
            log_info "Deteniendo frontend (PID: $PID)..."
            kill $PID
            rm "$PROJECT_DIR/.frontend.pid"
            log_success "Frontend detenido"
        fi
    fi
    # También matar procesos de node relacionados
    pkill -f "react-scripts start" 2>/dev/null || true
}

# Mostrar estado
show_status() {
    echo ""
    echo "============================================================"
    echo "  ReplicarIA - Estado del Sistema"
    echo "============================================================"

    # Docker containers
    echo ""
    echo "Contenedores Docker:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep replicaria || echo "  No hay contenedores corriendo"

    # Backend
    echo ""
    if [ -f "$PROJECT_DIR/.backend.pid" ] && kill -0 $(cat "$PROJECT_DIR/.backend.pid") 2>/dev/null; then
        echo -e "Backend: ${GREEN}Corriendo${NC} (http://localhost:5000)"
    else
        echo -e "Backend: ${RED}Detenido${NC}"
    fi

    # Frontend
    if [ -f "$PROJECT_DIR/.frontend.pid" ] && kill -0 $(cat "$PROJECT_DIR/.frontend.pid") 2>/dev/null; then
        echo -e "Frontend: ${GREEN}Corriendo${NC} (http://localhost:3000)"
    else
        echo -e "Frontend: ${RED}Detenido${NC}"
    fi

    echo ""
    echo "============================================================"
}

# Función principal
main() {
    echo ""
    echo "============================================================"
    echo "  ReplicarIA - Sistema de Agentes IA"
    echo "============================================================"
    echo ""

    case "${1:-all}" in
        db|databases)
            setup_env
            load_env
            start_databases
            ;;
        backend)
            setup_env
            load_env
            install_backend_deps
            start_backend
            ;;
        frontend)
            setup_env
            load_env
            install_frontend_deps
            start_frontend
            ;;
        stop)
            stop_frontend
            stop_backend
            stop_databases
            log_success "Todo detenido"
            ;;
        status)
            show_status
            ;;
        all|"")
            setup_env
            load_env
            start_databases
            install_backend_deps
            start_backend
            install_frontend_deps
            start_frontend
            echo ""
            log_success "Sistema iniciado completamente!"
            echo ""
            echo "  - Backend:  http://localhost:5000"
            echo "  - Frontend: http://localhost:3000"
            echo "  - API Docs: http://localhost:5000/docs"
            echo ""
            echo "  Para detener: ./start.sh stop"
            echo ""
            ;;
        *)
            echo "Uso: $0 {all|db|backend|frontend|stop|status}"
            exit 1
            ;;
    esac
}

# Ejecutar
main "$@"
