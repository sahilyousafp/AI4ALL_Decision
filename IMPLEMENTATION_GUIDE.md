# Ideology Questionnaire Redesign - Implementation Guide

## Quick Start

### For Developers
All changes are backward-incompatible. Update your frontend/backend integration:

```python
# Old API (DEPRECATED)
responses = [0, 1, 1, 0, 1]  # Binary 0/1
score = sum(responses) * 20   # Single 0-100 score

# New API (CURRENT)
responses = [0, 1, 2, 1, 0]   # Tri-option 0/1/2
result = service.interpret_score(responses)
# Returns: {radar_scores: {environment, comfort, economic, social}, lean, interpretation}
```

### API Endpoints

#### GET /api/ideology/questions
Returns 5 questions, each with 3 options.

```json
[
  {
    "id": 1,
    "text": "When considering land-use development...",
    "options": [
      "Economic growth and job creation",
      "Balanced growth with environmental safeguards",
      "Environmental preservation and biodiversity"
    ]
  }
]
```

#### POST /api/ideology/interpret
Request:
```json
{
  "radar_scores": {"environment": 0, "comfort": 0, "economic": 0, "social": 0},
  "lean": "",
  "responses": [0, 1, 2, 1, 0]
}
```

Response:
```json
{
  "radar_scores": {
    "environment": 52,
    "comfort": 68,
    "economic": 48,
    "social": 48
  },
  "lean": "comfort",
  "interpretation": "You prioritize economic growth and convenience..."
}
```

## Scoring Algorithm

### Input Validation
- Exactly 5 responses required (1 per question)
- Each response must be 0, 1, or 2
- Raises ValueError if invalid

### Score Distribution

For each response, points are distributed to 4 categories:

| Response | Environment | Comfort | Economic | Social |
|----------|-------------|---------|----------|--------|
| 0        | 5           | 25      | 10       | 10     |
| 1        | 15          | 15      | 15       | 15     |
| 2        | 25          | 5       | 10       | 10     |

### Normalization
- Raw score per category: Sum across 5 responses
- Max possible per category: 5 × 25 = 125
- Normalized: (raw_score / 125) × 100 = 0-100

### Lean Determination
```
if environment > comfort + 10:
    lean = "environmental"
elif comfort > environment + 10:
    lean = "comfort"
else:
    lean = "balanced"
```

## Integration Examples

### Python Backend Integration

```python
from backend.ideology_agent_service import get_ideology_service

service = get_ideology_service()

# Get questions for frontend
questions = service.get_questions()

# Calculate scores from user responses
responses = [0, 1, 2, 0, 1]  # User selections
result = service.calculate_score(responses)

print(result.radar_scores.environment)  # 0-100
print(result.radar_scores.comfort)      # 0-100
print(result.lean)                      # "environmental" | "balanced" | "comfort"

# Get interpretation
interpretation = service.interpret_score(
    responses,
    use_ollama=False  # Set to True if Ollama is running
)
print(interpretation.interpretation)
```

### Frontend Integration (React/TypeScript)

```typescript
// 1. Fetch questions
const response = await fetch('/api/ideology/questions');
const questions = await response.json();

// 2. Collect user responses [0, 1, or 2 per question]
const responses: number[] = [0, 1, 2, 1, 0];

// 3. Send to backend
const scoreResult = await fetch('/api/ideology/interpret', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    radar_scores: { environment: 0, comfort: 0, economic: 0, social: 0 },
    lean: '',
    responses: responses
  })
});

const result = await scoreResult.json();

// 4. Display results
console.log(result.radar_scores);    // {environment: 52, comfort: 68, ...}
console.log(result.interpretation);  // "You balance both perspectives..."
```

## Response Interpretation

### High Comfort (100 comfort, 20 environment)
- Strong preference for development and economic growth
- Views airport expansion as beneficial
- Secondary concern for environmental impact

### Balanced (60 environment, 60 comfort)
- Values both growth and environmental protection
- Supports development with conditions
- Seeks middle ground on most issues

### High Environment (100 environment, 20 comfort)
- Strong environmental priorities
- Opposed to airport expansion due to ecosystem impact
- Prefers sustainable alternatives

### Mixed Profiles (e.g., 52 environment, 68 comfort)
- Primary lean toward one side (in this case, comfort)
- Secondary consideration for other perspectives
- Nuanced positioning within a dominant viewpoint

## Data Storage

If storing results, capture:
1. **responses**: List of 5 integers (0-2)
2. **radar_scores**: 4 integer values (0-100 each)
3. **lean**: String identifier
4. **timestamp**: When responses were submitted
5. **user_id**: (Optional) For multi-session tracking

Example database schema:
```sql
CREATE TABLE ideology_responses (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(255),
    timestamp DATETIME,
    q1_response INTEGER,  -- 0, 1, or 2
    q2_response INTEGER,
    q3_response INTEGER,
    q4_response INTEGER,
    q5_response INTEGER,
    environment_score INTEGER,  -- 0-100
    comfort_score INTEGER,
    economic_score INTEGER,
    social_score INTEGER,
    lean VARCHAR(20)  -- "environmental", "comfort", "balanced"
);
```

## Debugging

### Common Issues

**Issue**: "Expected 5 responses, got X"
- **Solution**: Check that you're sending exactly 5 responses, one per question

**Issue**: "Response values must be 0, 1, or 2"
- **Solution**: Ensure all responses are integers 0, 1, or 2. No other values allowed.

**Issue**: Scores not in expected range
- **Solution**: Scores are normalized to 0-100. Verify calculation with test data.

**Issue**: Interpretation text is placeholder
- **Solution**: Ollama integration may have failed. Check `use_ollama=False` works as fallback.

### Testing Locally

```python
# Test all response types
service = IdeologyAgentService()

# Comfort-heavy
result = service.calculate_score([0, 0, 0, 0, 0])
assert result.lean == "comfort"

# Environment-heavy
result = service.calculate_score([2, 2, 2, 2, 2])
assert result.lean == "environmental"

# Balanced
result = service.calculate_score([1, 1, 1, 1, 1])
assert result.lean == "balanced"

print("All tests passed!")
```

## Performance Considerations

- Scoring calculation: O(n) where n=5 (constant time)
- No database calls needed for basic scoring
- Ollama integration may add 1-2 seconds latency (optional)
- Frontend rendering: 3 buttons per question (no extra complexity vs 2 options)

## Future Enhancements

Possible extensions:
1. Add question weighting (some questions more important than others)
2. Add sub-categories within the 4 main categories
3. Generate custom graphics based on radar scores
4. Compare user profile against demographic aggregates
5. Track score changes over time
6. Add question explanations/context
7. Export results as PDF report
