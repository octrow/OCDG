from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class LLMInterface:
    """Handles interaction with the chosen Large Language Model using LangChain."""

    def __init__(self, llm_type, **kwargs):
        """Initializes the LLM based on the provided type and settings."""
        if llm_type == "openai":
            self.llm = OpenAI(**kwargs)  # Pass OpenAI specific arguments here (e.g., api_key, temperature)
        # Add elif conditions for other LLMs (Llama3, Gemini) with their respective initialization
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

        # Define a prompt template for commit message generation
        self.prompt_template = PromptTemplate(
            input_variables=["diff", "old_message"],
            template="""
            ## Commit Message Generation

            **Diff:**
            ```diff
            {diff}
            ```

            **Old Message:**
            {old_message}

            **New Message (Conventional Commit format):**
            """,
        )

    def generate_commit_message(self, diff, old_message):
        """Generates a new commit message using the LLM."""
        prompt = self.prompt_template.format(diff=diff, old_message=old_message)
        new_message = self.llm(prompt)
        return new_message.strip()