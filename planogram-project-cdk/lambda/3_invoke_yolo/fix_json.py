import json
import re

def fix_json_newlines(json_string):
    """
    Fix JSON string by properly escaping newline characters
    """
    # Method 1: Replace literal \n with \\n in the JSON string
    # This regex finds \n that are inside quoted strings
    pattern = r'("(?:[^"\\]|\\.)*")'
    
    def replace_newlines(match):
        # Replace unescaped newlines within the matched string
        content = match.group(1)
        # Replace actual newline characters with escaped version
        content = content.replace('\n', '\\n')
        return content
    
    fixed_json = re.sub(pattern, replace_newlines, json_string)
    return fixed_json

def parse_json_safely(json_string):
    """
    Safely parse JSON with multiple fallback methods
    """
    # Method 1: Try parsing as-is
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Initial parse failed: {e}")
        
        # Method 2: Try fixing newlines
        try:
            fixed_json = fix_json_newlines(json_string)
            return json.loads(fixed_json)
        except json.JSONDecodeError as e:
            print(f"Parse with fixed newlines failed: {e}")
            
            # Method 3: Remove all newlines and extra spaces
            try:
                # Remove newlines and collapse multiple spaces
                cleaned_json = ' '.join(json_string.split())
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                print(f"Parse with removed newlines failed: {e}")
                raise

def create_clean_json_response(response):
    """
    Create a properly formatted JSON response
    """
    return json.dumps(response, ensure_ascii=False, indent=2)

def create_structured_json_response(response):
    """
    Create a better structured JSON response
    """
    return json.dumps(response, ensure_ascii=False, indent=2)

# Example usage in Lambda function
def fix_json_structure(response):
    try:
        # Method 1: Use safe parser
        llm_result = parse_json_safely(response)
        print("Successfully parsed JSON:")
        print(json.dumps(llm_result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"All parsing methods failed: {e}")
        
        # Fallback: Generate clean JSON
        print("\nGenerating clean JSON instead:")
        clean_json = create_clean_json_response()
        llm_result = json.loads(clean_json)
        # print(clean_json)
    
    return  json.dumps(llm_result, ensure_ascii=False)

