def enforce_citations_and_confidence(answer_text: str, hits, min_conf=0.70):
    """Garantiza citaciones y escala por confianza baja"""
    metas = (hits or {}).get('metadatas', [[]])[0]
    dists = (hits or {}).get('distances', [[]])[0]
    conf = 1.0 - min(dists) if dists else 0.0
    
    # Agregar citaciones si no existen
    if "[Documento:" not in answer_text and metas:
        footer = []
        for m in metas[:3]:
            footer.append(f"[Documento: {m.get('doc_title','(sin título)')}] (Fecha: {m.get('created_at','')[:10]}) - {m.get('webViewLink','')}")
        answer_text = answer_text.rstrip() + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**Fuentes Consultadas:**\n" + "\n".join(footer)
    
    # Escalamiento por confianza baja
    if conf < min_conf:
        answer_text = "[REQUIERE VALIDACIÓN HUMANA] Fuentes insuficientes o confianza baja.\n\n" + answer_text
    
    return answer_text
