from core.promptlab.fixtures import list_fixtures, load_fixture


def test_list_fixtures_returns_summaries():
    fixtures = list_fixtures()
    assert len(fixtures) >= 2
    for f in fixtures:
        assert "name" in f
        assert "module" in f
        assert "description" in f


def test_load_fixture_returns_new_format():
    fixture = load_fixture("Cognitive Superpowers - Deceptive Alignment Discussion")
    assert fixture is not None
    assert "instructions" in fixture
    assert "context" in fixture
    assert "conversations" in fixture
    assert len(fixture["conversations"]) >= 1
    conv = fixture["conversations"][0]
    assert "label" in conv
    assert "messages" in conv
    assert len(conv["messages"]) >= 2


def test_load_fixture_not_found():
    fixture = load_fixture("Nonexistent Fixture")
    assert fixture is None
