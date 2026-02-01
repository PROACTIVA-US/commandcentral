# Software Documentation Skill

Standards for code documentation, including FedRAMP-compliant security annotations.

## When to Use

- Writing new code (any language)
- Reviewing code for documentation completeness
- Adding security-sensitive functionality
- Generating API documentation
- Creating changelogs

## Module-Level Documentation

Every Python module should have:

```python
"""
Module: filename.py
Purpose: Brief description of what this module does

Security Classification: CUI | Public | Internal
FedRAMP Controls: SC-XX, AU-XX (if security-relevant)
"""
```

For TypeScript/JavaScript:

```typescript
/**
 * @module filename
 * @description Brief description
 * @security CUI | Public | Internal
 */
```

## Class Documentation

```python
class ServiceName:
    """
    Brief description of the class.

    Attributes:
        attr_name: Description of attribute
        another_attr: Another description

    Security:
        - Relevant security considerations
        - FedRAMP control references if applicable

    Example:
        >>> service = ServiceName()
        >>> service.do_thing()
    """
```

## Function Documentation

```python
def function_name(param: Type, other: OtherType) -> ReturnType:
    """
    Brief description of what this function does.

    Args:
        param: Description of parameter
        other: Description of other parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Security:
        - Only include if security-relevant
        - Reference specific FedRAMP controls

    Example:
        >>> result = function_name("input", other_value)
    """
```

## When Security Section is Required

Include a `Security:` section in docstrings when code:

| Category | Examples |
|----------|----------|
| Authentication | Login, logout, session management |
| Authorization | Permission checks, role validation |
| User Input | Form processing, API parameters |
| Sensitive Data | PII, financial data, credentials |
| Cryptography | Encryption, hashing, signing |
| Network | HTTP requests, WebSocket, external APIs |
| Storage | Database writes, file I/O |
| Shell | subprocess, os.system, exec |

## FedRAMP Control Reference

Common controls to reference:

| Control | Description | When to Reference |
|---------|-------------|-------------------|
| SC-28 | Protection of Information at Rest | Encryption at rest |
| SC-8 | Transmission Confidentiality | Encryption in transit |
| SC-13 | Cryptographic Protection | Crypto operations |
| AU-3 | Content of Audit Records | Logging |
| AU-6 | Audit Review, Analysis | Log analysis |
| IA-2 | Identification and Authentication | Auth flows |
| AC-3 | Access Enforcement | Authorization |
| SI-10 | Information Input Validation | Input validation |

## Complete Example

```python
"""
Module: tiered_memory_service.py
Purpose: Manages tiered memory storage with hot/warm/cold/archive tiers

Security Classification: CUI
FedRAMP Controls: SC-28 (encryption), AU-3 (logging)
"""

from typing import Optional
from dataclasses import dataclass

@dataclass
class MemoryEntry:
    """
    Represents a memory entry in the tiered storage system.

    Attributes:
        id: Unique identifier for the entry
        content: The actual memory content
        tier: Current storage tier (hot, warm, cold, archive)

    Security:
        - Content encrypted before storage (SC-28)
        - Access logged for audit trail (AU-3)
    """
    id: str
    content: str
    tier: str


class TieredMemoryService:
    """
    Service for managing memory entries across storage tiers.

    Provides automatic promotion/demotion based on access patterns
    and ensures all data is encrypted at rest.

    Security:
        - All data encrypted at rest using AES-256 (SC-28)
        - All access operations logged (AU-3)
        - Supports audit export for FedRAMP compliance (AU-6)
    """

    def store(self, content: str, metadata: Optional[dict] = None) -> str:
        """
        Store content in the hot tier.

        Args:
            content: The content to store
            metadata: Optional metadata to associate with entry

        Returns:
            The unique ID of the stored entry

        Raises:
            StorageError: If encryption or storage fails
            ValidationError: If content exceeds size limits

        Security:
            - Validates input size before processing (SI-10)
            - Encrypts content before write (SC-28)
            - Logs storage operation (AU-3)
        """
        ...

    def retrieve(self, entry_id: str, requester: str) -> Optional[MemoryEntry]:
        """
        Retrieve an entry by ID.

        Args:
            entry_id: The unique ID of the entry
            requester: Identity of the requester for audit

        Returns:
            The memory entry if found, None otherwise

        Security:
            - Validates requester authorization (AC-3)
            - Logs retrieval with requester identity (AU-3)
            - Decrypts content on retrieval (SC-28)
        """
        ...
```

## CHANGELOG Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature description (#issue-number)

### Changed
- Modification to existing functionality

### Deprecated
- Features scheduled for removal

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Vulnerability fixes (reference CVE if applicable)
```

## API Documentation

For REST APIs, document:

```python
@router.post("/memories", response_model=MemoryResponse)
async def create_memory(
    request: MemoryCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new memory entry.

    **Endpoint:** POST /api/v1/memories

    **Request Body:**
    - content (str): The memory content (max 10000 chars)
    - metadata (dict, optional): Additional metadata

    **Response:**
    - 201: Memory created successfully
    - 400: Invalid request body
    - 401: Authentication required
    - 403: Insufficient permissions

    **Security:**
    - Requires authentication (IA-2)
    - Content validated and sanitized (SI-10)
    - Creates audit log entry (AU-3)
    """
```

## Documentation Triggers

| Event | Documentation Generated |
|-------|------------------------|
| PR Merge | Docstrings, CHANGELOG, API docs, security notes |
| Release | Version bump, release notes, migration guide |
| Continuous | ADRs, plan updates, master plan sync |

## Quick Checklist

Before completing code:

- [ ] Module-level docstring present?
- [ ] All public functions documented?
- [ ] All public classes documented?
- [ ] Type hints on all parameters/returns?
- [ ] Security section where needed?
- [ ] Examples for complex functions?
- [ ] CHANGELOG updated if user-facing?

---

*Well-documented code is maintainable code. Security documentation enables compliance.*
