# ClusterCloud - 3-Minute Explainer Video Script

**Duration:** 3 minutes  
**Format:** Code walkthrough with architecture explanation

---

## COMPLETE SCRIPT

### [0:00 - 0:25] INTRODUCTION & PROBLEM

"Hi, I'm going to walk you through ClusterCloud—a distributed compute marketplace with AI-powered automatic failure recovery.

The problem is simple: 3D rendering studios and game developers need massive compute power, but only for short bursts. A single animated film can require 100 million CPU hours. Traditional cloud providers are expensive and rigid. ClusterCloud solves this by creating a marketplace where anyone can share spare compute capacity—gaming PCs, crypto miners, over-provisioned cloud instances.

Let me show you how it works by walking through the code and architecture."

---

### [0:25 - 0:55] ARCHITECTURE OVERVIEW

"The system has three main layers.

At the top, customers use our Next.js web application to submit rendering jobs. They specify requirements—frame count, resolution, deadline, budget—and the system handles everything else.

In the middle, we have the FastAPI control plane. This is the brain of the system. It's a modular monolith that handles job orchestration, task scheduling, failure detection, recovery, and economic settlement. All state persists in a database—SQLite for the demo, PostgreSQL for production.

At the bottom, we have the distributed worker network. Community providers run our Python node agent on their machines. These agents register with the control plane, execute tasks, and send heartbeat signals to prove they're alive.

Real-time updates flow through WebSockets so customers see exactly what's happening as their jobs execute."

---

### [0:55 - 1:30] CONTROL PLANE CODE WALKTHROUGH

"Let me show you the control plane code. Opening main.py—this is our FastAPI entry point.

We have six core domain modules. Workloads handles job requirements and type definitions. Jobs and Tasks manages execution state—each job splits into parallelizable tasks. Nodes tracks provider registration and hardware capabilities. Scheduling assigns tasks to compatible nodes using a multi-criteria scoring algorithm. Recovery handles automatic failure recovery. And Ledger manages the CLSTR token economics.

Looking at the scheduler code—here's the algorithm. We filter nodes by compatibility first: does the node have enough CPU, RAM, and GPU? Then we score each compatible node on three factors: reliability gets 40% weight, cost gets 30%, and available capacity gets 30%. We sort by score and select the best nodes.

This is deterministic—same inputs always produce the same output. No randomness, fully predictable."

---

### [1:30 - 2:05] AI ORCHESTRATION LAYER

"Here's the key innovation: the AI Orchestration Layer.

We integrate with AWS Bedrock using Claude Sonnet 3.5 for intelligent recommendations. We have three specialized agents.

Opening workload_agent.py—the Workload Analysis Agent examines customer requirements and estimates compute time, parallelization potential, and resource needs.

The Provider Recommendation Agent suggests optimal node combinations based on capabilities, cost, and reliability history.

Opening recovery_agent.py—the Recovery Agent recommends replacement nodes when failures occur. It analyzes affected tasks, identifies compatible nodes, and suggests the best recovery strategy.

But here's what's critical: every AI recommendation goes through our Deterministic Validator. The AI suggests, the validator enforces hard constraints—budget limits, hardware compatibility, capacity checks. If AWS Bedrock isn't available, the system automatically falls back to pure deterministic algorithms. AI enhances decisions but never breaks guarantees."

---

### [2:05 - 2:35] DISTRIBUTED EXECUTION & FAILURE RECOVERY

"Now the distributed execution. Opening the node agent code—agent.py.

When a provider starts the agent, it does three things. First, it discovers local hardware—CPU cores, RAM, GPU availability—using cross-platform detection. Second, it registers with the control plane and sends heartbeat signals every 5 seconds. Third, it polls for assigned tasks, executes them in isolated processes with resource limits, and returns results.

Tasks execute independently with restricted filesystem access and memory limits. If a node crashes, it only affects its own tasks.

Now the automatic recovery—this is the magic. Opening failure_detector.py and recovery_service.py.

The failure detector monitors heartbeats. If a node misses three consecutive heartbeats—that's 15 seconds—it's marked unhealthy. An incident is created immediately.

