/**
 * ARINC768Forge Pro — Core Engine
 * Airborne Integrated Data System (AIDS) / Aircraft Condition Monitoring System (ACMS)
 * Standards: ARINC Characteristic 768, FAA AC 120-82, ICAO Annex 6 Part I
 */

class ARINC768Engine {
  constructor() {
    this.flightInfo = {
      tailNumber: 'A6-EGA',
      flightNumber: 'UAE768',
      aircraftType: 'Boeing 777-300ER',
      engines: 'GE90-115B',
      flightPhase: 'CRUISE' // PREFLIGHT, TAXI, TAKEOFF, CLIMB, CRUISE, DESCENT, APPROACH, LANDING
    };

    // Engine 1 & 2 Real-Time Telemetry
    this.engines = {
      eng1: {
        n1Pct: 88.4,
        n2Pct: 92.1,
        egtDegC: 785.0,
        fuelFlowKgHr: 3420.0,
        oilPressPsi: 85.0,
        oilTempDegC: 112.0,
        vibN1Ips: 0.65,
        vibN2Ips: 0.82
      },
      eng2: {
        n1Pct: 88.5,
        n2Pct: 92.2,
        egtDegC: 788.0,
        fuelFlowKgHr: 3435.0,
        oilPressPsi: 86.0,
        oilTempDegC: 114.0,
        vibN1Ips: 0.70,
        vibN2Ips: 0.85
      }
    };

    // Aircraft Flight Dynamics (from ADIRS & Transducers)
    this.dynamics = {
      vertAccelG: 1.00,
      latAccelG: 0.01,
      longAccelG: 0.00,
      altitudeFt: 37000.0,
      mach: 0.84,
      casKt: 285.0,
      satDegC: -52.0,
      rollRateDegS: 0.0
    };

    // Exceedance Threshold Matrix (Trigger Criteria)
    this.thresholds = {
      hardLandingG: 1.80,       // Max vertical acceleration on touchdown
      takeoffEgtMaxDegC: 950.0, // Max takeoff exhaust gas temp
      cruiseEgtMaxDegC: 840.0,  // Max continuous cruise EGT
      vibrationMaxIps: 2.50,    // High airframe / rotor vibration
      lowOilPressPsi: 40.0,     // Minimum engine oil pressure
      maxRollRateDegS: 25.0     // Roll upset boundary
    };

    // ACARS Generated Reports Buffer
    this.reports = [];
    this.activeExceedance = null;
    this.qarRecording = true;
    this.reportSequence = 0;

    // Generate initial cruise baseline report
    this.generateCruiseReport();
  }

  setFlightPhase(phase) {
    if (['PREFLIGHT', 'TAXI', 'TAKEOFF', 'CLIMB', 'CRUISE', 'DESCENT', 'APPROACH', 'LANDING'].includes(phase)) {
      this.flightPhase = phase;
      this.flightInfo.flightPhase = phase;
      return true;
    }
    return false;
  }

