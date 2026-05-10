"""
PDF report generation for EVE using ReportLab.
Produces a professional A4 report from analysis results.
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'greengrey-logo.png',
)


def generate_pdf_report(
    results: Dict[str, Any],
    auth_user: Optional[Dict] = None,
    area_name: str = "Analysis Area",
    country: str = "",
    bbox: Optional[Dict] = None,
    coordinates: Optional[list] = None,
    summary_stats: Optional[Dict] = None,
) -> bytes:
    """
    Build a PDF report from analysis results and return the raw bytes.

    Args:
        results:        st.session_state.analysis_results dict
        auth_user:      st.session_state.get('auth_user') dict or None
        area_name:      user-facing name for the area
        country:        display country/region string
        bbox:           dict with min_lat/max_lat/min_lon/max_lon (optional)
        coordinates:    polygon vertex list (optional, for vertex count)
        summary_stats:  dict from the UI's Summary Statistics section
                        (sample_points_total, land_points, water_points,
                         country_counts, ecosystem_counts, average_eei,
                         ecosystem_eei, eei_enabled, predominant_country)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, PageBreak
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
    analysis_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    regional_factor = results.get('regional_adjustment_factor', results.get('regional_factor', 1.0))

    meta_rows = [
        ['Analysis Date', analysis_date, 'Country / Region', country or '—'],
        ['Water excluded', f'{water_ha:,.1f} ha' if water_ha else '—',
         'Regional Factor', f'{regional_factor:.2f}×'],
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

    # --------------------------------------------------- geographic coordinates
    if bbox:
        story.append(Paragraph('Geographic Coordinates', h2))
        min_lat = bbox.get('min_lat', 0)
        max_lat = bbox.get('max_lat', 0)
        min_lon = bbox.get('min_lon', 0)
        max_lon = bbox.get('max_lon', 0)
        c_lat = (min_lat + max_lat) / 2
        c_lon = (min_lon + max_lon) / 2
        geo_rows = [
            ['Centre', f'{c_lat:.5f}, {c_lon:.5f}',
             'Bounding box (N, S)', f'{max_lat:.5f}, {min_lat:.5f}'],
            ['Area (land)', f'{area_ha:,.1f} ha',
             'Bounding box (E, W)', f'{max_lon:.5f}, {min_lon:.5f}'],
        ]
        geo_table = Table(geo_rows, colWidths=[4 * cm, 6 * cm, 4 * cm, 4 * cm])
        geo_table.setStyle(TableStyle([
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
        story.append(geo_table)
        story.append(Spacer(1, 0.4 * cm))

    esvd = results.get('esvd_results', {})

    # --------------------------------------------------- sample-point summary
    if summary_stats and summary_stats.get('sample_points_total'):
        story.append(Paragraph('Sample Point Summary', h2))

        total_pts = summary_stats.get('sample_points_total', 0)
        land_pts = summary_stats.get('land_points', 0)
        water_pts = summary_stats.get('water_points', 0)
        avg_eei = summary_stats.get('average_eei')
        eei_enabled = summary_stats.get('eei_enabled', False)

        sample_meta = [
            ['Total Sample Points', str(total_pts),
             'Land Points', str(land_pts)],
            ['Water Points (excluded)', str(water_pts),
             'Average EEI',
             f'{avg_eei:.3f} ({avg_eei * 100:.1f}%)' if (eei_enabled and avg_eei is not None) else '—'],
        ]
        sm_table = Table(sample_meta, colWidths=[4 * cm, 6 * cm, 4 * cm, 4 * cm])
        sm_table.setStyle(TableStyle([
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
        story.append(sm_table)
        story.append(Spacer(1, 0.25 * cm))

        # Ecosystem composition from sample points
        eco_counts = summary_stats.get('ecosystem_counts', {})
        if eco_counts:
            eco_rows = [['Ecosystem Type (from samples)', 'Points', '%']]
            for eco, count in sorted(eco_counts.items(), key=lambda x: -x[1]):
                pct = (count / total_pts * 100) if total_pts else 0
                eco_rows.append([eco, str(count), f'{pct:.1f}%'])
            eco_table = Table(eco_rows, colWidths=[10 * cm, 4 * cm, 4 * cm])
            eco_table.setStyle(_standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT))
            story.append(eco_table)
            story.append(Spacer(1, 0.25 * cm))

        # Country distribution (water bodies excluded)
        country_counts = summary_stats.get('country_counts', {})
        if country_counts and land_pts > 0:
            country_rows = [['Country (land points only)', 'Points', '%']]
            for c, count in sorted(country_counts.items(), key=lambda x: -x[1]):
                pct = (count / land_pts * 100) if land_pts else 0
                country_rows.append([c, str(count), f'{pct:.1f}%'])
            country_table = Table(country_rows, colWidths=[10 * cm, 4 * cm, 4 * cm])
            country_table.setStyle(_standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT))
            story.append(country_table)
            story.append(Spacer(1, 0.25 * cm))

        # EEI by ecosystem type (if available)
        ecosystem_eei = summary_stats.get('ecosystem_eei', {})
        if eei_enabled and ecosystem_eei:
            eei_rows = [['Ecosystem Type', 'EEI', 'EEI %']]
            for eco_type, eei_v in sorted(ecosystem_eei.items()):
                if eei_v is None:
                    continue
                eei_rows.append([eco_type, f'{eei_v:.3f}', f'{eei_v * 100:.1f}%'])
            if len(eei_rows) > 1:
                eei_table = Table(eei_rows, colWidths=[10 * cm, 4 * cm, 4 * cm])
                eei_table.setStyle(_standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT))
                story.append(eei_table)
                story.append(Spacer(1, 0.25 * cm))

        story.append(Spacer(1, 0.15 * cm))

    # ------------------------------------------------------ service value table
    story.append(Paragraph('Ecosystem Service Values', h2))

    categories = ['provisioning', 'regulating', 'cultural', 'supporting']
    # Build a flat {cat: {'total': N, 'services': {...}}} dict that works for
    # both single-ecosystem (categories at top level of esvd) and
    # multi-ecosystem (categories nested under ecosystem_breakdown /
    # ecosystem_results). Mirrors app.py _render_service_columns wiring.
    categories_data = _resolve_categories_data(esvd, results, categories)
    has_cats = categories_data is not None and any(
        categories_data.get(c, {}).get('total', 0) for c in categories
    )

    if has_cats:
        svc_rows = [
            ['Service Category', 'Total (Int$/yr)', 'Per Hectare (Int$/ha/yr)', '% of Total'],
        ]
        grand_total = sum(categories_data.get(c, {}).get('total', 0) for c in categories)
        for cat in categories:
            cat_data = categories_data.get(cat, {})
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
    story.append(Spacer(1, 0.3 * cm))

    # ------------------------------------------------ service-by-service breakdown
    if has_cats:
        _SERVICE_LABELS = {
            'food': 'Food',
            'water': 'Water',
            'raw_materials': 'Raw Materials',
            'genetic_resources': 'Genetic Resources',
            'medicinal_resources': 'Medicinal Resources',
            'ornamental_resources': 'Ornamental Resources',
            'air_quality_regulation': 'Air Quality Regulation',
            'climate_regulation': 'Climate Regulation',
            'moderation_of_extreme_events': 'Moderation of Extreme Events',
            'regulation_of_water_flows': 'Water Flow Regulation',
            'waste_treatment': 'Waste Treatment',
            'erosion_prevention': 'Erosion Prevention',
            'maintenance_of_soil_fertility': 'Soil Fertility',
            'pollination': 'Pollination',
            'biological_control': 'Biological Control',
            'aesthetic_information': 'Aesthetic Information',
            'recreation_and_tourism': 'Recreation & Tourism',
            'culture_art_and_design': 'Culture, Art & Design',
            'spiritual_experience': 'Spiritual & Existence',
            'cognitive_development': 'Cognitive Development',
            'maintenance_of_life_cycles': 'Maintenance of Life Cycles',
            'maintenance_of_genetic_diversity': 'Maintenance of Genetic Diversity',
        }
        detail_rows = [['Category', 'Ecosystem Service', 'Annual Value (Int$/yr)', 'Per Ha (Int$/ha/yr)', '% of Total']]
        for cat in categories:
            services = categories_data.get(cat, {}).get('services', {})
            if not services:
                continue
            first_in_cat = True
            for svc_key, svc_val in sorted(services.items(), key=lambda x: -x[1]):
                if not isinstance(svc_val, (int, float)) or svc_val == 0:
                    continue
                svc_per_ha = svc_val / area_ha if area_ha else 0
                pct = (svc_val / grand_total * 100) if grand_total else 0
                detail_rows.append([
                    cat.title() if first_in_cat else '',
                    _SERVICE_LABELS.get(svc_key, svc_key.replace('_', ' ').title()),
                    f'Int$ {svc_val:,.0f}',
                    f'Int$ {svc_per_ha:,.0f}',
                    f'{pct:.1f}%',
                ])
                first_in_cat = False

        if len(detail_rows) > 1:
            story.append(PageBreak())
            story.append(Paragraph('Service-by-Service Breakdown', h2))
            detail_table = Table(detail_rows, colWidths=[2.5 * cm, 5 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm])
            ts2 = _standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT)
            ts2.add('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')
            ts2.add('TEXTCOLOR', (0, 1), (0, -1), EVE_DARK)
            detail_table.setStyle(ts2)
            story.append(detail_table)
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
        '<i>Analysis is rerun each time using the latest satellite and coefficient data. '
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
    story.append(Spacer(1, 0.2 * cm))
    try:
        if os.path.exists(_LOGO_PATH):
            logo = Image(_LOGO_PATH, width=1.5 * cm, height=1.48 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
    except Exception:
        pass
    attribution_text = (
        'Built by '
        '<link href="https://www.greenandgreyassociates.com" color="#2E7D32">'
        'Green &amp; Grey Associates</link>'
    )
    story.append(Paragraph(attribution_text, footer_style))
    story.append(Paragraph('© 2026 Green &amp; Grey Associates', footer_style))

    doc.build(story)
    return buf.getvalue()


def _resolve_categories_data(esvd: Dict[str, Any], results: Dict[str, Any], categories) -> Optional[Dict]:
    """Return a flat {cat: {'total', 'services'}} dict, aggregating from
    ecosystem_breakdown / ecosystem_results when categories are nested
    (multi-ecosystem analyses)."""
    if any(c in esvd for c in categories):
        return {c: esvd.get(c, {}) for c in categories}

    ecosystem_data = esvd.get('ecosystem_breakdown', esvd.get('ecosystem_results', {}))
    if ecosystem_data:
        aggregated = {c: {'total': 0, 'services': {}} for c in categories}
        for eco_result in ecosystem_data.values():
            if not isinstance(eco_result, dict):
                continue
            for category in categories:
                if category in eco_result and isinstance(eco_result[category], dict):
                    aggregated[category]['total'] += eco_result[category].get('total', 0)
                    for svc, val in (eco_result[category].get('services', {}) or {}).items():
                        if isinstance(val, (int, float)):
                            aggregated[category]['services'][svc] = (
                                aggregated[category]['services'].get(svc, 0) + val
                            )
        return aggregated
    return None


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
