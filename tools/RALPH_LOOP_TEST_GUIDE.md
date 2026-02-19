# Ralph Wiggum Loop (Gold Tier) - Test Guide

## Overview

The Gold Tier Ralph Wiggum Loop handles autonomous multi-step tasks with full workflow integration:
- **Sales lead** → **Draft post** → **HITL approval** → **MCP execution** → **Audit log**
- Maximum iterations: 20
- Integrates with: Cross Domain Integrator, Audit Logger, Skills

---

## Command to Run

```bash
./ralph-loop "Process multi-step task in Needs_Action" --max-iterations 20
```

Or on Windows:
```bash
python tools\ralph_loop_runner.py "Process multi-step task in Needs_Action" --max-iterations 20
```

---

## Test Guide: Multi-Step Task Processing

### Test 1: Complete Multi-Step Workflow

**Objective:** Test full workflow from sales lead to completion.

**Steps:**

1. **Create multi-step test file in Needs_Action:**
   ```bash
   cat > Needs_Action/test_sales_lead.md << 'EOF'
   ---
   type: facebook_message
   platform: facebook
   from: "John Doe"
   subject: "Sales inquiry - interested in services"
   received: "2026-02-20T10:00:00"
   priority: high
   status: pending
   keyword: sales
   ---

   # Facebook Message - Sales Lead

   ## Original Content
   Hi! I'm interested in your sales services for my new project.
   Can you provide pricing information and timeline?
   
   This is urgent - need response ASAP.

   ## Detection Details
   - **Keyword Found:** sales
   - **Platform:** facebook
   - **Type:** message
   - **Detected At:** 2026-02-20 10:00:00
   EOF
   ```

2. **Run Ralph Wiggum Loop:**
   ```bash
   ./ralph-loop "Process sales leads" --max-iterations 20
   ```

3. **Expected Output:**
   ```
   ============================================================
   RALPH WIGGUM REASONING LOOP (Gold Tier)
   ============================================================
   Prompt: Process sales leads
   Max Iterations: 20
   Audit Logging: Enabled
   ============================================================

   ============================================================
   --- Ralph Wiggum Loop - Iteration 1/20 ---
   ============================================================

   Found 1 files to process

   Processing: test_sales_lead.md (Stage: analysis)
   Analyzing: test_sales_lead.md

   Executing task: facebook_message for test_sales_lead.md
     Workflow: analysis -> skill_execution -> hitl_approval -> mcp_execution -> audit_logging -> completion

     Stage: Analysis
     Task Type: facebook_message
     Multi-step: True

     Stage: Skill Execution
     Triggering skill: social_summary_generator
     Draft created: Pending_Approval/draft_test_sales_lead.md
     Skill triggered successfully
     Draft created, moving to HITL approval

     Stage: HITL Approval
     Awaiting HITL approval (file in Pending_Approval)

   --- Iteration Summary ---
   Tasks Completed: 0
   Tasks Pending: 1
   ```

4. **Simulate HITL Approval:**
   ```bash
   # Move draft from Pending_Approval to Approved
   mv Pending_Approval/draft_test_sales_lead.md Approved/
   ```

5. **Run loop again to continue:**
   ```bash
   ./ralph-loop "Continue processing" --max-iterations 20
   ```

6. **Expected Output (after approval):**
   ```
     Stage: HITL Approval
     Approval granted, proceeding to MCP execution

     Stage: MCP Execution
     MCP execution simulated

     Stage: Audit Logging
     TASK_COMPLETE: test_sales_lead.md
     Moved to Done: Done/test_sales_lead.md

   ============================================================
   TASK_COMPLETE: All tasks finished successfully!
   ============================================================
   ```

7. **Verify file movement:**
   ```bash
   # File should be in Done
   ls Done/test_sales_lead.md

   # Check audit log
   cat Logs/audit_$(date +%Y%m%d).json | jq '.[-1]'
   ```

---

### Test 2: Multiple Files Processing

**Objective:** Test processing multiple files in single loop run.

**Steps:**

1. **Create multiple test files:**
   ```bash
   # Sales lead
   cat > Needs_Action/sales_lead_1.md << 'EOF'
   ---
   type: twitter_dm
   platform: twitter
   keyword: sales
   priority: high
   ---

   # Twitter DM - Sales
   Interested in your services. Please contact me.
   EOF

   # Client inquiry
   cat > Needs_Action/client_inquiry.md << 'EOF'
   ---
   type: facebook_message
   platform: facebook
   keyword: client
   priority: medium
   ---

   # Facebook Message - Client
   Need help with my account.
   EOF

   # Project opportunity
   cat > Needs_Action/project_lead.md << 'EOF'
   ---
   type: linkedin_message
   platform: linkedin
   keyword: project
   priority: high
   ---

   # LinkedIn Message - Project
   Interested in partnership for new project.
   EOF
   ```

