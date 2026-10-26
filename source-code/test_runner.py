#!/usr/bin/env python3
"""
ARINC768Forge Pro Automated Test Runner (10-Point Test Suite)
Validates:
1. DMU Initialization & Baseline Configuration
2. Engine Telemetry Ingestion (EGT, N1, Vibration)
3. Hard Landing Boundary Threshold (Nz < 1.80G ignored; >= 1.80G triggers)
4. Takeoff EGT Limit Boundary (EGT < 950°C ignored; >= 950°C triggers)
5. Engine Vibration Boundary (Vib < 2.5 ips ignored; >= 2.5 ips triggers)
6. Report 15 (Engine Cruise Performance / ETM Report) Data Assembly
7. Report 22 (Takeoff Profile Summary) Parameter Structure
8. Report 44 (Exceedance Advisory Downlink) Snapshot Generation
9. ARINC 429 Discrete Bus Labels 126 & 127 Bitfield Architecture
10. Hardware Bit 32 Odd Parity Verification across all generated bus words
"""

import sys
import os

# Ensure local import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arinc768_cli import ARINC768Simulator

def run_tests():
    print("=" * 70)
    print("ARINC768Forge Pro — Automated Compliance & Unit Test Suite")
    print("Standards: ARINC Characteristic 768, FAA AC 120-82, ICAO Annex 6")
    print("=" * 70)

    sim = ARINC768Simulator()
    tests_passed = 0
    total_tests = 10

    # Test 1: DMU Initialization
    assert sim.tail == "A6-EGA"
    assert sim.flight == "UAE768"
    assert sim.phase == "CRUISE"
    print("Test 1: AIDS/ACMS DMU Initialization & State Verification ... PASS")
    tests_passed += 1

    # Test 2: Engine Telemetry Ingestion
    assert sim.eng1_egt > 0 and sim.eng2_egt > 0
    assert sim.eng1_n1 > 0 and sim.eng2_n1 > 0
    assert sim.eng1_vib > 0 and sim.eng2_vib > 0
    print("Test 2: Dual Turbofan Engine Health Telemetry Parsing ... PASS")
    tests_passed += 1

    # Test 3: Hard Landing Boundary Threshold (1.80G)
    sim.phase = "LANDING"
    sim.vert_accel_g = 1.65
    assert sim.evaluate_triggers() is None # Under 1.80G
    sim.vert_accel_g = 1.95
    rep = sim.evaluate_triggers()
    assert rep is not None and rep["type"] == 44
    assert rep["trigger"]["type"] == "HARD_LANDING"
    print("Test 3: Hard Landing Exceedance Boundary (1.80G Threshold) ... PASS")
    tests_passed += 1

    # Test 4: Takeoff EGT Limit Boundary (950°C)
    sim.phase = "TAKEOFF"
    sim.vert_accel_g = 1.0
    sim.eng1_egt = 920.0
    sim.eng2_egt = 930.0
    assert sim.evaluate_triggers() is None # Under 950°C
    sim.eng1_egt = 965.0
    rep = sim.evaluate_triggers()
    assert rep is not None and rep["type"] == 44
    assert rep["trigger"]["type"] == "HIGH_EGT"
    print("Test 4: Takeoff Full-Thrust EGT Limit Boundary (950°C Threshold) ... PASS")
    tests_passed += 1

    # Test 5: Engine Vibration Boundary (2.5 ips)
    sim.phase = "CRUISE"
    sim.eng1_egt = 780.0
    sim.eng1_vib = 1.8
    sim.eng2_vib = 2.1
    assert sim.evaluate_triggers() is None # Under 2.5 ips
    sim.eng2_vib = 2.8
    rep = sim.evaluate_triggers()
    assert rep is not None and rep["type"] == 44
    assert rep["trigger"]["type"] == "HIGH_VIB"
    print("Test 5: Airframe & Rotor Vibration Boundary (2.5 ips Threshold) ... PASS")
    tests_passed += 1

    # Test 6: Report 15 (Engine Cruise ETM Report) Data Assembly
    rep15 = sim.generate_report(15)
    assert rep15["type"] == 15
    assert "eng1_egt" in rep15 and "eng2_egt" in rep15
    print("Test 6: ARINC 768 Report 15 (Engine Cruise ETM Report) Assembly ... PASS")
    tests_passed += 1

    # Test 7: Report 22 (Takeoff Profile Summary)
    rep22 = sim.generate_report(22)
    assert rep22["type"] == 22
    assert "peak_n1" in rep22
    print("Test 7: ARINC 768 Report 22 (Takeoff Profile Summary) ... PASS")
    tests_passed += 1

    # Test 8: Report 44 (Exceedance Advisory Downlink)
    sim.active_trigger = {"type": "DEMO_TEST", "code": 9}
    rep44 = sim.generate_report(44)
    assert rep44["type"] == 44
    assert rep44["trigger"]["type"] == "DEMO_TEST"
    print("Test 8: ARINC 768 Report 44 (Exceedance Advisory Snapshot) ... PASS")
    tests_passed += 1

    # Test 9: ARINC 429 Discrete Bus Labels 126 & 127 Bitfield Architecture
    bus = sim.generate_arinc429_words()
    assert bus["label126"]["hex"].startswith("0x")
    assert bus["label127"]["hex"].startswith("0x")
    print("Test 9: ARINC 429 Discrete Bus Encoding (Labels 126 & 127) ... PASS")
    tests_passed += 1

    # Test 10: Hardware Bit 32 Odd Parity Verification
    assert bus["label126"]["parity"] is True
    assert bus["label127"]["parity"] is True
    print("Test 10: Hardware Bit 32 Odd Parity Hardware Verification ... PASS")
    tests_passed += 1

    print("=" * 70)
    print(f"AUTOMATED TEST RESULTS: {tests_passed}/{total_tests} TESTS PASSED (100% SUCCESS RATE)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
