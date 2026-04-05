$adminEmail = "admin@test.com"
$adminPassword = "Admin123456!"

$users = @(
    @{email="xiaowang@test.com"; password="Test123456!"; name="Xiaowang"; query="Shenzhen Nanshan tech park"},
    @{email="xiaoli@test.com"; password="Test123456!"; name="Xiaoli"; query="Beijing Chaoyang CBD"},
    @{email="laozhang@test.com"; password="Test123456!"; name="Laozhang"; query="Shanghai Pudong Lujiazui"},
    @{email="chenjie@test.com"; password="Test123456!"; name="Chenjie"; query="Guangzhou Tianhe Zhujiang"}
)

Write-Host "=== 1. Admin Login ===" -ForegroundColor Cyan
$loginBody = @{email=$adminEmail; password=$adminPassword} | ConvertTo-Json -Compress
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
    $adminToken = $loginResponse.access_token
    Write-Host "Admin login success!" -ForegroundColor Green
} catch {
    Write-Host "Admin login failed: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit
}

Write-Host "`n=== 2. Get User List ===" -ForegroundColor Cyan
$headers = @{Authorization = "Bearer $adminToken"}
try {
    $usersResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/admin/users" -Method GET -Headers $headers
    Write-Host "Total users: $($usersResponse.total)" -ForegroundColor Green
    foreach ($u in $usersResponse.users) {
        Write-Host "  - $($u.email) | $($u.full_name) | source: $($u.source) | integral: $($u.integral)"
    }
} catch {
    Write-Host "Get users failed: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host "`n=== 3. Create Tasks for Each User ===" -ForegroundColor Cyan
foreach ($user in $users) {
    Write-Host "`n--- $($user.name) ($($user.email)) ---" -ForegroundColor Yellow
    
    $userLoginBody = @{email=$user.email; password=$user.password} | ConvertTo-Json -Compress
    try {
        $userLoginResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/auth/login" -Method POST -ContentType "application/json" -Body $userLoginBody
        $userToken = $userLoginResponse.access_token
        Write-Host "  Login success" -ForegroundColor Green
    } catch {
        Write-Host "  Login failed: $($_.ErrorDetails.Message)" -ForegroundColor Red
        continue
    }
    
    $taskBody = @{query=$user.query} | ConvertTo-Json -Compress
    $userHeaders = @{Authorization = "Bearer $userToken"}
    try {
        $taskResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/tasks" -Method POST -ContentType "application/json" -Headers $userHeaders -Body $taskBody
        Write-Host "  Task created! ID: $($taskResponse.id)" -ForegroundColor Green
        Write-Host "  Query: $($user.query)"
    } catch {
        Write-Host "  Task failed: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== 4. Check Audit Logs ===" -ForegroundColor Cyan
try {
    $auditLogs = Invoke-RestMethod -Uri "http://localhost:9000/api/admin/audit-logs?limit=20" -Method GET -Headers $headers
    Write-Host "Total audit logs: $($auditLogs.total)" -ForegroundColor Green
    Write-Host "Recent 20 records:"
    foreach ($log in $auditLogs.logs) {
        Write-Host "  [$($log.created_at)] $($log.action) - $($log.resource_type) by $($log.user_email)"
    }
} catch {
    Write-Host "Get audit logs failed: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