2. **Run loop:**
   ```bash
   ./ralph-loop "Process all leads" --max-iterations 20
   ```

3. **Expected:**
   - All 3 files analyzed
   - Drafts created in Pending_Approval
   - Tasks pending HITL approval

---

### Test 3: Audit Log Verification

**Objective:** Verify audit logging is working correctly.

**Steps:**

1. **Run loop with audit enabled:**
   ```bash
   ./ralph-loop "Test audit logging" --max-iterations 5
   ```

2. **Check audit log:**
   ```bash
   # View today's audit log
   cat Logs/audit_$(date +%Y%m%d).json | python -m json.tool | tail -50
   ```

3. **Expected entries:**
   ```json
   {
     "timestamp": "2026-02-20T10:30:00.000000",
     "action_type": "ralph_loop_started",
     "target": "ralph_loop_runner",
     "result": "success",
     "message": "Ralph Wiggum Loop started"
   }
   {
     "timestamp": "2026-02-20T10:30:01.000000",
     "action_type": "task_analyzed",
     "target": "Needs_Action/test_sales_lead.md",
     "result": "success",
     "message": "Analyzed test_sales_lead.md: facebook_message"
   }
   {
     "timestamp": "2026-02-20T10:30:05.000000",
     "action_type": "task_completed",
     "target": "Needs_Action/test_sales_lead.md",
     "result": "success",
     "message": "Task completed: test_sales_lead.md"
   }
   ```

---

### Test 4: Max Iterations Limit

**Objective:** Verify loop respects max iterations.

**Steps:**

1. **Create many test files:**
   ```bash
   for i in {1..25}; do
     cat > Needs_Action/test_file_$i.md << EOF
   ---
   type: general
   keyword: test
   ---
   Test file $i
   EOF
   done
   ```

2. **Run with limited iterations:**
   ```bash
   ./ralph-loop "Process with limit" --max-iterations 5
   ```

3. **Expected:**
   ```
   WARNING: Reached maximum iterations (5)
   ```

---

### Test 5: Disable Audit Logging

**Objective:** Test running without audit logging.

**Steps:**

1. **Run with audit disabled:**
   ```bash
   ./ralph-loop "Test no audit" --max-iterations 5 --no-audit
   ```

2. **Expected:**
   ```
   Audit Logging: Disabled
   ```

---

## Workflow Stages Explained

| Stage | Description | Action |
|-------|-------------|--------|
| **analysis** | Analyze file content | Parse frontmatter, determine task type |
| **skill_execution** | Trigger appropriate skill | Create draft/summary |
| **hitl_approval** | Wait for human approval | Check if moved to /Approved |
| **mcp_execution** | Execute via MCP server | Send email, post to social |
| **audit_logging** | Log completion | Write to audit log |
| **completion** | Finalize task | Move to /Done |

---

## File Movement

```
Needs_Action/          # Starting point
    ↓ (analysis)
    ↓ (skill_execution - draft created)
Pending_Approval/      # Awaiting HITL
    ↓ (approval granted - moved by human)
Approved/              # Ready for MCP
    ↓ (mcp_execution)
    ↓ (audit_logging)
    ↓ (completion)
Done/                  # Task complete
```

---

## Command Reference

```bash
# Basic usage
./ralph-loop "Process all files" --max-iterations 20

# Process specific task type
./ralph-loop "Process sales leads" --max-iterations 15

# Disable audit logging
./ralph-loop "Quick process" --max-iterations 10 --no-audit

# View help
./ralph-loop --help
```

---

## Success Criteria

✓ Loop processes files from Needs_Action
✓ Multi-step workflow followed (analysis → skill → HITL → MCP → audit)
✓ Drafts created in Pending_Approval
✓ Approval check works (files in Approved)
✓ Files moved to Done on completion
✓ Audit logs created in Logs/audit_*.json
✓ Max iterations respected
✓ TASK_COMPLETE message displayed

---

## Troubleshooting

### Loop exits immediately
- Check if files exist in Needs_Action
- Verify file permissions

### Audit logs not created
- Check if utils/audit_logger.py exists
- Run without --no-audit flag

### Files not moving
- Check directory permissions
- Verify file isn't open in another process

### HITL approval not detected
- Ensure file is moved to /Approved (not just Pending_Approval)
- Check filename matches pattern

---

*Generated by Gold Tier Ralph Wiggum Loop*
*Autonomous multi-step task processing with full workflow integration*
