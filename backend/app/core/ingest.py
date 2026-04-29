"""Algoritmos de troceado de texto para indexacion semantica."""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """Divide texto en chunks intentando respetar separadores naturales.

    Los parametros `chunk_size` y `overlap` se expresan en palabras aproximadas.
    Internamente se convierten a caracteres con un factor fijo para mantener
    una implementacion ligera y suficientemente estable para documentos mixtos.
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

        split_point = text.rfind("\n\n", start, end)
        if split_point == -1 or split_point < start + (char_chunk // 2):
            split_point = text.rfind("\n", start, end)
        if split_point == -1 or split_point < start + (char_chunk // 2):
            split_point = text.rfind(" ", start, end)
        if split_point == -1 or split_point <= start:
            split_point = end

        chunk = text[start:split_point].strip()
        if chunk:
            chunks.append(chunk)

        advance = split_point - start
        actual_overlap = min(char_overlap, advance - 1)
        if actual_overlap < 0:
            actual_overlap = 0
        start = split_point - actual_overlap

    return chunks
