# ClusterCloud Security Architecture

**Version:** MVP (Hackathon)  
**Last Updated:** 2024-01-15

---

## ⚠️ Security Disclaimer

**This is an MVP built for a hackathon demonstration.**

The current implementation includes **basic security controls** suitable for:
- Development environments
- Proof-of-concept demonstrations
- Trusted network testing
- Single-tenant evaluation

**DO NOT use in production without implementing the production hardening measures listed below.**

---

## Security Model

### Threat Model

**In Scope:**
- Malicious workloads from customers
- Accidental resource exhaustion
- Node impersonation
- Data leakage between tasks
- Network-based attacks

**Out of Scope (MVP):**
- Nation-state adversaries
- Hardware attacks
- Supply chain attacks
- Social engineering
- Physical security

---

## Current Security Controls (MVP)

### 1. Node Authentication

**Status:** 🟡 **Basic Implementation**

**What's Protected:**
- Node registration endpoint
- Heartbeat endpoint
- Task polling endpoint

**Implementation:**
```python
# API Key header
X-API-Key: <secret-key>

# Configuration
ENABLE_NODE_AUTH=false  # Disabled by default for MVP
NODE_API_KEY=<master-key>
```

**Limitations:**
- ❌ Single master key for all nodes
- ❌ No key rotation
- ❌ No per-node keys
- ❌ No key revocation
- ❌ Keys stored in plain text
- ❌ No rate limiting

**Production Requirements:**
- ✅ Per-node API keys
- ✅ Key rotation mechanism
- ✅ Encrypted key storage (Vault, AWS Secrets Manager)
- ✅ Key revocation API
- ✅ Rate limiting per key
- ✅ Audit logging of all authentication attempts
- ✅ mTLS for node-to-control-plane communication

---

### 2. Workload Isolation

**Status:** 🟢 **Implemented with Docker**

**What's Protected:**
- Task execution isolated in Docker containers
- Network isolation (no internet access by default)
- Filesystem isolation (read-only root)
- Resource limits enforced

**Implementation:**
```python
docker run \
  --rm \
  --memory=2048m \
  --memory-swap=2048m \
  --cpus=2.0 \
  --network=none \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --read-only \
  --tmpfs=/tmp:rw,noexec,nosuid,size=512m \
  --user=nobody \
  python:3.11-slim \
  python render_frame.py
```

**Security Controls:**
- ✅ Network isolation (`--network=none`)
- ✅ Resource limits (CPU, memory, disk)
- ✅ Read-only root filesystem
- ✅ No privileged mode
- ✅ All capabilities dropped
- ✅ Non-root user (nobody)
- ✅ No new privileges
- ✅ Temporary filesystem for /tmp

**Limitations:**
- ❌ No seccomp profile
- ❌ No AppArmor/SELinux profile
- ❌ No user namespaces
- ❌ No runtime security scanning
- ❌ Containers share kernel with host

**Production Requirements:**
- ✅ Custom seccomp profile (whitelist syscalls)
- ✅ AppArmor or SELinux mandatory access control
- ✅ User namespace isolation
- ✅ Container runtime security (Falco, Sysdig)
- ✅ Image vulnerability scanning
- ✅ Signed container images
- ✅ gVisor or Kata Containers for stronger isolation

---

### 3. Resource Limits

**Status:** 🟡 **Soft Limits**

**What's Protected:**
- CPU usage per task
- Memory usage per task
- Disk usage per task
- Task execution timeout

**Implementation:**
```python
# Per-task limits (configurable)
MAX_TASK_MEMORY_MB = 2048      # 2GB RAM
MAX_TASK_CPU_CORES = 2.0       # 2 CPU cores
MAX_TASK_DISK_MB = 5120        # 5GB disk
TASK_TIMEOUT_SECONDS = 120     # 2 minutes
```

**Limitations:**
- ❌ No node-level limits (can oversubscribe)
- ❌ No network bandwidth limits
- ❌ No IOPS limits
- ❌ No system-level cgroup enforcement

**Production Requirements:**
- ✅ Node-level resource quotas
- ✅ Network bandwidth limits
- ✅ Disk IOPS limits
- ✅ GPU time limits
- ✅ System-level cgroup enforcement
- ✅ Resource usage monitoring and alerting

---

### 4. Network Security

**Status:** 🟡 **Basic Isolation**

**What's Protected:**
- Tasks cannot access internet
- Tasks cannot access internal network
- Tasks cannot communicate with each other

**Implementation:**
```bash
# Docker network isolation
--network=none
```

**Limitations:**
- ❌ Control plane has no firewall rules
- ❌ No network segmentation
- ❌ No TLS for node-to-control-plane
- ❌ WebSocket connections not authenticated
- ❌ No DDoS protection

**Production Requirements:**
- ✅ TLS/HTTPS for all HTTP communication
- ✅ mTLS for node authentication
- ✅ Network segmentation (VPC, subnets)
- ✅ Firewall rules (allow list only)
- ✅ WebSocket authentication (JWT)
- ✅ DDoS protection (Cloudflare, AWS Shield)
- ✅ VPN for node-to-control-plane if over internet

