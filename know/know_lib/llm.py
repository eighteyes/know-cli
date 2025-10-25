"""
LLM provider integration for the know tool.
Supports multiple providers and workflows for graph enhancement.
"""

import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from string import Template
try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


class LLMProvider:
    """Base LLM provider interface."""

    def __init__(self, config: Dict, provider_name: str):
        """
        Initialize LLM provider.

        Args:
            config: Provider configuration
            provider_name: Name of the provider
        """
        self.config = config
        self.provider_name = provider_name
        self.name = config.get('name', provider_name)
        self.type = config.get('type', 'remote')
        self.base_url = config.get('base_url')
        self.models = config.get('models', [])
        self.headers = config.get('headers', {})
        self.request_format = config.get('request_format', 'openai')
        self.response_path = config.get('response_path', '.choices[0].message.content')
        self.usage_path = config.get('usage_path', '.usage')
        self.auth_env_var = config.get('auth_env_var')

        # Get API key from environment if needed
        self.api_key = None
        if self.auth_env_var:
            self.api_key = os.getenv(self.auth_env_var)

    def prepare_headers(self) -> Dict[str, str]:
        """Prepare request headers with authentication."""
        headers = {}
        for key, value in self.headers.items():
            if '${API_KEY}' in value and self.api_key:
                headers[key] = value.replace('${API_KEY}', self.api_key)
            else:
                headers[key] = value
        return headers

    def prepare_request(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        request_template: Dict
    ) -> Dict:
        """
        Prepare request payload from template.

        Args:
            prompt: User prompt
            model: Model ID
            max_tokens: Maximum tokens
            temperature: Temperature setting
            request_template: Request template

        Returns:
            Request payload
        """
        # Convert template to JSON string for substitution
        template_str = json.dumps(request_template)

        # Substitute variables
        template_str = template_str.replace('${MODEL}', model)
        template_str = template_str.replace('${MAX_TOKENS}', str(max_tokens))
        template_str = template_str.replace('${TEMPERATURE}', str(temperature))
        template_str = template_str.replace('${PROMPT}', prompt.replace('"', '\\"'))

        return json.loads(template_str)

    def extract_response(self, response_data: Dict) -> Tuple[str, Optional[Dict]]:
        """
        Extract response text and usage from API response.

        Args:
            response_data: Raw API response

        Returns:
            Tuple of (response_text, usage_data)
        """
        # Extract response text using JSONPath-like syntax
        text = self._extract_path(response_data, self.response_path)

        # Extract usage if available
        usage = None
        if self.usage_path:
            usage = self._extract_path(response_data, self.usage_path)

        return text or "", usage

    def _extract_path(self, data: Any, path: str) -> Any:
        """
        Extract value from nested dict using simple path syntax.

        Args:
            data: Source data
            path: Path like ".choices[0].message.content"

        Returns:
            Extracted value or None
        """
        if not path or path == 'null':
            return None

        # Remove leading dot
        path = path.lstrip('.')

        # Split path into parts
        parts = re.split(r'[\.\[]', path)

        current = data
        for part in parts:
            if not part:
                continue

            # Handle array index
            if part.endswith(']'):
                index = int(part.rstrip(']'))
                if isinstance(current, list) and len(current) > index:
                    current = current[index]
                else:
                    return None
            # Handle dict key
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current


class MockProvider(LLMProvider):
    """Mock provider for testing."""

    def __init__(self, config: Dict, provider_name: str):
        super().__init__(config, provider_name)
        self.mock_responses = config.get('mock_responses', {})

    def call(self, prompt: str, **kwargs) -> Tuple[str, Dict]:
        """
        Return mock response.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Tuple of (response, metadata)
        """
        # Determine response type from prompt
        response_type = 'default'
        if 'extract' in prompt.lower():
            response_type = 'entity_extraction'
        elif 'graph' in prompt.lower():
            response_type = 'graph_query'

        response = self.mock_responses.get(response_type, self.mock_responses.get('default'))

        metadata = {
            'provider': self.provider_name,
            'model': 'mock-model',
            'usage': {'input_tokens': 10, 'output_tokens': 20}
        }

        return response, metadata


