/**
 * Text processing utilities for message content
 */

/**
 * Convert single backticks `<text>` to single quotes '<text>' while preserving triple backticks (code blocks)
 * @param text - The input text to process
 * @returns Processed text with single backticks converted to quotes
 */
export function processSingleBackticks(text: string): string {
  if (!text) return text;

  // First, preserve all triple backtick code blocks
  const codeBlocks: string[] = [];
  const codeBlockPlaceholder = '___CODE_BLOCK_PLACEHOLDER___';
  
  // Extract and replace code blocks with placeholders
  let processedText = text.replace(/```[\s\S]*?```/g, (match) => {
    codeBlocks.push(match);
    return `${codeBlockPlaceholder}${codeBlocks.length - 1}`;
  });
  
  // Now process single backticks in the remaining text
  // This regex matches single backticks with content that are not adjacent to other backticks
  processedText = processedText.replace(/`([^`\n]+?)`/g, "'$1'");
  
  // Restore code blocks
  codeBlocks.forEach((codeBlock, index) => {
    processedText = processedText.replace(`${codeBlockPlaceholder}${index}`, codeBlock);
  });
  
  return processedText;
}

/**
 * Enhanced text processing that handles multiple text transformations
 * @param text - The input text to process
 * @returns Processed text with all transformations applied
 */
export function processMessageText(text: string): string {
  if (!text) return text;
  
  // Apply backtick to quotes conversion
  const processedText = processSingleBackticks(text);
  
  // Add more text processing functions here as needed
  // For example: processedText = removeExtraSpaces(processedText);
  
  return processedText;
}

/**
 * Utility to check if text contains code blocks
 * @param text - The text to check
 * @returns True if text contains code blocks (triple backticks)
 */
export function hasCodeBlocks(text: string): boolean {
  return /```[\s\S]*?```/.test(text);
}

/**
 * Extract code blocks from text
 * @param text - The text to extract from
 * @returns Array of code block contents (without the triple backticks)
 */
export function extractCodeBlocks(text: string): string[] {
  const matches = text.match(/```[\s\S]*?```/g);
  if (!matches) return [];
  
  return matches.map(match => 
    match.replace(/^```[^\n]*\n?/, '').replace(/\n?```$/, '')
  );
}

/**
 * Remove code blocks from text, leaving only regular text content
 * @param text - The text to process
 * @returns Text with code blocks removed
 */
export function removeCodeBlocks(text: string): string {
  return text.replace(/```[\s\S]*?```/g, '');
}
