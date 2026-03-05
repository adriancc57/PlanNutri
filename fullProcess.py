import re
import json
import argparse
from pathlib import Path

import pdfplumber
import pandas as pd


# Orden canónico que queremos SIEMPRE en la salida
MEAL_ORDER = ["Desayuno", "Colación 1", "Comida", "Colación 2"]


def clean_dinner(raw: str) -> str:
    """Limpia texto de la sección de Cena (extraído por recorte)."""
    if not raw:
        return ""

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # Basura típica por recorte/layout
    lines = [l for l in lines if l not in ("aneC", "aloC", "as", "ar")]

    # Intentar iniciar desde el primer platillo reconocible
    start = 0
    for i, l in enumerate(lines):
        if re.search(r"Ensalada|Sándwich|Sandwich|Jugo|Smoothie|Avena|Omelette|Huevos", l, re.IGNORECASE):
            start = i
            break
    lines = lines[start:]

    txt = "\n".join(lines).strip()

    # Arreglos típicos de saltos raros en fracciones
    txt = txt.replace("¼ d\ntaza", "¼ de taza").replace("¼ d\nde\ntaza", "¼ de taza")
    txt = txt.replace("¼ dee", "¼ de").replace("¼ de de", "¼ de")
    return txt


def extract_cell_text(page: pdfplumber.page.Page, x0: float, top: float, x1: float, bottom: float) -> str:
    """Extrae texto de una región de la página (bbox)."""
    crop = page.crop((x0, top, x1, bottom))
    return crop.extract_text(x_tolerance=1, y_tolerance=2) or ""


def _row_has_content(row, col_indices) -> bool:
    """True si la fila tiene contenido en cualquiera de las columnas de días."""
    if not row:
        return False
    for ci in col_indices:
        if ci < len(row):
            v = row[ci]
            if v is not None and str(v).strip() != "":
                return True
    return False


def _pick_main_meal_rows(main_table, day_cols):
    """
    Selecciona las 4 filas de comidas (desayuno/col1/comida/col2)
    SIN depender de que exista el texto del encabezado en el PDF.
    Estrategia:
      - Identifica columnas de días por índices (del mapping day_cols)
      - Filtra filas que tengan contenido en esas columnas
      - Toma las primeras 4 filas con contenido (orden natural del PDF)
    """
    day_col_indices = list(day_cols.values())
    candidate_rows = [r for r in main_table if _row_has_content(r, day_col_indices)]

    if len(candidate_rows) < 4:
        # fallback: usa lo que haya, pero rellena con vacíos al final
        while len(candidate_rows) < 4:
            candidate_rows.append([])
    return candidate_rows[:4]


def pdf_to_excel(pdf_path: Path, out_xlsx: Path) -> pd.DataFrame:
    """
    Convierte el PDF a un Excel normalizado.
    Retorna el DataFrame normalizado (Día, Comida, Contenido).
    """
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[0]

        tables = page.extract_tables()
        if not tables:
            raise RuntimeError(
                "No se pudo extraer ninguna tabla del PDF. Puede ser un PDF escaneado o con layout no-tabular."
            )

        # Normalmente la primera tabla contiene Desayuno/Colaciones/Comida
        main_table = tables[0]

        # Mapeo de columnas por día (según el layout observado en tus planes)
        # OJO: si el template cambia mucho, estos índices podrían ajustarse.
        day_cols = {"Lunes": 1, "Martes": 2, "Miércoles": 4, "Jueves": 5, "Viernes": 6, "Sábado": 7}

        # NUEVO: elegimos 4 filas de comidas por estructura, no por encabezados
        meal_rows = _pick_main_meal_rows(main_table, day_cols)

        # CENA: extraída por recortes por columna (rangos aproximados)
        # Ojo: si cambia el formato del PDF, estos rangos podrían requerir ajuste.
        col_ranges = [(0, 156), (156, 292), (292, 429), (429, 551), (551, 682), (682, 820)]
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

        dinners = {}
        for day, (x0, x1) in zip(days, col_ranges):
            raw = extract_cell_text(page, x0=x0, x1=x1, top=465, bottom=610)
            dinners[day] = clean_dinner(raw)

        # Normalizar a filas Día / Comida / Contenido
        rows = []
        for day, col_idx in day_cols.items():
            # 4 comidas fijas por posición
            for meal_name, row in zip(MEAL_ORDER, meal_rows):
                val = ""
                if row and col_idx < len(row):
                    val = row[col_idx] or ""
                rows.append({"Día": day, "Comida": meal_name, "Contenido": str(val).strip()})

            # Cena
            rows.append({"Día": day, "Comida": "Cena", "Contenido": dinners.get(day, "")})

        df = pd.DataFrame(rows)

        # Exportar a Excel (normalizado + pivot)
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="plan")
            pivot = df.pivot(index="Día", columns="Comida", values="Contenido")
            pivot.to_excel(writer, sheet_name="pivot")

    return df


def excel_to_json(xlsx_path: Path, out_json: Path) -> dict:
    """Convierte el Excel normalizado (sheet 'plan') a JSON plan[dia][comida] = contenido."""
    df = pd.read_excel(xlsx_path, sheet_name="plan")

    for col in ("Día", "Comida", "Contenido"):
        if col not in df.columns:
            raise RuntimeError(f"El Excel no contiene la columna requerida: {col}")

    df["Día"] = df["Día"].astype(str).str.strip()
    df["Comida"] = df["Comida"].astype(str).str.strip()
    df["Contenido"] = df["Contenido"].fillna("").astype(str).str.strip()

    # Asegura que existan todas las comidas aunque vengan vacías
    plan = {}
    for _, row in df.iterrows():
        dia = row["Día"]
        comida = row["Comida"]
        contenido = row["Contenido"]
        plan.setdefault(dia, {})[comida] = contenido

    # Completar faltantes por si alguna no vino (para que UI no falle)
    for dia in plan.keys():
        for m in (MEAL_ORDER + ["Cena"]):
            plan[dia].setdefault(m, "")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    return plan


def main():
    parser = argparse.ArgumentParser(
        description="Convierte un plan de alimentación PDF a Excel normalizado y JSON (mismo nombre base)."
    )
    parser.add_argument("pdf", help="Ruta al PDF de entrada")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el PDF: {pdf_path}")

    out_xlsx = pdf_path.with_suffix(".xlsx")
    out_json = pdf_path.with_suffix(".json")

    print(f"PDF entrada:  {pdf_path}")
    print(f"Excel salida: {out_xlsx}")
    print(f"JSON salida:  {out_json}")

    # 1) PDF -> Excel
    df = pdf_to_excel(pdf_path, out_xlsx)
    print(f"Excel generado con {len(df)} filas (normalizado).")

    # 2) Excel -> JSON
    plan = excel_to_json(out_xlsx, out_json)
    print(f"JSON generado con {len(plan)} días.")

    print("✅ Listo.")


if __name__ == "__main__":
    main()
