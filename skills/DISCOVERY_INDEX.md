# Skills Discovery Index

> Auto-generated from skill front matter. Do not edit directly.
> Run `python scripts/generate-skill-index.py` to regenerate.

| Skill | Description | Priority |
|-------|-------------|----------|
| lessons | Hard-won lessons and anti-patterns - mistakes that wasted ho... | P0 |
| operations | How to run CommandCenter V3 - startup, execution modes, pipe... | P0 |
| patterns | Code patterns that work in CommandCenter - frontend and agen... | P1 |
| cc3-autonomous-pipeline | "Operational knowledge for CommandCenter V3 autonomous execu... | P2 |

**Total Skills:** 4

## Usage

```python
from app.tools.skill_tools import search_skills, load_skill

# Search by keyword (returns summaries)
results = search_skills('pipeline')

# Load full content when needed
content = load_skill('operations')
```