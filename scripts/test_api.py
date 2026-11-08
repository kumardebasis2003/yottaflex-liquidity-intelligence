
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:8000"

results = []


def test_api(name, path, expected_status=200, check=None):
    try:
        with urlopen(BASE_URL + path, timeout=60) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = response.read()

        passed = status == expected_status
        data = None

        if "application/json" in content_type:
            data = json.loads(body.decode("utf-8"))

        if passed and check:
            passed = check(data, body, content_type)

        results.append((name, passed, status))
        print(f"{'PASS' if passed else 'FAIL'} | {name} | HTTP {status}")

    except HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8", errors="replace")
        passed = status == expected_status

        if passed and check:
            try:
                data = json.loads(body)
                passed = check(data, body, error.headers.get("Content-Type", ""))
            except Exception:
                passed = False

        results.append((name, passed, status))
        print(f"{'PASS' if passed else 'FAIL'} | {name} | HTTP {status}")
        if not passed:
            print(body[:500])

    except (URLError, TimeoutError) as error:
        results.append((name, False, "CONNECTION ERROR"))
        print(f"FAIL | {name} | {error}")

    except Exception as error:
        results.append((name, False, "ERROR"))
        print(f"FAIL | {name} | {error}")


print("\nYOTTAFLEX LIQUIDITY INTELLIGENCE")
print("=" * 55)

test_api("Home API", "/", check=lambda d, b, c: d["status"] == "running")

test_api(
    "Health API",
    "/health",
    check=lambda d, b, c: d["postgresql"] == "connected",
)

test_api(
    "Database Summary",
    "/api/v1/summary",
    check=lambda d, b, c: d["total_records"] == 140491,
)

for scenario in ["BASE", "DELAYED_RECEIPT", "STRESS"]:
    test_api(
        f"{scenario} Forecast",
        f"/api/v1/forecast?scenario={scenario}",
        check=lambda d, b, c: (
            d["forecast_days"] == 30
            and len(d["forecast"]) == 30
        ),
    )

test_api(
    "Invalid Forecast Scenario",
    "/api/v1/forecast?scenario=INVALID",
    expected_status=400,
)

test_api(
    "Forecast CSV Export",
    "/api/v1/forecast/export.csv?scenario=BASE",
    check=lambda d, b, c: (
        "text/csv" in c and len(b) > 0
    ),
)

test_api(
    "Forecast JSON Export",
    "/api/v1/forecast/export.json?scenario=STRESS",
    check=lambda d, b, c: (
        d["scenario"] == "STRESS"
        and len(d["forecast"]) == 30
    ),
)

test_api(
    "Exception Detection",
    "/api/v1/exceptions",
    check=lambda d, b, c: (
        "total_exceptions" in d and "exceptions" in d
    ),
)

test_api(
    "Exception CSV Export",
    "/api/v1/exceptions/export.csv",
    check=lambda d, b, c: (
        "text/csv" in c and len(b) > 0
    ),
)

test_api(
    "Ground Truth Validation",
    "/api/v1/validation",
    check=lambda d, b, c: (
        d["status"] == "PASS"
        and d["total_checks"] == 5
        and d["passed"] == 5
        and d["failed"] == 0
    ),
)

print("\n" + "=" * 55)
passed = sum(1 for _, ok, _ in results if ok)
failed = len(results) - passed

print(f"TOTAL TESTS : {len(results)}")
print(f"PASSED      : {passed}")
print(f"FAILED      : {failed}")

if failed == 0:
    print("\nALL API TESTS PASSED!")
else:
    print("\nSOME TESTS FAILED. CHECK THE ERRORS ABOVE.")
