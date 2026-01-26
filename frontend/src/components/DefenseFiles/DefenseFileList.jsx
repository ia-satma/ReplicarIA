import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  Plus,
  Search,
  Filter,
  Clock,
  Lock,
  AlertTriangle,
  CheckCircle,
  FileText,
  Users,
  RefreshCw,
  ChevronRight,
  Calendar,
  Building
} from 'lucide-react';

const API_BASE = '/api/defense-files';

const ESTADO_CONFIG = {
  abierto: { color: 'border-green-500 bg-green-500/10', text: 'Abierto', icon: CheckCircle, iconColor: 'text-green-400' },
  en_revision: { color: 'border-yellow-500 bg-yellow-500/10', text: 'En Revisión', icon: AlertTriangle, iconColor: 'text-yellow-400' },
  pendiente: { color: 'border-orange-500 bg-orange-500/10', text: 'Pendiente', icon: Clock, iconColor: 'text-orange-400' },
  cerrado: { color: 'border-blue-500 bg-blue-500/10', text: 'Cerrado', icon: Lock, iconColor: 'text-blue-400' },
  archivado: { color: 'border-gray-500 bg-gray-500/10', text: 'Archivado', icon: FileText, iconColor: 'text-gray-400' }
};

export default function DefenseFileList() {
  const navigate = useNavigate();
  const [defenseFiles, setDefenseFiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    estado: '',
    anio_fiscal: '',
    search: ''
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newExpediente, setNewExpediente] = useState({
    cliente_id: 1,
    nombre: '',
    anio_fiscal: new Date().getFullYear(),
    descripcion: ''
  });
  const [creating, setCreating] = useState(false);

  const fetchDefenseFiles = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.estado) params.append('estado', filters.estado);
      if (filters.anio_fiscal) params.append('anio_fiscal', filters.anio_fiscal);
      
      const response = await fetch(`${API_BASE}?${params.toString()}`);
      const data = await response.json();
      if (data.success) {
        let files = data.defense_files || [];
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          files = files.filter(f => 
            f.nombre?.toLowerCase().includes(searchLower) ||
            f.descripcion?.toLowerCase().includes(searchLower)
          );
        }
        setDefenseFiles(files);
      }
    } catch (err) {
      console.error('Error fetching defense files:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      if (data.success) {
        setStats(data.estadisticas);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  useEffect(() => {
    fetchDefenseFiles();
    fetchStats();
  }, [fetchDefenseFiles, fetchStats]);

  const handleCreateExpediente = async () => {
    if (!newExpediente.nombre) {
      alert('El nombre es requerido');
      return;
    }
    setCreating(true);
    try {
      const response = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newExpediente)
      });
      const data = await response.json();
      if (data.success) {
        setShowCreateModal(false);
        setNewExpediente({ cliente_id: 1, nombre: '', anio_fiscal: new Date().getFullYear(), descripcion: '' });
        fetchDefenseFiles();
        fetchStats();
        navigate(`/defense-files/${data.defense_file.id}`);
      } else {
        alert('Error: ' + (data.error || data.detail));
      }
    } catch (err) {
      alert('Error de conexión');
    } finally {
      setCreating(false);
    }
  };

  const calculateProgress = (df) => {
    const stats = df.estadisticas || {};
    const total = (stats.total_eventos || 0) + (stats.total_proveedores || 0) + 
                  (stats.total_cfdis || 0) + (stats.total_fundamentos || 0) + (stats.total_calculos || 0);
    if (total === 0) return 0;
    return Math.min(100, Math.round((total / 20) * 100));
  };

  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-blue-400" />
            <h1 className="text-2xl font-bold">Expedientes de Defensa</h1>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" /> Nuevo Expediente
          </button>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-400">{stats.total_expedientes || 0}</p>
              <p className="text-sm text-gray-400">Total Expedientes</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-green-400">{stats.expedientes_abiertos || 0}</p>
              <p className="text-sm text-gray-400">Abiertos</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-purple-400">{stats.expedientes_cerrados || 0}</p>
              <p className="text-sm text-gray-400">Cerrados</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-orange-400">{stats.total_eventos || 0}</p>
              <p className="text-sm text-gray-400">Eventos</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-yellow-400">${((stats.monto_total_cfdis || 0) / 1000000).toFixed(1)}M</p>
              <p className="text-sm text-gray-400">Monto CFDIs</p>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar expedientes..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
            <select
              value={filters.estado}
              onChange={(e) => setFilters(prev => ({ ...prev, estado: e.target.value }))}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="">Todos los estados</option>
              {Object.entries(ESTADO_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.text}</option>
              ))}
            </select>
            <select
              value={filters.anio_fiscal}
              onChange={(e) => setFilters(prev => ({ ...prev, anio_fiscal: e.target.value }))}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="">Todos los años</option>
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
            <button
              onClick={() => { fetchDefenseFiles(); fetchStats(); }}
              className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {defenseFiles.map((df) => {
              const estadoConfig = ESTADO_CONFIG[df.estado] || ESTADO_CONFIG.abierto;
              const EstadoIcon = estadoConfig.icon;
              const progress = calculateProgress(df);
              const stats = df.estadisticas || {};

              return (
                <div
                  key={df.id}
                  onClick={() => navigate(`/defense-files/${df.id}`)}
                  className={`bg-gray-800 rounded-lg p-5 border-l-4 ${estadoConfig.color} cursor-pointer hover:bg-gray-750 transition-colors`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg truncate">{df.nombre}</h3>
                      <p className="text-sm text-gray-400 flex items-center mt-1">
                        <Calendar className="w-4 h-4 mr-1" /> {df.anio_fiscal}
                        <span className="mx-2">•</span>
                        <Building className="w-4 h-4 mr-1" /> Cliente #{df.cliente_id}
                      </p>
                    </div>
                    <div className={`flex items-center ${estadoConfig.iconColor}`}>
                      <EstadoIcon className="w-5 h-5" />
                    </div>
                  </div>

                  {df.descripcion && (
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{df.descripcion}</p>
                  )}

                  <div className="grid grid-cols-4 gap-2 text-center text-xs mb-3">
                    <div>
                      <p className="text-blue-400 font-semibold">{stats.total_eventos || 0}</p>
                      <p className="text-gray-500">Eventos</p>
                    </div>
                    <div>
                      <p className="text-purple-400 font-semibold">{stats.total_proveedores || 0}</p>
                      <p className="text-gray-500">Provs</p>
                    </div>
                    <div>
                      <p className="text-green-400 font-semibold">{stats.total_cfdis || 0}</p>
                      <p className="text-gray-500">CFDIs</p>
                    </div>
                    <div>
                      <p className="text-orange-400 font-semibold">{stats.total_fundamentos || 0}</p>
                      <p className="text-gray-500">Funds</p>
                    </div>
                  </div>

                  <div className="mb-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-500">Progreso</span>
                      <span className="text-gray-400">{progress}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>Creado: {df.created_at?.split('T')[0]}</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!loading && defenseFiles.length === 0 && (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">No hay expedientes que coincidan con los filtros</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Crear primer expediente
            </button>
          </div>
        )}

        {showCreateModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <Plus className="w-5 h-5 mr-2 text-blue-400" /> Nuevo Expediente
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nombre *</label>
                  <input
                    type="text"
                    value={newExpediente.nombre}
                    onChange={(e) => setNewExpediente(prev => ({ ...prev, nombre: e.target.value }))}
                    placeholder="Ej: Expediente Defensa 2024"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Año Fiscal</label>
                  <select
                    value={newExpediente.anio_fiscal}
                    onChange={(e) => setNewExpediente(prev => ({ ...prev, anio_fiscal: parseInt(e.target.value) }))}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    {years.map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Cliente ID</label>
                  <input
                    type="number"
                    value={newExpediente.cliente_id}
                    onChange={(e) => setNewExpediente(prev => ({ ...prev, cliente_id: parseInt(e.target.value) || 1 }))}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Descripción</label>
                  <textarea
                    value={newExpediente.descripcion}
                    onChange={(e) => setNewExpediente(prev => ({ ...prev, descripcion: e.target.value }))}
                    placeholder="Descripción opcional..."
                    rows={3}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreateExpediente}
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  {creating ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Creando...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" /> Crear
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
