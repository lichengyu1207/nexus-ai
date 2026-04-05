$users = @("xiaowang@test.com", "xiaoli@test.com", "laozhang@test.com", "chenjie@test.com")

Write-Host "Checking test users..."
Write-Host "========================`n"

foreach ($email in $users) {
    # Login first
    $loginBody = @{
        email = $email
        password = "Test123456!"
    } | ConvertTo-Json -Compress
    
    try {
        $loginResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
        $token = $loginResponse.access_token
        
        # Get integral info
        $headers = @{
            Authorization = "Bearer $token"
        }
        $integralInfo = Invoke-RestMethod -Uri "http://localhost:9000/api/user/integral" -Method GET -Headers $headers
        
        Write-Host "User: $email"
        Write-Host "  Name: $($integralInfo.recent_logs[0] | Out-Null)"
        Write-Host "  Integral: $($integralInfo.integral)"
        Write-Host "  Source: $($integralInfo.source)"
        Write-Host "  Source Name: $($integralInfo.source_name)"
        Write-Host "  Bonus Label: $($integralInfo.bonus_label)"
        Write-Host "  Initial Integral: $($integralInfo.initial_integral)"
        Write-Host "  Is Member: $($integralInfo.is_member)"
        Write-Host ""
    } catch {
        Write-Host "Error for $email : $($_.ErrorDetails.Message)"
    }
}
