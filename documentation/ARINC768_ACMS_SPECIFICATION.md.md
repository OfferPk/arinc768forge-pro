# ARINC Characteristic 768 Engineering Specification

## Airborne Integrated Data System (AIDS) / Aircraft Condition Monitoring System (ACMS)

**Document Version:** 1.0.0 • **Status:** Approved for Implementation • **Standard Baseline:** ARINC 768, FAA AC 120-82, ICAO Annex 6 Part I, ARINC 429-19

---

### 1\. Executive Summary

ARINC Characteristic 768 defines the commercial avionics architecture and functional interfaces for the **Airborne Integrated Data System (AIDS)**, typically implemented via the onboard **Data Management Unit (DMU)** or **Aircraft Condition Monitoring System (ACMS)**.

The ACMS continuously acquires multi-channel flight telemetry from across the aircraft—including FADEC turbofan engine controllers (ARINC 751), Air Data and Inertial Reference Systems (ARINC 704/706), Flight Management Computers (ARINC 702A), and Environmental Control Systems. It evaluates real-time flight parameters against programmable safety and maintenance trigger thresholds, generates automated ACARS downlink reports (e.g., Reports 15, 22, and 44), buffers high-resolution flight frames to the Quick Access Recorder (QAR), and drives discrete cockpit ARINC 429 annunciations.

ARINC768Forge Pro delivers an avionics-grade software reference implementation of the DMU telemetry acquisition engine, exceedance trigger matrix, standardized ACARS report synthesizer, QAR data buffer, and 10-point normative compliance audit suite.

---

### 2\. Normative Industry Standards Baseline

1. **ARINC Characteristic 768**: *Airborne Integrated Data System (AIDS)* — Specifications for DMU LRU form factors, sensor ingestion interfaces, programmable logic algorithms, and digital bus reporting.  
2. **FAA Advisory Circular AC 120-82**: *Flight Operational Quality Assurance (FOQA)* — Regulatory guidance for air carrier operational quality assurance, exceedance event thresholds, and flight data safety archives.  
3. **ICAO Annex 6 Part I (International Commercial Air Transport \- Aeroplanes)**: Standard 3.3.1 mandates that operators of aeroplanes with a maximum certificated take-off mass exceeding 27,000 kg shall establish and maintain a flight data analysis program (FDAP / FOQA).  
4. **ARINC 429-19**: *Mark 33 Digital Information Transfer System* — High-speed (100 kbps) avionics bus word format, BNR/discrete encoding, and Bit 32 odd parity.

---

### 3\. ACMS DMU Functional Architecture

The ARINC 768 DMU operates across eight deterministic flight phases:

1. `PREFLIGHT`: On-ground, engines shutdown, electrical power established.  
2. `TAXI`: Ground taxi operations, \$N1 \< 50%\$, ground speed \$\< 35\\text{ kt}\$.  
3. `TAKEOFF`: High thrust roll (\$N1 \> 85%\$) from brake release through liftoff.  
4. `CLIMB`: Accelerated climb from gear retraction to cruise level.  
5. `CRUISE`: Stabilized level flight (\$M \> 0.70\$, \$\\Delta Alt \< 50\\text{ ft}\$).  
6. `DESCENT`: Top-of-descent through terminal transition.  
7. `APPROACH`: Final approach fix (FAF) through decision height.  
8. `LANDING`: Main gear touchdown (\$N\_z\$ acceleration peak) through reverser stowing.

---

### 4\. Engine Health & Condition Monitoring (ETM / ECM)

The system tracks dual-spool turbofan performance parameters (GE90, CFM LEAP, Rolls-Royce Trent) to enable predictive maintenance and early detection of turbine degradation:

- **EGT Margin Tracking**: Compares measured Exhaust Gas Temperature (EGT) against engine redline limits to project turbine blade thermal life.  
- **Rotor Vibration Profiling**: Monitors dynamic vibration on the N1 low-pressure spool and N2 high-pressure core in inches per second (ips). Exceedance threshold: \$2.50\\text{ ips}\$.  
- **Fuel Flow & Core Speed**: Ingests fuel burn (kg/hr) relative to ambient Mach and pressure altitude to identify compressor fouling or turbine nozzle erosion.

---

### 5\. Automated Standard ACARS AIDS Reports

ARINC 768 establishes standard report structures downlinked over ACARS or recorded to QAR:

#### 5.1 Report 15: Engine Cruise Performance Report (ETM)

Triggered during stable cruise conditions (\$M \> 0.70\$, \$\\Delta N1 \< 0.2%\$, \$\\Delta Alt \< 50\\text{ ft}\$ for 60 seconds). Records baseline EGT, N1, N2, fuel flow, and ambient conditions to feed ground-based airline predictive maintenance software.

#### 5.2 Report 22: Takeoff Profile Summary Report

Triggered at maximum takeoff thrust (\$N1 \> 85%\$). Captures peak takeoff EGT, runway ambient temperature, bleed air status, and spool-up time constants.

#### 5.3 Report 44: Real-Time Exceedance Advisory Downlink

Automatically dispatched upon violation of any safety or airworthiness threshold:

- **Hard Landing**: Touchdown vertical acceleration \$N\_z \\ge 1.80\\text{G}\$.  
- **Takeoff EGT Exceedance**: Engine EGT \$\\ge 950^\\circ\\text{C}\$ during takeoff.  
- **Excessive Vibration**: Rotor vibration \$\\ge 2.50\\text{ ips}\$.  
- **Low Oil Pressure**: Engine oil pressure \$\\le 40\\text{ psi}\$.  
- **Roll Upset**: Roll rate \$\|p\| \\ge 25^\\circ/\\text{s}\$. Includes pre-event (5s), peak event, and post-event (10s) high-resolution parameter snapshots.

---

### 6\. ARINC 429 Discrete Bus Output Specification

The DMU broadcasts two dedicated ARINC 429 words at high speed (100 kbps) with **Bit 32 Odd Parity**:

#### Label 126 (Octal 126 / Hex 0x56): ACMS System Status & Trigger Code

- **Bits 1–8**: ARINC 429 Label `126` (Hex `56`).  
- **Bits 9–10**: SDI (`00` \= All/System).  
- **Bits 11–14**: Exceedance Trigger Code (`0` \= None, `1` \= Hard Landing, `2` \= High EGT, `3` \= High Vib, `4` \= Low Oil).  
- **Bits 15–17**: Flight Phase Code (`0` \= Preflight through `7` \= Landing).  
- **Bit 18**: Exceedance Active Alert (`1` \= Active Warning).  
- **Bit 19**: QAR Recording Active (`1` \= Streaming 128 wps).  
- **Bits 20–28**: Reserved / Subsystem Diagnostics.  
- **Bits 29–30**: SSM (`11` \= Normal Operation).  
- **Bit 32**: Odd Parity bit.

#### Label 127 (Octal 127 / Hex 0x57): ACMS Report Downlink Request & Sequence Count

- **Bits 1–8**: ARINC 429 Label `127` (Hex `57`).  
- **Bits 9–10**: SDI (`00`).  
- **Bits 11–18**: Downlink Report Type (`15` \= Cruise, `22` \= Takeoff, `44` \= Exceedance).  
- **Bits 19–24**: Cumulative Report Sequence Number (\$0–63\$).  
- **Bits 25–28**: Reserved.  
- **Bits 29–30**: SSM (`11` \= Normal).  
- **Bit 32**: Odd Parity bit.