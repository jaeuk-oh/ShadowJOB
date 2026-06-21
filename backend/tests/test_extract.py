import io

from app.diagnosis.extract import (
    EmptyExtraction,
    FileTooLarge,
    UnsupportedFileType,
    extract_text,
)


def _make_docx(text: str) -> bytes:
    from docx import Document

    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_pdf(text: str) -> bytes:
    """오프셋이 맞는 최소 단일페이지 PDF(텍스트 추출 가능)."""
    objs = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    stream = b"BT /F1 24 Tf 72 700 Td (" + text.encode("latin-1") + b") Tj ET"
    objs.append(b"<</Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream")

    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf += str(i).encode() + b" 0 obj" + body + b"endobj\n"
    xref_pos = len(pdf)
    n = len(objs) + 1
    pdf += b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        pdf += ("%010d 00000 n \n" % off).encode()
    pdf += (
        b"trailer<</Size " + str(n).encode() + b"/Root 1 0 R>>\nstartxref\n"
        + str(xref_pos).encode() + b"\n%%EOF"
    )
    return pdf


def test_extract_txt():
    out = extract_text("resume.txt", "이력서 내용\n경력 3년".encode("utf-8"))
    assert "이력서 내용" in out
    assert "경력 3년" in out


def test_extract_md_cp949():
    out = extract_text("resume.md", "한글 인코딩 테스트".encode("cp949"))
    assert "한글 인코딩" in out


def test_extract_docx():
    data = _make_docx("PM 경력 요약\n전환율 30% 개선")
    out = extract_text("resume.docx", data)
    assert "PM 경력 요약" in out
    assert "전환율 30% 개선" in out


def test_extract_pdf():
    out = extract_text("resume.pdf", _make_pdf("FIELD resume test"))
    assert "FIELD" in out and "resume" in out


def test_doc_legacy_unsupported():
    try:
        extract_text("resume.doc", b"\xd0\xcf\x11\xe0")  # OLE 매직(구형 doc)
    except UnsupportedFileType as e:
        assert "docx" in str(e)
        return
    raise AssertionError(".doc인데 예외 없음")


def test_unknown_extension_unsupported():
    try:
        extract_text("resume.hwp", b"data")
    except UnsupportedFileType:
        return
    raise AssertionError("미지원 확장자인데 예외 없음")


def test_empty_text_raises():
    try:
        extract_text("resume.txt", b"   \n  ")
    except EmptyExtraction:
        return
    raise AssertionError("빈 추출인데 예외 없음")


def test_too_large_raises():
    big = b"x" * (10 * 1024 * 1024 + 1)
    try:
        extract_text("resume.txt", big)
    except FileTooLarge:
        return
    raise AssertionError("초과 크기인데 예외 없음")
