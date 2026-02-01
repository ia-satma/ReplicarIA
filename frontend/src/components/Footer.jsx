import { useState } from 'react';
import DisclaimerModal from './DisclaimerModal';
import PrivacyNoticeModal from './PrivacyNoticeModal';

// Build info - generado automaticamente en cada deploy
const BUILD_INFO = {
  version: process.env.REACT_APP_VERSION || '2.0.0',
  buildDate: process.env.REACT_APP_BUILD_DATE || 'Dev Mode',
  gitCommit: process.env.REACT_APP_GIT_COMMIT || 'local',
  gitBranch: process.env.REACT_APP_GIT_BRANCH || 'main',
};

const Footer = () => {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showBuildInfo, setShowBuildInfo] = useState(false);

  return (
    <>
      <footer className="bg-gray-900 text-gray-300 py-8 mt-auto">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

            <div>
              <h3 className="text-white font-bold text-lg mb-4">Revisar.IA</h3>
              <p className="text-sm">
                Plataforma tecnologica de apoyo para la gestion de riesgos fiscales
                y cumplimiento en Mexico.
              </p>
            </div>

            <div>
              <h3 className="text-white font-bold text-lg mb-4">Informacion Legal</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <button
                    onClick={() => setShowDisclaimer(true)}
                    className="hover:text-white transition-colors"
                  >
                    Disclaimer Legal
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => setShowPrivacy(true)}
                    className="hover:text-white transition-colors"
                  >
                    Aviso de Privacidad
                  </button>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-white font-bold text-lg mb-4">Contacto</h3>
              <div className="text-sm">
                <a href="mailto:soporte@revisar-ia.com" className="hover:text-white transition-colors font-semibold">SOPORTE@REVISAR-IA.COM</a>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-700 mt-8 pt-6 text-center">
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} Revisar.IA
              <strong className="text-gray-300"> · Plataforma tecnologica de apoyo</strong>
            </p>
            <p className="text-xs text-gray-500 mt-2">
              No somos despacho contable ni legal. La IA es herramienta auxiliar.
            </p>

            {/* Version and Build Info */}
            <div className="mt-4 pt-4 border-t border-gray-800">
              <button
                onClick={() => setShowBuildInfo(!showBuildInfo)}
                className="text-xs text-gray-600 hover:text-gray-400 transition-colors font-mono"
              >
                v{BUILD_INFO.version} · {BUILD_INFO.gitCommit}
              </button>

              {showBuildInfo && (
                <div className="mt-2 p-3 bg-gray-800 rounded-lg text-left max-w-md mx-auto">
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <span className="text-gray-500">Version:</span>
                    <span className="text-green-400">{BUILD_INFO.version}</span>

                    <span className="text-gray-500">Ultima actualizacion:</span>
                    <span className="text-blue-400">{BUILD_INFO.buildDate}</span>

                    <span className="text-gray-500">Commit:</span>
                    <span className="text-yellow-400">{BUILD_INFO.gitCommit}</span>

                    <span className="text-gray-500">Branch:</span>
                    <span className="text-purple-400">{BUILD_INFO.gitBranch}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    Click para cerrar
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </footer>

      {showDisclaimer && (
        <DisclaimerModal onClose={() => setShowDisclaimer(false)} />
      )}
      {showPrivacy && (
        <PrivacyNoticeModal onClose={() => setShowPrivacy(false)} />
      )}
    </>
  );
};

export default Footer;
