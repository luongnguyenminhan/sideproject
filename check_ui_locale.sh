#!/bin/bash

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Reading translations and detecting usage..."

# Create temporary files
extracted_file=$(mktemp)
usage_file=$(mktemp)
output_json=$(mktemp)

# Find all t('...') patterns with dot notation only - must contain at least one dot
# This regex specifically looks for t('key.subkey') or t("key.subkey") patterns
find ./frontend/src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec grep -Hn "t(['\"][a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*['\"])" {} \; | 
sed -n "s/\(.*\):\(.*\).*t(['\"]\\([a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*\\)['\"])/\\1:\\2:\\3/p" > "$usage_file"

# Extract translation keys with dot notation only - improved regex
find ./frontend/src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -print0 | 
xargs -0 grep -Ho "t(['\"][a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*['\"])" | 
grep -o "t(['\"][a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*['\"])" | 
sed "s/t(['\"]//; s/['\"])$//" | 
sort -u >> "$extracted_file"

# More comprehensive pattern matching for dot notation with different quote types
find ./frontend/src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec grep -Hn "t('[a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*')" {} \; | 
sed "s/.*t('\\([a-zA-Z][a-zA-Z0-9]*\\.[a-zA-Z0-9.]*\\)').*/\\1/" >> "$extracted_file"

find ./frontend/src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec grep -Hn 't("[a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z0-9.]*")' {} \; | 
sed 's/.*t("\\([a-zA-Z][a-zA-Z0-9]*\\.[a-zA-Z0-9.]*\\)").*/\\1/' >> "$extracted_file"

# Remove duplicates and sort
sort -u "$extracted_file" -o "$extracted_file"

echo "Found $(wc -l < "$extracted_file") unique translation strings with dot notation in frontend code."

# Function to generate nested JSON structure
generate_nested_json() {
    local keys_file=$1
    local output_file=$2
    
    # Start with empty object
    echo "{}" > "$output_file"
    
    while IFS= read -r key; do
        # Skip empty lines
        [ -z "$key" ] && continue
        
        # Validate that the key has proper dot notation format
        if [[ ! "$key" =~ ^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z0-9]+)+$ ]]; then
            continue
        fi
        
        # Split key by dots and build nested structure
        IFS='.' read -ra PARTS <<< "$key"
        
        # Build jq expression to set nested value
        jq_path=""
        for i in "${!PARTS[@]}"; do
            if [ $i -eq 0 ]; then
                jq_path=".\"${PARTS[$i]}\""
            else
                jq_path="$jq_path.\"${PARTS[$i]}\""
            fi
        done
        
        # Set the value to "Waiting for translation"
        jq "$jq_path = \"Waiting for translation\"" "$output_file" > "${output_file}.tmp" && mv "${output_file}.tmp" "$output_file"
        
    done < "$keys_file"
}

# Function to get nested JSON keys with dot notation
get_nested_keys() {
    local json_file=$1
    if [ -f "$json_file" ]; then
        jq -r '
            def paths: 
                if type == "object" then
                    to_entries[] | 
                    .key as $k | 
                    .value | 
                    if type == "object" then
                        paths | "\($k).\(.)"
                    else
                        $k
                    end
                else
                    empty
                end;
            paths
        ' "$json_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Generate the main output JSON
echo "{" > "$output_json"
echo "  \"summary\": {" >> "$output_json"
echo "    \"totalTranslationKeys\": $(wc -l < "$extracted_file")," >> "$output_json"

# Count existing keys in en.json and vi.json if they exist
en_keys=$(mktemp)
vi_keys=$(mktemp)
en_count=0
vi_count=0

if [ -f "./frontend/src/locales/en.json" ]; then
    get_nested_keys ./frontend/src/locales/en.json > "$en_keys"
    en_count=$(wc -l < "$en_keys")
fi

if [ -f "./frontend/src/locales/vi.json" ]; then
    get_nested_keys ./frontend/src/locales/vi.json > "$vi_keys"
    vi_count=$(wc -l < "$vi_keys")
fi

echo "    \"totalEnKeys\": $en_count," >> "$output_json"
echo "    \"totalViKeys\": $vi_count" >> "$output_json"
echo "  }," >> "$output_json"

# Add usage information
echo "  \"usage\": [" >> "$output_json"
first=true
while IFS=: read -r file line key; do
    # Validate the key format before adding to JSON
    if [[ "$key" =~ ^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z0-9]+)+$ ]]; then
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$output_json"
        fi
        # Remove ./frontend/src prefix from file path
        clean_file=$(echo "$file" | sed 's|^\./frontend/src/||')
        echo -n "    {" >> "$output_json"
        echo -n "\"file\": \"$clean_file\", " >> "$output_json"
        echo -n "\"line\": $line, " >> "$output_json"
        echo -n "\"key\": \"$key\"" >> "$output_json"
        echo -n "}" >> "$output_json"
    fi
