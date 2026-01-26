const PrivacyNoticeModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-y-auto">
        
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            Aviso de Privacidad Integral
          </h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="px-6 py-6 space-y-6 text-gray-700">
          
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              1. Identidad y domicilio del responsable
            </h3>
            <p className="mb-3">
              El responsable del tratamiento de los datos personales es{' '}
              <strong>SERVICIOS DE ADMINISTRACIÓN, TECNOLOGÍA, Y MERCADOTECNIA PARA ABOGADOS</strong>{' '}
              (en adelante, "el Responsable"), con:
            </p>
            <ul className="list-disc ml-6 space-y-1 text-sm bg-gray-50 p-4 rounded">
              <li><strong>RFC:</strong> SAT180723RW3</li>
              <li><strong>Domicilio:</strong> Avenida Simón Bolívar 224, OF 301, Colonia Chepevera, CP 64030, Monterrey, Nuevo León, México</li>
              <li><strong>Correo de contacto para temas de privacidad:</strong> santiago@satma.mx</li>
            </ul>
            <p className="mt-3 text-sm">
              Este Aviso de Privacidad se emite en cumplimiento de la{' '}
              <strong>Ley Federal de Protección de Datos Personales en Posesión de los Particulares</strong>{' '}
              y su Reglamento.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              2. Datos personales que tratamos
            </h3>
            <p className="mb-3">
              En la operación de la plataforma <strong>Revisar‑IA</strong> podremos tratar los siguientes tipos de datos personales:
            </p>
            
            <div className="space-y-3">
              <div className="bg-blue-50 p-3 rounded">
                <h4 className="font-semibold text-blue-900 mb-2">Datos de identificación y contacto:</h4>
                <p className="text-sm">
                  Nombre, apellidos, puesto, área, correo electrónico corporativo, teléfono, usuario en la plataforma, empresa.
                </p>
              </div>

              <div className="bg-green-50 p-3 rounded">
                <h4 className="font-semibold text-green-900 mb-2">Datos laborales/corporativos:</h4>
                <p className="text-sm">
                  Área, departamento, rol en procesos de contratación/aprobación/auditoría, facultades de autorización.
                </p>
              </div>

              <div className="bg-purple-50 p-3 rounded">
                <h4 className="font-semibold text-purple-900 mb-2">Datos de uso de la plataforma:</h4>
                <p className="text-sm">
                  Credenciales de acceso, fecha/hora de ingreso, acciones realizadas, logs técnicos.
                </p>
              </div>

              <div className="bg-yellow-50 p-3 rounded">
                <h4 className="font-semibold text-yellow-900 mb-2">Datos en documentos cargados:</h4>
                <p className="text-sm">
                  Contratos, facturas, CFDI, reportes. La empresa usuaria es responsable primaria de estos datos; 
                  Revisar‑IA actúa como <strong>encargado</strong>.
                </p>
              </div>
            </div>

            <p className="mt-3 text-red-600 font-semibold text-sm">
              No solicitamos datos personales sensibles de forma intencional.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              3. Finalidades del tratamiento
            </h3>
            
            <h4 className="font-semibold text-gray-900 mb-2">Finalidades primarias (necesarias):</h4>
            <ul className="list-disc ml-6 space-y-1 text-sm mb-4">
              <li>Prestación del servicio de la plataforma Revisar‑IA</li>
              <li>Creación y administración de cuentas de usuario</li>
              <li>Ejecución de funciones de control interno y auditoría preventiva</li>
              <li>Generación de Defense Files y reportes</li>
              <li>Registro de actividades y trazabilidad</li>
              <li>Soporte técnico y atención a usuarios</li>
            </ul>

            <h4 className="font-semibold text-gray-900 mb-2">Finalidades secundarias (opcionales):</h4>
            <ul className="list-disc ml-6 space-y-1 text-sm">
              <li>Fines comerciales y comunicación corporativa</li>
              <li>Envío de boletines informativos y actualizaciones</li>
              <li>Mejora continua y análisis estadístico (agregado y anonimizado)</li>
            </ul>

            <p className="mt-3 bg-yellow-50 p-3 rounded text-sm">
              Puedes negarte al uso de tus datos para finalidades secundarias escribiendo a{' '}
              <strong>santiago@satma.mx</strong>. Esto no afectará el uso de la plataforma.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              4. Base de licitud del tratamiento
            </h3>
            <p>El tratamiento se realiza con base en:</p>
            <ul className="list-disc ml-6 space-y-1 text-sm mt-2">
              <li>La <strong>relación jurídica</strong> entre tu empresa y el Responsable</li>
              <li>La <strong>necesidad del tratamiento</strong> para la ejecución del servicio</li>
              <li>El <strong>consentimiento</strong> otorgado al aceptar este Aviso</li>
            </ul>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              5. Transferencias de datos personales
            </h3>
            <p className="mb-2">Podremos realizar transferencias a:</p>
            <ul className="list-disc ml-6 space-y-1 text-sm">
              <li><strong>Proveedores de servicios tecnológicos</strong> (hosting, nube, respaldo) que actúan como encargados</li>
              <li><strong>Empresas del mismo grupo corporativo</strong> para gestión interna</li>
            </ul>
            <p className="mt-3 text-sm">
              Todas las transferencias se realizan bajo <strong>contratos de confidencialidad</strong>{' '}
              y con el mismo nivel de protección.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              6. Medidas de seguridad
            </h3>
            <p className="mb-2">Implementamos medidas técnicas y administrativas:</p>
            <ul className="list-disc ml-6 space-y-1 text-sm">
              <li>Controles de acceso lógico (usuarios, contraseñas, roles)</li>
              <li>Cifrado de información en tránsito y en reposo</li>
              <li>Registros de actividad (logs) para auditoría</li>
              <li>Políticas de confidencialidad y acceso restringido</li>
            </ul>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              7. Derechos ARCO y medios para ejercerlos
            </h3>
            <p className="mb-3">
              Puedes ejercer tus derechos de <strong>Acceso, Rectificación, Cancelación u Oposición (ARCO)</strong>{' '}
              mediante solicitud enviada a:
            </p>
            <div className="bg-blue-50 p-4 rounded">
              <p className="font-semibold">Correo: santiago@satma.mx</p>
              <p className="text-sm mt-2">Asunto: "Ejercicio de derechos ARCO – Revisar‑IA"</p>
            </div>
            <p className="mt-3 text-sm">
              La solicitud debe contener: nombre del titular, medio de contacto, descripción de los datos, 
              y copia de identificación oficial.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              8. Uso de cookies y tecnologías similares
            </h3>
            <p className="text-sm">
              El sitio web y la plataforma pueden utilizar <strong>cookies</strong> para mejorar la experiencia, 
              recordar preferencias y analizar patrones de uso. Puedes configurar tu navegador para aceptar o rechazar cookies.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              9. Actualizaciones del Aviso de Privacidad
            </h3>
            <p className="text-sm">
              Este Aviso puede ser modificado en cualquier momento. Los cambios sustanciales serán comunicados 
              a través de la plataforma o del sitio web <strong>revisar-ia.com</strong>.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              10. Contacto
            </h3>
            <div className="bg-gray-50 p-4 rounded">
              <p><strong>Responsable:</strong> Pablo Santiago Álvarez Rincón</p>
              <p><strong>Correo:</strong> santiago@satma.mx</p>
              <p><strong>Domicilio:</strong> Av. Simón Bolívar 224, OF 301, Chepevera, CP 64030, Monterrey, N.L.</p>
            </div>
          </section>

          <div className="text-center text-xs text-gray-500 mt-8 pt-4 border-t">
            Última actualización: Enero 2026
          </div>

        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t">
          <button 
            onClick={onClose}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};

export default PrivacyNoticeModal;