  evaluateExceedances() {
    // 1. Hard Landing
    if (this.flightInfo.flightPhase === 'LANDING' && this.dynamics.vertAccelG >= this.thresholds.hardLandingG) {
      return this.triggerExceedance('HARD_LANDING', `Vertical touchdown acceleration ${this.dynamics.vertAccelG.toFixed(2)}G exceeded limit ${this.thresholds.hardLandingG}G`, 1);
    }

    // 2. High EGT
    const maxEgt = Math.max(this.engines.eng1.egtDegC, this.engines.eng2.egtDegC);
    const limitEgt = this.flightInfo.flightPhase === 'TAKEOFF' ? this.thresholds.takeoffEgtMaxDegC : this.thresholds.cruiseEgtMaxDegC;
    if (maxEgt >= limitEgt) {
      return this.triggerExceedance('HIGH_EGT', `Engine EGT ${maxEgt.toFixed(1)}°C exceeded limit ${limitEgt}°C`, 2);
    }

    // 3. Vibration Exceedance
    const maxVib = Math.max(
      this.engines.eng1.vibN1Ips, this.engines.eng1.vibN2Ips,
      this.engines.eng2.vibN1Ips, this.engines.eng2.vibN2Ips
    );
    if (maxVib >= this.thresholds.vibrationMaxIps) {
      return this.triggerExceedance('HIGH_VIBRATION', `Rotor vibration ${maxVib.toFixed(2)} ips exceeded limit ${this.thresholds.vibrationMaxIps} ips`, 3);
    }

    // 4. Low Oil Pressure
    const minOil = Math.min(this.engines.eng1.oilPressPsi, this.engines.eng2.oilPressPsi);
    if (minOil <= this.thresholds.lowOilPressPsi) {
      return this.triggerExceedance('LOW_OIL_PRESS', `Engine oil pressure ${minOil.toFixed(1)} psi dropped below ${this.thresholds.lowOilPressPsi} psi`, 4);
    }

    // 5. Roll Rate Exceedance
    if (Math.abs(this.dynamics.rollRateDegS) >= this.thresholds.maxRollRateDegS) {
      return this.triggerExceedance('EXCESSIVE_ROLL_RATE', `Roll rate ${Math.abs(this.dynamics.rollRateDegS).toFixed(1)}°/s exceeded ${this.thresholds.maxRollRateDegS}°/s`, 5);
    }

    this.activeExceedance = null;
    return null;
  }

  triggerExceedance(type, details, code) {
    this.activeExceedance = {
      type: type,
      details: details,
      code: code,
      timestamp: new Date().toISOString()
    };
    return this.generateExceedanceReport(type, details);
  }

  generateCruiseReport() {
    this.reportSequence++;
    const rep = {
      reportId: `REP15-${Date.now()}`,
      reportType: 15,
      title: 'ARINC 768 Report 15: Engine Cruise Performance Report (ETM)',
      timestamp: new Date().toISOString(),
      tail: this.flightInfo.tailNumber,
      flight: this.flightInfo.flightNumber,
      phase: this.flightInfo.flightPhase,
      conditions: {
        altitudeFt: this.dynamics.altitudeFt,
        mach: this.dynamics.mach,
        satDegC: this.dynamics.satDegC,
        casKt: this.dynamics.casKt
      },
      eng1: { ...this.engines.eng1, egtMarginDegC: 45.2 },
      eng2: { ...this.engines.eng2, egtMarginDegC: 42.8 },
      status: 'CRUISE_STABLE_RECORDED'
    };
    this.reports.unshift(rep);
    if (this.reports.length > 20) this.reports.pop();
    return rep;
  }

  generateTakeoffReport() {
    this.reportSequence++;
    const rep = {
      reportId: `REP22-${Date.now()}`,
      reportType: 22,
      title: 'ARINC 768 Report 22: Takeoff Profile & Full-Thrust Summary',
      timestamp: new Date().toISOString(),
      tail: this.flightInfo.tailNumber,
      flight: this.flightInfo.flightNumber,
      phase: 'TAKEOFF',
      conditions: {
        altitudeFt: 50.0,
        mach: 0.28,
        satDegC: 28.0,
        casKt: 168.0
      },
      eng1: { n1Pct: 98.6, n2Pct: 97.4, egtDegC: 912.0, fuelFlowKgHr: 7850.0, vibN1Ips: 1.15 },
      eng2: { n1Pct: 98.5, n2Pct: 97.5, egtDegC: 915.0, fuelFlowKgHr: 7890.0, vibN1Ips: 1.20 },
      status: 'TAKEOFF_BURST_RECORDED'
    };
    this.reports.unshift(rep);
    if (this.reports.length > 20) this.reports.pop();
    return rep;
  }