The recovery service kicks in. It identifies all tasks that were running on the failed node. It calls the AI Recovery Agent for recommendations, validates them against constraints, and reassigns tasks to healthy replacement nodes. The economic ledger automatically settles: the failed provider loses stake, the customer gets compensated, and the replacement provider earns a bonus.

The entire process—detection to reassignment—takes 30 to 60 seconds with zero human intervention."

---

### [2:35 - 3:00] ECONOMIC SYSTEM & CLOSING

"The economic system uses CLSTR tokens—internal accounting units like AWS credits.

Opening ledger/service.py—every transaction is auditable. Providers earn tokens for successful task completion. They lose tokens for failures through automatic penalties. Customers pay per task with automatic refunds if things go wrong.

The reliability engine tracks provider reputation over time. Higher reliability scores mean more job assignments and better pricing. It creates a self-regulating marketplace where quality providers naturally rise to the top.

Looking at the live dashboard—customers submit jobs through a simple interface, watch real-time progress as tasks distribute across nodes, see automatic recovery happen when failures occur, and get their rendered frames with full economic transparency.

That's ClusterCloud: distributed compute with AI-powered recovery, deterministic guarantees, and economic incentives that align quality with rewards.

Thanks for watching. The complete code is open source and the system is running live for this demo."

---

---

---

# TRIMMED 3-MINUTE VERSION (Exactly 3:00)

**Duration:** 3 minutes exactly  
**Word Count:** ~450 words at 150 wpm

---

### [0:00 - 0:20] INTRODUCTION

"Hi, I'm walking you through ClusterCloud—a distributed compute marketplace with automatic failure recovery.

The problem: 3D rendering studios need massive compute power for short bursts. A single film can require 100 million CPU hours. Traditional cloud is expensive. ClusterCloud creates a marketplace where anyone can share spare compute—gaming PCs, crypto miners, cloud instances."

---

### [0:20 - 0:50] ARCHITECTURE

"Three layers: Frontend—customers submit jobs through our Next.js web app. Control plane—FastAPI backend handles orchestration, scheduling, recovery, and economics. Worker network—Python agents on provider machines execute tasks.

The control plane is modular: Workloads analyzes requirements. Jobs and Tasks manages state. Nodes tracks providers. Scheduling assigns work. Recovery handles failures. Ledger manages economics. Real-time updates via WebSockets."

---

### [0:50 - 1:20] SCHEDULING & EXECUTION

"Here's the scheduler algorithm. Filter nodes by compatibility—CPU, RAM, GPU requirements. Score each node: 40% reliability, 30% cost, 30% capacity. Select the highest-scoring nodes. Fully deterministic.

The node agent discovers hardware, registers with control plane, sends heartbeats every 5 seconds, and polls for tasks. Tasks execute in isolated processes with resource limits. Cross-platform: Windows, Mac, Linux."

---

### [1:20 - 2:00] AI ORCHESTRATION

"Key innovation: AI with deterministic validation.

We use AWS Bedrock with Claude Sonnet for three agents. Workload Agent analyzes requirements and estimates parallelization. Provider Agent recommends optimal nodes. Recovery Agent suggests replacements when failures happen.

Critical point: every AI recommendation goes through our Deterministic Validator—enforces budget, compatibility, capacity. If AWS isn't available, we fall back to pure deterministic algorithms. AI enhances but never breaks guarantees."

---

### [2:00 - 2:40] AUTOMATIC RECOVERY

"The magic: automatic failure recovery.

Heartbeat monitoring detects failures in 15 seconds. Recovery service identifies affected tasks, gets AI recommendations, validates them, and reassigns to healthy nodes. Economic settlement is automatic—failed provider penalized, customer compensated, replacement rewarded.

Detection to reassignment: 30-60 seconds, zero human intervention."

---

### [2:40 - 3:00] ECONOMICS & CLOSE

"CLSTR token economics: providers earn for success, lose for failure. Reliability scores tracked over time. Quality providers get more work.

The result: customers submit jobs, watch live progress, see automatic recovery, get results with full transparency. Distributed compute with AI recovery, deterministic guarantees, and aligned economic incentives.

Thanks for watching!"

---

## END SCRIPT