---

### 5. Secrets Management

**Status:** 🔴 **Not Implemented**

**Current State:**
- API keys stored in environment variables
- No secret rotation
- No encryption at rest
- Secrets in plain text logs (risk)

**Production Requirements:**
- ✅ Secrets stored in Vault or AWS Secrets Manager
- ✅ Automatic secret rotation
- ✅ Encryption at rest and in transit
- ✅ Audit logging of secret access
- ✅ Least-privilege access control
- ✅ No secrets in logs or error messages

---

### 6. Data Security

**Status:** 🟡 **Basic Protection**

**What's Protected:**
- Ephemeral task files deleted after completion
- Task data isolated per container
- No cross-customer data access

**Implementation:**
```python
# Ephemeral work directory
/tmp/clustercloud/task-<id>/
# Cleaned up after task completion or 24 hours
```

**Limitations:**
- ❌ No encryption at rest
- ❌ No encryption in transit (rendered frames)
- ❌ No data retention policies
- ❌ No GDPR/compliance controls
- ❌ Database not encrypted

**Production Requirements:**
- ✅ Encryption at rest (disk encryption)
- ✅ Encryption in transit (TLS)
- ✅ Database encryption
- ✅ Customer data isolation (multi-tenancy)
- ✅ Data retention and deletion policies
- ✅ GDPR compliance (data portability, right to be forgotten)
- ✅ Backup encryption

---

### 7. Audit Logging

**Status:** 🟡 **Basic Logging**

**What's Logged:**
- Node registration
- Job creation
- Task assignment
- Task completion/failure
- Recovery actions
- Economic transactions

**Implementation:**
```python
logger.info(f"Node {node_id} registered")
logger.warning(f"Task {task_id} failed: {error}")
```

**Limitations:**
- ❌ No centralized log aggregation
- ❌ No log integrity verification
- ❌ No tamper-proof logging
- ❌ No SIEM integration
- ❌ Logs not retained long-term

**Production Requirements:**
- ✅ Centralized log aggregation (ELK, Splunk)
- ✅ Tamper-proof logging (append-only, signed)
- ✅ SIEM integration for threat detection
- ✅ Long-term log retention (compliance)
- ✅ Log access controls
- ✅ Automated alerting on security events

---

### 8. Dependency Security

**Status:** 🟡 **Basic**

**Current State:**
- Python dependencies in `requirements.txt`
- No vulnerability scanning
- No automatic updates

**Production Requirements:**
- ✅ Automated vulnerability scanning (Dependabot, Snyk)
- ✅ Dependency pinning with hash verification
- ✅ Regular dependency updates
- ✅ Software Bill of Materials (SBOM)
- ✅ Container image scanning
- ✅ License compliance checking

---

## Attack Scenarios & Mitigations

### Scenario 1: Malicious Rendering Task

**Attack:**
Customer submits task with malicious code that attempts to:
- Mine cryptocurrency
- Scan internal network
- Exfiltrate data
- Consume excessive resources

**Current Mitigation:**
- ✅ Docker isolation prevents network access
- ✅ Resource limits prevent excessive consumption
- ✅ Read-only filesystem prevents persistence
- ✅ Timeout kills long-running tasks

**Residual Risk:**
- ⚠️ Task can still consume allocated resources for mining
- ⚠️ No runtime behavior monitoring

**Production Mitigation:**
- Monitor CPU patterns for crypto mining
- Runtime security scanning (Falco)
- Workload analysis with ML anomaly detection

---

### Scenario 2: Node Impersonation

**Attack:**
Attacker registers fake node to:
- Steal task data
- Report false results
- Earn CLSTR tokens fraudulently

**Current Mitigation:**
- ⚠️ API key required (if enabled)
- ⚠️ Single master key (weak)

**Residual Risk:**
- 🔴 Master key compromise affects all nodes
- 🔴 No node identity verification

**Production Mitigation:**
- Per-node certificates (mTLS)
- Hardware-based attestation (TPM)
- Node reputation scoring
- Multi-factor authentication

---

### Scenario 3: Data Exfiltration

**Attack:**
Malicious task attempts to:
- Access other tasks' data
- Send data over network
- Write data to persistent storage

**Current Mitigation:**
- ✅ Network isolation (no egress)
- ✅ Filesystem isolation (per-task directory)
- ✅ Read-only root filesystem

**Residual Risk:**
- ⚠️ Task data not encrypted at rest
- ⚠️ No data loss prevention monitoring

**Production Mitigation:**
- Encrypt all data at rest
- Monitor for unusual file access patterns
- Data loss prevention (DLP) tools

---

### Scenario 4: Resource Exhaustion

**Attack:**
Customer submits many tasks to:
- Exhaust node resources
- Deny service to others
- Inflate costs

**Current Mitigation:**
- ✅ Per-task resource limits
- ⚠️ Budget limits (customer balance)