class LLMManager:
    """Manages LLM providers and workflows."""

    def __init__(
        self,
        providers_path: Optional[str] = None,
        workflows_path: Optional[str] = None
    ):
        """
        Initialize LLM manager.

        Args:
            providers_path: Path to providers config
            workflows_path: Path to workflows config
        """
        # Load configs
        if providers_path is None:
            providers_path = Path(__file__).parent.parent / "config" / "llm-providers.json"
        if workflows_path is None:
            workflows_path = Path(__file__).parent.parent / "config" / "llm-workflows.json"

        with open(providers_path, 'r') as f:
            self.providers_config = json.load(f)

        with open(workflows_path, 'r') as f:
            self.workflows_config = json.load(f)

        self.providers: Dict[str, LLMProvider] = {}
        self.defaults = self.providers_config.get('defaults', {})
        self.request_formats = self.providers_config.get('request_formats', {})

        # Initialize providers
        self._init_providers()

    def _init_providers(self):
        """Initialize provider instances."""
        for provider_name, provider_config in self.providers_config.get('providers', {}).items():
            if provider_config.get('type') == 'mock':
                self.providers[provider_name] = MockProvider(provider_config, provider_name)
            else:
                self.providers[provider_name] = LLMProvider(provider_config, provider_name)

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get provider instance.

        Args:
            provider_name: Provider name (uses default if None)

        Returns:
            Provider instance
        """
        if provider_name is None:
            provider_name = self.defaults.get('provider', 'mock')

        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        return self.providers[provider_name]

    def execute_workflow(
        self,
        workflow_name: str,
        inputs: Dict,
        provider_name: Optional[str] = None
    ) -> Dict:
        """
        Execute a workflow.

        Args:
            workflow_name: Workflow name
            inputs: Input data
            provider_name: Provider to use

        Returns:
            Workflow output
        """
        workflows = self.workflows_config.get('workflows', {})

        if workflow_name not in workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow = workflows[workflow_name]

        # Build prompt from template
        prompt = self._build_prompt(workflow['prompt_template'], inputs)

        # Get model preferences
        prefs = workflow.get('model_preferences', {})
        temperature = prefs.get('temperature', self.defaults.get('temperature', 0.7))
        max_tokens = prefs.get('max_tokens', self.defaults.get('max_tokens', 4096))

        # Execute call
        provider = self.get_provider(provider_name)

        # For mock provider, return directly
        if isinstance(provider, MockProvider):
            response, metadata = provider.call(prompt)
            return self._parse_response(response, workflow['output_schema'])

        # For real providers, make HTTP request
        return self._execute_http_call(
            provider,
            prompt,
            max_tokens,
            temperature,
            workflow['output_schema']
        )

    def _build_prompt(self, template: str, inputs: Dict) -> str:
        """
        Build prompt from template and inputs.

        Args:
            template: Prompt template
            inputs: Input values

        Returns:
            Formatted prompt
        """
        # Convert inputs to strings
        string_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (dict, list)):
                string_inputs[key] = json.dumps(value, indent=2)
            else:
                string_inputs[key] = str(value)

        # Use Template for safe substitution
        tmpl = Template(template)
        return tmpl.safe_substitute(string_inputs)

    def _parse_response(self, response: str, schema: Dict) -> Dict:
        """
        Parse response according to schema.

        Args:
            response: Raw response text
            schema: Expected output schema

        Returns:
            Parsed response
        """
        # Try to parse as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If not JSON, return as-is with schema keys
            return {'raw_response': response}

    def list_workflows(self) -> List[Dict]:
        """
        List available workflows.

        Returns:
            List of workflow info
        """
        workflows = []
        for name, config in self.workflows_config.get('workflows', {}).items():
            workflows.append({
                'name': name,
                'description': config.get('description', ''),
                'inputs': config.get('input_schema', {}),
                'outputs': config.get('output_schema', {})
            })
        return workflows

    def list_providers(self) -> List[Dict]:
        """
        List available providers.

        Returns:
            List of provider info
        """
        providers = []
        for name, config in self.providers_config.get('providers', {}).items():
            providers.append({
                'name': name,
                'display_name': config.get('name', name),
                'type': config.get('type', 'remote'),
                'models': [m.get('name') for m in config.get('models', [])]
            })
        return providers

    def validate_workflow_inputs(self, workflow_name: str, inputs: Dict) -> Tuple[bool, List[str]]:
        """
        Validate inputs for a workflow.

        Args:
            workflow_name: Workflow name
            inputs: Input data

        Returns:
            Tuple of (is_valid, list of errors)
        """
        workflows = self.workflows_config.get('workflows', {})

        if workflow_name not in workflows:
            return False, [f"Unknown workflow: {workflow_name}"]

        workflow = workflows[workflow_name]
        schema = workflow.get('input_schema', {})
        errors = []

        # Check required inputs
        for key, type_spec in schema.items():
            is_optional = type_spec.endswith('?')
            field_type = type_spec.rstrip('?')

            if not is_optional and key not in inputs:
                errors.append(f"Missing required input: {key}")

            if key in inputs:
                # Basic type checking
                value = inputs[key]
                if field_type == 'string' and not isinstance(value, str):
                    errors.append(f"Input '{key}' must be a string")
                elif field_type == 'array' and not isinstance(value, list):
                    errors.append(f"Input '{key}' must be an array")
                elif field_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Input '{key}' must be an object")

        return len(errors) == 0, errors

    def get_workflow_chain(self, chain_name: str) -> List[str]:
        """
        Get workflow chain.

        Args:
            chain_name: Chain name

        Returns:
            List of workflow names in order
        """
        chains = self.workflows_config.get('workflow_chains', {})
        return chains.get(chain_name, [])

    def execute_chain(
        self,
        chain_name: str,
        initial_inputs: Dict,
        provider_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Execute a workflow chain.

        Args:
            chain_name: Chain name
            initial_inputs: Initial input data
            provider_name: Provider to use

        Returns:
            List of outputs from each workflow
        """
        chain = self.get_workflow_chain(chain_name)

        if not chain:
            raise ValueError(f"Unknown workflow chain: {chain_name}")

        results = []
        current_inputs = initial_inputs.copy()

        for workflow_name in chain:
            # Execute workflow
            output = self.execute_workflow(workflow_name, current_inputs, provider_name)
            results.append({
                'workflow': workflow_name,
                'output': output
            })

            # Merge output into inputs for next workflow
            if isinstance(output, dict):
                current_inputs.update(output)

        return results

    def _execute_http_call(
        self,
        provider: LLMProvider,
        prompt: str,
        max_tokens: int,
        temperature: float,
        output_schema: Dict
    ) -> Dict:
        """
        Execute HTTP call to LLM provider.

        Args:
            provider: Provider instance
            prompt: User prompt
            max_tokens: Max tokens
            temperature: Temperature
            output_schema: Expected output schema

        Returns:
            Parsed response
        """
        if not HAS_URLLIB:
            raise RuntimeError("urllib not available for HTTP requests")

        # Get model
        model = self.defaults.get('model', 'gpt-3.5-turbo')
        if provider.models:
            model = provider.models[0]['id']

        # Get request template
        request_format = self.request_formats.get(provider.request_format, {})
        template = request_format.get('template', {})

        # Prepare request payload
        payload = provider.prepare_request(
            prompt,
            model,
            max_tokens,
            temperature,
            template
        )

        # Prepare headers
        headers = provider.prepare_headers()

        # Make HTTP request with retry logic
        retry_count = self.defaults.get('retry_count', 3)
        retry_delay = self.defaults.get('retry_delay', 2)
        timeout = self.defaults.get('timeout', 30)

        for attempt in range(retry_count):
            try:
                # Create request
                request = urllib.request.Request(
                    provider.base_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )

                # Execute request
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    response_data = json.loads(response.read().decode('utf-8'))

                # Extract response
                text, usage = provider.extract_response(response_data)

                # Parse and return
                return self._parse_response(text, output_schema)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else "No error body"

                # Handle rate limiting
                if e.code == 429 and attempt < retry_count - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue

                # Handle other HTTP errors
                raise RuntimeError(
                    f"HTTP {e.code} error from {provider.name}: {error_body}"
                )

            except urllib.error.URLError as e:
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Network error calling {provider.name}: {e.reason}")

            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON response from {provider.name}: {e}")

            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Error calling {provider.name}: {e}")

        raise RuntimeError(f"Failed after {retry_count} attempts")
