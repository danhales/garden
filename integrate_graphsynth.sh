#!/bin/bash

# Script to integrate GraphSynth into G.A.R.D.E.N. repository
# This sets up GraphSynth as a Git submodule for independent development

# Define color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths
DOWNLOADS_DIR=~/Downloads
GARDEN_DIR=/Users/danhales/aprog/garden
GRAPHSYNTH_DIR=${GARDEN_DIR}/middleware/graphsynth

# Print welcome message
echo -e "${BLUE}=== GraphSynth Integration Script ===${NC}"
echo -e "This script will integrate GraphSynth into your G.A.R.D.E.N. repository"
echo -e "while maintaining independent version control.\n"

# Check if GARDEN_DIR exists
if [ ! -d "$GARDEN_DIR" ]; then
    echo -e "${YELLOW}The G.A.R.D.E.N. directory doesn't exist at $GARDEN_DIR${NC}"
    echo -e "Creating it now...\n"
    mkdir -p "$GARDEN_DIR"
fi

# Create middleware directory if it doesn't exist
if [ ! -d "${GARDEN_DIR}/middleware" ]; then
    echo -e "Creating middleware directory..."
    mkdir -p "${GARDEN_DIR}/middleware"
fi

# Create GraphSynth directory
echo -e "Setting up GraphSynth directory..."
mkdir -p "$GRAPHSYNTH_DIR"

# Find GraphSynth files in Downloads folder
echo -e "Looking for GraphSynth files in $DOWNLOADS_DIR..."
GRAPHSYNTH_FILES=$(find "$DOWNLOADS_DIR" -name "graphsynth*.py" -o -name "*_discovery.py" -o -name "*_synthesis.py" -o -name "*_inference.py" -o -name "*_factory.py" -o -name "middleware*.py" 2>/dev/null)
README_FILES=$(find "$DOWNLOADS_DIR" -name "README.md" -o -name "*.md" -o -name "setup.py" -o -name "requirements.txt" 2>/dev/null)

# Check if files were found
if [ -z "$GRAPHSYNTH_FILES" ] && [ -z "$README_FILES" ]; then
    echo -e "${YELLOW}No GraphSynth files found in $DOWNLOADS_DIR${NC}"
    echo -e "Please make sure the files are in your Downloads folder."
    exit 1
fi

# Initialize Git repository for GraphSynth
echo -e "\n${GREEN}Initializing GraphSynth as a Git repository...${NC}"
cd "$GRAPHSYNTH_DIR"
git init

# Create directory structure
echo -e "Creating directory structure..."
mkdir -p graphsynth/{core,middleware,utils,api,tests,examples,docs}

# Copy files to appropriate directories
echo -e "Copying files to appropriate directories..."

# Function to copy files if they exist
copy_if_exists() {
    local source=$1
    local dest=$2
    if [ -f "$source" ]; then
        cp "$source" "$dest"
        echo -e "Copied $(basename $source) to $dest"
    fi
}

# Copy core files
for file in $(find "$DOWNLOADS_DIR" -name "module_generator.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/core/"
done

# Copy middleware files
for file in $(find "$DOWNLOADS_DIR" -name "*_discovery.py" -o -name "*_synthesis.py" -o -name "*_inference.py" -o -name "*_factory.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/middleware/"
done

# Copy utils files
for file in $(find "$DOWNLOADS_DIR" -name "graph_utils.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/utils/"
done

# Copy API files
for file in $(find "$DOWNLOADS_DIR" -name "flask_blueprint.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/api/"
done

# Copy test files
for file in $(find "$DOWNLOADS_DIR" -name "test_*.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/tests/"
done

# Copy example files
for file in $(find "$DOWNLOADS_DIR" -name "basic_usage.py" -o -name "*_analysis.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/examples/"
done

# Copy documentation files
for file in $(find "$DOWNLOADS_DIR" -name "architecture.md" -o -name "middleware.md" -o -name "visual_guide.md" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/graphsynth/docs/"
done

# Copy root files
for file in $(find "$DOWNLOADS_DIR" -name "README.md" -o -name "setup.py" -o -name "requirements.txt" -o -name "__init__.py" -o -name "run_tests.py" 2>/dev/null); do
    copy_if_exists "$file" "$GRAPHSYNTH_DIR/"
done

# Create a default .gitignore file
cat > "$GRAPHSYNTH_DIR/.gitignore" << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db
EOL

# Commit the initial GraphSynth repository
echo -e "\n${GREEN}Committing GraphSynth files...${NC}"
git add .
git commit -m "Initial commit of GraphSynth middleware"

# Navigate to the GARDEN repository
echo -e "\n${BLUE}Setting up GraphSynth as a submodule in G.A.R.D.E.N...${NC}"
cd "$GARDEN_DIR"

# Check if GARDEN_DIR is a Git repository
if [ ! -d "$GARDEN_DIR/.git" ]; then
    echo -e "${YELLOW}The G.A.R.D.E.N. directory is not a Git repository.${NC}"
    echo -e "Initializing it as a Git repository..."
    git init
fi

# Add GraphSynth as a submodule (first remove the directory)
rm -rf "${GARDEN_DIR}/middleware/graphsynth"
git submodule add file://${GRAPHSYNTH_DIR} middleware/graphsynth

# Commit the changes to the main repository
git add .
git commit -m "Add GraphSynth as a submodule"

# Print success message
echo -e "\n${GREEN}Success! GraphSynth has been integrated into your G.A.R.D.E.N. repository.${NC}"
echo -e "\nYou can now develop GraphSynth independently while keeping it as part of G.A.R.D.E.N."
echo -e "\n${BLUE}How to work with GraphSynth:${NC}"
echo -e "1. To develop GraphSynth: cd ${GARDEN_DIR}/middleware/graphsynth"
echo -e "2. Make your changes, then commit them normally with git add and git commit"
echo -e "3. Your changes will be tracked separately from the main G.A.R.D.E.N. repository"
echo -e "\n${BLUE}How to update G.A.R.D.E.N. with new GraphSynth changes:${NC}"
echo -e "1. After committing changes to GraphSynth, go to the G.A.R.D.E.N. directory"
echo -e "2. Run: git add middleware/graphsynth"
echo -e "3. Run: git commit -m \"Update GraphSynth submodule\""
echo -e "\nThis keeps both repositories in sync while allowing independent development."
