"""Parametrized tests for LLMService across providers.

Scenarios covered:
- Gemini provider (requires GOOGLE_API_KEY)
- Ollama provider (requires local Ollama running and reachable at OLLAMA_URL)
- Fallback (no provider ready) returns template JSON.

Set environment variables before running to enable specific providers:
  LLM_PROVIDER=gemini GOOGLE_API_KEY=sk-... pytest backend/test_llm_models.py -k gemini
  LLM_PROVIDER=ollama OLLAMA_URL=http://localhost:11434 pytest backend/test_llm_models.py -k ollama

The test will gracefully skip provider-specific cases if required env is missing.
"""
import os
import json
import pytest
import asyncio
from services.llm_service import LLMService

VISION_FIXTURE = {
    'detections': [{'class': 'bathroom', 'confidence': 0.88}],
    'measurements': {'estimated_area_sqft': 55},
    'scene_description': 'Standard bathroom with tub and vanity'
}
PROJECT_TYPE = 'bathroom'
DESCRIPTION = 'Replace old tiles and install new vanity with modern fixtures.'

# --- Helper assertions ---

def assert_common_structure(result):
    assert isinstance(result, dict), 'Result should be a dict'
    assert 'analysis' in result, 'Missing analysis'
    assert 'materials_needed' in result, 'Missing materials_needed'
    assert 'recommendations' in result, 'Missing recommendations'

    # materials_needed may be empty if model failed, but should be a list
    assert isinstance(result['materials_needed'], list)
    assert isinstance(result['recommendations'], list)

    # If analysis looks like JSON ensure it parses
    analysis = result['analysis']
    if isinstance(analysis, str) and analysis.strip().startswith('{'):
        try:
            data = json.loads(analysis)
            assert 'materials' in data, 'LLM JSON missing materials'
        except json.JSONDecodeError:
            # Allow non-JSON responses from remote models; fallback always JSON
            pass

# --- Provider-specific tests ---

@pytest.mark.provider
@pytest.mark.integration
def test_gemini_provider():
    if os.getenv('LLM_PROVIDER', '').lower() != 'gemini':
        pytest.skip('LLM_PROVIDER not set to gemini')
    if not os.getenv('GOOGLE_API_KEY'):
        pytest.skip('GOOGLE_API_KEY required for gemini test')

    llm = LLMService()
    assert llm.provider == 'gemini'
    assert llm.is_ready(), 'Gemini should be ready when API key is present'

    result = asyncio.run(llm.reason_about_project(VISION_FIXTURE, PROJECT_TYPE, DESCRIPTION))
    assert_common_structure(result)
    # Expect some materials extracted
    assert len(result['materials_needed']) > 0, 'Gemini should return >0 materials'

@pytest.mark.provider
@pytest.mark.integration
def test_ollama_provider():
    if os.getenv('LLM_PROVIDER', '').lower() != 'ollama':
        pytest.skip('LLM_PROVIDER not set to ollama')

    llm = LLMService()
    if not llm.is_ready():
        pytest.skip('Ollama not reachable; skipping')

    result = asyncio.run(llm.reason_about_project(VISION_FIXTURE, PROJECT_TYPE, DESCRIPTION))
    assert_common_structure(result)
    # Ollama may stream natural language; materials_needed may still parse
    assert isinstance(result['materials_needed'], list)

@pytest.mark.small
def test_fallback_response():
    # Force fallback by setting unknown provider
    os.environ['LLM_PROVIDER'] = 'unknown_provider_xyz'
    llm = LLMService()
    assert not llm.is_ready()

    result = asyncio.run(llm.reason_about_project(VISION_FIXTURE, PROJECT_TYPE, DESCRIPTION))
    assert_common_structure(result)
    # Fallback templates should have materials
    assert len(result['materials_needed']) >= 1, 'Fallback should include template materials'

@pytest.mark.small
def test_json_material_extraction():
    # Ensure JSON extraction logic tolerates markdown fences
    os.environ['LLM_PROVIDER'] = 'unknown_provider_xyz'
    llm = LLMService()
    raw = """```json\n{\n  \"materials\": [{\"name\": \"tile\", \"quantity\": \"50\", \"unit\": \"sqft\"}],\n  \"labor_hours\": 10,\n  \"challenges\": [\"waterproofing\"],\n  \"approach\": \"standard\"\n}\n```"""
    # Emulate structure returned by reason_about_project
    materials = llm._extract_materials(raw)
    assert materials and materials[0]['name'] == 'tile'

@pytest.mark.small
def test_invalid_json_extraction():
    os.environ['LLM_PROVIDER'] = 'unknown_provider_xyz'
    llm = LLMService()
    raw = '{ not-valid-json'
    materials = llm._extract_materials(raw)
    # Should fail gracefully and return empty list
    assert materials == []

# Reset environment side effects after tests
@pytest.fixture(autouse=True)
def _cleanup_env():
    original_provider = os.environ.get('LLM_PROVIDER')
    yield
    if original_provider is not None:
        os.environ['LLM_PROVIDER'] = original_provider
    else:
        os.environ.pop('LLM_PROVIDER', None)
