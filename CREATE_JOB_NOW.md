# Create a Test Job - SIMPLE METHOD

## Open a NEW PowerShell terminal and run these commands ONE BY ONE:

### Step 1: Set the JSON body
```powershell
$json = '{"workload_type":"blender_render","customer_id":"customer:customer-demo-001","project_name":"Hackathon Demo","total_frames":5,"frame_range_start":1,"frame_range_end":5,"requirements":{"cpu_cores":2,"ram_gb":4,"gpu_required":false},"input_files":{"blend_file":"test.blend"},"total_budget_clstr":500}'
```

### Step 2: Create the job
```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/jobs/' -Method POST -Body $json -ContentType 'application/json'
```

## What You'll See:

1. **In the response** - Job details with job_id
2. **In backend terminal** - Job creation logs
3. **In node agent terminal** - Tasks being assigned and executed
4. **In browser (Jobs page)** - New job appearing with progress bar

## Then Watch:

1. **Refresh Jobs page** - http://localhost:3000/jobs
2. **Watch Network page** - Node status changes to "busy"
3. **Check backend logs** - Task assignment happening
4. **Check node agent logs** - Tasks being executed

The node will pick up the 5 tasks (one per frame) and process them!

---

## Alternative: Create via the script file

```powershell
cd C:\Users\mdkta\OneDrive\Desktop\cluster_cloud
.\create_job.ps1
```

---

## If you get an error about execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the commands again.
