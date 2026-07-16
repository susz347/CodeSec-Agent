$ErrorActionPreference = "Stop"

$repo = "C:\Users\sz\Documents\Codex\2026-06-29\yu\CodeSec-Agent-Project"
Set-Location $repo

git -c safe.directory=$repo branch -M main

$remote = git -c safe.directory=$repo remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
  git -c safe.directory=$repo remote add origin https://github.com/susz347/CodeSec-Agent.git
} else {
  git -c safe.directory=$repo remote set-url origin https://github.com/susz347/CodeSec-Agent.git
}

git -c safe.directory=$repo push -u origin main
