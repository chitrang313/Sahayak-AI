"""Prompt builders for the Sahayak AI desktop app."""

from __future__ import annotations


RESPONSE_LENGTH_GUIDANCE = {
    "Short response message": (
        "Keep the response concise, focused, and compact while still being complete."
    ),
    "Mid response message": (
        "Provide a balanced response with practical detail and clear structure."
    ),
    "Long response message": (
        "Provide a detailed, well-structured response with richer depth where helpful."
    ),
}

DEVELOPER_MODE_OPTIONS = [
    ("code_explain", "Code Understanding"),
    ("debug", "Debugging Errors"),
    ("refactor", "Code Refactoring"),
    ("boilerplate", "Boilerplate Code Generation"),
    ("api_explain", "API Understanding"),
    ("precommit", "Pre-Commit Code Validation"),
    ("security", "Security Analysis"),
    ("performance", "Performance Optimization"),
]

BOILERPLATE_LANGUAGES = [
    "C#",
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "Go",
    "C++",
    "PHP",
]

LANGUAGE_FENCE_TAGS = {
    "C#": "csharp",
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Java": "java",
    "Go": "go",
    "C++": "cpp",
    "PHP": "php",
}


def build_chat_prompt(history: list[dict[str, str]]) -> str:
    """Build a conversational prompt from prior messages."""
    lines = [
        "You are Sahayak AI, a precise and helpful AI assistant inside the Sahayak AI desktop app.",
        "Answer accurately, naturally, and directly.",
        "If the user asks for code or technical help, provide clear and correct guidance.",
        "Do not invent facts. If something is uncertain, say so plainly.",
        "",
        "Conversation:",
    ]

    for item in history:
        role = "User" if item["role"] == "user" else "Assistant"
        lines.append(f"{role}: {item['content'].strip()}")

    lines.append("Assistant:")
    return "\n".join(lines)


