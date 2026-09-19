"""Validate static example structure and embedded inputs, not runtime semantics."""
from pathlib import Path
from copy import deepcopy
import json
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent

def main() -> None:
    schema = json.loads((ROOT.parent.parent / "schemas/dgp.schema.json").read_text())
    frame_schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/Frame"}
    validator = Draft202012Validator(frame_schema, format_checker=FormatChecker())
    frames = []
    for path in sorted((ROOT / "examples").glob("*-frame.json")):
        record = json.loads(path.read_text())
        validator.validate(record)
        frames.append(record)
        print(f"PASS frame structure: {path.name}")
    location = Draft202012Validator(frames[0]["decisions"][0]["input_schema"])
    point = {"kind":"point", "crs":"EPSG:4326", "latitude":0, "longitude":0, "source":"map"}
    # Coordinates here are arbitrary validation fixtures, not a farm location.
    cases = [
        (location, {"kind":"address_query", "query":"Example farm address"}, True, "address query"),
        (location, point, True, "map point"),
        (location, {**point, "source":"coordinate_entry"}, True, "entered coordinates"),
        (location, {**point, "latitude":91}, False, "invalid latitude"),
        (location, {**point, "battery_kwh":20}, False, "later-stage input at location stage"),
        (location, {"kind":"address_query", "query":""}, False, "empty address"),
    ]
    batch = Draft202012Validator(frames[1]["decisions"][0]["input_schema"])
    variant = {"site_ref":"site-01", "turbine_configuration_ref":"turbine-A", "battery_configuration_ref":"battery-20"}
    valid = {"base_scenario_ref":"base-001", "variants":[variant]}
    different_load = deepcopy(valid)
    different_load["variants"][0]["annual_consumption_kwh"] = 1000
    unknown_battery = deepcopy(valid)
    unknown_battery["variants"][0]["battery_configuration_ref"] = "battery-25"
    too_large = {"base_scenario_ref":"base-001", "variants":[
        {"site_ref":f"site-{i//3+1:02}", "turbine_configuration_ref":["turbine-A","turbine-B","turbine-C"][i%3],
         "battery_configuration_ref":"battery-20"} for i in range(17)]}
    cases += [
        (batch, valid, True, "valid explicit variant"),
        (batch, {"base_scenario_ref":"base-001", "variants":[]}, False, "empty batch"),
        (batch, different_load, False, "attempt to optimize farm demand"),
        (batch, unknown_battery, False, "unavailable battery step"),
        (batch, too_large, False, "batch larger than 16"),
        (batch, {"base_scenario_ref":"base-001", "variants":[variant, variant]}, False, "duplicate variants"),
    ]
    for check, value, expected, name in cases:
        actual = check.is_valid(value)
        if actual != expected:
            raise AssertionError(f"Unexpected result for {name}: {actual}")
        print(f"PASS input case: {name} ({'accepted' if expected else 'rejected'})")
    print(f"Validated {len(frames)} frame structures and {len(cases)} input cases.")
    print("Not tested: runtime admission, quotas, async jobs, geocoding, energy calculations, or model providers.")

if __name__ == "__main__":
    main()