  generateExceedanceReport(exceedanceType, details) {
    this.reportSequence++;
    const rep = {
      reportId: `REP44-${Date.now()}`,
      reportType: 44,
      title: `ARINC 768 Report 44: Exceedance Advisory (${exceedanceType})`,
      timestamp: new Date().toISOString(),
      tail: this.flightInfo.tailNumber,
      flight: this.flightInfo.flightNumber,
      phase: this.flightInfo.flightPhase,
      exceedanceType: exceedanceType,
      details: details,
      snapshot: {
        vertAccelG: this.dynamics.vertAccelG,
        altitudeFt: this.dynamics.altitudeFt,
        eng1Egt: this.engines.eng1.egtDegC,
        eng2Egt: this.engines.eng2.egtDegC,
        eng1Vib: this.engines.eng1.vibN1Ips,
        eng2Vib: this.engines.eng2.vibN1Ips
      },
      status: 'EXCEEDANCE_DOWNLINK_DISPATCHED'
    };
    this.reports.unshift(rep);
    if (this.reports.length > 20) this.reports.pop();
    return rep;
  }

  // --- ARINC 429 Bus Synthesis ---
  generateARINC429Words() {
    // Label 126 (Octal 126, Hex 0x56): ACMS System Status & Exceedance Discrete
    const label126 = 0x56;
    let data126 = 0;

    const phaseMap = { PREFLIGHT: 0, TAXI: 1, TAKEOFF: 2, CLIMB: 3, CRUISE: 4, DESCENT: 5, APPROACH: 6, LANDING: 7 };
    const phaseCode = phaseMap[this.flightInfo.flightPhase] || 0;
    const triggerCode = this.activeExceedance ? this.activeExceedance.code : 0;
    const warningBit = this.activeExceedance ? 1 : 0;
    const qarBit = this.qarRecording ? 1 : 0;

    data126 |= (triggerCode & 0x0F) << 10; // Bits 11-14: Exceedance Trigger Code
    data126 |= (phaseCode & 0x07) << 14;   // Bits 15-17: Flight Phase Code
    data126 |= (warningBit & 0x01) << 18;  // Bit 19: Exceedance Active Warning
    data126 |= (qarBit & 0x01) << 19;      // Bit 20: QAR Recording Status
    data126 |= 0x03 << 28;                 // Bits 29-30: SSM (Normal Operation)

    let word126 = (data126 & 0x7FFFFF00) | (label126 & 0xFF);
    word126 = this.applyOddParity(word126);

    // Label 127 (Octal 127, Hex 0x57): ACMS Report Downlink Request & Sequence Count
    const label127 = 0x57;
    let data127 = 0;

    const lastRep = this.reports[0] || { reportType: 15 };
    data127 |= (lastRep.reportType & 0xFF) << 10; // Bits 11-18: Report Type (15, 22, 44)
    data127 |= (this.reportSequence & 0x3F) << 18; // Bits 19-24: Report Sequence Number (0-63)
    data127 |= 0x03 << 28;                         // Bits 29-30: SSM

    let word127 = (data127 & 0x7FFFFF00) | (label127 & 0xFF);
    word127 = this.applyOddParity(word127);

    return {
      label126: {
        octal: '126',
        hex: '0x' + (word126 >>> 0).toString(16).toUpperCase().padStart(8, '0'),
        parity: this.verifyOddParity(word126),
        triggerCode: triggerCode,
        phaseCode: phaseCode
      },
      label127: {
        octal: '127',
        hex: '0x' + (word127 >>> 0).toString(16).toUpperCase().padStart(8, '0'),
        parity: this.verifyOddParity(word127),
        reportType: lastRep.reportType,
        sequence: this.reportSequence
      }
    };
  }

  applyOddParity(word32) {
    let bits = word32 & 0x7FFFFFFF;
    let count = 0;
    for (let i = 0; i < 31; i++) {
      if ((bits >> i) & 1) count++;
    }
    if (count % 2 === 0) {
      bits |= (1 << 31);
    }
    return bits >>> 0;
  }

  verifyOddParity(word32) {
    let count = 0;
    for (let i = 0; i < 32; i++) {
      if ((word32 >>> i) & 1) count++;
    }
    return count % 2 === 1;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ARINC768Engine };
}
