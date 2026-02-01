"""
Financial Tools for ReplicarIA Agents.
Includes ROI calculation, currency conversion, and financial validation.
"""

from typing import Dict, Any, List
from .registry import tool
from datetime import datetime

@tool(
    name="calculate_roi",
    description="Calculates Return on Investment (ROI) and payback period.",
    parameters={
        "type": "object",
        "properties": {
            "investment": {"type": "number", "description": "Total investment amount"},
            "returns": {"type": "number", "description": "Total expected returns"},
            "period_months": {"type": "integer", "description": "Period in months"}
        },
        "required": ["investment", "returns"]
    }
)
def calculate_roi(investment: float, returns: float, period_months: int = 12) -> Dict[str, Any]:
    """Calculate ROI metrics."""
    if investment <= 0:
        return {"error": "Investment must be greater than 0"}
        
    net_profit = returns - investment
    roi_percentage = (net_profit / investment) * 100
    
    monthly_return = returns / period_months if period_months > 0 else 0
    payback_months = investment / monthly_return if monthly_return > 0 else 0
    
    return {
        "roi_percentage": round(roi_percentage, 2),
        "net_profit": round(net_profit, 2),
        "payback_months": round(payback_months, 1),
        "is_positive": net_profit > 0
    }

import requests
from xml.etree import ElementTree as ET

@tool(
    name="validate_cfdi",
    description="Validates a CFDI using the OFFICIAL SAT SOAP Web Service.",
    parameters={
        "type": "object",
        "properties": {
            "uuid": {"type": "string", "description": "Fiscal UUID"},
            "monto": {"type": "number", "description": "Total amount (Exact match required)"},
            "rfc_emisor": {"type": "string", "description": "RFC Issuer"},
            "rfc_receptor": {"type": "string", "description": "RFC Receiver"}
        },
        "required": ["uuid", "monto", "rfc_emisor", "rfc_receptor"]
    }
)
def validate_cfdi(uuid: str, monto: float, rfc_emisor: str, rfc_receptor: str) -> Dict[str, Any]:
    """Validate CFDI status via SAT Web Service."""
    
    # SAT SOAP Endpoint
    url = "https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc"
    
    # SOAP Action
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta'
    }
    
    # Construct SOAP Body based on SAT requirements:
    # re=RFC Emisor, rr=RFC Receptor, tt=Total Amount (fixed 10 chars), id=UUID
    # Total formatting: 123.45 -> 123.450000 (must be padded) -> actually SAT is flexible but recommends formatted
    formatted_total = f"{monto:.6f}" 
    expression = f"?re={rfc_emisor}&rr={rfc_receptor}&tt={formatted_total}&id={uuid}"
    
    soap_envelope = f"""<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
    <s:Body>
        <Consulta xmlns="http://tempuri.org/">
            <expresionImpresa><![CDATA[{expression}]]></expresionImpresa>
        </Consulta>
    </s:Body>
</s:Envelope>"""

    try:
        response = requests.post(url, data=soap_envelope, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse XML Response
        # Start looking for the result inside the XML to avoid complex namespace handling if possible
        # Typically returns: Checksum, CodigoEstatus, EsCancelable, Estado, EstatusCancelacion...
        
        root = ET.fromstring(response.content)
        # Find the 'ConsultaResult' - namespaces can be tricky in ElementTree, stripping or wildcards help
        # Namespace map usually: {http://tempuri.org/}ConsultaResult or {http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio}Result
        
        # Simple string search fallback if namespaces break (robustness)
        content_str = response.text
        
        def extract_tag(tag):
            start = content_str.find(f"<{tag}>")
            end = content_str.find(f"</{tag}>")
            if start != -1 and end != -1:
                return content_str[start+len(tag)+2 : end]
            # Try with namespace prefix
            start = content_str.find(f":{tag}>") # likely a:Estado or similar
            if start != -1:
                # Find start of tag
                tag_start = content_str.rfind("<", 0, start)
                end = content_str.find(f"</", start) # Rough find
                if tag_start != -1 and end != -1:
                     # This is a bit dirty, let's try proper XML first
                     pass
            return "Unknown"

        # Proper XML parsing (ignoring namespaces for simplicity by just searching all elements)
        result_data = {}
        for elem in root.iter():
            if elem.tag.endswith("CodigoEstatus"):
                result_data["codigo_estatus"] = elem.text
            elif elem.tag.endswith("Estado"):
                result_data["estado"] = elem.text
            elif elem.tag.endswith("EsCancelable"):
                result_data["es_cancelable"] = elem.text
            elif elem.tag.endswith("EstatusCancelacion"):
                result_data["estatus_cancelacion"] = elem.text

        status = result_data.get("estado", "No Encontrado")
        
        return {
            "uuid": uuid,
            "status_sat": status,
            "codigo_estatus": result_data.get("codigo_estatus", "N/A"),
            "es_cancelable": result_data.get("es_cancelable", "N/A"),
            "estatus_cancelacion": result_data.get("estatus_cancelacion", "N/A"),
            "fecha_consulta": datetime.now().isoformat(),
            "validations": {
                "sat_connection": "OK",
                "is_active": "OK" if status == "Vigente" else "FAIL"
            },
            "raw_response": "Parsed from SOAP"
        }
        
    except Exception as e:
        return {
            "uuid": uuid,
            "error": str(e),
            "status_sat": "Error de Conexión",
            "validations": {"sat_connection": "FAIL"}
        }
