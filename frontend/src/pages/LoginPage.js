import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Apple Green accent color
const ACCENT = '#34C759';
const ACCENT_LIGHT = '#3CD366';
const ACCENT_GLOW = 'rgba(52, 199, 89, 0.4)';

const LoginPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { loginWithOTP, isAuthenticated } = useAuth();

  const [step, setStep] = useState('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [authMethod, setAuthMethod] = useState('otp');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userInfo, setUserInfo] = useState(null);
  const [autoSubmitDone, setAutoSubmitDone] = useState(false);

  const inputRefs = useRef([]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const testEmail = searchParams.get('test_email');
    if (testEmail && !autoSubmitDone && !loading && step === 'email') {
      setEmail(testEmail);
      setAutoSubmitDone(true);
      setTimeout(() => {
        const submitOTP = async () => {
          setLoading(true);
          setError('');
          const API_URL = process.env.REACT_APP_BACKEND_URL || '';
          try {
            const response = await fetch(`${API_URL}/api/auth/otp/request-code`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: testEmail.trim() })
            });
            const data = await response.json();
            if (response.ok && data.success) {
              setUserInfo(data.data);
              setStep('code');
            } else {
              setError(data.detail || data.message || 'Correo no autorizado');
            }
          } catch (err) {
            setError('Error al solicitar codigo: ' + err.message);
          } finally {
            setLoading(false);
          }
        };
        submitOTP();
      }, 500);
    }
  }, [searchParams, autoSubmitDone, loading, step]);

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setError('');



    const API_URL = process.env.REACT_APP_BACKEND_URL || '';

    try {
      // 1. Check Auth Method explicitly
      const authCheckResponse = await fetch(`${API_URL}/api/auth/check-auth-method`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() })
      });

      // Handle raw network/server errors on the check
      if (!authCheckResponse.ok) {
        // If check fails, we cannot safely assume OTP. Show error.
        const errText = await authCheckResponse.text();
        throw new Error(`Error verificando usuario: ${authCheckResponse.status}`);
      }

      const authCheckData = await authCheckResponse.json();

      // 2. Route based on explicit response
      if (authCheckData.success && authCheckData.data?.auth_method === 'password') {
        setAuthMethod('password');
        setStep('password');
        setLoading(false);
        return;
      }

      // 3. Fallback to OTP *only if* confirmed or default
      // Proceed to request code
      const response = await fetch(`${API_URL}/api/auth/otp/request-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() })
      });

      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error("Respuesta inválida del servidor (OTP)");
      }

      if (response.ok && data.success) {
        setUserInfo(data.data);
        setStep('code');
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      } else {
        setError(data.detail || data.message || 'Correo no autorizado');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.message && err.message.includes('Failed to fetch')) {
        setError('Error de conexion. Verifica tu internet.');
      } else {
        setError(err.message || 'Error al procesar solicitud. Intenta de nuevo.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) return;

    setLoading(true);
    setError('');

    const API_URL = process.env.REACT_APP_BACKEND_URL || '';

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password: password })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem('auth_token', data.data.access_token);
        localStorage.setItem('auth_user', JSON.stringify(data.data.user));
        window.location.href = '/dashboard';
      } else {
        setError(data.detail || data.message || 'Contrasena incorrecta');
        setPassword('');
      }
    } catch (err) {
      console.error('Password login error:', err);
      setError('Error de autenticacion');
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newCode = code.split('');
    newCode[index] = value;
    const updatedCode = newCode.join('').slice(0, 6);
    setCode(updatedCode);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (updatedCode.length === 6) {
      handleCodeSubmit(updatedCode);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    setCode(pastedData);
    if (pastedData.length === 6) {
      handleCodeSubmit(pastedData);
    } else {
      inputRefs.current[pastedData.length]?.focus();
    }
  };

  const handleCodeSubmit = async (submittedCode = code) => {
    if (submittedCode.length !== 6) return;

    setLoading(true);
    setError('');

    try {
      const result = await loginWithOTP(email, submittedCode);

      if (result.success) {
        navigate('/dashboard');
      } else {
        setError(result.error || 'Codigo invalido o expirado');
        setCode('');
        inputRefs.current[0]?.focus();
      }
    } catch (err) {
      setError('Error de conexion');
      setCode('');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep('email');
    setCode('');
    setPassword('');
    setAuthMethod('otp');
    setError('');
  };

  const Spinner = () => (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );

  const ErrorMessage = ({ message }) => (
    <div className="text-sm text-center rounded-xl p-3 bg-red-500/10 border border-red-500/20 text-red-400">
      {message}
    </div>
  );

  const renderEmailForm = () => (
    <form onSubmit={handleEmailSubmit} className="space-y-5">
      <div className="text-center mb-4">
        <h2 className="text-xl font-semibold text-white">
          Acceso Seguro
        </h2>
        <p className="text-gray-400 text-sm mt-1">Recibe un codigo en tu correo</p>
      </div>

      <div>
        <label className="block text-xs text-gray-300 mb-2 font-medium tracking-wide">
          Correo electronico
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="tu@empresa.com"
          className="w-full px-4 py-3.5 rounded-xl text-white text-sm placeholder-gray-500
                     bg-white/5 border border-white/10
                     focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
                     transition-all duration-200"
          disabled={loading}
          autoFocus
          autoComplete="email"
        />
      </div>

      {error && <ErrorMessage message={error} />}

      <button
        type="submit"
        disabled={loading || !email.trim()}
        className="w-full py-3.5 text-sm font-semibold rounded-xl transition-all
                   disabled:opacity-40 disabled:cursor-not-allowed
                   hover:scale-[1.02] active:scale-[0.98]
                   text-gray-900"
        style={{
          background: `linear-gradient(180deg, ${ACCENT_LIGHT} 0%, ${ACCENT} 100%)`,
          boxShadow: `0 4px 14px ${ACCENT_GLOW}`
        }}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner />
            Enviando...
          </span>
        ) : (
          'Solicitar codigo de acceso'
        )}
      </button>

      <div className="flex justify-center gap-6 pt-2">
        <span className="text-gray-500 text-xs flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" style={{ color: ACCENT }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Sin contrasenas
        </span>
        <span className="text-gray-500 text-xs flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" style={{ color: ACCENT }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          Acceso seguro
        </span>
      </div>
    </form>
  );

  const renderPasswordForm = () => (
    <form onSubmit={handlePasswordSubmit} className="space-y-5">
      <div className="text-center mb-4">
        <div
          className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
          style={{ background: `${ACCENT}15`, border: `1px solid ${ACCENT}30` }}
        >
          <svg className="w-6 h-6" style={{ color: ACCENT }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-white">
          Acceso Super Admin
        </h2>
        <p className="text-sm mt-1 font-medium" style={{ color: ACCENT }}>{email}</p>
      </div>

      <div>
        <label className="block text-xs text-gray-300 mb-2 font-medium tracking-wide">
          Contrasena
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Ingresa tu contrasena"
          className="w-full px-4 py-3.5 rounded-xl text-white text-sm placeholder-gray-500
                     bg-white/5 border border-white/10
                     focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
                     transition-all duration-200"
          disabled={loading}
          autoFocus
          autoComplete="current-password"
        />
      </div>

      {error && <ErrorMessage message={error} />}

      <button
        type="submit"
        disabled={loading || !password.trim()}
        className="w-full py-3.5 text-sm font-semibold rounded-xl transition-all
                   disabled:opacity-40 disabled:cursor-not-allowed
                   hover:scale-[1.02] active:scale-[0.98]
                   text-gray-900"
        style={{
          background: `linear-gradient(180deg, ${ACCENT_LIGHT} 0%, ${ACCENT} 100%)`,
          boxShadow: `0 4px 14px ${ACCENT_GLOW}`
        }}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner />
            Verificando...
          </span>
        ) : (
          'Ingresar'
        )}
      </button>

      <div className="flex justify-center pt-1">
        <button
          type="button"
          onClick={handleBack}
          className="text-gray-500 hover:text-white text-xs transition-colors flex items-center gap-1"
          disabled={loading}
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Usar otro correo
        </button>
      </div>
    </form>
  );

  const renderCodeForm = () => (
    <div className="space-y-5">
      <div className="text-center">
        <div
          className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
          style={{ background: `${ACCENT}15`, border: `1px solid ${ACCENT}30` }}
        >
          <svg className="w-6 h-6" style={{ color: ACCENT }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-white mb-1">Verifica tu identidad</h2>
        <p className="text-gray-500 text-sm">Codigo enviado a</p>
        <p className="text-sm font-medium mt-0.5" style={{ color: ACCENT }}>{email}</p>
        {userInfo?.nombre && (
          <p className="text-gray-400 text-xs mt-2">Hola, {userInfo.nombre}</p>
        )}
        {userInfo?.rol && userInfo.rol !== 'user' && (
          <span
            className="inline-block mt-2 px-2 py-0.5 text-[10px] font-semibold rounded-full"
            style={{
              background: `${ACCENT}20`,
              color: ACCENT,
              border: `1px solid ${ACCENT}30`
            }}
          >
            {userInfo.rol === 'admin' ? 'Administrador' : userInfo.rol}
          </span>
        )}
      </div>

      <div>
        <label className="block text-xs text-gray-400 mb-2.5 text-center font-medium">
          Codigo de 6 digitos
        </label>
        <div className="flex justify-center gap-2.5" onPaste={handlePaste}>
          {[0, 1, 2, 3, 4, 5].map((index) => (
            <input
              key={index}
              ref={(el) => (inputRefs.current[index] = el)}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={code[index] || ''}
              onChange={(e) => handleCodeChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className="w-11 h-13 text-center text-xl font-bold rounded-xl transition-all focus:outline-none"
              style={{
                background: code[index] ? `${ACCENT}15` : 'rgba(255, 255, 255, 0.05)',
                border: code[index] ? `1px solid ${ACCENT}50` : '1px solid rgba(255, 255, 255, 0.1)',
                color: code[index] ? ACCENT : 'white',
                boxShadow: code[index] ? `0 0 15px ${ACCENT}30` : 'none'
              }}
              disabled={loading}
            />
          ))}
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading && (
        <div className="flex justify-center">
          <div className="flex items-center gap-2 text-sm" style={{ color: ACCENT }}>
            <Spinner />
            <span>Verificando...</span>
          </div>
        </div>
      )}

      <div className="flex flex-col items-center gap-2 pt-1">
        <button
          onClick={handleBack}
          className="text-gray-500 hover:text-white text-xs transition-colors flex items-center gap-1"
          disabled={loading}
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Usar otro correo
        </button>
        <span className="text-gray-600 text-[10px]">
          El codigo expira en 5 minutos
        </span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#1C1C1E]">
      {/* Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover opacity-60"
      >
        <source src="/revisar-ia-background.mp4" type="video/mp4" />
      </video>

      {/* Gradient Overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(180deg, rgba(28,28,30,0.4) 0%, rgba(28,28,30,0.2) 40%, rgba(28,28,30,0.6) 100%)'
        }}
      />

      {/* Content */}
      <div className="relative w-full max-w-sm z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <img
            src="/logo-revisar-white.png"
            alt="Revisar.IA"
            className="max-w-[260px] w-full mx-auto mb-4 object-contain"
            style={{
              filter: `drop-shadow(0 0 30px ${ACCENT_GLOW})`
            }}
            onError={(e) => {
              e.target.onerror = null;
              e.target.style.display = 'none';
            }}
          />
          <p
            className="text-xs tracking-[0.3em] uppercase font-medium"
            style={{ color: ACCENT }}
          >
            Auditoria Fiscal Inteligente
          </p>
        </div>

        {/* Login Card */}
        <div
          className="backdrop-blur-2xl rounded-2xl p-6 border border-white/10"
          style={{
            background: 'rgba(28, 28, 30, 0.8)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)'
          }}
        >
          {step === 'email' && renderEmailForm()}
          {step === 'password' && renderPasswordForm()}
          {step === 'code' && renderCodeForm()}
        </div>

        {/* Register Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-500 text-sm mb-2">
            No tienes acceso?
          </p>
          <Link
            to="/register"
            className="text-sm font-medium hover:underline transition-colors"
            style={{ color: ACCENT }}
          >
            Solicitar acceso a Revisar.IA
          </Link>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] mt-6 text-gray-600">
          2026 Revisar.IA - Plataforma de Cumplimiento Fiscal
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
