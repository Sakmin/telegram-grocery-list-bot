from grocery_bot.duplicate_detection import looks_like_duplicate


def test_duplicate_detection_ignores_case_and_spacing():
    assert looks_like_duplicate("Milk", " milk ")


def test_duplicate_detection_collapses_internal_spaces():
    assert looks_like_duplicate("Almond   Milk", "almond milk")
