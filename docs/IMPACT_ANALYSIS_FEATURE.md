# Impact Analysis & Decision Support System

**Status:** Implemented  
**Type:** Predictive Analytics Layer  
**Purpose:** PREDICT → SIMULATE → EXPLAIN → ACT

---

## Overview

This feature adds intelligent decision support to ClusterCloud's incident response system. When a node failure occurs, the system now:

1. **Analyzes cascade impact** using actual system relationships
2. **Simulates counterfactual scenarios** (DO_NOTHING vs RECOVER_NOW)
3. **Calculates decision windows** with urgency levels
4. **Generates AI explanations** of recommendations
5. **Provides one-click recovery execution**

---

## 1. CASCADE IMPACT ENGINE

**File:** `apps/api/domains/impact/cascade_analyzer.py`

**Purpose:** Trace downstream effects of incidents using real database relationships.

**Flow:**
```
Node Failure
  ↓
Affected Tasks (query: tasks WHERE node_id = failed_node)
  ↓
Affected Jobs (query: jobs WHERE job_id IN affected_task_job_ids)
  ↓
Deadline Risks (calculate: remaining_time vs estimated_completion)
  ↓
Customer Impact (assess: percentage of job affected)
```

**Key Methods:**
- `analyze_node_failure(node_id)` - Full cascade analysis
- `analyze_incident(incident)` - Analysis from existing incident
- `_estimate_task_duration(task)` - Deterministic time estimates
- `_assess_deadline_risk(job, deadline, delay)` - Risk calculation
- `_assess_customer_impact(job, impact)` - Customer-level effects

**Output Example:**
```json
{
  "affected_node": { "node_id": "...", "name": "...", "status": "UNHEALTHY" },
  "affected_tasks": [
    {
      "task_id": "...",
      "job_id": "...",
      "estimated_completion_minutes": 5.0
    }
  ],
  "affected_jobs": [...],
  "estimated_delay_minutes": 45.0,
  "deadline_risks": [
    {
      "job_id": "...",
      "risk_level": "HIGH",
      "slack_minutes": -15.0
    }
  ],
  "cascade_chain": [
    { "step": "node_failure", "description": "Node failed", "timestamp": "..." },
    { "step": "tasks_affected", "description": "18 tasks interrupted", "timestamp": "..." },
    { "step": "deadline_risk", "description": "2 jobs at deadline risk", "timestamp": "..." }
  ]
}
```

**Important:** Uses ONLY real relationships from database. Does not fabricate dependencies.

---

## 2. COUNTERFACTUAL SIMULATION ENGINE

**File:** `apps/api/domains/simulation/scenario_simulator.py`

**Purpose:** Simulate future outcomes WITHOUT mutating production state.

**Scenarios:**

### A. DO_NOTHING Scenario
Simulates passive response - tasks remain unassigned until timeout.

**Timeline:**
```
T+0:  Node failure detected
T+5:  Tasks approaching timeout
T+9:  Job delays visible
T+14: Deadline breaches (if applicable)
T+19: Eventual timeout recovery (manual intervention)
```

**Estimates:**
- Completion time: ~19 minutes
- Deadline breaches: Variable (depends on job deadlines)
- Cost: Normal cost + 50% delay penalty
- Impact: HIGH to SEVERE

### B. RECOVER_NOW Scenario
Simulates immediate recovery action - tasks reassigned to healthy nodes.

**Timeline:**
```
T+0:   Node failure detected
T+0.5: AI recommendation generated
T+2:   Replacement nodes found
T+3:   Tasks reassigned
T+4:   Execution resumed
T+6:   Cluster stable
```

**Estimates:**
- Completion time: ~6 minutes
- Deadline breaches: Minimal (usually 0)
- Cost: Normal cost + 10% recovery overhead
- Impact: LOW to MEDIUM

### Comparison Output

```json
{
  "scenarios": {
    "do_nothing": { /* detailed timeline and estimates */ },
    "recover_now": { /* detailed timeline and estimates */ }
  },
  "comparison": {
    "time_saved_minutes": 13.0,
    "deadline_delta": 2,  // Breaches prevented
    "cost_delta_clstr": 80.0,
    "recommended_action": "RECOVER_NOW"
  },
  "recommendation": {
    "action": "RECOVER_NOW",
    "reason": "Recovery saves 13 minutes and prevents 2 deadline breaches",
    "confidence": "HIGH"
  }
}
```

**Key Methods:**
- `simulate_do_nothing(node_id, affected_task_ids)` - Passive scenario
- `simulate_recovery(node_id, affected_task_ids)` - Active recovery
- `compare_scenarios(node_id, affected_task_ids)` - Side-by-side comparison
- `_load_tasks_snapshot(task_ids)` - Read-only state clone
- `_load_jobs_for_tasks(tasks)` - Related job state

**Critical:** All simulation is IN-MEMORY. Production database is NEVER mutated.

---

