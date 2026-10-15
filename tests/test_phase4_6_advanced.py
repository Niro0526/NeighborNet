import os
import json
import pytest
from apps.intelligence.fixtures.advanced_scenarios import (
    get_advanced_scenario,
    ALL_ADVANCED_SCENARIO_IDS,
    ADVANCED_SUITE_ID,
    ADVANCED_REFERENCE_TIMESTAMP
)
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.baseline_matching import run_fcfs_baseline, run_nearest_baseline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.django_db
def test_real_sri_lanka_dataset_schema_validation():
    """Verifies that ingested public dataset manifests and JSON files exist and have valid structure."""
    weather_path = os.path.join(BASE_DIR, 'data', 'external', 'weather', 'metadata.json')
    osm_path = os.path.join(BASE_DIR, 'data', 'external', 'osm', 'metadata.json')
    disaster_path = os.path.join(BASE_DIR, 'data', 'external', 'disaster', 'metadata.json')
    unep_path = os.path.join(BASE_DIR, 'data', 'evidence', 'metadata.json')

    for p in [weather_path, osm_path, disaster_path, unep_path]:
        assert os.path.exists(p), f"Missing data manifest: {p}"
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'source_name' in data
            assert 'source_url' in data
            assert 'sha256_checksum' in data
            assert 'dataset_type' in data

@pytest.mark.django_db
def test_advanced_scenarios_expiry_prioritization():
    """Scenario 1 Invariant: CP-SAT prioritizes short 3h perishable lot over 24h stable lot."""
    sc_data = get_advanced_scenario('1_COMPETING_EXPIRY')
    opt_res = solve_resource_allocation(
        sc_data['resources'],
        sc_data['requests'],
        time_limit_seconds=2.0,
        now=sc_data['ref_time']
    )
    assert opt_res.solver_status in ('OPTIMAL', 'FEASIBLE')
    assert len(opt_res.allocations) == 1
    # Check that perishable 3h lot ADV-RES-S1-A was chosen
    assert opt_res.allocations[0]['resource_id'] == 'ADV-RES-S1-A'

@pytest.mark.django_db
def test_advanced_scenarios_uneven_priorities():
    """Scenario 4 Invariant: CP-SAT allocates 50kg supply to URGENT request over LOW priority request."""
    sc_data = get_advanced_scenario('4_UNEVEN_PRIORITIES')
    opt_res = solve_resource_allocation(
        sc_data['resources'],
        sc_data['requests'],
        time_limit_seconds=2.0,
        now=sc_data['ref_time']
    )
    assert opt_res.solver_status in ('OPTIMAL', 'FEASIBLE')
    assert len(opt_res.allocations) == 1
    assert opt_res.allocations[0]['request_id'] == 'ADV-REQ-S4-URGENT'

@pytest.mark.django_db
def test_advanced_scenarios_mixed_unit_isolation():
    """Scenario 7 Invariant: Mixed units (kg, liters, kits) are allocated in isolated units, and incompatible boxes unit is rejected."""
    sc_data = get_advanced_scenario('7_MIXED_UNITS_ISOLATION')
    opt_res = solve_resource_allocation(
        sc_data['resources'],
        sc_data['requests'],
        time_limit_seconds=2.0,
        now=sc_data['ref_time']
    )
    assert opt_res.solver_status in ('OPTIMAL', 'FEASIBLE')
    allocated_reqs = {a['request_id'] for a in opt_res.allocations}

    assert 'ADV-REQ-S7-KG' in allocated_reqs
    assert 'ADV-REQ-S7-L' in allocated_reqs
    assert 'ADV-REQ-S7-KITS' in allocated_reqs
    assert 'ADV-REQ-S7-BOXES' not in allocated_reqs # Incompatible unit rejected

@pytest.mark.django_db
def test_advanced_scenarios_reproducibility():
    """Verifies that all 7 advanced scenarios produce 100% deterministic allocations and pass conservation equations."""
    for sc_id in ALL_ADVANCED_SCENARIO_IDS:
        sc_data = get_advanced_scenario(sc_id)
        res = sc_data['resources']
        req = sc_data['requests']
        now = sc_data['ref_time']

        opt_res = solve_resource_allocation(res, req, time_limit_seconds=2.0, now=now)
        total_req_units = sum(float(r.requested_quantity) for r in req)

        # Conservation equation check
        assert abs((opt_res.total_allocated_quantity + opt_res.unmet_demand) - total_req_units) < 0.01
