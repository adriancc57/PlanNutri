import re
import json
import argparse
from pathlib import Path

import pdfplumber
import pandas as pd
#python3 -m http.server 8001


def clean_dinner(raw: str) -> str:
    """Limpia texto de la sección de Cena (extraído por recorte)."""
    if not raw:
        return ""

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # Basura típica por recorte/ocr/layout
    lines = [l for l in lines if l not in ("aneC", "aloC", "as", "ar")]

    # Intentar iniciar desde el primer platillo reconocible
    start = 0
    for i, l in enumerate(lines):
        if re.search(r"Ensalada|Sándwich|Sandwich|Jugo", l, re.IGNORECASE):
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


def pdf_to_excel(pdf_path: Path, out_xlsx: Path) -> pd.DataFrame:
    """
    Convierte el PDF a un Excel normalizado.
    Retorna el DataFrame normalizado (Día, Comida, Contenido).
    """
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[0]

        tables = page.extract_tables()
        if not tables:
            raise RuntimeError("No se pudo extraer ninguna tabla del PDF. Puede ser un PDF escaneado o con layout no-tabular.")

        # Tabla principal (Desayuno, Colación 1, Comida, Colación 2)
        main_table = tables[0]

        # Mapeo de columnas por día (según el layout observado)
        day_cols = {"Lunes": 1, "Martes": 2, "Miércoles": 4, "Jueves": 5, "Viernes": 6, "Sábado": 7}
        meals = [("Desayuno", 0), ("Colación 1", 1), ("Comida", 2), ("Colación 2", 3)]

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
            for meal_name, row_idx in meals:
                val = main_table[row_idx][col_idx] if row_idx < len(main_table) else ""
                rows.append(
                    {"Día": day, "Comida": meal_name, "Contenido": (val or "").strip()}
                )
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

    plan = {}
    for _, row in df.iterrows():
        dia = row["Día"]
        comida = row["Comida"]
        contenido = row["Contenido"]
        plan.setdefault(dia, {})[comida] = contenido

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
    out_json = "plan.json"
    #out_json = pdf_path.with_suffix(".json")

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