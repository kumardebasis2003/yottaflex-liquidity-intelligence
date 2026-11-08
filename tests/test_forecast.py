from app.forecast import build_forecast

def test_scenarios_return_30_days():
    base = build_forecast("BASE")
    delayed = build_forecast("DELAYED_RECEIPT")
    stress = build_forecast("STRESS")
    assert len(base) == 30
    assert len(delayed) == 30
    assert len(stress) == 30
    assert base["scenario"].iloc[0] == "BASE"