def build_developer_prompt(
    mode: str,
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build one of the structured developer-assistant prompts."""
    builders = {
        "code_explain": _build_code_explain_prompt,
        "debug": _build_debug_prompt,
        "refactor": _build_refactor_prompt,
        "boilerplate": _build_boilerplate_prompt,
        "api_explain": _build_api_explain_prompt,
        "precommit": _build_precommit_prompt,
        "security": _build_security_prompt,
        "performance": _build_performance_prompt,
    }

    try:
        builder = builders[mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported developer mode: {mode}") from exc

    return builder(prepared_input, language=language)


def _developer_prompt_prefix() -> str:
    """Shared rules for developer-focused prompts."""
    return (
        "Role: Senior developer.\n"
        "Strict rules:\n"
        "- Use only the provided input.\n"
        "- Do not hallucinate missing files, runtime behavior, APIs, or test results.\n"
        "- If the input is incomplete or truncated, mention that briefly instead of guessing.\n"
        "- Keep the output structured, practical, and directly useful.\n\n"
    )


def _developer_prompt_suffix() -> str:
    """Shared ending for developer-focused prompts."""
    return "Return ONLY the requested format. Do not add extra explanation."


def _build_code_explain_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the code understanding prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Explain the provided file or directory context. Focus on the purpose, flow, "
        "main components, and practical risks that are clearly supported by the input.\n\n"
        "Output Format:\n"
        "Purpose\n"
        "- One or more bullets describing what the code is for.\n"
        "Flow\n"
        "- Step-by-step bullets describing how the logic moves.\n"
        "Components\n"
        "- Component or file name: responsibility.\n"
        "Risks\n"
        "- Concrete risks, assumptions, or weak spots.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_debug_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the debugging prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Analyze the error text. Explain the likely root cause in simple language, say "
        "where the user should look first, and suggest the most direct fix. If the error "
        "text is not enough to know the exact cause, say the most likely cause and note "
        "what detail is missing.\n\n"
        "Output Format:\n"
        "Root Cause\n"
        "- Clear and simple explanation.\n"
        "Why It Happened\n"
        "- Short bullets describing the chain of events.\n"
        "Where To Check First\n"
        "- The first file, config, log, or code area to inspect.\n"
        "Fix\n"
        "- Direct steps to resolve it.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_refactor_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the code refactoring prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Review the provided code, identify design or readability issues, and refactor it "
        "without changing the behavior. Keep the same language and preserve functionality.\n\n"
        "Output Format:\n"
        "Issues\n"
        "- Problems or weaknesses in the original code.\n"
        "Refactored Code\n"
        "```text\n"
        "Provide only the improved code here.\n"
        "```\n"
        "Improvements\n"
        "- Short bullets describing what got better.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_boilerplate_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the boilerplate generation prompt."""
    selected_language = language or "Python"
    code_fence = LANGUAGE_FENCE_TAGS.get(selected_language, "text")
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        f"Generate optimized, production-ready boilerplate code in {selected_language}. "
        "Respect the selected language, include the full working code, and keep the "
        "implementation practical for real development.\n\n"
        "Output Format:\n"
        "Full Working Code\n"
        f"```{code_fence}\n"
        "Provide the complete implementation here.\n"
        "```\n"
        "Short Explanation\n"
        "- Brief bullets describing the main parts.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_api_explain_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the API understanding prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Explain the JSON structure clearly. Show the hierarchy in a tree-like layout, "
        "describe important fields in simple language, and give a short summary of what "
        "this payload represents.\n\n"
        "Output Format:\n"
        "Hierarchy\n"
        "- Use tree-style plain text to show nesting.\n"
        "Field Explanation\n"
        "- field.path: simple explanation.\n"
        "Short Summary\n"
        "- Concise summary bullets.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_precommit_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the pre-commit review prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Act as a strict code reviewer for the provided git changes. Focus on bugs, "
        "logic problems, regression risk, weak validation, unsafe assumptions, and poor "
        "maintainability. Do not praise the code. Only report findings supported by the input.\n\n"
        "Output Format:\n"
        "Critical Issues\n"
        "- High-impact bugs or release blockers. Use '- None found.' if none exist.\n"
        "Logic Issues\n"
        "- Incorrect behavior, edge cases, or missing checks. Use '- None found.' if none exist.\n"
        "Code Smells\n"
        "- Maintainability or readability issues. Use '- None found.' if none exist.\n"
        "Suggestions\n"
        "- Practical next steps.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_security_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the security analysis prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Review the provided repository diff and file contents for security issues. Look "
        "for secrets, tokens, unsafe auth flows, injection risk, insecure storage, weak "
        "input handling, and clearly supported vulnerabilities.\n\n"
        "Output Format:\n"
        "Vulnerabilities\n"
        "- One bullet per issue. Use '- None found.' if no clear issue is supported.\n"
        "Severity\n"
        "- Map each issue to High, Medium, or Low with a short reason.\n"
        "Fix Suggestions\n"
        "- Direct mitigation steps.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def _build_performance_prompt(
    prepared_input: str,
    *,
    language: str | None = None,
) -> str:
    """Build the performance optimization prompt."""
    del language
    return (
        f"{_developer_prompt_prefix()}"
        "Task:\n"
        "Analyze the provided code for performance bottlenecks. Suggest an optimized "
        "version that keeps the same behavior, and explain the likely impact of the changes.\n\n"
        "Output Format:\n"
        "Issues\n"
        "- Performance bottlenecks or wasteful patterns.\n"
        "Optimized Version\n"
        "```text\n"
        "Provide only the optimized code here.\n"
        "```\n"
        "Impact\n"
        "- Practical effect of the improvements.\n\n"
        "Input:\n"
        f"{prepared_input}\n\n"
        f"{_developer_prompt_suffix()}"
    )


def build_grammar_prompt(user_input: str) -> str:
    """Build the grammar correction prompt."""
    cleaned_input = user_input.strip()
    return (
        "You are an expert proofreader.\n"
        "Correct the spelling, grammar, punctuation, and minor clarity issues of the following text.\n"
        "Preserve the original meaning and tone.\n"
        "Only return the corrected version.\n\n"
        "Text:\n"
        f"\"{cleaned_input}\""
    )


def build_translation_prompt(
    user_input: str, source_language: str, target_language: str
) -> str:
    """Build the translator prompt."""
    cleaned_input = user_input.strip()
    return (
        "Act as a professional human translator.\n"
        f"Translate the text from {source_language} to {target_language} with high accuracy and natural fluency.\n"
        "Ensure the output sounds like a native speaker wrote it.\n"
        "Do not include any explanation.\n\n"
        "Text:\n"
        f"\"{cleaned_input}\""
    )


