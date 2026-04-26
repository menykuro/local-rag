from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """
    Divide el texto respetando los párrafos y tablas.
    chunk_size y overlap son referenciales a palabras, por lo que multiplicamos por 5 para caracteres.
    """
    char_chunk = chunk_size * 5
    char_overlap = overlap * 5
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + char_chunk
        
        if end >= text_len:
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break
            
        # Buscar punto de corte ideal (doble salto, salto, o espacio)
        split_point = text.rfind('\n\n', start, end)
        if split_point == -1 or split_point < start + (char_chunk // 2):
            split_point = text.rfind('\n', start, end)
            
        if split_point == -1 or split_point < start + (char_chunk // 2):
            split_point = text.rfind(' ', start, end)
            
        # Si no hay donde cortar, corte duro
        if split_point == -1 or split_point <= start:
            split_point = end
            
        chunk = text[start:split_point].strip()
        if chunk:
            chunks.append(chunk)
            
        # Calcular el avance garantizando que nunca entremos en bucle infinito
        advance = split_point - start
        actual_overlap = min(char_overlap, advance - 1)
        if actual_overlap < 0:
            actual_overlap = 0
            
        start = split_point - actual_overlap
        
    return chunks
