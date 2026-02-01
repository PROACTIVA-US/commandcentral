# RLM Decomposition Skill

**Category**: architecture  
**When to use**: Complex reasoning over large corpora, O(n) or O(n²) tasks, cross-referencing multiple documents

## The Problem

Standard LLMs fail catastrophically on complex tasks over large contexts:

| Context | Task | Success Rate |
|---------|------|--------------|
| 32k tokens | O(n²) reasoning | **0.04%** |
| 1M tokens | Complex synthesis | **~0%** |

"Attention is not all you need."

## The Solution: RLM Pattern

```
Root LLM (Sonnet) → Generates Python Code → Code Spawns Sub-LLMs (Haiku) → Deterministic Aggregation
```

1. **Root LLM** = Meta-programmer (writes decomposition strategy)
2. **Symbolic Layer** = Python (guarantees logical coherence)
3. **Sub-LLMs** = Cheap extractors (don't reason, just parse)

### Results After Applying This Pattern

| Context | Task | Success Rate |
|---------|------|--------------|
| 32k tokens | O(n²) reasoning | **58%** |
| 1M tokens | Complex synthesis | **~50%** |

**1000x improvement for 2x cost.**

## When to Use RLM

### Use RLM When:
- Task requires reasoning across many documents
- Complexity is O(n) with n > 10
- Complexity is O(n²) with any n > 3
- Keywords: "all pairs", "cross-reference", "correlate", "compare each"

### Don't Use RLM When:
- Simple retrieval (needle in haystack)
- Small corpus (< 5 chunks)
- Single-document tasks

## Complexity Detection

```python
COMPLEXITY_PATTERNS = {
    "O(1)": ["find the", "what is the", "retrieve", "lookup"],
    "O(n)": ["summarize all", "list every", "for each document"],
    "O(n²)": ["find all pairs", "cross-reference", "correlate", "relationships between"],
}
```

## Implementation Pattern

### 1. Generate Decomposition Strategy

```python
prompt = f"""You are a meta-programmer. Write Python code to solve this task.

Task: {task}
Corpus: {n_chunks} chunks

Available functions:
- extract(chunk, instruction) -> str  # Sub-LLM call
- extract_all(chunks, instruction) -> list[str]  # Parallel
- combine(results, method) -> str  # Aggregate

Write code that decomposes the task appropriately.
Assign final answer to `result` variable.
"""

strategy_code = await root_llm.complete(prompt)
```

### 2. Execute with Sub-LLMs

```python
async def extract(chunk: str, instruction: str) -> str:
    """Sub-LLM (Haiku) extracts specific info. No reasoning."""
    return await haiku.complete(f"Extract: {instruction}\n\nText: {chunk}")

# Execute generated code
exec(strategy_code, {"extract": extract, "chunks": corpus})
result = locals()["result"]
```

### 3. Synthesize Results

```python
final_answer = await root_llm.complete(f"""
    Task: {task}
    Sub-results: {aggregated_results}
    
    Synthesize the final answer.
""")
```

## Example: O(n²) Task

**Task**: "Find all pairs of companies that are partners"

**Generated Strategy**:
```python
# Extract partnerships from each chunk
partnerships = await extract_all(chunks, "List company partnerships mentioned")

# Parse into structured format
pairs = []
for p in partnerships:
    # Extract pairs from each result
    extracted = parse_partnerships(p)
    pairs.extend(extracted)

# Deduplicate
result = list(set(pairs))
```

**Result**: Correct pairings found in 11 sub-calls, 17.4s

## Cost Model

| Corpus Size | Complexity | Sub-Calls | Est. Cost |
|-------------|------------|-----------|-----------|
| 10 chunks | O(n) | 10 | $0.01 |
| 50 chunks | O(n) | 50 | $0.05 |
| 50 chunks | O(n²) | 1,225 | $1.23 |
| 100 chunks | O(n²) | 4,950 | $4.95 |

**Key**: The cost is predictable and the result is reliable. Standard LLM would fail completely at these scales.

## Integration with CC2

```python
# In AgentService
if ComplexityAnalyzer.detect(task, corpus_size)["class"] in ["O(n²)"]:
    return await self._run_with_rlm(task, corpus, session)
```

## References

- MIT RLM Paper: arXiv:2512.24601
- CC2 Architecture: `docs/architecture/RLM-NATIVE-COMMANDCENTER.md`
- Prototype: `experiments/rlm_prototype.py`
- Results: `experiments/RESULTS-rlm-prototype.md`

---

*"The LLM provides the strategic 'what,' and the code provides the deterministic 'how.'"*
