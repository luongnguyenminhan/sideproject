#!/bin/bash

# filepath: /Users/anlnm/Desktop/Project/meobeo-ai-api/check_exception.sh

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}Analyzing exception usage patterns in Python files...${NC}"

# Check for raw Exception or HTTPException that are not CustomHTTPException
echo -e "\n${BLUE}Checking for raw Exception or HTTPException usage:${NC}"
raw_exceptions=$(find ./app -type f -name "*.py" | xargs grep -l "raise \(Exception\|HTTPException\)" 2>/dev/null)

if [ -z "$raw_exceptions" ]; then
    echo -e "${GREEN}No raw Exception or HTTPException usage found. Good job!${NC}"
else
    echo -e "${RED}Found raw Exception or HTTPException usage in the following files:${NC}"
    for file in $raw_exceptions; do
        echo -e "\n${YELLOW}$file:${NC}"
        grep -n "raise \(Exception\|HTTPException\)" "$file" | 
        while IFS=":" read -r line_num content; do
            echo -e "${RED}Line $line_num:${NC} $content"
        done
    done
fi

# Check for CustomHTTPException usage patterns
echo -e "\n${BLUE}Checking CustomHTTPException usage patterns:${NC}"

custom_exceptions=$(find ./app -type f -name "*.py" | xargs grep -l "raise.*CustomHTTPException" 2>/dev/null)

if [ -z "$custom_exceptions" ]; then
    echo -e "${YELLOW}No CustomHTTPException usage found.${NC}"
else
    echo -e "${GREEN}Analyzing CustomHTTPException patterns in files...${NC}"
    
    # Track error counts
    missing_status=0
    invalid_status=0
    missing_message=0
    invalid_message=0
    extra_attrs=0
    
    for file in $custom_exceptions; do
        # Extract all raise CustomHTTPException instances with their line numbers
        while IFS= read -r line_info; do
            if [ -z "$line_info" ]; then
                continue
            fi
            
            line_num=$(echo "$line_info" | cut -d':' -f1)
            
            # Extract all lines of the exception, from raise to the closing parenthesis
            exception_text=""
            parenthesis_count=0
            in_exception=false
            current_line=$line_num
            
            while true; do
                line_content=$(sed -n "${current_line}p" "$file")
                
                if echo "$line_content" | grep -q "raise.*CustomHTTPException"; then
                    in_exception=true
                    exception_text+="$line_content"
                    # Count opening parentheses
                    open_count=$(echo "$line_content" | grep -o "(" | wc -l)
                    # Count closing parentheses
                    close_count=$(echo "$line_content" | grep -o ")" | wc -l)
                    parenthesis_count=$((parenthesis_count + open_count - close_count))
                elif [ "$in_exception" = true ]; then
                    exception_text+="$line_content"
                    # Count opening parentheses
                    open_count=$(echo "$line_content" | grep -o "(" | wc -l)
                    # Count closing parentheses
                    close_count=$(echo "$line_content" | grep -o ")" | wc -l)
                    parenthesis_count=$((parenthesis_count + open_count - close_count))
                fi
                
                # Exit if we've found the closing parenthesis or reached EOF
                if [ "$in_exception" = true ] && [ $parenthesis_count -le 0 ]; then
                    break
                fi
                
                current_line=$((current_line + 1))
                # Check if we've reached EOF
                if [ $current_line -gt $(wc -l < "$file") ]; then
                    break
                fi
            done
            
            # Clean up the exception text
            exception_text=$(echo "$exception_text" | tr -d '\n' | sed 's/  */ /g')
            
            has_error=false
            
            # Check if status_code attribute exists
            if ! echo "$exception_text" | grep -q "status_code="; then
                echo -e "\n${RED}[$file:$line_num] Missing status_code attribute:${NC}"
                echo "  $exception_text"
                missing_status=$((missing_status + 1))
                has_error=true
            # Check if status_code uses status.XXX format
            elif ! echo "$exception_text" | grep -q "status_code=status"; then
                echo -e "\n${RED}[$file:$line_num] status_code should use 'status.XXX' format:${NC}"
                echo "  $exception_text"
                invalid_status=$((invalid_status + 1))
                has_error=true
            fi
            
            # Check if message attribute exists
            if ! echo "$exception_text" | grep -q "message="; then
                echo -e "\n${RED}[$file:$line_num] Missing message attribute:${NC}"
                echo "  $exception_text"
                missing_message=$((missing_message + 1))
                has_error=true
            # Check if message uses translation pattern _('string')
            elif ! echo "$exception_text" | grep -q "message=_([\"'][^\"']*[\"'])"; then
                echo -e "\n${RED}[$file:$line_num] message should use translation pattern _('string'):${NC}"
                echo "  $exception_text"
                invalid_message=$((invalid_message + 1))
                has_error=true
            fi
            
            # Check for extra attributes
            extra_attr=$(echo "$exception_text" | grep -o "[a-zA-Z_][a-zA-Z0-9_]*=" | grep -v "status_code=" | grep -v "message=")
            if [ ! -z "$extra_attr" ]; then
                echo -e "\n${RED}[$file:$line_num] Found extra attributes (only status_code and message allowed):${NC}"
                echo "  $exception_text"
                echo -e "  ${YELLOW}Extra attributes: $extra_attr${NC}"
                extra_attrs=$((extra_attrs + 1))
                has_error=true
            fi
            
            # Print exceptions with correct format for reference
            if [ "$has_error" = true ]; then
                echo -e "${GREEN}Correct format should be: CustomHTTPException(status_code=status.XXX, message=_('message'))${NC}"
            fi
            
        done < <(grep -n "raise.*CustomHTTPException" "$file")
    done
    
    # Summary of findings
    echo -e "\n${BLUE}Exception Check Summary:${NC}"
    
    total_errors=$((missing_status + invalid_status + missing_message + invalid_message + extra_attrs))
    
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}All CustomHTTPException usages follow the correct pattern. Great job!${NC}"
    else
        echo -e "${RED}Found $total_errors issues with CustomHTTPException usage:${NC}"
        [ $missing_status -gt 0 ] && echo -e "${RED}- Missing status_code attribute: $missing_status occurrences${NC}"
        [ $invalid_status -gt 0 ] && echo -e "${RED}- Invalid status_code format: $invalid_status occurrences${NC}"
        [ $missing_message -gt 0 ] && echo -e "${RED}- Missing message attribute: $missing_message occurrences${NC}"
        [ $invalid_message -gt 0 ] && echo -e "${RED}- Invalid message translation format: $invalid_message occurrences${NC}"
        [ $extra_attrs -gt 0 ] && echo -e "${RED}- Extra attributes found: $extra_attrs occurrences${NC}"
        
        echo -e "\n${YELLOW}Please update these instances to follow the pattern:${NC}"
        echo -e "${GREEN}CustomHTTPException(status_code=status.XXX, message=_('message'))${NC}"
    fi
fi

echo -e "\n${GREEN}Exception pattern check complete.${NC}"