## 3. DECISION WINDOW CALCULATOR

**File:** `apps/api/domains/impact/decision_window.py`

**Purpose:** Calculate time-sensitive decision urgency.

**Formula:**
```
Base Window = 120 seconds

Factors:
- Task Count: More tasks = less time (×0.7 if >10 tasks)
- Available Capacity: No capacity = urgent (×0.3)
- Deadline Proximity: Close deadline = urgent (×0.5)
- Task Timeout Risk: Cap at 70% of timeout threshold
```

**Urgency Levels:**
- **CRITICAL:** < 60 seconds
- **HIGH:** 60-90 seconds
- **MEDIUM:** 90-180 seconds
- **LOW:** > 180 seconds

**Output Example:**
```json
{
  "decision_window_seconds": 74,
  "urgency_level": "HIGH",
  "urgency_reason": "Limited replacement capacity",
  "factors": {
    "affected_tasks": 18,
    "available_replacement_nodes": 2,
    "time_until_task_timeout_seconds": 180,
    "deadline_risk": true
  },
  "after_window_impact": {
    "expected_impact": "HIGH",
    "description": "Partial capacity available. Extended recovery time.",
    "estimated_additional_delay_minutes": 90,
    "recovery_difficulty": "MEDIUM"
  },
  "recommendation": "Immediate recovery recommended"
}
```

**Key Methods:**
- `calculate_for_node_failure(node_id, task_ids)` - Calculate window
- `calculate_for_incident(incident)` - Window from incident
- `_count_available_nodes(exclude_node_id)` - Capacity check
- `_check_deadline_proximity(task_ids)` - Deadline urgency
- `_calculate_post_window_impact(task_count, capacity)` - After-window effects

---

## 4. AI EXPLANATION LAYER

**File:** `apps/api/domains/impact/router.py` (function `_generate_explanation`)

**Purpose:** Generate human-friendly explanations of impact and recommendations.

**Input to AI:**
- Current impact (tasks, jobs, delay)
- DO_NOTHING scenario (time, breaches, cost)
- RECOVER_NOW scenario (time, breaches, cost)
- Decision window (seconds, urgency)

**AI Prompt:**
```
Explain this incident impact and recovery recommendation in clear, customer-friendly language.

CURRENT IMPACT:
- 18 tasks affected
- 2 jobs impacted
- Estimated delay: 45 minutes

DO NOTHING SCENARIO:
- Completion time: 19 minutes
- Deadline breaches: 2
- Cost: 945 CLSTR

RECOVER NOW SCENARIO:
- Completion time: 6 minutes
- Deadline breaches: 0
- Cost: 865 CLSTR

DECISION WINDOW: 74 seconds
URGENCY: HIGH

Provide a concise 2-3 sentence explanation...
```

**Example Output:**
> "Node-03's failure has interrupted 18 tasks across 2 customer jobs. Without action, tasks will timeout causing 2 deadline breaches and costing 945 CLSTR. Recovering now limits the impact to 6 minutes and saves 80 CLSTR while preventing all deadline breaches."

**Important:**
- AI explains DETERMINISTIC simulation results
- AI does NOT fabricate numbers
- Falls back gracefully if unavailable

---

## 5. API ENDPOINTS

**File:** `apps/api/domains/impact/router.py`

### GET `/api/impact/node-failure/{node_id}/analysis`

Complete impact analysis for node failure.

**Returns:**
- Cascade impact chain
- DO_NOTHING vs RECOVER_NOW scenarios
- Decision window with countdown
- AI explanation (if available)

### GET `/api/impact/incident/{incident_id}/analysis`

Complete impact analysis for existing incident.

**Returns:** Same as node-failure endpoint

### POST `/api/impact/incident/{incident_id}/execute-recovery`

Execute recovery for incident.

**Important:** Calls existing `RecoveryService.recover_from_node_failure()` - does NOT duplicate recovery logic.

**Returns:**
```json
{
  "incident_id": "...",
  "recovery_executed": true,
  "result": { /* RecoveryService result */ },
  "message": "Recovery initiated using existing RecoveryService"
}
```

---

## 6. FRONTEND VISUALIZATION

**File:** `apps/web/src/components/demo/ImpactAnalysisPanel.tsx`

**Features:**

### Critical Incident Header
- Urgency badge (CRITICAL/HIGH/MEDIUM/LOW)
- Node status
- Color-coded by urgency

### Current Impact Section
- Affected tasks count
- Affected jobs count
- Estimated delay

### Decision Window Display
- Live countdown timer
- Urgency reason
- After-window impact warning

### Scenario Comparison
Side-by-side visualization:

**DO_NOTHING:**
- Timeline events (T+5m, T+9m, T+14m, T+19m)
- Final delay time
- Deadline breaches
- Cost estimate
- Red/warning styling

**RECOVER_NOW:**
- Timeline events (T+0.5m, T+2m, T+3m, T+6m)
- Final delay time
- Deadline breaches prevented
- Cost estimate
- Green/success styling

