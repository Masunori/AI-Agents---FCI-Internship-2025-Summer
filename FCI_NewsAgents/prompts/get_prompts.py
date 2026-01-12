guardrail_prompt_path = r"FCI_NewsAgents\prompts\guardrails_prompt.md"
pointwise_prompt_path = r"FCI_NewsAgents\prompts\pointwise_guardrails_prompt.md"
generation_prompt_path = r"FCI_NewsAgents\prompts\report_generation_prompt.md"

def get_guardrails_prompt() -> str:
    try:
        with open(guardrail_prompt_path, 'r', encoding= 'utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"Error: {e}")
        return ""

def get_generation_prompt() -> str:
    try:
        with open(generation_prompt_path, 'r', encoding= 'utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"Error: {e}")
        return ""
    
def get_pointwise_guardrails_prompt() -> str:
    try:
        with open(pointwise_prompt_path, 'r', encoding= 'utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"Error: {e}")
        return ""

if __name__ == "__main__":
    print(get_generation_prompt()[:100])

