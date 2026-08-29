$body = @{
    workload_type = "blender_render"
    customer_id = "customer:customer-demo-001"
    project_name = "Hackathon Demo Job"
    total_frames = 5
    frame_range_start = 1
    frame_range_end = 5
    requirements = @{
        cpu_cores = 2
        ram_gb = 4
        gpu_required = $false
    }
    input_files = @{
        blend_file = "demo.blend"
    }
    total_budget_clstr = 500
} | ConvertTo-Json

Write-Host "Creating job..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Green
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