### Recovery Impact Summary
- Time saved
- Breaches prevented
- Cost savings
- Visual comparison chart

### AI Recommendation
- Purple accent card
- Confidence level badge
- Plain-language explanation
- Action reasoning

### Execute Recovery Button
- Large, prominent
- Calls `/api/impact/incident/{id}/execute-recovery`
- Shows loading state during execution
- Note: "Calls existing RecoveryService"

---

## Integration Points

### Reuses Existing Components

**1. RecoveryService (Phase 7)**
- Impact analysis does NOT duplicate recovery logic
- Execute button calls `RecoveryService.recover_from_node_failure()`
- Maintains single source of truth

**2. AI Agents (Phase 8)**
- Uses existing BedrockClient
- Falls back gracefully if unavailable
- AI explains deterministic results (does not generate data)

**3. Database Models**
- Uses existing Incident, Task, Job, Node models
- Read-only queries for simulation
- No new tables required

**4. WebSocket Events**
- Hooks into existing event system
- Real-time updates for recovery progress
- No new event types needed

---

## Demo Flow

1. **Start job** - Customer submits 20-frame rendering job
2. **Distribute tasks** - Tasks assigned across 3 nodes
3. **Monitor execution** - Real-time progress updates
4. **Trigger failure** - Click "Simulate Node Failure"
5. **Impact analysis loads** - Cascade analysis appears
6. **Decision window starts** - Countdown begins (74 seconds)
7. **Scenarios displayed** - DO_NOTHING vs RECOVER_NOW side-by-side
8. **AI explains** - Plain-language recommendation
9. **Click "EXECUTE RECOVERY"** - Calls existing RecoveryService
10. **Watch recovery** - Tasks reassigned, job continues
11. **Complete** - Job finishes successfully

---

## Key Design Principles

### 1. No Duplicate Logic
- Recovery execution uses existing `RecoveryService`
- Does not reimplement task reassignment
- Single source of truth

### 2. No Production Mutation
- Simulation clones state in-memory
- All projections are deterministic calculations
- Database never touched during "what-if" analysis

### 3. AI as Explainer, Not Decider
- AI explains deterministic simulation results
- AI does not generate numerical predictions
- All numbers come from simulation engine

### 4. Transparent Simulation
- Simple, understandable formulas
- No black-box ML predictions
- Clear assumptions documented

### 5. Real Relationships Only
- Cascade analysis uses actual DB foreign keys
- No invented dependencies
- Deterministic from current state

---

## Testing Suggestions

### Unit Tests
```python
# Test cascade analyzer
def test_cascade_analysis_identifies_affected_tasks()
def test_deadline_risk_assessment()
def test_customer_impact_calculation()

# Test scenario simulator
def test_do_nothing_scenario_timeline()
def test_recovery_scenario_timeline()
def test_comparison_calculations()

# Test decision window
def test_window_calculation_with_no_capacity()
def test_window_reduction_for_deadlines()
def test_urgency_level_classification()
```

### Integration Tests
```python
def test_full_impact_analysis_endpoint()
def test_execute_recovery_calls_recovery_service()
def test_ai_explanation_fallback_when_unavailable()
```

### Demo Verification
1. Start 3 nodes
2. Submit 30-frame job
3. Wait for 10 frames to complete
4. Kill one node manually
5. Verify impact analysis appears
6. Verify countdown starts
7. Verify scenarios calculated correctly
8. Click execute recovery
9. Verify recovery service called
10. Verify job completes

---

## Limitations & Future Work

### MVP Limitations
- Simple time estimates (not ML-based)
- Decision window formula is heuristic
- No real-world validation of predictions
- Assumes homogeneous task complexity

### Future Enhancements
- Historical data for better time estimates
- ML-based prediction models
- Multi-node failure scenarios
- Capacity planning simulation
- Cost optimization what-if analysis
- SLA breach probability calculations

---

## Files Changed

### Backend
- `apps/api/domains/impact/cascade_analyzer.py` (NEW)
- `apps/api/domains/impact/decision_window.py` (NEW)
- `apps/api/domains/impact/router.py` (NEW)
- `apps/api/domains/impact/__init__.py` (NEW)
- `apps/api/domains/simulation/scenario_simulator.py` (NEW)
- `apps/api/domains/simulation/__init__.py` (NEW)
- `apps/api/main.py` (MODIFIED - added impact router)

### Frontend
- `apps/web/src/components/demo/ImpactAnalysisPanel.tsx` (NEW)
- `apps/web/src/app/demo/page.tsx` (MODIFIED - integrated panel)

### Documentation
- `docs/IMPACT_ANALYSIS_FEATURE.md` (NEW - this file)

---

**This feature dramatically enhances ClusterCloud's intelligence without adding unnecessary complexity or duplicate code. It provides clear, actionable insights for incident response.**
