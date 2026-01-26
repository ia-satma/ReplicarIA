const DisclaimerModal = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            Disclaimer Legal y Alcance del Servicio
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
              1. Naturaleza del servicio
            </h3>
            <p className="mb-3">
              Revisar-IA es una <strong>plataforma tecnológica de apoyo</strong> para la{' '}
              <strong>gestión de riesgos fiscales y de cumplimiento</strong> en la contratación 
              de servicios e intangibles (consultorías, software, marketing, servicios 
              intra-grupo, entre otros).
            </p>
            <p className="mb-3">
              Su objetivo es ayudar a las empresas a:
            </p>
            <ul className="list-disc ml-6 space-y-1">
              <li><strong>Documentar</strong> la razón de negocios y el beneficio económico esperado</li>
              <li><strong>Evaluar</strong> la materialidad y trazabilidad documental</li>
              <li><strong>Organizar</strong> evidencias y expedientes útiles en auditorías</li>
            </ul>
            <p className="mt-3 text-red-600 font-semibold">
              Revisar-IA NO es un despacho de abogados ni un despacho contable, 
              ni presta servicios de asesoría legal o fiscal individualizada.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              2. Uso de Inteligencia Artificial como herramienta auxiliar
            </h3>
            <p className="mb-3">
              Revisar-IA utiliza <strong>tecnologías de Inteligencia Artificial (IA)</strong> como{' '}
              <strong>herramienta auxiliar</strong> para aplicar checklists normativos, 
              calcular riesgos fiscales e identificar brechas documentales.
            </p>
            <p className="text-blue-600 font-semibold">
              La IA NO sustituye la voluntad ni la responsabilidad de la empresa usuaria, 
              ni el juicio profesional de sus abogados, fiscalistas o contadores.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              3. Alcance y límites de la información generada
            </h3>
            <p className="mb-3">
              Los resultados generados (matrices de riesgo, checklists, alertas, Defense Files) 
              son <strong>insumos técnicos de apoyo</strong>, NO constituyen:
            </p>
            <ul className="list-disc ml-6 space-y-1 text-red-600">
              <li>Una opinión legal o fiscal definitiva</li>
              <li>Una determinación de obligaciones fiscales</li>
              <li>Una garantía de que el SAT aceptará la deducibilidad de un gasto</li>
            </ul>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              4. Responsabilidad sobre decisiones y datos
            </h3>
            <p className="mb-3">
              La empresa usuaria es la <strong>única responsable</strong> de:
            </p>
            <ul className="list-disc ml-6 space-y-1">
              <li>La veracidad e integridad de los datos cargados</li>
              <li>Aprobar o rechazar contratos, pagos y deducciones fiscales</li>
              <li>Validar los análisis antes de tomar decisiones con efectos jurídicos</li>
            </ul>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              5. Marco normativo de referencia
            </h3>
            <p className="mb-3">
              La plataforma está inspirada en la aplicación práctica de:
            </p>
            <ul className="list-disc ml-6 space-y-1">
              <li><strong>CFF Art. 5-A</strong> (razón de negocios)</li>
              <li><strong>CFF Art. 69-B</strong> (materialidad)</li>
              <li><strong>LISR</strong> (estricta indispensabilidad)</li>
              <li><strong>NOM-151-SCFI-2016</strong> (trazabilidad documental)</li>
            </ul>
            <p className="mt-3 text-sm">
              <a 
                href="https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Ver Código Fiscal de la Federación (CFF)
              </a>
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              6. Recomendación de uso responsable
            </h3>
            <p className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              Los servicios de <strong>alto monto, complejidad o riesgo</strong> deben 
              ser siempre revisados por asesores externos especializados. 
              Revisar-IA es un <strong>punto de partida</strong>, no un sustituto de la 
              debida diligencia profesional.
            </p>
          </section>

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

export default DisclaimerModal;
