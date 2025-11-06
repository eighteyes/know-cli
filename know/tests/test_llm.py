"""
Tests for LLM integration.
"""

import pytest
import json
from pathlib import Path

from know_lib import LLMManager, MockProvider


def test_llm_manager_initialization():
    """Test LLM manager initializes correctly."""
    llm = LLMManager()

    assert llm.providers_config is not None
    assert llm.workflows_config is not None
    assert len(llm.providers) > 0


def test_list_providers():
    """Test listing available providers."""
    llm = LLMManager()
    providers = llm.list_providers()

    assert len(providers) > 0
    assert any(p['name'] == 'mock' for p in providers)


def test_list_workflows():
    """Test listing available workflows."""
    llm = LLMManager()
    workflows = llm.list_workflows()

    assert len(workflows) > 0
    assert any('vision_statement' in w['name'] for w in workflows)


def test_get_mock_provider():
    """Test getting mock provider."""
    llm = LLMManager()
    provider = llm.get_provider('mock')

    assert isinstance(provider, MockProvider)
    assert provider.type == 'mock'


def test_mock_provider_call():
    """Test mock provider returns response."""
    llm = LLMManager()
    provider = llm.get_provider('mock')

    response, metadata = provider.call("Test prompt")

    assert response is not None
    assert 'provider' in metadata
    assert metadata['provider'] == 'mock'


def test_execute_workflow():
    """Test executing a workflow."""
    llm = LLMManager()

    result = llm.execute_workflow(
        'node_extraction',
        {
            'question': 'What features are needed?',
            'answer': 'User authentication and dashboard',
            'graph_context': {}
        },
        provider_name='mock'
    )

    assert result is not None


def test_validate_workflow_inputs_valid():
    """Test validating valid workflow inputs."""
    llm = LLMManager()

    is_valid, errors = llm.validate_workflow_inputs(
        'node_extraction',
        {
            'question': 'Test?',
            'answer': 'Test answer'
        }
    )

    assert is_valid
    assert len(errors) == 0


def test_validate_workflow_inputs_invalid():
    """Test validating invalid workflow inputs."""
    llm = LLMManager()

    is_valid, errors = llm.validate_workflow_inputs(
        'node_extraction',
        {
            'question': 'Test?'
            # Missing required 'answer' field
        }
    )

    assert not is_valid
    assert len(errors) > 0


def test_get_workflow_chain():
    """Test getting workflow chain."""
    llm = LLMManager()

    chain = llm.get_workflow_chain('discovery_session')

    assert len(chain) > 0
    assert 'vision_statement' in chain


def test_execute_chain():
    """Test executing workflow chain."""
    llm = LLMManager()

    results = llm.execute_chain(
        'discovery_session',
        {
            'vision': 'Build a fleet management system',
            'context': {}
        },
        provider_name='mock'
    )

    assert len(results) > 0
    assert all('workflow' in r for r in results)
    assert all('output' in r for r in results)


def test_build_prompt():
    """Test prompt building."""
    llm = LLMManager()

    template = "Question: ${question}\nAnswer: ${answer}"
    inputs = {
        'question': 'What is this?',
        'answer': 'A test'
    }

    prompt = llm._build_prompt(template, inputs)

    assert 'What is this?' in prompt
    assert 'A test' in prompt


def test_parse_response_json():
    """Test parsing JSON response."""
    llm = LLMManager()

    response = '{"type": "feature", "key": "test"}'
    schema = {'type': 'string', 'key': 'string'}

    result = llm._parse_response(response, schema)

    assert result['type'] == 'feature'
    assert result['key'] == 'test'


def test_parse_response_non_json():
    """Test parsing non-JSON response."""
    llm = LLMManager()

    response = 'Plain text response'
    schema = {}

    result = llm._parse_response(response, schema)

    assert 'raw_response' in result
    assert result['raw_response'] == 'Plain text response'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