def build_email_prompt(
    title: str,
    name: str,
    subject: str,
    content: str,
    response_length: str,
    profile: dict[str, str],
) -> str:
    """Build the email helper prompt."""
    return (
        "You are a professional executive email writer.\n"
        "Write a polished, natural, and professional email that is ready to send.\n"
        f"Preferred response length: {response_length}\n"
        f"Length guidance: {RESPONSE_LENGTH_GUIDANCE[response_length]}\n"
        "Use the sender profile naturally in the sign-off when the information is available.\n"
        "Keep the message accurate, respectful, and aligned with the user's purpose.\n\n"
        "Recipient Details:\n"
        f"Recipient Title: {title}\n"
        f"Recipient Name: {name.strip()}\n"
        f"Subject: {subject.strip()}\n"
        f"Details: {content.strip()}\n\n"
        "Sender Profile:\n"
        f"Full Name: {profile.get('full_name', '').strip() or 'Not provided'}\n"
        f"Email Address: {profile.get('email', '').strip() or 'Not provided'}\n"
        f"Phone Number: {profile.get('phone', '').strip() or 'Not provided'}\n"
        f"LinkedIn Profile: {profile.get('linkedin', '').strip() or 'Not provided'}\n\n"
        "Return only the complete formatted email."
    )


def build_prompt_creator_prompt(
    category: str, user_input: str, response_length: str
) -> str:
    """Build the detailed prompt creator prompt."""
    cleaned_input = user_input.strip()
    return (
        "You are an expert AI assistant capable of handling multiple professional roles.\n\n"
        "## Task\n\n"
        "Based on the selected Category, generate a high-quality, structured, and professional response for the given user input.\n\n"
        "---\n\n"
        "## Context\n\n"
        "The user will select one category from:\n\n"
        "* Programmer\n"
        "* Designer\n"
        "* Content Writer\n"
        "* General Work\n"
        "* Medical Expert\n"
        "* Marketing Expert\n"
        "* Product Manager\n"
        "* Data Analyst\n"
        "* Teacher\n"
        "* Legal Advisor\n\n"
        "You must adapt your response style, depth, and format according to the selected category.\n\n"
        "---\n\n"
        "## Input\n\n"
        f"Category: {category}\n"
        f"User Request: \"{cleaned_input}\"\n"
        f"Preferred Response Length: {response_length}\n"
        f"Length Guidance: {RESPONSE_LENGTH_GUIDANCE[response_length]}\n\n"
        "---\n\n"
        "## Instructions\n\n"
        "1. First, understand the intent of the user request.\n\n"
        "2. Act as an expert in the selected category.\n\n"
        "3. Generate a response that is:\n\n"
        "   * Accurate\n"
        "   * Practical\n"
        "   * Easy to understand\n"
        "   * Well-structured\n\n"
        "4. Customize behavior based on category:\n\n"
        "* Programmer -> Provide code, logic, explanation\n"
        "* Designer -> Provide UI/UX structure, colors, layout\n"
        "* Content Writer -> Provide engaging written content\n"
        "* General Work -> Provide simple and useful answers\n"
        "* Medical Expert -> Provide general medical guidance with appropriate caution\n"
        "* Marketing Expert -> Provide strategy, copy, ideas\n"
        "* Product Manager -> Provide PRD, user stories, planning\n"
        "* Data Analyst -> Provide insights, breakdown, logic\n"
        "* Teacher -> Explain step-by-step clearly\n"
        "* Legal Advisor -> Provide general legal information without claiming formal legal representation\n\n"
        "---\n\n"
        "## Output Format\n\n"
        "Structure the response as:\n\n"
        "1. Understanding of Request\n"
        "2. Solution / Output\n"
        "3. Additional Suggestions (optional)\n\n"
        "---\n\n"
        "## Rules\n\n"
        "* Do NOT hallucinate unknown facts\n"
        "* Keep response relevant to selected category\n"
        "* Do NOT mix roles\n"
        "* Keep output clean and structured\n"
        "* Avoid unnecessary long explanations unless needed\n\n"
        "---\n\n"
        "## Goal\n\n"
        "Provide a professional, category-specific response that feels like it was created by a real expert in that domain."
    )
