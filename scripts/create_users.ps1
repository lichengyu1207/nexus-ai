$users = @(
    @{email="xiaowang@test.com"; password="Test123456!"; full_name="小王"; source="laohai"; referred_by="ip"},
    @{email="xiaoli@test.com"; password="Test123456!"; full_name="小李"; source="direct"; referred_by="casual"},
    @{email="laozhang@test.com"; password="Test123456!"; full_name="老张"; source="seo"; referred_by="search"},
    @{email="chenjie@test.com"; password="Test123456!"; full_name="陈姐"; source="urgent"; referred_by="friend"}
)

foreach ($user in $users) {
    $body = @{
        email = $user.email
        password = $user.password
        full_name = $user.full_name
        source = $user.source
        referred_by = $user.referred_by
    } | ConvertTo-Json -Compress
    
    Write-Host "Creating user: $($user.full_name) ($($user.email))"
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/api/auth/register" -Method POST -ContentType "application/json" -Body $body
        Write-Host "  Success! ID: $($response.id)"
    } catch {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        if ($errorDetail.detail -like "*已被注册*") {
            Write-Host "  User already exists"
        } else {
            Write-Host "  Error: $($errorDetail.detail)"
        }
    }
}

Write-Host "`nDone! Test users created."
Write-Host "Login credentials:"
Write-Host "  小王: xiaowang@test.com / Test123456!"
Write-Host "  小李: xiaoli@test.com / Test123456!"
Write-Host "  老张: laozhang@test.com / Test123456!"
Write-Host "  陈姐: chenjie@test.com / Test123456!"
