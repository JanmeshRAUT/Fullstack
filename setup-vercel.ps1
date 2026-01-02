# setup-vercel.ps1 - Quick setup script for Vercel deployment (Windows)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "FatigueGuard Pro - Vercel Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Python not found. Please install Python 3.8+" -ForegroundColor Yellow
    exit 1
}

# Check if pyngrok is installed
$pyngrokInstalled = pip show pyngrok 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📥 Installing pyngrok..." -ForegroundColor Yellow
    pip install pyngrok
}

Write-Host ""
Write-Host "🚀 Starting backend with ngrok tunnel..." -ForegroundColor Green
Write-Host ""

# Change to backend directory and run
Set-Location backend
python run_with_ngrok.py

Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy the ngrok URL from above (https://...ngrok.io)" -ForegroundColor White
Write-Host "2. Go to Vercel Dashboard → Your Project → Settings → Environment Variables" -ForegroundColor White
Write-Host "3. Create/Update variable:" -ForegroundColor White
Write-Host "   Name: REACT_APP_API_URL" -ForegroundColor Yellow
Write-Host "   Value: (paste the ngrok URL)" -ForegroundColor Yellow
Write-Host "4. Click Save and trigger a redeploy" -ForegroundColor White
Write-Host "5. Your Vercel app will now connect to your local backend!" -ForegroundColor Green
