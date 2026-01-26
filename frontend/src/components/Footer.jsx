import { useState } from 'react';
import DisclaimerModal from './DisclaimerModal';
import PrivacyNoticeModal from './PrivacyNoticeModal';

const Footer = () => {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);

  return (
    <>
      <footer className="bg-gray-900 text-gray-300 py-8 mt-auto">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            <div>
              <h3 className="text-white font-bold text-lg mb-4">Revisar.IA</h3>
              <p className="text-sm">
                Plataforma tecnológica de apoyo para la gestión de riesgos fiscales
                y cumplimiento en México.
              </p>
            </div>

            <div>
              <h3 className="text-white font-bold text-lg mb-4">Información Legal</h3>
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
              <strong className="text-gray-300"> · Plataforma tecnológica de apoyo</strong>
            </p>
            <p className="text-xs text-gray-500 mt-2">
              No somos despacho contable ni legal. La IA es herramienta auxiliar.
            </p>
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
