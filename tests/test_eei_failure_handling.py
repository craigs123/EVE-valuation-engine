"""End-to-end check of the new failure path, without touching the live service.

Simulates the three states the EEI service can now be in and asserts EVE
classifies each correctly - in particular that a measurement failure takes the
conservative fallback rather than the optimistic 100% default.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.eei_api as eei

SAMPLES = {
    'point_0': {'coordinates': {'lat': 51.75, 'lon': -1.25}, 'ecosystem_type': 'Grassland'},
    'point_1': {'coordinates': {'lat': 51.74, 'lon': -1.26}, 'ecosystem_type': 'Grassland'},
    'point_2': {'coordinates': {'lat': 51.73, 'lon': -1.27}, 'ecosystem_type': 'Wetland'},
}

QUOTA_ERROR = ("Error fetching EEI data: Your usage exceeded the custom quota "
               "for 'earthengine.googleapis.com/daily_eecu_usage_time'")

BANDS = ("eii", "functional_integrity", "structural_integrity", "compositional_integrity")


def real(eii):
    return {"geometry_type": "Point", "source": "Google Earth Engine - Landler Open Data",
            "values": {b: eii for b in BANDS}}


def failed():
    return {"geometry_type": "Point", "values": {b: None for b in BANDS},
            "error": QUOTA_ERROR, "measurement_failed": True}


def demo():
    return {"geometry_type": "Point", "demo_mode": True,
            "note": "Demo data - set up Google Earth Engine for real data",
            "values": {b: 0.411 for b in BANDS}}


def no_pixel():
    return {"geometry_type": "Point", "values": {b: None for b in BANDS},
            "message": "No data available for this location (likely ocean or data gap)"}


def run(label, response, expect):
    eei.get_eei_batch = lambda coords, timeout=30: response
    values, avg, status = eei.extract_eei_for_sample_points(SAMPLES)
    got = {k: status[k] for k in ('real', 'demo', 'failed', 'null')}
    ok = got == expect
    print(f'  {"PASS" if ok else "FAIL"}  {label}: {got}'
          + ('' if ok else f'  expected {expect}'))
    assert ok, label
    return values, status


print('classification of each service state:')
run('all real', {"results": [real(0.4), real(0.5), real(0.6)]},
    {'real': 3, 'demo': 0, 'failed': 0, 'null': 0})
run('all demo (EE never initialised)',
    {"demo_mode": True, "results": [demo(), demo(), demo()]},
    {'real': 0, 'demo': 3, 'failed': 0, 'null': 0})
_, st_mixed = run('partial measurement failure',
                  {"results": [real(0.4), failed(), failed()],
                   "failed_count": 2, "error": QUOTA_ERROR},
                  {'real': 1, 'demo': 0, 'failed': 2, 'null': 0})
run('real response, no pixel (ocean)',
    {"results": [real(0.4), no_pixel(), no_pixel()]},
    {'real': 3, 'demo': 0, 'failed': 0, 'null': 2})

print('\nfailure reason reaches the caller:')
print('  error_detail:', (st_mixed.get('error_detail') or '')[:60], '...')
assert st_mixed['error_detail'] == QUOTA_ERROR
assert st_mixed['any_failed'] is True
assert st_mixed['failed_point_ids'] == ['point_1', 'point_2']
print('  PASS  any_failed set, failed_point_ids identified')

print('\nconservative fallback applied to a wholly unmeasured ecosystem:')
values, status = run('wetland fails, grassland real',
                     {"results": [real(0.4), real(0.5), failed()],
                      "failed_count": 1, "error": QUOTA_ERROR},
                     {'real': 2, 'demo': 0, 'failed': 1, 'null': 0})
affected = eei.get_demo_affected_ecosystems(
    SAMPLES, values,
    status['demo_point_ids'] + status['failed_point_ids'])
print('  ecosystems taking the conservative default:', affected)
assert affected == ['Wetland'], affected
assert 'Grassland' not in affected
print(f'  PASS  Wetland -> {eei.DEMO_FALLBACK_INTACTNESS_PCT:.0f}% not 100%; '
      f'Grassland keeps its real reading')

print('\nHTTP error body is preserved:')


class FakeResponse:
    status_code = 503

    @staticmethod
    def json():
        return {"error": QUOTA_ERROR, "results": [], "failed_count": 3}


import utils.eei_api as mod
mod.requests.post = lambda *a, **k: FakeResponse()
# reload the real function (run() above monkeypatched it)
import importlib
importlib.reload(mod)
mod.requests.post = lambda *a, **k: FakeResponse()
mod._get_headers = lambda: {}
out = mod.get_eei_batch([(51.75, -1.25)])
print('  returned error:', (out.get('error') or '')[:60], '...')
assert out['error'] == QUOTA_ERROR, out
print('  PASS  503 body surfaced instead of a bare status code')

print('\nall checks passed')
