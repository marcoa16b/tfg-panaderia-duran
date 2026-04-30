import pytest

from dev.services.export_service import ExportService


class TestExportServicePDF:
    def test_generate_pdf_con_datos(self):
        pdf_bytes = ExportService.generate_pdf(
            titulo="Reporte de prueba",
            subtitulo="Subtítulo",
            headers=["Col1", "Col2", "Col3"],
            rows=[["a", "b", "c"], ["d", "e", "f"]],
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_sin_datos(self):
        pdf_bytes = ExportService.generate_pdf(
            titulo="Reporte vacío",
            subtitulo="Sin datos",
            headers=["Col1"],
            rows=[],
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


class TestExportServiceExcel:
    def test_generate_excel_con_datos(self):
        xlsx_bytes = ExportService.generate_excel(
            titulo="Reporte",
            headers=["Nombre", "Cantidad"],
            rows=[["Harina", "50"], ["Azúcar", "30"]],
        )
        assert isinstance(xlsx_bytes, bytes)
        assert len(xlsx_bytes) > 0
        assert xlsx_bytes[:4] == b"PK\x03\x04"

    def test_generate_excel_sin_datos(self):
        xlsx_bytes = ExportService.generate_excel(
            titulo="Vacío",
            headers=["Col1"],
            rows=[],
        )
        assert isinstance(xlsx_bytes, bytes)
        assert len(xlsx_bytes) > 0
