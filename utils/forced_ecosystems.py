"""Registry of satellite-undetectable restoration ecosystems.

Some restoration ecosystems (e.g. Peatland) are not classified by the
OpenLandMap / ESA WorldCover landcover layers, so auto-detection can never
produce them. When one of these is chosen as the ecosystem override, EVE must
FORCE it onto the whole drawn area: every sample point is stamped with the
ecosystem (skipping the landcover lookup) and the valuation uses its ESVD
coefficient set.

Each entry maps the EVE ecosystem **display name** to its **calc key** in
``PrecomputedESVDCoefficients.coefficients`` (lowercase, underscore-joined).

To add one (see ``docs/adding_indicator_sets.md``):
  1. Add the ESVD coefficient block under that calc key in
     ``utils/precomputed_esvd_coefficients.py``.
  2. Add the display name here.
  3. (handled automatically) ``ECOSYSTEM_DISPLAY_OPTIONS`` in ``app.py`` appends
     these names, and the analysis override mapping picks up the calc key, so
     the ecosystem becomes selectable and is forced onto the area.
  4. Optionally seed a project type + indicator set for it.

Satellite-*detectable* ecosystems must NOT be listed here — detection already
produces them and forcing would override real per-point classification.
"""

# display name -> ESVD coefficient calc key. Empty until the first
# satellite-undetectable ecosystem is added with its coefficient block, e.g.:
#     'Peatland': 'peatland',
FORCED_ECOSYSTEM_TO_KEY: dict[str, str] = {}


def is_forced_ecosystem(display_name) -> bool:
    """True if ``display_name`` is a satellite-undetectable ecosystem that must
    be forced onto the whole area."""
    return display_name in FORCED_ECOSYSTEM_TO_KEY


def forced_display_names() -> list[str]:
    """Display names to append to the ecosystem override dropdown."""
    return list(FORCED_ECOSYSTEM_TO_KEY.keys())
