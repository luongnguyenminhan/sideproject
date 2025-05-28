#!/bin/bash

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "Searching for translation strings in Python files..."

# Create a temporary file for extracted strings
extracted_file=$(mktemp)

# Find all strings marked for translation in Python files
find ./app -type f -name "*.py" -exec grep -o "_('[^']*')" {} \; | 
sed "s/_('\([^']*\)')/\1/" | 
sort -u > "$extracted_file"

# Also find message keys in route responses
find ./app -type f -name "*.py" -exec grep -o "message=_('[^']*')" {} \; | 
sed "s/message=_('\([^']*\)')/\1/" | 
sort -u >> "$extracted_file"

# Find additional format used in responses
find ./app -type f -name "*.py" -exec grep -o "message=['\"].*['\"]" {} \; | 
grep -v "message=_" | 
sed "s/message=[\"\']//g" | 
sed "s/[\"\']//g" | 
sort -u >> "$extracted_file"

# Remove duplicates
sort -u "$extracted_file" -o "$extracted_file"

echo "Found $(wc -l < "$extracted_file") unique translation strings in code."

# Extract keys from JSON files
en_keys=$(mktemp)
vi_keys=$(mktemp)

# Use jq to extract keys from JSON files
jq -r 'keys[]' ./app/locales/en.json > "$en_keys"
jq -r 'keys[]' ./app/locales/vi.json > "$vi_keys"

echo -e "\n${GREEN}Checking for missing translations...${NC}"

# Check for missing translations in en.json
echo -e "\n${GREEN}Missing in en.json:${NC}"
missing_count_en=0
while IFS= read -r string; do
    if ! grep -q "^$string$" "$en_keys"; then
        echo -e "${RED}\"$string\"${NC}"
        ((missing_count_en++))
    fi
done < "$extracted_file"

if [ $missing_count_en -eq 0 ]; then
    echo "No missing translations in en.json"
else
    echo -e "${RED}Found $missing_count_en missing translations in en.json${NC}"
fi

# Check for missing translations in vi.json
echo -e "\n${GREEN}Missing in vi.json:${NC}"
missing_count_vi=0
while IFS= read -r string; do
    if ! grep -q "^$string$" "$vi_keys"; then
        echo -e "${RED}\"$string\"${NC}"
        ((missing_count_vi++))
    fi
done < "$extracted_file"

if [ $missing_count_vi -eq 0 ]; then
    echo "No missing translations in vi.json"
else
    echo -e "${RED}Found $missing_count_vi missing translations in vi.json${NC}"
fi

# Check for keys in en.json but not in vi.json
echo -e "\n${GREEN}In en.json but missing in vi.json:${NC}"
missing_count_en_vi=0
while IFS= read -r key; do
    if ! grep -q "^$key$" "$vi_keys"; then
        echo -e "${RED}\"$key\"${NC}"
        ((missing_count_en_vi++))
    fi
done < "$en_keys"

if [ $missing_count_en_vi -eq 0 ]; then
    echo "No keys in en.json that are missing in vi.json"
else
    echo -e "${RED}Found $missing_count_en_vi keys in en.json that are missing in vi.json${NC}"
fi

# Check for unnecessary translations (keys in locale files but not used in code)
echo -e "\n${GREEN}Checking for unnecessary translations...${NC}"

# Temp files for new JSON content
en_json_new=$(mktemp)
vi_json_new=$(mktemp)

# Check en.json for unused keys and create a new JSON without unused keys
echo -e "\n${YELLOW}Removing unused translations from en.json:${NC}"
unused_count_en=0
jq -c . ./app/locales/en.json > "$en_json_new.tmp"
while IFS= read -r key; do
    if ! grep -q "^$key$" "$extracted_file"; then
        # Also do a broader check in the codebase for this key
        if ! grep -r --include="*.py" "$key" ./app > /dev/null; then
            echo -e "${YELLOW}Removing \"$key\"${NC}"
            # Remove this key from the JSON
            jq "del(.[\"$key\"])" "$en_json_new.tmp" > "$en_json_new"
            mv "$en_json_new" "$en_json_new.tmp"
            ((unused_count_en++))
        fi
    fi
done < "$en_keys"

# Format the JSON nicely
jq . "$en_json_new.tmp" > "$en_json_new"

if [ $unused_count_en -eq 0 ]; then
    echo "No unused translations in en.json"
else
    echo -e "${YELLOW}Removed $unused_count_en unused translations from en.json${NC}"
    # Backup original file and replace with new one
    cp ./app/locales/en.json ./app/locales/en.json.bak
    cp "$en_json_new" ./app/locales/en.json
    echo -e "${GREEN}Updated en.json (backup saved as en.json.bak)${NC}"
fi

# Check vi.json for unused keys and create a new JSON without unused keys
echo -e "\n${YELLOW}Removing unused translations from vi.json:${NC}"
unused_count_vi=0
jq -c . ./app/locales/vi.json > "$vi_json_new.tmp"
while IFS= read -r key; do
    if ! grep -q "^$key$" "$extracted_file"; then
        # Also do a broader check in the codebase for this key
        if ! grep -r --include="*.py" "$key" ./app > /dev/null; then
            echo -e "${YELLOW}Removing \"$key\"${NC}"
            # Remove this key from the JSON
            jq "del(.[\"$key\"])" "$vi_json_new.tmp" > "$vi_json_new"
            mv "$vi_json_new" "$vi_json_new.tmp"
            ((unused_count_vi++))
        fi
    fi
done < "$vi_keys"

# Format the JSON nicely
jq . "$vi_json_new.tmp" > "$vi_json_new"

if [ $unused_count_vi -eq 0 ]; then
    echo "No unused translations in vi.json"
else
    echo -e "${YELLOW}Removed $unused_count_vi unused translations from vi.json${NC}"
    # Backup original file and replace with new one
    cp ./app/locales/vi.json ./app/locales/vi.json.bak
    cp "$vi_json_new" ./app/locales/vi.json
    echo -e "${GREEN}Updated vi.json (backup saved as vi.json.bak)${NC}"
fi

# Clean up temporary files
rm "$extracted_file" "$en_keys" "$vi_keys" "$en_json_new" "$en_json_new.tmp" "$vi_json_new" "$vi_json_new.tmp" 2>/dev/null

echo -e "\n${GREEN}Check complete. Unused translations have been removed.${NC}"