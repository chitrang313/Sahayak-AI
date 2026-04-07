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
