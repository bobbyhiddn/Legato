#!/usr/bin/env python3
"""
Claude API wrapper for LEGATO.

Provides utilities for calling Claude API with prompts from the prompts/ directory.

Usage:
    python call_claude.py --prompt classifier --input "transcript text"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)


def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.md"

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")

    return prompt_file.read_text()


def call_claude(
    prompt_name: str,
    user_input: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    system_override: Optional[str] = None
) -> str:
    """
    Call Claude API with a prompt template.

    Args:
        prompt_name: Name of the prompt file (without .md extension)
        user_input: The user's input to process
        model: Claude model to use
        max_tokens: Maximum tokens in response
        system_override: Optional system prompt override

    Returns:
        Claude's response text
    """
    client = anthropic.Anthropic()

    # Load the prompt template
    prompt_template = load_prompt(prompt_name)

    # Use template as system prompt unless override provided
    system_prompt = system_override or prompt_template

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_input}
        ]
    )

    return message.content[0].text


def call_claude_json(
    prompt_name: str,
    user_input: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096
) -> dict:
    """
    Call Claude API and parse JSON response.

    Args:
        prompt_name: Name of the prompt file
        user_input: The user's input to process
        model: Claude model to use
        max_tokens: Maximum tokens in response

    Returns:
        Parsed JSON response
    """
    response = call_claude(prompt_name, user_input, model, max_tokens)

    # Try to extract JSON from the response
    # Claude sometimes wraps JSON in markdown code blocks
    text = response.strip()

    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def main():
    parser = argparse.ArgumentParser(description="Call Claude API with a prompt")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt name (e.g., classifier, knowledge-extractor)"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input text or @filename to read from file"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Parse response as JSON"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Handle input from file
    if args.input.startswith("@"):
        input_file = Path(args.input[1:])
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)
        user_input = input_file.read_text()
    else:
        user_input = args.input

    try:
        if args.json:
            result = call_claude_json(args.prompt, user_input, args.model)
            output = json.dumps(result, indent=2)
        else:
            output = call_claude(args.prompt, user_input, args.model)

        if args.output:
            Path(args.output).write_text(output)
            print(f"Output written to {args.output}")
        else:
            print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIError as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
