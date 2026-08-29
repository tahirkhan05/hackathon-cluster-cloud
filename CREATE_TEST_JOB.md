# How to Create a Test Job

## Quick Method: Use PowerShell

Open a **new PowerShell terminal** and run:

```powershell
# Create a test rendering job
$body = @{
    workload_type = "blender_render"
    customer_id = "customer:customer-demo-001"
    project_name = "Test Demo Render"
    total_frames = 10
    frame_range_start = 1
    frame_range_end = 10
    requirements = @{
        cpu_cores = 4
        ram_gb = 8
        gpu_required = $false
    }
    input_files = @{
        blend_file = "demo.blend"
    }
    total_budget_clstr = 1000
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" | Select-Object -ExpandProperty Content
```

## Alternative: Simple curl-style

```powershell
$json = '{"workload_type":"blender_render","customer_id":"customer:customer-demo-001","project_name":"Hackathon Demo","total_frames":5,"frame_range_start":1,"frame_range_end":5,"requirements":{"cpu_cores":2,"ram_gb":4,"gpu_required":false},"input_files":{"blend_file":"test.blend"},"total_budget_clstr":500}'

Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/" -Method POST -Body $json -ContentType "application/json"
```

## What Happens Next:

1. **Job Created** - Backend creates the job and breaks it into tasks
2. **Tasks Assigned** - Scheduler assigns tasks to your registered node
3. **Node Executes** - Node agent picks up tasks and processes them
4. **UI Updates** - Dashboard shows job progress in real-time

## Check Job Status:

```powershell
# List all jobs
Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/" -Method GET | Select-Object -ExpandProperty Content

# Get specific job details (replace JOB_ID)
Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/JOB_ID" -Method GET | Select-Object -ExpandProperty Content
```

## Watch in Real-Time:

1. **Dashboard** - http://localhost:3000/dashboard shows system overview
2. **Jobs Page** - http://localhost:3000/jobs lists all jobs with progress
3. **Network Page** - http://localhost:3000/network shows your node processing tasks
4. **Backend Logs** - Terminal 1 shows API activity
5. **Node Agent Logs** - Terminal 2 shows task execution

---

## For Judges Demo:

Just run the first PowerShell command above to create a job, then:

1. Refresh the Jobs page - you'll see the new job
2. Watch the node agent terminal - it will pick up and process tasks
3. Show the Network page - node status will change to "BUSY"
4. Refresh Jobs page - progress bar will update in real-time

This demonstrates the **full end-to-end distributed execution flow!**
