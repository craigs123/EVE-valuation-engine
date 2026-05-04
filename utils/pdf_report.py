"""
PDF report generation for EVE using ReportLab.
Produces a professional A4 report from analysis results.
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional


def generate_pdf_report(
    results: Dict[str, Any],
    auth_user: Optional[Dict] = None,
    area_name: str = "Analysis Area",
    country: str = "",
) -> bytes:
    """
    Build a PDF report from analysis results and return the raw bytes.

    Args:
        results:   st.session_state.analysis_results dict
        auth_user: st.session_state.get('auth_user') dict or None
        area_name: user-facing name for the area
        country:   display country/region string
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    # --- colour palette ---
    EVE_GREEN = colors.HexColor('#2E7D32')
    EVE_GREEN_LIGHT = colors.HexColor('#E8F5E9')
    EVE_DARK = colors.HexColor('#1B5E20')
    GREY = colors.HexColor('#666666')
    LIGHT_GREY = colors.HexColor('#F5F5F5')

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"EVE Analysis Report — {area_name}",
        author="Ecosystem Valuation Engine",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('EVEh1', parent=styles['Heading1'],
                        textColor=EVE_DARK, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle('EVEh2', parent=styles['Heading2'],
                        textColor=EVE_GREEN, fontSize=13, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle('EVEbody', parent=styles['Normal'],
                          fontSize=9, leading=13, textColor=colors.black)
    caption = ParagraphStyle('EVEcaption', parent=styles['Normal'],
                              fontSize=8, leading=11, textColor=GREY)
    footer_style = ParagraphStyle('EVEfooter', parent=styles['Normal'],
                                  fontSize=7.5, leading=10, textColor=GREY,
                                  alignment=TA_CENTER)

    story = []

    # ------------------------------------------------------------------ header
    story.append(Paragraph("🌱 Ecosystem Valuation Engine", h1))
    story.append(Paragraph(f"<b>Natural Capital Analysis Report</b> — {area_name}", h2))
    story.append(HRFlowable(width="100%", thickness=1.5, color=EVE_GREEN, spaceAfter=6))

    # --- summary meta table ---
    area_ha = results.get('area_ha', results.get('area_hectares', 0))
    water_ha = results.get('water_area_hectares', 0)
    total_value = results.get('total_value', 0)
    per_ha = results.get('value_per_ha', total_value / area_ha if area_ha else 0)
    ecosystem_type = results.get('ecosystem_type', 'Unknown')
    analysis_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    regional_factor = results.get('regional_adjustment_factor', results.get('regional_factor', 1.0))

    meta_rows = [
        ['Analysis Date', analysis_date, 'Country / Region', country or '—'],
        ['Area (land)', f'{area_ha:,.1f} ha',
         'Water excluded', f'{water_ha:,.1f} ha' if water_ha else '—'],
        ['Ecosystem Type', ecosystem_type, 'Regional Factor', f'{regional_factor:.2f}×'],
        ['Total Annual Value', f'Int$ {total_value:,.0f}/yr',
         'Value per Hectare', f'Int$ {per_ha:,.0f}/ha/yr'],
    ]
    meta_table = Table(meta_rows, colWidths=[4 * cm, 6 * cm, 4 * cm, 4 * cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), EVE_GREEN_LIGHT),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), EVE_DARK),
        ('TEXTCOLOR', (2, 0), (2, -1), EVE_DARK),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.white),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [EVE_GREEN_LIGHT, colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # -------------------------------------------------------- ecosystem composition
    esvd = results.get('esvd_results', {})
    metadata = esvd.get('metadata', {})
    composition = metadata.get('ecosystem_composition', {})
    if composition:
        story.append(Paragraph('Ecosystem Composition', h2))
        comp_rows = [['Ecosystem Type', 'Coverage (%)']]
        for eco, prop in sorted(composition.items(), key=lambda x: -x[1]):
            comp_rows.append([eco, f'{prop * 100:.0f}%'])
        comp_table = Table(comp_rows, colWidths=[10 * cm, 8 * cm])
        comp_table.setStyle(_standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT))
        story.append(comp_table)
        story.append(Spacer(1, 0.3 * cm))

    # ------------------------------------------------------ service value table
    story.append(Paragraph('Ecosystem Service Values', h2))

    categories = ['provisioning', 'regulating', 'cultural', 'supporting']
    has_cats = any(c in esvd for c in categories)

    if has_cats:
        svc_rows = [
            ['Service Category', 'Total (Int$/yr)', 'Per Hectare (Int$/ha/yr)', '% of Total'],
        ]
        grand_total = sum(esvd.get(c, {}).get('total', 0) for c in categories)
        for cat in categories:
            cat_data = esvd.get(cat, {})
            cat_total = cat_data.get('total', 0)
            cat_per_ha = cat_total / area_ha if area_ha else 0
            pct = (cat_total / grand_total * 100) if grand_total else 0
            svc_rows.append([
                cat.title(),
                f'Int$ {cat_total:,.0f}',
                f'Int$ {cat_per_ha:,.0f}',
                f'{pct:.0f}%',
            ])
        svc_rows.append([
            'TOTAL',
            f'Int$ {total_value:,.0f}',
            f'Int$ {per_ha:,.0f}',
            '100%',
        ])
        svc_table = Table(svc_rows, colWidths=[5 * cm, 5 * cm, 5.5 * cm, 2.5 * cm])
        ts = _standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT)
        ts.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ts.add('BACKGROUND', (0, -1), (-1, -1), EVE_GREEN)
        ts.add('TEXTCOLOR', (0, -1), (-1, -1), colors.white)
        svc_table.setStyle(ts)
        story.append(svc_table)
    else:
        story.append(Paragraph(
            f'Total Annual Value: <b>Int$ {total_value:,.0f}/yr</b>  |  '
            f'Per Hectare: <b>Int$ {per_ha:,.0f}/ha/yr</b>', body))
    story.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------- embedded chart (if kaleido)
    chart_img = _try_chart_image(results)
    if chart_img:
        story.append(Paragraph('Service Value Breakdown', h2))
        img_obj = Image(io.BytesIO(chart_img), width=14 * cm, height=7 * cm)
        story.append(img_obj)
        story.append(Spacer(1, 0.3 * cm))

    # ------------------------------------------------------------ methodology note
    story.append(Paragraph('Methodology', h2))
    story.append(Paragraph(
        'Values are sourced from the <b>Ecosystem Services Valuation Database (ESVD/TEEB)</b>, '
        'drawing on 10,874+ peer-reviewed estimates from 1,100+ scientific studies. '
        'A regional GDP adjustment (income-elasticity method, World Bank 2024 GDP per capita data) '
        'is applied: <i>factor = 1 + (elasticity × (country_GDP / global_GDP − 1))</i>, '
        'bounded to 0.4–2.5×. Ecosystem Ecological Integrity (EEI) intactness multipliers '
        'are applied where available. Open-water areas are excluded from natural capital totals '
        '(NDWI masking). All values are in 2024 International dollars per hectare per year.',
        body,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        '<i>Analysis is run fresh each time using the latest satellite and coefficient data. '
        'Past reports may differ from current values if data sources have been updated.</i>',
        caption,
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY, spaceAfter=4))

    # -------------------------------------------------------------------- footer
    user_display = ''
    if auth_user:
        name = auth_user.get('display_name') or auth_user.get('email', '')
        email = auth_user.get('email', '')
        user_display = f'{name} ({email})' if name != email else email

    footer_text = (
        f'Generated by Ecosystem Valuation Engine (EVE) &nbsp;|&nbsp; '
        f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} &nbsp;|&nbsp; '
        f'{user_display}'
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    return buf.getvalue()


