#!/usr/bin/env python3
"""
ARINC768Forge Pro — Standalone Python 3 CLI Runner & ACMS Report Parser
Airborne Integrated Data System (AIDS) & Flight Data Monitoring
Standards: ARINC Characteristic 768, FAA AC 120-82, ICAO Annex 6
"""

import sys
import json
import time

class ARINC768Simulator:
    def __init__(self):
        self.tail = "A6-EGA"
        self.flight = "UAE768"
        self.phase = "CRUISE" # PREFLIGHT, TAKEOFF, CRUISE, LANDING
        
        # Engine Telemetry
        self.eng1_egt = 785.0
        self.eng2_egt = 788.0
        self.eng1_n1 = 88.4
        self.eng2_n1 = 88.5
        self.eng1_vib = 0.65
        self.eng2_vib = 0.70
        self.vert_accel_g = 1.00

        # Trigger Thresholds
        self.threshold_hard_landing_g = 1.80
        self.threshold_takeoff_egt = 950.0
        self.threshold_vibration_ips = 2.50

        self.reports_count = 0
        self.active_trigger = None

    def evaluate_triggers(self):
        if self.phase == "LANDING" and self.vert_accel_g >= self.threshold_hard_landing_g:
            self.active_trigger = {"type": "HARD_LANDING", "code": 1, "val": self.vert_accel_g}
            return self.generate_report(44)
        if self.phase == "TAKEOFF" and max(self.eng1_egt, self.eng2_egt) >= self.threshold_takeoff_egt:
            self.active_trigger = {"type": "HIGH_EGT", "code": 2, "val": max(self.eng1_egt, self.eng2_egt)}
            return self.generate_report(44)
        if max(self.eng1_vib, self.eng2_vib) >= self.threshold_vibration_ips:
            self.active_trigger = {"type": "HIGH_VIB", "code": 3, "val": max(self.eng1_vib, self.eng2_vib)}
            return self.generate_report(44)
        self.active_trigger = None
        return None

    def generate_report(self, report_type):
        self.reports_count += 1
        if report_type == 15:
            return {
                "report_id": f"REP15-{int(time.time())}",
                "type": 15,
                "title": "Report 15: Engine Cruise Performance Report (ETM)",
                "tail": self.tail,
                "flight": self.flight,
                "eng1_egt": self.eng1_egt,
                "eng2_egt": self.eng2_egt,
                "status": "CRUISE_STABLE"
            }
        elif report_type == 22:
            return {
                "report_id": f"REP22-{int(time.time())}",
                "type": 22,
                "title": "Report 22: Takeoff Profile Summary",
                "tail": self.tail,
                "flight": self.flight,
                "peak_n1": 98.6,
                "status": "TAKEOFF_RECORDED"
            }
        elif report_type == 44:
            return {
                "report_id": f"REP44-{int(time.time())}",
                "type": 44,
                "title": f"Report 44: Exceedance Advisory ({self.active_trigger['type'] if self.active_trigger else 'TEST'})",
                "tail": self.tail,
                "flight": self.flight,
                "trigger": self.active_trigger,
                "status": "EXCEEDANCE_DOWNLINK_DISPATCHED"
            }

    def generate_arinc429_words(self):
        # Label 126: ACMS Status & Trigger (Octal 126 = 0x56)
        label126 = 0x56
        trig_code = self.active_trigger["code"] if self.active_trigger else 0
        phase_map = {"PREFLIGHT": 0, "TAXI": 1, "TAKEOFF": 2, "CRUISE": 4, "LANDING": 7}
        p_code = phase_map.get(self.phase, 4)
        warn_bit = 1 if self.active_trigger else 0

        data126 = ((trig_code & 0x0F) << 10) | ((p_code & 0x07) << 14) | (warn_bit << 18) | (1 << 19) | (0x03 << 28)
        w126 = (data126 & 0x7FFFFF00) | label126
        w126 = self.apply_odd_parity(w126)

        # Label 127: ACMS Report Request (Octal 127 = 0x57)
        label127 = 0x57
        rep_type = 44 if self.active_trigger else 15
        data127 = ((rep_type & 0xFF) << 10) | ((self.reports_count & 0x3F) << 18) | (0x03 << 28)
        w127 = (data127 & 0x7FFFFF00) | label127
        w127 = self.apply_odd_parity(w127)

        return {
            "label126": {"octal": "126", "hex": hex(w126), "parity": self.verify_odd_parity(w126)},
            "label127": {"octal": "127", "hex": hex(w127), "parity": self.verify_odd_parity(w127)}
        }

    def apply_odd_parity(self, word):
        bits = word & 0x7FFFFFFF
        count = bin(bits).count('1')
        if count % 2 == 0:
            bits |= (1 << 31)
        return bits

    def verify_odd_parity(self, word):
        return bin(word).count('1') % 2 == 1

def run_cli():
    sim = ARINC768Simulator()
    print("=" * 70)
    print("ARINC768Forge Pro — Airborne Integrated Data System (AIDS/ACMS) CLI")
    print("Standards: ARINC Characteristic 768, FAA AC 120-82, ICAO Annex 6")
    print("=" * 70)
    print(f"\n[AIRCRAFT STATUS: {sim.tail} / {sim.flight} ({sim.phase})]")
    print(f"  Turbofan Engines     : GE90-115B Dual Installation")
    print(f"  Engine 1 EGT / N1    : {sim.eng1_egt}°C | {sim.eng1_n1}% RPM (Vib: {sim.eng1_vib} ips)")
    print(f"  Engine 2 EGT / N1    : {sim.eng2_egt}°C | {sim.eng2_n1}% RPM (Vib: {sim.eng2_vib} ips)")
    print(f"  Vertical Accel G     : {sim.vert_accel_g:.2f} G (Touchdown limit: {sim.threshold_hard_landing_g} G)")

    # Generate Cruise Report
    rep15 = sim.generate_report(15)
    print(f"\n[ACARS AUTO-REPORT SYNTHESIS: {rep15['title']}]")
    print(f"  Report ID            : {rep15['report_id']}")
    print(f"  Status               : {rep15['status']} (Ready for Ground ETM Ingestion)")

    # Simulate Hard Landing Trigger
    print("\n[SIMULATING EXCEEDANCE TRIGGER: TOUCHDOWN G-LOAD 2.15G]")
    sim.phase = "LANDING"
    sim.vert_accel_g = 2.15
    rep44 = sim.evaluate_triggers()
    if rep44:
        print(f"  ⚠️ EXCEEDANCE DOWNLINK TRIGGERED: {rep44['title']}")
        print(f"  Trigger Details      : {rep44['trigger']['type']} ({rep44['trigger']['val']}G)")

    bus = sim.generate_arinc429_words()
    print("\n" + "-" * 70)
    print("ARINC 429 Discrete Avionics Bus Stream (100 kbps):")
    print(f"  Label 126 (DMU Status & Trigger)  : {bus['label126']['hex']:<12} | Parity: {'VALID (PASS)' if bus['label126']['parity'] else 'FAIL'}")
    print(f"  Label 127 (Report Downlink Req)   : {bus['label127']['hex']:<12} | Parity: {'VALID (PASS)' if bus['label127']['parity'] else 'FAIL'}")
    print("=" * 70)

if __name__ == "__main__":
    run_cli()
