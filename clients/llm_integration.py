import os
import traceback

from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
# from commit_message_generator import generate_commit_message_prefix

# Replace with your API key and model name
API_KEY = "YOUR_API_KEY"
MODEL_NAME = "meta/llama3-70b-instruct"

llm = ChatNVIDIA(model=MODEL_NAME, api_key=API_KEY)

def split_diff(diff, chunk_size=1500, chunk_overlap=200):
    """Splits a large diff into smaller chunks with overlap."""
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(diff)
    return chunks

def generate_prompt(diff_chunk, old_description, is_partial=False):
    """Generates a prompt for Llama 3 based on diff chunk and old description."""
    # prefix = generate_commit_message_prefix(old_description)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are a helpful AI assistant that generates commit messages based on code changes and previous descriptions. Follow the commit guidelines of the GitHub repository."
            ),
            HumanMessage(content=f"Previous commit message: {old_description}"),
            HumanMessage(
                content=f"Code changes:{' (partial)' if is_partial else ''} \n```\n{diff_chunk}\n```"
            ),
            HumanMessage(content="Generate a new commit message based on these changes."),
        ]
    )
    prompt = prompt_template.format()
    return prompt

def generate_commit_description(history):
    """Generates a commit description for a potentially large diff."""
    logger.info(f'history.get_oldest_commit.diff: {history.get_oldest_commit().diff[:100]}')
    logger.info(f'history.get_oldest_commit.description: {history.get_oldest_commit().message}')
    logger.info(f'delete oldest_commit: {history.get_oldest_commit().delete()}')
    logger.info(f'history.get_oldest_commit.description: {history.get_oldest_commit().message}')
    diff, old_description = history
    if len(diff) <= 2000:
        # Diff is small enough, process directly
        prompt = generate_prompt(diff, old_description)
        new_description = llm.invoke(prompt).content
    else:
        # Split diff and process chunks
        chunks = split_diff(diff)
        partial_descriptions = []
        for i, chunk in enumerate(chunks):
            is_partial = i != len(chunks) - 1
            prompt = generate_prompt(chunk, old_description, is_partial)
            partial_description = llm.invoke(prompt).content
            partial_descriptions.append(partial_description)

        # Merge partial descriptions into final description
        merge_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="You are a helpful AI assistant that merges partial commit messages into a final, comprehensive message."
                ),
                HumanMessage(content="Partial commit messages:"),
            ]
            + [HumanMessage(content=desc) for desc in partial_descriptions]
            + [HumanMessage(content="Merge these into a single commit message.")]
        )
        new_description = llm.invoke(merge_prompt).content
    return new_description