def _standard_table_style(header_colour, stripe_colour):
    from reportlab.platypus import TableStyle
    from reportlab.lib import colors
    ts = TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), header_colour),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, stripe_colour]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#C8E6C9')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    return ts


def _try_chart_image(results: Dict[str, Any]) -> Optional[bytes]:
    """Attempt to render a Plotly bar chart as PNG bytes using kaleido. Returns None on failure."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        esvd = results.get('esvd_results', {})
        categories = ['provisioning', 'regulating', 'cultural', 'supporting']
        labels = [c.title() for c in categories]
        values = [esvd.get(c, {}).get('total', 0) for c in categories]

        if not any(values):
            return None

        bar_colours = ['#2E7D32', '#4CAF50', '#81C784', '#C8E6C9']
        fig = go.Figure(go.Bar(
            x=labels,
            y=values,
            marker_color=bar_colours,
            text=[f'Int$ {v:,.0f}' for v in values],
            textposition='outside',
            textfont=dict(size=10),
        ))
        fig.update_layout(
            title=dict(text='Annual Value by Ecosystem Service Category (Int$/yr)',
                       font=dict(size=12, color='#1B5E20')),
            yaxis_title='Int$/year',
            xaxis_title='',
            plot_bgcolor='#F9FBF9',
            paper_bgcolor='white',
            height=320,
            width=600,
            margin=dict(t=60, b=40, l=60, r=20),
            showlegend=False,
        )
        return pio.to_image(fig, format='png', width=600, height=320, scale=1.5)
    except Exception:
        return None
