def add_citations_if_missing(answer_text: str, rag_hits: dict) -> str:
    """Agrega citaciones si faltan en la respuesta"""
    txt = answer_text or ""
    
    if "[Documento:" in txt:
        return txt
    
    metas = (rag_hits or {}).get("metadatas") or []
    metas = metas[0] if metas and isinstance(metas[0], list) else metas
    
    if not metas:
        return txt
    
    blocks = []
    for m in metas:
        title = m.get("doc_title", "")
        date = m.get("created_at", "")
        link = m.get("webViewLink", "")
        blocks.append(f"[Documento: {title}] ({date[:10] if date else ''}) – {link}")
    
    return f"{txt}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**Fuentes:**\n" + "\n".join(blocks)
