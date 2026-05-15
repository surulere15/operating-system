#!/bin/bash

# Projects to push
PROJECTS=(
  "regulatory_scraper_bot:Regulatory scraper bot for compliance monitoring"
  "insider_alerts:Insider trading alerts and monitoring system"
  "capital_recovery:Capital recovery and debt collection tools"
)

for project_info in "${PROJECTS[@]}"; do
  IFS=':' read -r project desc <<< "$project_info"
  
  echo "=== Processing $project ==="
  cd "$project" || continue
  
  # Initialize git if needed
  if [ ! -d ".git" ]; then
    git init
    cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.Python
venv/
ENV/
.env
*secret*
.vscode/
.DS_Store
node_modules/
*.log
EOF
    git add .
    git commit -m "Initial commit: ${project}

${desc}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
    
    # Create and push to GitHub
    repo_name=$(echo "$project" | tr '_' '-')
    gh repo create "surulere15/${repo_name}" --private --source=. --remote=origin --push --description "$desc" 2>&1 | tail -3
  fi
  
  cd ..
done

echo "✅ All projects pushed!"