**Residual Risk:**
- 🔴 No node-level limits (oversubscription)
- 🔴 No rate limiting on job creation

**Production Mitigation:**
- Node-level resource quotas
- Rate limiting per customer
- Admission control based on capacity
- Cost-based throttling

---

## Compliance Considerations

### GDPR (if operating in EU)

**Not Implemented:**
- ❌ Data processing agreements
- ❌ Data portability
- ❌ Right to be forgotten
- ❌ Data breach notification
- ❌ Privacy by design

**Required for Production:**
- Legal review and DPA templates
- Data export functionality
- Data deletion API
- Incident response plan
- Privacy impact assessment

---

### SOC 2 (for enterprise customers)

**Not Implemented:**
- ❌ Access controls
- ❌ Change management
- ❌ Vendor management
- ❌ Business continuity
- ❌ Incident response

**Required for Production:**
- Formal security policies
- Access control matrix
- Change approval process
- Third-party security assessments
- Disaster recovery plan

---

## Security Testing

### Performed (MVP)

- ✅ Basic unit tests
- ✅ Integration tests
- ✅ Manual security review

### Not Performed (Production Required)

- ❌ Penetration testing
- ❌ Vulnerability scanning
- ❌ Fuzzing
- ❌ Red team exercises
- ❌ Security audit by third party

---

## Incident Response

### MVP State

**No formal incident response plan.**

In case of security incident:
1. Contact repository maintainer
2. Review logs manually
3. Restart affected services
4. No notification process

### Production Requirements

- Written incident response plan
- Designated security team
- Automated detection and alerting
- Customer notification procedures
- Post-incident review process
- Communication templates

---

## Secure Development Practices

### Current

- ✅ Code in public repository
- ✅ Basic input validation
- ✅ Error handling

### Production Requirements

- ✅ Security code review process
- ✅ Static application security testing (SAST)
- ✅ Dynamic application security testing (DAST)
- ✅ Dependency scanning
- ✅ Secret scanning (no secrets in code)
- ✅ Security training for developers

---

## Configuration Security

### Development (Current)

```bash
# .env.development (NOT FOR PRODUCTION)
ENABLE_NODE_AUTH=false
NODE_API_KEY=changeme
DATABASE_URL=sqlite:///./clustercloud.db
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env.production (EXAMPLE - use secrets manager)
ENABLE_NODE_AUTH=true
NODE_API_KEY=<from-secrets-manager>
DATABASE_URL=postgresql://<encrypted-connection>
LOG_LEVEL=INFO
ENABLE_DOCKER_ISOLATION=true
MAX_TASK_MEMORY_MB=1024
MAX_TASK_CPU_CORES=1.0
```

---

## Security Roadmap

### Phase 1: Authentication Hardening
- [ ] Per-node API keys
- [ ] JWT for customer authentication
- [ ] WebSocket authentication
- [ ] Rate limiting

### Phase 2: Data Protection
- [ ] TLS everywhere
- [ ] Database encryption
- [ ] Secret management (Vault)
- [ ] Backup encryption

### Phase 3: Workload Security
- [ ] Seccomp profiles
- [ ] AppArmor/SELinux
- [ ] Runtime security monitoring
- [ ] Image scanning

### Phase 4: Monitoring & Response
- [ ] SIEM integration
- [ ] Automated alerting
- [ ] Incident response plan
- [ ] Penetration testing

### Phase 5: Compliance
- [ ] GDPR compliance
- [ ] SOC 2 audit
- [ ] Security certifications
- [ ] Legal review

---

## Security Contact

For security issues in this MVP:
- **GitHub Issues:** Report vulnerabilities privately
- **Pull Requests:** Security improvements welcome

For production deployments:
- Hire a security consultant
- Perform penetration testing
- Get legal review
- Implement monitoring

---

## Summary: MVP vs Production

| Security Control | MVP Status | Production Status |
|------------------|------------|-------------------|
| Node Authentication | 🟡 Basic | ✅ mTLS + Per-node keys |
| Workload Isolation | 🟢 Docker | ✅ Docker + Seccomp + AppArmor |
| Resource Limits | 🟡 Soft | ✅ Hard + Quotas |
| Network Security | 🟡 Basic | ✅ TLS + Segmentation + Firewall |
| Secrets Management | 🔴 None | ✅ Vault/Secrets Manager |
| Data Encryption | 🔴 None | ✅ At rest + In transit |
| Audit Logging | 🟡 Basic | ✅ Centralized + SIEM |
| Dependency Scanning | 🔴 None | ✅ Automated |
| Incident Response | 🔴 None | ✅ Formal plan |
| Compliance | 🔴 None | ✅ GDPR + SOC 2 |

**Legend:**
- 🟢 Production-ready
- 🟡 MVP-quality (needs hardening)
- 🔴 Not implemented (critical for production)

---

**Remember: This is a hackathon MVP. Deploy to production only after implementing production hardening measures and conducting security assessments.**
