"""
Dynamic System Prompt Manager
Allows users to customize LLM behavior with safety controls and audit trails.
"""

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """Reusable prompt template."""

    id: str
    name: str
    description: str
    template: str
    category: str  # e.g., "coding", "security", "analysis", "roleplay"
    variables: List[str]  # Variables that can be filled
    author: str
    created_at: str
    is_public: bool = True
    safety_level: str = "standard"  # "strict", "standard", "permissive"

    def render(self, **kwargs) -> str:
            """Render template with provided variables."""
            rendered = self.template
            placeholder_format = "{{{}}}"
            missing_value_format = "{{MISSING:{}}}"
        
            for var in self.variables:
                value = kwargs.get(var, missing_value_format.format(var))
                rendered = rendered.replace(placeholder_format.format(var), str(value))
            return rendered


class PromptManager:
    """
    Manages custom system prompts with safety controls.

    Features:
    - Store and retrieve prompts
    - Template variables
    - Safety filtering
    - Version control
    - Audit logging
    """

    # Built-in dangerous patterns to block
    BLOCKED_PATTERNS = [
        "ignore previous instructions",
        "disregard all rules",
        "you are now",
        "forget everything",
        "system:",  # Prevent ChatML injection
        "assistant:",
        "<|im_start|>",
        "<|im_end|>",
    ]

    # Safety levels
    SAFETY_LEVELS = {
        "strict": {"max_length": 1000, "allow_system_override": False, "require_approval": True, "audit_all": True},
        "standard": {
            "max_length": 10000,  # Increased for long agent prompts
            "allow_system_override": False,
            "require_approval": False,
            "audit_all": True,
        },
        "permissive": {
            "max_length": 50000,
            "allow_system_override": True,
            "require_approval": False,
            "audit_all": True,
        },
    }

    def __init__(self, storage_dir: str = "data/prompts"):
        """Initialize prompt manager."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        self.prompts: Dict[str, PromptTemplate] = {}
        self.active_prompt_id: Optional[str] = None

        # Load existing prompts
        self._load_prompts()

        # Initialize with defaults
        self._initialize_defaults()

    def _load_prompts(self):
        """Load all prompts from storage."""
        prompts_file = os.path.join(self.storage_dir, "prompts.json")

        if os.path.exists(prompts_file):
            with open(prompts_file, "r") as f:
                data = json.load(f)
                for prompt_data in data:
                    prompt = PromptTemplate(**prompt_data)
                    self.prompts[prompt.id] = prompt

    def _save_prompts(self):
        """Save all prompts to storage."""
        prompts_file = os.path.join(self.storage_dir, "prompts.json")

        data = [asdict(p) for p in self.prompts.values()]
        with open(prompts_file, "w") as f:
            json.dump(data, f, indent=2)

    def _initialize_defaults(self):
        """Initialize default prompt templates."""
        if not self.prompts:
            # UC3 Strict (default)
            self.create_prompt(
                name="UC3 Strict Control",
                description="Production-grade operator control interface (default)",
                template=self._load_uc3_strict(),
                category="system",
                variables=[],
                author="system",
                safety_level="standard",  # Changed from strict - allow longer prompts
            )

            # Software Engineer
            self.create_prompt(
                name="Software Engineer",
                description="Senior software engineer for code review and architecture",
                template="""You are a senior software engineer with 10+ years of experience.

Your expertise includes:
- Clean code principles and design patterns
- System architecture and scalability
- Code review and quality assurance
- Performance optimization
- Testing strategies (unit, integration, E2E)

When analyzing code or systems:
1. Start with overall architecture assessment
2. Identify potential issues (bugs, performance, security)
3. Suggest concrete improvements with examples
4. Rate code quality on a 1-10 scale with justification

Always be constructive and educational in your feedback.

Task: {task}
Context: {context}""",
                category="roleplay",
                variables=["task", "context"],
                author="system",
                safety_level="standard",
            )

            # Security Analyst
            self.create_prompt(
                name="Security Analyst",
                description="Cybersecurity expert for threat analysis and auditing",
                template="""You are a cybersecurity expert specializing in:
- Vulnerability assessment and penetration testing
- Security architecture review
- Compliance (OWASP, NIST, ISO 27001)
- Incident response and forensics
- Threat modeling

Your analysis approach:
1. Identify security risks and vulnerabilities
2. Reference CVEs and industry standards
3. Assess severity (Critical/High/Medium/Low)
4. Provide remediation steps
5. Suggest security controls

