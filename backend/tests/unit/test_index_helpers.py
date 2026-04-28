def test_is_source_inside_folder_avoids_prefix_false_positive():
    from app.api.index import _is_source_inside_folder

    assert _is_source_inside_folder("C:\\foo\\doc1.txt", "C:\\foo") is True
    assert _is_source_inside_folder("C:\\foobar\\doc1.txt", "C:\\foo") is False


def test_is_source_inside_folder_ignores_upload_sources():
    from app.api.index import _is_source_inside_folder

    assert _is_source_inside_folder("upload::readme.md", "C:\\foo") is False

