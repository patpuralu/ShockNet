# ============================================================
#  ShockNet — core/stats.py v1.0
# ============================================================

import json, os, csv
from datetime import datetime
from collections import Counter

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "history.json")


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def compute_stats(history: list) -> dict:
    if not history:
        return {}
    total    = len(history)
    enviados = sum(1 for e in history if e.get("status") == "enviado")
    tasa_ok  = round(enviados / total * 100) if total else 0
    dias_es  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    por_dia  = Counter()
    for e in history:
        try:
            ts = datetime.strptime(e["ts"], "%Y-%m-%d %H:%M:%S")
            por_dia[dias_es[ts.weekday()]] += 1
        except Exception:
            pass
    return {
        "total":    total,
        "enviados": enviados,
        "tasa_ok":  tasa_ok,
        "por_dia":  dict(por_dia),
        "por_ip":   dict(Counter(e.get("ip","?") for e in history).most_common(5)),
        "por_tema": dict(Counter(e.get("theme","oscuro") for e in history)),
    }


def export_csv(history: list, path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Fecha","IP","Título","Tema","Estado","ID"])
        for e in history:
            w.writerow([e.get("ts",""), e.get("ip",""), e.get("title",""),
                        e.get("theme",""), e.get("status",""), e.get("notif_id","")])


def export_pdf(history: list, path: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)

    doc  = SimpleDocTemplate(path, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
    stys = getSampleStyleSheet()
    RED  = colors.HexColor("#e63946")
    DARK = colors.HexColor("#0e0e0e")
    GRAY = colors.HexColor("#555555")

    title_sty = ParagraphStyle("t", parent=stys["Title"],
                                textColor=RED, fontSize=22, spaceAfter=4)
    sub_sty   = ParagraphStyle("s", parent=stys["Normal"],
                                textColor=GRAY, fontSize=10, spaceAfter=2)
    head_sty  = ParagraphStyle("h", parent=stys["Heading2"],
                                textColor=DARK, fontSize=12, spaceBefore=14)

    stats = compute_stats(history)
    story = []
    story.append(Paragraph("⚡ ShockNet — Informe de actividad", title_sty))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}  ·  "
        f"{stats.get('total',0)} avisos registrados", sub_sty))
    story.append(HRFlowable(width="100%", color=RED, thickness=1, spaceAfter=12))

    # Resumen
    story.append(Paragraph("Resumen", head_sty))
    t = Table([
        ["Total de avisos",        str(stats.get("total",0))],
        ["Enviados correctamente", str(stats.get("enviados",0))],
        ["Tasa de éxito",          f"{stats.get('tasa_ok',0)}%"],
        ["Dispositivos distintos", str(len(stats.get("por_ip",{})))],
    ], colWidths=[9*cm, 5*cm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#f5f5f5")]),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),10),
        ("PADDING",(0,0),(-1,-1),7),
        ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#dddddd")),
        ("TEXTCOLOR",(1,0),(1,-1),RED),
    ]))
    story.append(t); story.append(Spacer(1,14))

    # Top dispositivos
    if stats.get("por_ip"):
        story.append(Paragraph("Top dispositivos", head_sty))
        ip_data = [["IP","Avisos"]] + [[k,str(v)] for k,v in stats["por_ip"].items()]
        t2 = Table(ip_data, colWidths=[9*cm,5*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DARK),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f5f5")]),
            ("FONTSIZE",(0,0),(-1,-1),10),
            ("PADDING",(0,0),(-1,-1),7),
            ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#dddddd")),
        ]))
        story.append(t2); story.append(Spacer(1,14))

    # Historial
    story.append(Paragraph("Historial completo", head_sty))
    rows = [["Fecha","IP","Título","Tema","Estado"]]
    for e in history[:200]:
        rows.append([e.get("ts","")[:16], e.get("ip",""),
                     e.get("title","")[:40], e.get("theme",""), e.get("status","")])
    t3 = Table(rows, colWidths=[3.5*cm,3*cm,6*cm,2.5*cm,2*cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DARK),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f9f9f9")]),
        ("PADDING",(0,0),(-1,-1),5),
        ("GRID",(0,0),(-1,-1),.3,colors.HexColor("#e0e0e0")),
        ("TEXTCOLOR",(4,1),(4,-1),colors.HexColor("#2ecc71")),
    ]))
    story.append(t3)
    doc.build(story)
