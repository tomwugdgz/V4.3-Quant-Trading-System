$env:PYTHONIOENCODING="utf-8"
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
$output = & "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" test_trade_nzdusd.py 2>&1
$output | Out-File -FilePath "test_trade_output.txt" -Encoding UTF8
$output
