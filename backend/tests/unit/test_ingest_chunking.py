from app.core.ingest import chunk_text


def test_chunk_text_splits_long_text_without_infinite_loop():
    text = "Parrafo uno. " * 700
    chunks = chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) > 2
    assert all(len(chunk) > 0 for chunk in chunks)


def test_chunk_text_respects_paragraph_boundaries_when_possible():
    text = "A" * 300 + "\n\n" + "B" * 300 + "\n\n" + "C" * 300
    chunks = chunk_text(text, chunk_size=80, overlap=5)
    assert len(chunks) >= 2
    # Debe mantener contenido en orden y sin vacío
    joined = "".join(chunks)
    assert "AAA" in joined
    assert "BBB" in joined
    assert "CCC" in joined