done < "$usage_file"
echo "" >> "$output_json"
echo "  ]," >> "$output_json"

# Generate the nested structure for used translations
temp_nested=$(mktemp)
generate_nested_json "$extracted_file" "$temp_nested"

echo "  \"usedTranslations\": " >> "$output_json"
cat "$temp_nested" >> "$output_json"
echo "," >> "$output_json"

# Add analysis section
echo "  \"analysis\": {" >> "$output_json"

# Check missing in existing locale files
echo "    \"missingInEn\": [" >> "$output_json"
first=true
while IFS= read -r key; do
    # Validate key format and check if it exists in en.json
    if [[ "$key" =~ ^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z0-9]+)+$ ]]; then
        if [ -f "./frontend/src/locales/en.json" ] && ! grep -Fxq "$key" "$en_keys"; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$output_json"
            fi
            echo -n "      \"$key\"" >> "$output_json"
        elif [ ! -f "./frontend/src/locales/en.json" ]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$output_json"
            fi
            echo -n "      \"$key\"" >> "$output_json"
        fi
    fi
done < "$extracted_file"
echo "" >> "$output_json"
echo "    ]," >> "$output_json"

echo "    \"missingInVi\": [" >> "$output_json"
first=true
while IFS= read -r key; do
    # Validate key format and check if it exists in vi.json
    if [[ "$key" =~ ^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z0-9]+)+$ ]]; then
        if [ -f "./frontend/src/locales/vi.json" ] && ! grep -Fxq "$key" "$vi_keys"; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$output_json"
            fi
            echo -n "      \"$key\"" >> "$output_json"
        elif [ ! -f "./frontend/src/locales/vi.json" ]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$output_json"
            fi
            echo -n "      \"$key\"" >> "$output_json"
        fi
    fi
done < "$extracted_file"
echo "" >> "$output_json"
echo "    ]" >> "$output_json"

echo "  }" >> "$output_json"
echo "}" >> "$output_json"

# Validate JSON before proceeding
if ! jq empty "$output_json" 2>/dev/null; then
    echo -e "${RED}Error: Generated JSON is invalid. Please check the script.${NC}"
    exit 1
fi

# Display the results
echo -e "\n${GREEN}Translation Analysis Complete!${NC}"
echo -e "\n${BLUE}Summary:${NC}"
echo -e "Total translation keys with dot notation: ${YELLOW}$(wc -l < "$extracted_file")${NC}"
echo -e "Keys found in en.json: ${YELLOW}$en_count${NC}"  
echo -e "Keys found in vi.json: ${YELLOW}$vi_count${NC}"

# Save to file
output_file="translation_analysis_$(date +%Y%m%d_%H%M%S).json"
cp "$output_json" "$output_file"
echo -e "\n${GREEN}Results saved to: $output_file${NC}"

# Show a sample of the used translations structure
echo -e "\n${BLUE}Sample Used Translations Structure:${NC}"
if command -v jq >/dev/null 2>&1; then
    jq '.usedTranslations' "$output_json" | head -n 20
else
    head -n 20 "$temp_nested"
fi
echo "..."

# Show some analysis
echo -e "\n${BLUE}Analysis Summary:${NC}"
if command -v jq >/dev/null 2>&1; then
    missing_en=$(jq '.analysis.missingInEn | length' "$output_json")
    missing_vi=$(jq '.analysis.missingInVi | length' "$output_json")
else
    missing_en=$(grep -c '"' "$output_json" | grep missingInEn || echo "0")
    missing_vi=$(grep -c '"' "$output_json" | grep missingInVi || echo "0")
fi
echo -e "Missing in en.json: ${RED}$missing_en${NC}"
echo -e "Missing in vi.json: ${RED}$missing_vi${NC}"

# Clean up temporary files
rm "$extracted_file" "$usage_file" "$output_json" "$temp_nested" "$en_keys" "$vi_keys" 2>/dev/null

echo -e "\n${GREEN}Analysis exported to JSON format!${NC}"