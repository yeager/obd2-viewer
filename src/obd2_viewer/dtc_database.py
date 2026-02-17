"""Built-in database of common OBD-II Diagnostic Trouble Codes."""

# Severity levels
SEVERITY_CRITICAL = "critical"   # red
SEVERITY_WARNING = "warning"     # yellow

# fmt: off
DTC_DATABASE = {
    # Fuel and Air Metering
    "P0100": ("Mass or Volume Air Flow Circuit Malfunction", SEVERITY_WARNING),
    "P0101": ("Mass or Volume Air Flow Circuit Range/Performance", SEVERITY_WARNING),
    "P0102": ("Mass or Volume Air Flow Circuit Low Input", SEVERITY_WARNING),
    "P0103": ("Mass or Volume Air Flow Circuit High Input", SEVERITY_WARNING),
    "P0104": ("Mass or Volume Air Flow Circuit Intermittent", SEVERITY_WARNING),
    "P0105": ("Manifold Absolute Pressure/Barometric Pressure Circuit Malfunction", SEVERITY_WARNING),
    "P0106": ("Manifold Absolute Pressure/Barometric Pressure Circuit Range/Performance", SEVERITY_WARNING),
    "P0107": ("Manifold Absolute Pressure/Barometric Pressure Circuit Low Input", SEVERITY_WARNING),
    "P0108": ("Manifold Absolute Pressure/Barometric Pressure Circuit High Input", SEVERITY_WARNING),
    "P0110": ("Intake Air Temperature Circuit Malfunction", SEVERITY_WARNING),
    "P0111": ("Intake Air Temperature Circuit Range/Performance", SEVERITY_WARNING),
    "P0112": ("Intake Air Temperature Circuit Low Input", SEVERITY_WARNING),
    "P0113": ("Intake Air Temperature Circuit High Input", SEVERITY_WARNING),
    "P0115": ("Engine Coolant Temperature Circuit Malfunction", SEVERITY_WARNING),
    "P0116": ("Engine Coolant Temperature Circuit Range/Performance", SEVERITY_WARNING),
    "P0117": ("Engine Coolant Temperature Circuit Low Input", SEVERITY_WARNING),
    "P0118": ("Engine Coolant Temperature Circuit High Input", SEVERITY_WARNING),
    "P0120": ("Throttle Position Sensor/Switch A Circuit Malfunction", SEVERITY_WARNING),
    "P0121": ("Throttle Position Sensor/Switch A Circuit Range/Performance", SEVERITY_WARNING),
    "P0122": ("Throttle Position Sensor/Switch A Circuit Low Input", SEVERITY_WARNING),
    "P0123": ("Throttle Position Sensor/Switch A Circuit High Input", SEVERITY_WARNING),
    "P0125": ("Insufficient Coolant Temperature for Closed Loop Fuel Control", SEVERITY_WARNING),
    "P0128": ("Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)", SEVERITY_WARNING),
    "P0130": ("O2 Sensor Circuit Malfunction (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0131": ("O2 Sensor Circuit Low Voltage (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0132": ("O2 Sensor Circuit High Voltage (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0133": ("O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0134": ("O2 Sensor Circuit No Activity Detected (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0135": ("O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 1)", SEVERITY_WARNING),
    "P0136": ("O2 Sensor Circuit Malfunction (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0137": ("O2 Sensor Circuit Low Voltage (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0138": ("O2 Sensor Circuit High Voltage (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0139": ("O2 Sensor Circuit Slow Response (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0140": ("O2 Sensor Circuit No Activity Detected (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0141": ("O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 2)", SEVERITY_WARNING),
    "P0150": ("O2 Sensor Circuit Malfunction (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0151": ("O2 Sensor Circuit Low Voltage (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0152": ("O2 Sensor Circuit High Voltage (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0153": ("O2 Sensor Circuit Slow Response (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0154": ("O2 Sensor Circuit No Activity Detected (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0155": ("O2 Sensor Heater Circuit Malfunction (Bank 2 Sensor 1)", SEVERITY_WARNING),
    "P0156": ("O2 Sensor Circuit Malfunction (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0157": ("O2 Sensor Circuit Low Voltage (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0158": ("O2 Sensor Circuit High Voltage (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0159": ("O2 Sensor Circuit Slow Response (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0160": ("O2 Sensor Circuit No Activity Detected (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0161": ("O2 Sensor Heater Circuit Malfunction (Bank 2 Sensor 2)", SEVERITY_WARNING),
    "P0170": ("Fuel Trim Malfunction (Bank 1)", SEVERITY_WARNING),
    "P0171": ("System Too Lean (Bank 1)", SEVERITY_WARNING),
    "P0172": ("System Too Rich (Bank 1)", SEVERITY_WARNING),
    "P0173": ("Fuel Trim Malfunction (Bank 2)", SEVERITY_WARNING),
    "P0174": ("System Too Lean (Bank 2)", SEVERITY_WARNING),
    "P0175": ("System Too Rich (Bank 2)", SEVERITY_WARNING),

    # Ignition System or Misfire
    "P0300": ("Random/Multiple Cylinder Misfire Detected", SEVERITY_CRITICAL),
    "P0301": ("Cylinder 1 Misfire Detected", SEVERITY_CRITICAL),
    "P0302": ("Cylinder 2 Misfire Detected", SEVERITY_CRITICAL),
    "P0303": ("Cylinder 3 Misfire Detected", SEVERITY_CRITICAL),
    "P0304": ("Cylinder 4 Misfire Detected", SEVERITY_CRITICAL),
    "P0305": ("Cylinder 5 Misfire Detected", SEVERITY_CRITICAL),
    "P0306": ("Cylinder 6 Misfire Detected", SEVERITY_CRITICAL),
    "P0307": ("Cylinder 7 Misfire Detected", SEVERITY_CRITICAL),
    "P0308": ("Cylinder 8 Misfire Detected", SEVERITY_CRITICAL),
    "P0309": ("Cylinder 9 Misfire Detected", SEVERITY_CRITICAL),
    "P0310": ("Cylinder 10 Misfire Detected", SEVERITY_CRITICAL),
    "P0311": ("Cylinder 11 Misfire Detected", SEVERITY_CRITICAL),
    "P0312": ("Cylinder 12 Misfire Detected", SEVERITY_CRITICAL),
    "P0325": ("Knock Sensor 1 Circuit Malfunction (Bank 1)", SEVERITY_WARNING),
    "P0326": ("Knock Sensor 1 Circuit Range/Performance (Bank 1)", SEVERITY_WARNING),
    "P0327": ("Knock Sensor 1 Circuit Low Input (Bank 1)", SEVERITY_WARNING),
    "P0328": ("Knock Sensor 1 Circuit High Input (Bank 1)", SEVERITY_WARNING),
    "P0330": ("Knock Sensor 2 Circuit Malfunction (Bank 2)", SEVERITY_WARNING),
    "P0335": ("Crankshaft Position Sensor A Circuit Malfunction", SEVERITY_CRITICAL),
    "P0336": ("Crankshaft Position Sensor A Circuit Range/Performance", SEVERITY_CRITICAL),
    "P0340": ("Camshaft Position Sensor Circuit Malfunction (Bank 1)", SEVERITY_CRITICAL),
    "P0341": ("Camshaft Position Sensor Circuit Range/Performance (Bank 1)", SEVERITY_WARNING),

    # Emission Controls
    "P0400": ("Exhaust Gas Recirculation Flow Malfunction", SEVERITY_WARNING),
    "P0401": ("Exhaust Gas Recirculation Flow Insufficient Detected", SEVERITY_WARNING),
    "P0402": ("Exhaust Gas Recirculation Flow Excessive Detected", SEVERITY_WARNING),
    "P0410": ("Secondary Air Injection System Malfunction", SEVERITY_WARNING),
    "P0411": ("Secondary Air Injection System Incorrect Flow Detected", SEVERITY_WARNING),
    "P0420": ("Catalyst System Efficiency Below Threshold (Bank 1)", SEVERITY_WARNING),
    "P0421": ("Warm Up Catalyst Efficiency Below Threshold (Bank 1)", SEVERITY_WARNING),
    "P0430": ("Catalyst System Efficiency Below Threshold (Bank 2)", SEVERITY_WARNING),
    "P0440": ("Evaporative Emission Control System Malfunction", SEVERITY_WARNING),
    "P0441": ("Evaporative Emission Control System Incorrect Purge Flow", SEVERITY_WARNING),
    "P0442": ("Evaporative Emission Control System Leak Detected (small leak)", SEVERITY_WARNING),
    "P0443": ("Evaporative Emission Control System Purge Control Valve Circuit Malfunction", SEVERITY_WARNING),
    "P0446": ("Evaporative Emission Control System Vent Control Circuit Malfunction", SEVERITY_WARNING),
    "P0450": ("Evaporative Emission Control System Pressure Sensor Malfunction", SEVERITY_WARNING),
    "P0455": ("Evaporative Emission Control System Leak Detected (large leak)", SEVERITY_WARNING),
    "P0456": ("Evaporative Emission Control System Leak Detected (very small leak)", SEVERITY_WARNING),

    # Vehicle Speed/Idle Control
    "P0500": ("Vehicle Speed Sensor Malfunction", SEVERITY_WARNING),
    "P0501": ("Vehicle Speed Sensor Range/Performance", SEVERITY_WARNING),
    "P0505": ("Idle Control System Malfunction", SEVERITY_WARNING),
    "P0506": ("Idle Control System RPM Lower Than Expected", SEVERITY_WARNING),
    "P0507": ("Idle Control System RPM Higher Than Expected", SEVERITY_WARNING),

    # Computer Output Circuit
    "P0600": ("Serial Communication Link Malfunction", SEVERITY_CRITICAL),
    "P0601": ("Internal Control Module Memory Check Sum Error", SEVERITY_CRITICAL),
    "P0602": ("Control Module Programming Error", SEVERITY_CRITICAL),

    # Transmission
    "P0700": ("Transmission Control System Malfunction", SEVERITY_CRITICAL),
    "P0705": ("Transmission Range Sensor Circuit Malfunction", SEVERITY_WARNING),
    "P0710": ("Transmission Fluid Temperature Sensor Circuit Malfunction", SEVERITY_WARNING),
    "P0715": ("Input/Turbine Speed Sensor Circuit Malfunction", SEVERITY_WARNING),
    "P0720": ("Output Speed Sensor Circuit Malfunction", SEVERITY_WARNING),
    "P0725": ("Engine Speed Input Circuit Malfunction", SEVERITY_WARNING),
    "P0730": ("Incorrect Gear Ratio", SEVERITY_WARNING),
    "P0740": ("Torque Converter Clutch Circuit Malfunction", SEVERITY_WARNING),
    "P0741": ("Torque Converter Clutch Circuit Performance or Stuck Off", SEVERITY_WARNING),
    "P0750": ("Shift Solenoid A Malfunction", SEVERITY_WARNING),
    "P0755": ("Shift Solenoid B Malfunction", SEVERITY_WARNING),
    "P0760": ("Shift Solenoid C Malfunction", SEVERITY_WARNING),

    # Turbo/Boost
    "P0234": ("Engine Overboost Condition", SEVERITY_CRITICAL),
    "P0235": ("Turbocharger Boost Sensor A Circuit Malfunction", SEVERITY_WARNING),
    "P0236": ("Turbocharger Boost Sensor A Circuit Range/Performance", SEVERITY_WARNING),
    "P0237": ("Turbocharger Boost Sensor A Circuit Low", SEVERITY_WARNING),
    "P0238": ("Turbocharger Boost Sensor A Circuit High", SEVERITY_WARNING),
    "P0243": ("Turbocharger Wastegate Solenoid A Malfunction", SEVERITY_WARNING),
    "P0244": ("Turbocharger Wastegate Solenoid A Range/Performance", SEVERITY_WARNING),
    "P0245": ("Turbocharger Wastegate Solenoid A Low", SEVERITY_WARNING),
    "P0246": ("Turbocharger Wastegate Solenoid A High", SEVERITY_WARNING),
    "P0299": ("Turbocharger/Supercharger Underboost", SEVERITY_WARNING),

    # BMW-specific (common)
    "P0011": ("Intake Camshaft Position Timing - Over-Advanced (Bank 1)", SEVERITY_WARNING),
    "P0012": ("Intake Camshaft Position Timing - Over-Retarded (Bank 1)", SEVERITY_WARNING),
    "P0013": ("Exhaust Camshaft Position Actuator Circuit (Bank 1)", SEVERITY_WARNING),
    "P0014": ("Exhaust Camshaft Position Timing - Over-Advanced (Bank 1)", SEVERITY_WARNING),
    "P0015": ("Exhaust Camshaft Position Timing - Over-Retarded (Bank 1)", SEVERITY_WARNING),
    "P0021": ("Intake Camshaft Position Timing - Over-Advanced (Bank 2)", SEVERITY_WARNING),
    "P0022": ("Intake Camshaft Position Timing - Over-Retarded (Bank 2)", SEVERITY_WARNING),

    # Body codes
    "B1000": ("ECU Malfunction", SEVERITY_CRITICAL),
    "B1001": ("Option Configuration Error", SEVERITY_WARNING),

    # Chassis codes
    "C0035": ("Left Front Wheel Speed Sensor Circuit Malfunction", SEVERITY_WARNING),
    "C0040": ("Right Front Wheel Speed Sensor Circuit Malfunction", SEVERITY_WARNING),
    "C0045": ("Left Rear Wheel Speed Sensor Circuit Malfunction", SEVERITY_WARNING),
    "C0050": ("Right Rear Wheel Speed Sensor Circuit Malfunction", SEVERITY_WARNING),

    # Network codes
    "U0100": ("Lost Communication with ECM/PCM", SEVERITY_CRITICAL),
    "U0101": ("Lost Communication with TCM", SEVERITY_CRITICAL),
    "U0121": ("Lost Communication with ABS", SEVERITY_CRITICAL),
    "U0140": ("Lost Communication with Body Control Module", SEVERITY_WARNING),
    "U0155": ("Lost Communication with Instrument Panel Cluster", SEVERITY_WARNING),
}
# fmt: on


def lookup_dtc(code: str) -> tuple[str, str]:
    """Look up a DTC code and return (description, severity).

    Returns a generic description if code is not in the database.
    """
    code = code.upper().strip()
    if code in DTC_DATABASE:
        return DTC_DATABASE[code]

    # Generate generic description from code prefix
    prefixes = {
        "P0": "Powertrain (Generic OBD-II)",
        "P1": "Powertrain (Manufacturer Specific)",
        "P2": "Powertrain (Generic OBD-II)",
        "P3": "Powertrain (Generic OBD-II)",
        "C0": "Chassis (Generic OBD-II)",
        "C1": "Chassis (Manufacturer Specific)",
        "B0": "Body (Generic OBD-II)",
        "B1": "Body (Manufacturer Specific)",
        "U0": "Network (Generic OBD-II)",
        "U1": "Network (Manufacturer Specific)",
    }
    prefix = code[:2] if len(code) >= 2 else ""
    category = prefixes.get(prefix, "Unknown")
    return (f"{category} Code {code}", SEVERITY_WARNING)