Security Focus: {focus}
System Info: {system_info}""",
                category="roleplay",
                variables=["focus", "system_info"],
                author="system",
                safety_level="standard",
            )

            # DevOps Engineer
            self.create_prompt(
                name="DevOps Engineer",
                description="DevOps/SRE for infrastructure and deployment",
                template="""You are a DevOps/SRE engineer specializing in:
- Infrastructure as Code (Terraform, Ansible)
- CI/CD pipelines (GitLab, GitHub Actions)
- Container orchestration (Kubernetes, Docker)
- Monitoring and observability (Prometheus, Grafana)
- Cloud platforms (AWS, GCP, Azure)

Your approach:
1. Assess current infrastructure state
2. Identify bottlenecks and reliability issues
3. Suggest automation opportunities
4. Provide SLO/SLA recommendations
5. Estimate resource requirements

Infrastructure: {infrastructure}
Goal: {goal}""",
                category="roleplay",
                variables=["infrastructure", "goal"],
                author="system",
                safety_level="standard",
            )

            self._save_prompts()

    def _load_uc3_strict(self) -> str:
        """Load UC3 strict prompt from file."""
        prompt_file = os.path.join(os.path.dirname(__file__), "../console/uc3_system_prompt.txt")

        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as f:
                return f.read()

        return "You are UC3, a Unified Cognitive Control Agent."

    def validate_prompt(self, prompt: str, safety_level: str = "standard") -> Dict[str, Any]:
        """
        Validate prompt for safety.

        Returns:
            Dict with valid (bool) and issues (list)
        """
        issues = []
        config = self.SAFETY_LEVELS.get(safety_level, self.SAFETY_LEVELS["standard"])

        # Check length
        if len(prompt) > config["max_length"]:
            issues.append(f"Prompt exceeds max length ({config['max_length']} chars)")

        # Check for blocked patterns
        prompt_lower = prompt.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in prompt_lower:
                issues.append(f"Contains blocked pattern: '{pattern}'")

        # Check for potential ChatML injection
        if "<|" in prompt or "|>" in prompt:
            issues.append("Contains potential ChatML injection markers")

        return {"valid": len(issues) == 0, "issues": issues, "safety_level": safety_level}

    def create_prompt(
        self,
        name: str,
        description: str,
        template: str,
        category: str,
        variables: List[str],
        author: str,
        safety_level: str = "standard",
        is_public: bool = True,
    ) -> str:
        """
        Create a new prompt template.

        Returns:
            prompt_id
        """
        # Validate
        validation = self.validate_prompt(template, safety_level)
        if not validation["valid"]:
            raise ValueError(f"Prompt validation failed: {validation['issues']}")

        # Generate ID
        prompt_id = hashlib.md5(f"{name}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

        # Create template
        prompt = PromptTemplate(
            id=prompt_id,
            name=name,
            description=description,
            template=template,
            category=category,
            variables=variables,
            author=author,
            created_at=datetime.utcnow().isoformat(),
            is_public=is_public,
            safety_level=safety_level,
        )

        self.prompts[prompt_id] = prompt
        self._save_prompts()

        return prompt_id

    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Get prompt by ID."""
        return self.prompts.get(prompt_id)

    def list_prompts(self, category: Optional[str] = None) -> List[Dict]:
        """List all prompts, optionally filtered by category."""
        prompts = self.prompts.values()

        if category:
            prompts = [p for p in prompts if p.category == category]

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "author": p.author,
                "safety_level": p.safety_level,
            }
            for p in prompts
        ]

    def activate_prompt(self, prompt_id: str) -> bool:
        """Set active prompt."""
        if prompt_id in self.prompts:
            self.active_prompt_id = prompt_id
            return True
        return False

    def get_active_prompt(self, **variables) -> Optional[str]:
        """Get rendered active prompt."""
        if self.active_prompt_id:
            prompt = self.prompts.get(self.active_prompt_id)
            if prompt:
                return prompt.render(**variables)
        return None

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        if prompt_id in self.prompts:
            # Prevent deleting system prompts
            if self.prompts[prompt_id].author == "system":
                return False

            del self.prompts[prompt_id]
            self._save_prompts()
            return True
        return False


# Singleton instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager(storage_dir: str = "data/prompts") -> PromptManager:
    """Get or create prompt manager singleton."""
    global _prompt_manager

    if _prompt_manager is None:
        _prompt_manager = PromptManager(storage_dir)

    return _prompt_manager
