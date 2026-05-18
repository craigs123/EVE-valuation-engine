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
    'static', 'greengrey-logo-no-circle.png',
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
    # keepWithNext=1: a heading is never left as the last flowable on a page —
    # ReportLab pushes it to the next page with the content that follows, so
    # headers and subheaders are never orphaned.
    h1 = ParagraphStyle('EVEh1', parent=styles['Heading1'],
                        textColor=EVE_DARK, fontSize=18, spaceAfter=4,
                        keepWithNext=1)
    h2 = ParagraphStyle('EVEh2', parent=styles['Heading2'],
                        textColor=EVE_GREEN, fontSize=13, spaceBefore=10,
                        spaceAfter=4, keepWithNext=1)
    body = ParagraphStyle('EVEbody', parent=styles['Normal'],
                          fontSize=9, leading=13, textColor=colors.black)
    caption = ParagraphStyle('EVEcaption', parent=styles['Normal'],
                              fontSize=8, leading=11, textColor=GREY)
    # Bold inline sub-heading (e.g. "Assumptions"); keepWithNext so it never
    # orphans at the foot of a page.
    subhead = ParagraphStyle('EVEsubhead', parent=styles['Normal'],
                             fontSize=9, leading=13, textColor=colors.black,
                             spaceBefore=4, keepWithNext=1)
    footer_style = ParagraphStyle('EVEfooter', parent=styles['Normal'],
                                  fontSize=7.5, leading=10, textColor=GREY,
                                  alignment=TA_CENTER)

    story = []

    # ===================================================================
    # Investment-grade front matter — rendered only for project runs (an
    # EROI metrics dict is present). Non-project reports are unchanged.
    # ===================================================================
    eroi = (summary_stats or {}).get('eroi')
    if eroi:
        baseline_val = results.get('total_value') or 0
        target_val = results.get('total_value_target') or 0
        _irr_s = (f'{eroi["irr"] * 100:.1f}%'
                  if eroi.get('irr') is not None else '—')
        _pb = eroi.get('payback_years')
        _pb_s = (f'{_pb:.1f} yr' if _pb is not None
                 else f'> {eroi["horizon_years"]} yr')

        def _fmt_date(d):
            try:
                return d.strftime('%d %b %Y')
            except Exception:
                return '—'

        # ---- Page 1: cover ---------------------------------------------
        cover_title = ParagraphStyle('cover_title', parent=h1, fontSize=26,
                                     alignment=TA_CENTER, spaceAfter=6, leading=30)
        cover_sub = ParagraphStyle('cover_sub', parent=h2, fontSize=15,
                                   alignment=TA_CENTER, textColor=EVE_DARK,
                                   spaceBefore=2, spaceAfter=2)
        cover_meta = ParagraphStyle('cover_meta', parent=caption,
                                    alignment=TA_CENTER, fontSize=10, leading=14)
        story.append(Spacer(1, 3.5 * cm))
        try:
            if os.path.exists(_LOGO_PATH):
                _cover_logo = Image(_LOGO_PATH, width=3.2 * cm, height=3.16 * cm)
                _cover_logo.hAlign = 'CENTER'
                story.append(_cover_logo)
                story.append(Spacer(1, 0.8 * cm))
        except Exception:
            pass
        story.append(Paragraph('Natural Capital', cover_title))
        story.append(Paragraph('Investment Report', cover_title))
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="55%", thickness=1.5, color=EVE_GREEN,
                                spaceAfter=12, hAlign='CENTER'))
        story.append(Paragraph(area_name, cover_sub))
        if country:
            story.append(Paragraph(country, cover_meta))
        story.append(Spacer(1, 1.5 * cm))
        story.append(Paragraph(
            f'Prepared {datetime.utcnow().strftime("%d %B %Y")}', cover_meta))
        if auth_user:
            _nm = auth_user.get('display_name') or auth_user.get('email', '')
            if _nm:
                story.append(Paragraph(f'Prepared by {_nm}', cover_meta))
        story.append(PageBreak())

        # ---- Page 2: executive summary ---------------------------------
        story.append(Paragraph('Executive Summary', h1))
        story.append(HRFlowable(width="100%", thickness=1.5, color=EVE_GREEN,
                                spaceAfter=10))
        kpi_values = [f'{eroi["bcr"]:.2f}×', f'Int$ {eroi["npv"]:,.0f}',
                      _irr_s, _pb_s, f'{eroi["annual_yield"] * 100:.1f}%/yr']
        kpi_labels = ['Benefit–Cost Ratio', 'Net Present Value',
                      'Internal Rate of Return', 'Payback Period', 'Annual Yield']
        kpi_table = Table([kpi_values, kpi_labels], colWidths=[3.4 * cm] * 5)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), EVE_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, 1), EVE_GREEN_LIGHT),
            ('TEXTCOLOR', (0, 1), (-1, 1), EVE_DARK),
            ('FONTSIZE', (0, 1), (-1, 1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1.5, colors.white),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.4 * cm))

        _maint_clause = (
            f' Ongoing maintenance of Int$ {eroi["maintenance_cost"]:,.0f}/yr is '
            f'counted after the project ends.'
            if eroi['maintenance_cost'] > 0 else '')
        _irr_clause = (f' an internal rate of return of <b>{eroi["irr"] * 100:.1f}%</b>,'
                       if eroi.get('irr') is not None else '')
        _pb_clause = (f' and recovers the capital cost in about <b>{_pb:.1f} years</b>'
                      if _pb is not None else '')
        narrative = (
            f'This project at <b>{area_name}</b> calls for a capital investment of '
            f'<b>Int$ {eroi["cost"]:,.0f}</b> to raise the area’s annual '
            f'ecosystem-service value from <b>Int$ {baseline_val:,.0f}/yr</b> to '
            f'<b>Int$ {target_val:,.0f}/yr</b> — a permanent uplift of '
            f'<b>Int$ {eroi["uplift"]:,.0f}/yr</b>.{_maint_clause} Appraised over '
            f'{eroi["horizon_years"]} years at a {eroi["discount_rate"] * 100:.1f}% '
            f'discount rate, the investment returns a benefit–cost ratio of '
            f'<b>{eroi["bcr"]:.2f}×</b>, a net present value of '
            f'<b>Int$ {eroi["npv"]:,.0f}</b>,{_irr_clause}{_pb_clause}.'
        )
        story.append(Paragraph(narrative, body))
        story.append(Spacer(1, 0.35 * cm))
        _bt_chart = _baseline_target_chart(results)
        if _bt_chart:
            _bt_img = Image(io.BytesIO(_bt_chart), width=14 * cm, height=7 * cm)
            _bt_img.hAlign = 'CENTER'
            story.append(_bt_img)
        story.append(PageBreak())

        # ---- Page 3: project inputs + EROI detail ----------------------
        story.append(Paragraph('Project Inputs & Parameters', h2))
        _sel_ha = results.get('selected_area_ha', results.get('area_ha', 0)) or 0
        _b_pct = results.get('baseline_area_pct', 100)
        _t_pct = results.get('target_area_pct', 100)
        _b_ha = results.get('area_ha', 0) or 0
        _t_ha = results.get('area_ha_target', _b_ha) or 0
        _eei = (summary_stats or {}).get('average_eei')
        _eei_txt = f'{_eei:.3f}' if _eei is not None else '—'
        inputs_rows = [
            ['Baseline date', _fmt_date((summary_stats or {}).get('baseline_date')),
             'Target date', _fmt_date((summary_stats or {}).get('target_date'))],
            ['Ramp / project duration',
             (f'{eroi["duration_years"]:.1f} yr' if eroi.get('duration_years')
              else 'immediate'),
             'Appraisal horizon', f'{eroi["horizon_years"]} yr'],
            ['Selected area', f'{_sel_ha:,.1f} ha',
             'Discount rate', f'{eroi["discount_rate"] * 100:.1f}%'],
            ['Baseline project area', f'{_b_pct}%  ({_b_ha:,.1f} ha)',
             'Target project area', f'{_t_pct}%  ({_t_ha:,.1f} ha)'],
            ['Baseline annual value', f'Int$ {baseline_val:,.0f}/yr',
             'Target annual value', f'Int$ {target_val:,.0f}/yr'],
            ['Annual uplift (gross)', f'Int$ {eroi["uplift_gross"]:,.0f}/yr',
             'Capital cost (total)', f'Int$ {eroi["cost"]:,.0f}'],
            ['Annual maintenance (ongoing)',
             f'Int$ {eroi["maintenance_cost"]:,.0f}/yr',
             'Baseline EEI', _eei_txt],
        ]
        inputs_table = Table(inputs_rows,
                             colWidths=[4.5 * cm, 4 * cm, 4.5 * cm, 4 * cm])
        inputs_table.setStyle(TableStyle([
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
        story.append(inputs_table)
        story.append(Spacer(1, 0.35 * cm))

        story.append(Paragraph('Investment Returns (EROI)', h2))
        eroi_rows = [
            ['Annual uplift (gross)', f'Int$ {eroi["uplift_gross"]:,.0f}/yr',
             'Capital cost', f'Int$ {eroi["cost"]:,.0f}'],
            ['Reversal buffer applied',
             f'{eroi["reversal_buffer_pct"] * 100:.0f}%',
             'Buffer-adjusted annual uplift',
             f'Int$ {eroi["uplift"]:,.0f}/yr'],
            ['Annual maintenance', f'Int$ {eroi["maintenance_cost"]:,.0f}/yr',
             'PV of maintenance', f'Int$ {eroi["pv_maintenance"]:,.0f}'],
            ['Benefit–cost ratio', f'{eroi["bcr"]:.2f}×',
             'Net present value', f'Int$ {eroi["npv"]:,.0f}'],
            ['Internal rate of return', _irr_s,
             'Payback period', _pb_s],
            ['Annual yield (net)', f'{eroi["annual_yield"] * 100:.1f}% / yr',
             f'{eroi["horizon_years"]}-yr value (PV)',
             f'Int$ {eroi["pv_benefits"]:,.0f}'],
        ]
        eroi_table = Table(eroi_rows,
                           colWidths=[4.5 * cm, 4 * cm, 4.5 * cm, 4 * cm])
        eroi_table.setStyle(TableStyle([
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
        story.append(eroi_table)
        story.append(Spacer(1, 0.25 * cm))

        # ---- Counterfactual --------------------------------------------
        # TODO: the closing note is framed for mangroves; EVE should supply the
        # ecosystem type (and a degradation rate) so a non-static, declining
        # counterfactual can be modelled where the ecosystem warrants it.
        story.append(Paragraph('Counterfactual', h2))
        _cf_rows = [
            ['Counterfactual annual value (no intervention)',
             f'Int$ {baseline_val:,.0f}/yr'],
            ['With-project annual value at target',
             f'Int$ {target_val:,.0f}/yr'],
            ['Incremental annual uplift (pre-buffer)',
             f'Int$ {eroi["uplift_gross"]:,.0f}/yr'],
            [f'PV of counterfactual ({eroi["horizon_years"]}-yr appraisal)',
             f'Int$ {eroi["pv_counterfactual"]:,.0f}'],
            [f'PV of with-project benefits ({eroi["horizon_years"]}-yr appraisal)',
             f'Int$ {eroi["pv_with_project"]:,.0f}'],
            ['Net incremental PV',
             f'Int$ {eroi["pv_benefits"]:,.0f}'],
        ]
        _cf_table = Table(_cf_rows, colWidths=[11.5 * cm, 5.5 * cm])
        _cf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), EVE_GREEN_LIGHT),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), EVE_DARK),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.white),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [EVE_GREEN_LIGHT, colors.white]),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(_cf_table)
        story.append(Spacer(1, 0.15 * cm))
        _cf_eei_clause = f' (EEI = {_eei:.3f})' if _eei is not None else ''
        story.append(Paragraph(
            f'The counterfactual assumes no restoration intervention. The '
            f'intervention area retains its current ecological condition'
            f'{_cf_eei_clause} throughout the {eroi["horizon_years"]}-year '
            f'appraisal period. All benefit calculations represent incremental '
            f'value above this no-intervention baseline. This is a conservative '
            f'assumption: unprotected mangroves in this region face ongoing '
            f'anthropogenic pressure and the true counterfactual trajectory may '
            f'be declining rather than static.',
            caption))
        story.append(Spacer(1, 0.3 * cm))

        _ramp = eroi.get('duration_years')
        _ramp_txt = (f'a {_ramp:.1f}-year linear ramp' if _ramp
                     else 'an immediate uplift')
        story.append(Paragraph('<b>Assumptions</b>', subhead))
        story.append(Paragraph(
            f'Ecosystem-service values are annual flows, not one-off stocks. The '
            f'uplift (target minus baseline annual value) is treated as perpetual '
            f'once the target state is reached, via {_ramp_txt} during which the '
            f'uplift grows linearly from zero. The capital cost is spread evenly '
            f'across the project duration; maintenance is an ongoing annual cost '
            f'beginning after the project ends. Benefits, capital and maintenance '
            f'are appraised over a fixed {eroi["horizon_years"]}-year window '
            f'discounted at {eroi["discount_rate"] * 100:.1f}%; NPV and the '
            f'benefit&ndash;cost ratio are net of the present value of capital and '
            f'maintenance. Annual yield = net annual benefit (uplift after '
            f'maintenance) / capital cost; payback is the undiscounted time for '
            f'cumulative net cash flow to reach break-even; IRR is the discount '
            f'rate at which NPV is zero. '
            f'A {eroi["reversal_buffer_pct"] * 100:.0f}% reversal buffer is '
            f'applied to annual ecosystem service benefits, consistent with '
            f'permanence risk provisions in voluntary carbon market standards '
            f'(Verra VCS VM0033). Pre-buffer figures are shown in the '
            f'sensitivity analysis.',
            caption))
        story.append(Spacer(1, 0.3 * cm))
        _cum_chart = _cumulative_value_chart(eroi)
        if _cum_chart:
            _cum_img = Image(io.BytesIO(_cum_chart), width=14 * cm, height=7 * cm)
            _cum_img.hAlign = 'CENTER'
            story.append(_cum_img)
            story.append(Spacer(1, 0.1 * cm))
            story.append(Paragraph(
                'The cumulative net cash flow is the running, undiscounted total '
                'of the project’s annual net position — the buffered '
                'ecosystem-service uplift, less maintenance and the spread capital '
                'cost. It starts negative while capital is being outlaid; the year '
                'the curve crosses the zero break-even line is the payback period, '
                'after which the project is in cumulative surplus. Because this '
                'view is undiscounted, its end value exceeds the (discounted) net '
                'present value reported above.',
                caption))
        story.append(PageBreak())

        # ---- Sensitivity analysis --------------------------------------
        from utils.analysis_helpers import compute_eroi as _ch_eroi_s
        _base_kwargs = dict(
            baseline_value=baseline_val,
            target_value=target_val,
            cost=eroi['cost'],
            duration_years=eroi['duration_years'],
            discount_rate=eroi['discount_rate'],
            maintenance_cost=eroi['maintenance_cost'],
            reversal_buffer_pct=eroi['reversal_buffer_pct'],
            horizon=eroi['horizon_years'],
        )
        _ug = eroi['uplift_gross']
        _base_ramp = eroi.get('duration_years') or 0.0

        def _sens_variant(**override):
            _r = _ch_eroi_s(**{**_base_kwargs, **override})
            return (_r['bcr'], _r['npv']) if _r else (0.0, 0.0)

        # (label, pessimistic 'low' override, optimistic 'high' override)
        _sens_specs = [
            ('Capital cost  (+25% / -15%)',
             {'cost': eroi['cost'] * 1.25}, {'cost': eroi['cost'] * 0.85}),
            ('Annual maintenance  (+50% / -25%)',
             {'maintenance_cost': eroi['maintenance_cost'] * 1.50},
             {'maintenance_cost': eroi['maintenance_cost'] * 0.75}),
            ('Ecosystem service uplift  (-20% / +20%)',
             {'target_value': baseline_val + _ug * 0.80},
             {'target_value': baseline_val + _ug * 1.20}),
            ('Ramp duration  (+2 / -1 yr)',
             {'duration_years': _base_ramp + 2},
             {'duration_years': max(0.0, _base_ramp - 1)}),
            ('Discount rate  (7.0% / 2.0%)',
             {'discount_rate': 0.07}, {'discount_rate': 0.02}),
            ('Reversal buffer  (30% / 10%)',
             {'reversal_buffer_pct': 0.30}, {'reversal_buffer_pct': 0.10}),
        ]
        _central_bcr, _central_npv = eroi['bcr'], eroi['npv']
        _sens_rows = []
        for _lbl, _lo, _hi in _sens_specs:
            _lb, _ln = _sens_variant(**_lo)
            _hb, _hn = _sens_variant(**_hi)
            _sens_rows.append((_lbl, _lb, _ln, _hb, _hn))

        story.append(Paragraph('Sensitivity Analysis', h2))
        _sens_tbl = [['Parameter', 'Low BCR', 'Low NPV', 'Central BCR',
                      'Central NPV', 'High BCR', 'High NPV']]
        for _lbl, _lb, _ln, _hb, _hn in _sens_rows:
            _sens_tbl.append([
                _lbl,
                f'{_lb:.2f}×', f'{_ln:,.0f}',
                f'{_central_bcr:.2f}×', f'{_central_npv:,.0f}',
                f'{_hb:.2f}×', f'{_hn:,.0f}',
            ])
        _sens_table = Table(_sens_tbl, colWidths=[4.2 * cm, 1.8 * cm, 2.4 * cm,
                                                  1.85 * cm, 2.4 * cm, 1.8 * cm,
                                                  2.4 * cm])
        _sens_table.setStyle(_standard_table_style(EVE_GREEN, EVE_GREEN_LIGHT))
        story.append(_sens_table)
        story.append(Paragraph('All NPV figures in Int$. The Central column '
                               'repeats the base-case result for reference.',
                               caption))
        story.append(Spacer(1, 0.3 * cm))

        _torn = _tornado_chart(_sens_rows, _central_npv)
        if _torn:
            _torn_img = Image(io.BytesIO(_torn), width=15 * cm, height=9.5 * cm)
            _torn_img.hAlign = 'CENTER'
            story.append(_torn_img)
            story.append(Spacer(1, 0.25 * cm))

        # Interpretation — top driver, worst-case BCR floor, central IRR.
        _top = max(_sens_rows, key=lambda r: abs(r[4] - r[2]))
        _top_name = _top[0].split('  (')[0]
        _floor_bcr = min([_central_bcr] + [r[1] for r in _sens_rows]
                         + [r[3] for r in _sens_rows])
        _irr_disp = (f'{eroi["irr"]:.1%}' if eroi.get('irr') is not None
                     else 'not defined')
        # TODO: the Monte Carlo threshold is a policy parameter — EVE could
        # supply a deal-size cut-off above which stochastic analysis is required.
        story.append(Paragraph(
            f'The sensitivity analysis shows that the investment case is most '
            f'sensitive to <b>{_top_name}</b>. Even under the most pessimistic '
            f'single-parameter assumption tested, the benefit&ndash;cost ratio '
            f'remains <b>{_floor_bcr:.2f}×</b>. The central-case IRR of '
            f'<b>{_irr_disp}</b> should be treated as indicative; a full '
            f'stochastic Monte Carlo analysis is recommended before committing '
            f'capital at this scale.',
            body))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            'Sensitivity rows vary one parameter at a time (ceteris paribus). '
            'Interactions between parameters are not modelled. Pre-buffer uplift '
            'is used as the gross uplift baseline for the ecosystem service '
            'uplift sensitivity row.',
            caption))

        story.append(PageBreak())

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

        # Demo-data caveat: if the EEI service fell back to fabricated data
        # for any point, those points were excluded — say so explicitly so
        # the report never implies the EEI figures are fully measured.
        eei_status = summary_stats.get('eei_status') or {}
        if eei_enabled and eei_status.get('any_demo'):
            demo_ecos = summary_stats.get('eei_demo_ecosystems') or {}
            _note = (
                f'Note: the EEI service returned demo (fabricated) data for '
                f'{eei_status.get("demo", 0)} of {eei_status.get("total", 0)} '
                f'sample points (Earth Engine unavailable). Those points were '
                f'excluded; the EEI figures above and below reflect real '
                f'Earth Engine data only.'
            )
            if demo_ecos:
                _pct = list(demo_ecos.values())[0]
                _names = ', '.join(sorted(demo_ecos))
                _note += (
                    f' No real EEI data was available for: {_names} — these '
                    f'ecosystems default to {_pct:.0f}% intactness rather than '
                    f'the optimistic 100%.'
                )
            story.append(Paragraph(_note, caption))
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

    # Investment Returns (EROI) for project runs is rendered in the
    # investment-grade front matter above, not here.

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

    # ------------------------------------------------ embedded charts (if kaleido)
    # Pie chart of service-category share — included in every report.
    pie_img = _service_pie_chart(results)
    if pie_img:
        story.append(Paragraph('Service Category Share', h2))
        _pie_obj = Image(io.BytesIO(pie_img), width=11 * cm, height=7.3 * cm)
        _pie_obj.hAlign = 'CENTER'
        story.append(_pie_obj)
        story.append(Spacer(1, 0.3 * cm))

    # Service-category value bar chart — Investment Report (project runs) only.
    if eroi:
        chart_img = _try_chart_image(results)
        if chart_img:
            story.append(Paragraph('Service Value Breakdown', h2))
            img_obj = Image(io.BytesIO(chart_img), width=14 * cm, height=7 * cm)
            img_obj.hAlign = 'CENTER'
            story.append(img_obj)
            story.append(Spacer(1, 0.3 * cm))

    # ------------------------------------------------------------ methodology note
    story.append(Paragraph('Methodology', h2))
    story.append(Paragraph(
        'Values are sourced from the <b>Ecosystem Services Valuation Database (ESVD/TEEB)</b>, '
        'drawing on 10,874+ peer-reviewed estimates from 1,100+ scientific studies. '
        'A regional GDP adjustment (income-elasticity method, World Bank 2024 GDP per capita data) '
        'is applied: <i>factor = 1 + (elasticity × (country_GDP / global_GDP − 1))</i>, '
        'bounded to 0.4–2.5×. Ecosystem Ecological Integrity (EEI) intactness multipliers — '
        'sourced from live Google Earth Engine data via the EEI Explorer API — are applied '
        'where available; demo (fabricated) fallback data is never used, and an ecosystem '
        'with no real EEI data defaults to a conservative 50% intactness rather than 100%. '
        'Open-water areas are excluded from natural capital totals '
        '(NDWI masking). All values are in 2024 International dollars per hectare per year.',
        body,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        '<i>Past valuations may differ from current values if data sources '
        'have been updated.</i>',
        caption,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Brander, L.M. de Groot, R, Guisado Goñi, V., van 't Hoff, V., Schägner, P., "
        "Solomonides, S., McVittie, A., Eppink, F., Sposato, M., Do, L., Ghermandi, A., "
        "and Sinclair, M. (2025). <i>Ecosystem Services Valuation Database (ESVD)</i>. "
        "Foundation for Sustainable Development and Brander Environmental Economics.",
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
            logo = Image(_LOGO_PATH, width=2.25 * cm, height=2.22 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
    except Exception:
        pass
    def _draw_page_footer(canvas, page_doc):
        """Footer drawn on every page: attribution (linked) left-justified,
        copyright right-justified, within the bottom margin."""
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        _y = 1.4 * cm
        # Attribution — green, hyperlinked to the Green & Grey Associates site.
        _built = 'Built by Green & Grey Associates'
        canvas.setFillColor(EVE_GREEN)
        canvas.drawString(page_doc.leftMargin, _y, _built)
        _built_w = canvas.stringWidth(_built, 'Helvetica', 7.5)
        canvas.linkURL(
            'https://www.greenandgreyassociates.com',
            (page_doc.leftMargin, _y - 1.5,
             page_doc.leftMargin + _built_w, _y + 7.5),
            relative=0,
        )
        # Copyright — grey, right-justified.
        canvas.setFillColor(GREY)
        canvas.drawRightString(
            page_doc.leftMargin + page_doc.width, _y,
            '© 2026 Green & Grey Associates',
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_page_footer, onLaterPages=_draw_page_footer)
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


def _baseline_target_chart(results: Dict[str, Any]) -> Optional[bytes]:
    """Bar chart: baseline vs target annual ecosystem-service value, with the
    uplift in the title. PNG bytes, or None if unavailable / kaleido missing."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        baseline = results.get('total_value') or 0
        target = results.get('total_value_target')
        if target is None:
            return None
        uplift = target - baseline
        fig = go.Figure(go.Bar(
            x=['Baseline', 'Target'],
            y=[baseline, target],
            marker_color=['#81C784', '#2E7D32'],
            text=[f'Int$ {baseline:,.0f}', f'Int$ {target:,.0f}'],
            textposition='outside',
            textfont=dict(size=11),
        ))
        fig.update_layout(
            title=dict(text=f'Annual Ecosystem-Service Value — Baseline vs Target '
                            f'(uplift Int$ {uplift:,.0f}/yr)',
                       font=dict(size=12, color='#1B5E20')),
            yaxis_title='Int$/year',
            plot_bgcolor='#F9FBF9',
            paper_bgcolor='white',
            height=320,
            width=600,
            margin=dict(t=60, b=40, l=75, r=20),
            showlegend=False,
        )
        return pio.to_image(fig, format='png', width=600, height=320, scale=1.5)
    except Exception:
        return None


def _cumulative_value_chart(eroi: Dict[str, Any]) -> Optional[bytes]:
    """Line/area chart: cumulative net cash flow (benefit uplift, less
    maintenance, less the spread capital cost) over the appraisal horizon.
    The point where it crosses the zero break-even line is the payback
    period. PNG bytes, or None if unavailable / kaleido missing."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        yearly_net = eroi.get('yearly_net')
        if not yearly_net:
            return None
        years = list(range(1, len(yearly_net) + 1))
        cum = []
        run = 0.0
        for v in yearly_net:
            run += v
            cum.append(run)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=cum, mode='lines',
            line=dict(color='#2E7D32', width=2.5),
            fill='tozeroy', fillcolor='rgba(46,125,50,0.12)',
            name='Cumulative net cash flow',
        ))
        fig.add_hline(
            y=0, line=dict(color='#C62828', width=1.2, dash='dash'),
            annotation_text='Break-even',
            annotation_position='top left',
        )
        pb = eroi.get('payback_years')
        if pb is not None:
            fig.add_vline(
                x=pb, line=dict(color='#888888', width=1, dash='dot'),
                annotation_text=f'Payback {pb:.1f} yr',
                annotation_position='bottom right',
            )
        fig.update_layout(
            title=dict(text='Cumulative Net Cash Flow (after capital & maintenance)',
                       font=dict(size=12, color='#1B5E20')),
            xaxis_title='Year',
            yaxis_title='Cumulative Int$',
            plot_bgcolor='#F9FBF9',
            paper_bgcolor='white',
            height=320,
            width=600,
            margin=dict(t=60, b=40, l=75, r=20),
            showlegend=False,
        )
        return pio.to_image(fig, format='png', width=600, height=320, scale=1.5)
    except Exception:
        return None


def _service_pie_chart(results: Dict[str, Any]) -> Optional[bytes]:
    """Donut chart of each ecosystem-service category's share of total annual
    value. PNG bytes, or None if unavailable / kaleido missing."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        esvd = results.get('esvd_results', {})
        categories = ['provisioning', 'regulating', 'cultural', 'supporting']
        cat_data = _resolve_categories_data(esvd, results, categories)
        if not cat_data:
            return None
        values = [cat_data.get(c, {}).get('total', 0) for c in categories]
        if not any(values):
            return None
        fig = go.Figure(data=[go.Pie(
            labels=[c.title() for c in categories],
            values=values,
            hole=0.4,
            textinfo='label+percent',
            textposition='outside',
            marker=dict(colors=['#2E7D32', '#558B2F', '#1976D2', '#7B1FA2']),
            sort=False,
        )])
        fig.update_layout(
            title=dict(text='Share of Annual Value by Service Category',
                       font=dict(size=12, color='#1B5E20')),
            paper_bgcolor='white',
            showlegend=False,
            height=380,
            width=560,
            margin=dict(t=55, b=55, l=70, r=70),
        )
        return pio.to_image(fig, format='png', width=560, height=380, scale=1.5)
    except Exception:
        return None


def _tornado_chart(sens_rows, central_npv: float) -> Optional[bytes]:
    """Horizontal tornado chart of NPV sensitivity.

    ``sens_rows`` is a list of (label, low_bcr, low_npv, high_bcr, high_npv).
    Each bar spans the parameter's low→high NPV; bars are sorted by range so
    the widest sits at the top. The central NPV is a dashed vertical line.
    Bars are green where the high variant lifts NPV, amber where it lowers it.
    PNG bytes, or None if unavailable / kaleido missing."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        if not sens_rows:
            return None
        rows = sorted(sens_rows, key=lambda r: abs(r[4] - r[2]))  # widest last
        # Wrap each y-axis label onto two lines — parameter name, then the
        # variant range — so long labels are not clipped by the left margin.
        labels = [r[0].replace('  (', '<br>(') for r in rows]
        lows = [min(r[2], r[4]) for r in rows]
        highs = [max(r[2], r[4]) for r in rows]
        widths = [h - l for l, h in zip(lows, highs)]
        colours = ['#2E7D32' if (r[4] - r[2]) >= 0 else '#F39C12' for r in rows]
        fig = go.Figure(go.Bar(
            y=labels, x=widths, base=lows, orientation='h',
            marker_color=colours,
        ))
        fig.add_vline(
            x=central_npv, line=dict(color='#555555', width=1.5, dash='dash'),
            annotation_text=f'Central NPV Int$ {central_npv:,.0f}',
            annotation_position='top',
        )
        fig.update_layout(
            title=dict(text='NPV Sensitivity (tornado)',
                       font=dict(size=12, color='#1B5E20')),
            xaxis_title='Net present value (Int$)',
            plot_bgcolor='#F9FBF9',
            paper_bgcolor='white',
            height=420,
            width=660,
            margin=dict(t=55, b=45, l=200, r=30),
            showlegend=False,
        )
        return pio.to_image(fig, format='png', width=660, height=420, scale=1.5)
    except Exception:
        return None
