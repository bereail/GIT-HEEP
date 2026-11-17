"""Planilla de Excel (.xlsx) mínima, sin dependencias: varias hojas con
encabezado en negrita, fijo arriba y con filtro, y filas pintadas por color
si se pide. Alcanza para exportar tablas de texto; no hace fórmulas ni
formatos de número."""
import io
import re
import zipfile
from xml.sax.saxutils import escape

_NO_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Colores de fondo para las filas (los mismos tonos que la pantalla):
# nombre → (relleno ARGB, índice del estilo en styles.xml).
COLORES = {"verde": ("FFE8F6EE", 3), "rojo": ("FFFBECEB", 4), "naranja": ("FFFDF1E2", 5), "gris": ("FFF0F2F6", 6)}


def _estilos():
    rellenos = "".join(f'<fill><patternFill patternType="solid"><fgColor rgb="{argb}"/></patternFill></fill>'
                       for argb, _ in COLORES.values())
    pintados = "".join(f'<xf numFmtId="0" fontId="0" fillId="{3 + i}" borderId="0" xfId="0" applyFill="1" applyAlignment="1">'
                       '<alignment vertical="top" wrapText="1"/></xf>' for i in range(len(COLORES)))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            f'<fills count="{3 + len(COLORES)}"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
            f'<fill><patternFill patternType="solid"><fgColor rgb="FFEAF0FD"/></patternFill></fill>{rellenos}</fills>'
            '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            f'<cellXfs count="{3 + len(COLORES)}"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
            f'{pintados}</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


def _celda(ref, valor, estilo=0):
    texto = escape(_NO_XML.sub("", "" if valor is None else str(valor)))
    s = f' s="{estilo}"' if estilo else ""
    return f'<c r="{ref}" t="inlineStr"{s}><is><t xml:space="preserve">{texto}</t></is></c>'


def _columna(n):
    letras = ""
    while n:
        n, resto = divmod(n - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _ref_hoja(nombre):
    return "'" + nombre[:31].replace("'", "''") + "'"


def _hoja(encabezados, filas, anchos, colores=None):
    ultima = _columna(len(encabezados))
    cols = "".join(f'<col min="{i}" max="{i}" width="{a}" customWidth="1"/>' for i, a in enumerate(anchos, 1))
    renglones = ['<row r="1">' + "".join(_celda(f"{_columna(i)}1", v, 1) for i, v in enumerate(encabezados, 1)) + "</row>"]
    for r, fila in enumerate(filas, 2):
        color = colores[r - 2] if colores else None
        estilo = COLORES[color][1] if color in COLORES else 2
        renglones.append(f'<row r="{r}">' + "".join(_celda(f"{_columna(i)}{r}", v, estilo) for i, v in enumerate(fila, 1)) + "</row>")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            f'<cols>{cols}</cols><sheetData>{"".join(renglones)}</sheetData>'
            f'<autoFilter ref="A1:{ultima}{max(len(filas) + 1, 1)}"/></worksheet>')


def libro(hojas):
    """hojas: lista de (nombre, encabezados, filas, anchos[, colores]); `colores`
    trae, por fila, un nombre de COLORES o None. Devuelve los bytes del .xlsx."""
    n = len(hojas)
    tipos = "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, n + 1))
    partes = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + tipos + "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + "".join(f'<sheet name="{escape(h[0][:31])}" sheetId="{i}" r:id="rId{i}"/>' for i, h in enumerate(hojas, 1)) + "</sheets><definedNames>" + "".join(f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">{escape(_ref_hoja(h[0]))}!$A$1:${_columna(len(h[1]))}${len(h[2]) + 1}</definedName>' for i, h in enumerate(hojas)) + "</definedNames></workbook>",
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, n + 1)) + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
        "xl/styles.xml": _estilos(),
    }
    for i, hoja in enumerate(hojas, 1):
        partes[f"xl/worksheets/sheet{i}.xml"] = _hoja(*hoja[1:])
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in partes.items():
            z.writestr(nombre, contenido)
    return salida.getvalue()
