# Standard library
import textwrap
from typing import Dict, Any

# Third party
from pathlib import Path

# Local modules
from api.services.text_handler import json_to_text

NATURE_KEYWORDS_MASTER_PATH = Path("data") / "nature_keywords_master.json"

def _format_question_sequence(questions_dict: Dict[str, Dict[str, Any]]) -> str:
    lines = []

    for q_id, q in questions_dict.items():
        # Do not include skipped questions in diplayed sequence
        if q.get("Skip_AI_Grading", False):
            continue

        question_id = q.get("Question_ID", q_id)
        question_text = q.get("Question_Text", "").strip()

        lines.append(f"- {question_id}: {question_text}")

    return "\n".join(lines)

def get_grading_system_prompt(transcript_text, questions_dict):
    return textwrap.dedent(f"""
        {GRADING_BASE_PROMPT}

        --------------------------------------------------
        CALL TRANSCRIPT
        --------------------------------------------------

        {transcript_text}

        --------------------------------------------------
        CORRECT QUESTION SEQUENCE
        --------------------------------------------------

        {_format_question_sequence(questions_dict)}
    """)


def get_single_question_prompt(question: Dict[str, Any]) -> str:
    def val(x):
        return "None" if x is None else str(x)

    recap = textwrap.dedent("""
        Evaluate ONLY the protocol question shown below using the full transcript already provided earlier in this conversation.

        Reminder of grading rules:
        - Assign exactly ONE grade code: [1] (Asked Correctly), [2] (Not Asked), [3] (Asked Incorrectly), [4] (Not as Scripted), [5] (Not Applicable), or [6] (Obvious)
        - Begin your response with the bracketed grade code
        - Default assumption: every protocol question shown should have been asked by the dispatcher
        - The ONLY exception is when the question has a Condition and that Condition is not met by transcript evidence
        - [3] takes priority if wording changes meaning, even if the question was also out of order
        - Use [4] only if the wording is acceptable but the sequencing is wrong
        - Use [6] only if the caller plainly and directly stated the answer to this exact question, with no assumption or context required
        - Base your decision only on transcript evidence
        - Speaker labels may be incorrect; if the exchange appears implausible, use the most reasonable interpretation of who is speaking, but do not invent missing dialogue
        - After the grade, give concise reasoning and include direct supporting quote(s) with speaker, timestamp, and exact wording
        - Do not grade any other question
    """)

    core_info = textwrap.dedent(f"""
        Protocol Question:
        - Parent ID: {val(question.get("Parent_Question_ID"))}
        - Question ID: {val(question.get("Question_ID"))}
        - Text: {val(question.get("Question_Text"))}
    """)

    metadata = textwrap.dedent(f"""
        Associated Metadata:
        - Allowed Alternatives: {val(question.get("Allowed_Alternatives"))}
        - Condition: {val(question.get("Condition"))}
        - Situation: {val(question.get("Situation"))}
        - Scenario: {val(question.get("Scenario"))}
    """)

    return "\n".join([recap, core_info, metadata])

def get_nature_code_prompt(transcript_path, nature_codes_master):
    # Load transcript text
    transcript_text = json_to_text(file_path=transcript_path)

    # Format nature codes cleanly
    formatted_codes = []

    for code_id, code_data in nature_codes_master.items():
        # Skip case entry
        if str(code_id) == "0":
            continue

        nature_code_name = code_data.get("nature_code_name", "Unknown")
        classification = code_data.get("classification", {})
        keywords = classification.get("keywords", []) or []
        # common_confusions = classification.get("common_confusions", []) or []

        keyword_text = ", ".join(map(str, keywords)) if keywords else "None"

        formatted_codes.append(
            f"Nature Code ID [{code_id}]: {nature_code_name}\n"
            f"Keywords: {keyword_text}\n"
        )

    nature_codes_text = "\n\n".join(formatted_codes)

    output_format_reminder = textwrap.dedent("""
    --------------------------------------------------
    OUTPUT FORMAT REMINDER (IMPORTANT)
    --------------------------------------------------

    Return your answer in the following format:

    [ID] (NUMBER IN BRACKETS ONLY)

    Reasoning:
    - CONCISELY explain why this is the correct classification
    - Reference key parts of the transcript and/or keyword matches

    Possible Confusions (for each):
    - Nature code name
    - Why it could apply:
    - Why it is incorrect:

    (Include 2-3 total confusion comparisons)    
    """)

    return (
        f"{NATURE_CODE_PROMPT}\n\n"
        f"AVAILABLE NATURE CODES:\n"
        f"{nature_codes_text}\n\n"
        f"TRANSCRIPT:\n"
        f"{transcript_text}\n\n"
        f"{output_format_reminder}"
    )

GRADING_BASE_PROMPT = textwrap.dedent("""
    You are an expert evaluator of emergency dispatch (EMS/911) call transcripts. Your task is to analyze a dispatcher-caller conversation and grade whether a specific protocol question was handled correctly.

    You will be given:
    - A full transcript (with timestamps and speaker labels)
    - A single protocol question to evaluate

    You must assign exactly ONE grade code and justify it using the transcript.

    --------------------------------------------------
    GRADING CODES
    --------------------------------------------------

    1 = Asked Correctly  
    - Question was asked
    - Correct order
    - Meaning and intent preserved

    2 = Not Asked  
    - Question should have been asked based on context
    - It was omitted

    3 = Asked Incorrectly  
    - Question was asked, but wording altered meaning or intent
    - Includes leading, biased, or incomplete phrasing

    4 = Not As Scripted  
    - Question was asked with acceptable meaning
    - But asked out of order

    5 = Not Applicable  
    - Use only when the protocol question has a Condition and transcript evidence shows that Condition was not met

    6 = Obvious  
    - Caller plainly and directly stated the answer to the given question
    - No assumption, inference, or surrounding context is required to know the answer
    - Dispatcher appropriately did not ask it again

    --------------------------------------------------
    GRADING PRIORITY RULES
    --------------------------------------------------

    - If wording changes meaning → ALWAYS use (3), even if also out of order
    - Use (4) ONLY when wording is acceptable but sequencing is wrong
    - Use (6) ONLY when the answer to the given question is plainly, directly stated by the caller
    - Do NOT use (6) when the answer requires assumption, inference, interpretation, or surrounding context
    - Every protocol question presented to you SHOULD HAVE BEEN ASKED BY THE DISPATCHER by default
    - The ONLY TIME a presented question should not be asked is when it has a Condition and that Condition is not met by transcript evidence
    - If a question has no Condition, treat it as required and grade an omission as (2), not (5)
    - Do not infer missing context—base decisions only on transcript evidence
    - Evaluate strictly—protocol compliance overrides conversational naturalness

    --------------------------------------------------
    TRANSCRIPT RELIABILITY NOTE
    --------------------------------------------------

    - Speaker labels in the transcript may sometimes be incorrect
    - If the transcript appears to show the dispatcher talking to themselves, answering their own question, failing to wait for a caller response when one would normally be expected, or otherwise producing an implausible exchange, consider the possibility that speaker labels were assigned incorrectly
    - In those cases, evaluate the exchange based on the most reasonable interpretation of who is actually speaking
    - Do not automatically penalize the dispatcher for transcript labeling errors
    - However, do not invent missing dialogue; only reinterpret speaker identity when the transcript strongly suggests a labeling mistake
    - If quoting segments from the transcript you believe are mislabeled, do not relabel them, report them as is

    --------------------------------------------------
    EVALUATION RULES
    --------------------------------------------------

    - Do NOT assume intent; evaluate observable behavior only
    - Do NOT reward "reasonable" phrasing if it violates protocol intent
    - Identify whether the dispatcher preserved:
    - Meaning
    - Order
    - Necessity (should it have been asked?)
    - Consider surrounding context in the transcript only when determining whether an explicit Condition was met
    - Do not mark a question Not Applicable just because it seems unnecessary or conversationally redundant

    --------------------------------------------------
    OUTPUT FORMAT (STRICT)
    --------------------------------------------------

    Your response MUST:

    1. Begin with the grade code in brackets (e.g., [1], [2], etc.)
    2. Follow with a clear explanation of why that grade was assigned
    3. Include one or more DIRECT QUOTES from the transcript as evidence

    QUOTE REQUIREMENTS:
    - Quotes must include speaker label, timestamp, and exact wording
    - Quotes must directly support your reasoning
    - Do not paraphrase transcript content

    STYLE CONSTRAINTS:
    - Do not include JSON
    - Do not include bullet points
    - Do not include multiple grades
    - Do not omit explanation or evidence
    - Keep reasoning concise but specific

    --------------------------------------------------
    FINAL INSTRUCTION
    --------------------------------------------------

    Return exactly one grade with supporting reasoning and transcript evidence. No extra formatting or sections.
""")

NATURE_CODE_PROMPT = textwrap.dedent("""
    You are an expert EMS dispatch analyst responsible for determining the correct Nature Code for a 911 call.

    You will be given:
    - A full dispatcher-caller transcript
    - A list of Nature Codes with associated keywords and example phrases

    Your task is to determine the MOST APPROPRIATE Nature Code based on the ROOT CAUSE or INITIAL MECHANISM of the call.

    --------------------------------------------------
    CORE PRINCIPLE (CRITICAL)
    --------------------------------------------------

    The Nature Code must reflect the FIRST event or mechanism that led to the call, NOT secondary symptoms or later developments.

    Examples:
    - A fall followed by dizziness or vomiting → Falls (NOT Sick Person or Headache)
    - Allergic reaction causing breathing difficulty → Allergic Reaction (NOT Breathing Problems)
    - Substance exposure causing symptoms → Hazmat/Inhalation (NOT Breathing Problems)

    --------------------------------------------------
    CLASSIFICATION RULES
    --------------------------------------------------

    - Base your decision ONLY on information explicitly present in the transcript
    - Identify the earliest clear event/mechanism described
    - Ignore downstream symptoms when a clear cause exists
    - If multiple issues are present, prioritize the initiating event
    - Use keywords and phrases as guidance, not strict rules
    - Consider the full timeline of the call (events before, during, and after the incident)

    --------------------------------------------------
    KEYWORD REFERENCE
    --------------------------------------------------

    Use the provided keyword/phrase list as supporting evidence for classification

    - Match transcript language to keywords where appropriate
    - Do not rely solely on keyword matching; context and sequence matter more

    --------------------------------------------------
    EDGE CASE HANDLING
    --------------------------------------------------

    - If the caller initially describes vague symptoms but later clarifies a cause, use the clarified cause
    - If no clear mechanism exists, choose the best-fitting symptom-based Nature Code
    - If two causes are possible, choose the one most strongly supported by the transcript

    --------------------------------------------------
    CONFUSION ANALYSIS (IMPORTANT)
    --------------------------------------------------

    After selecting the primary Nature Code, you must also:

    1. Identify 2-3 Nature Codes that this call could reasonably be confused with
    2. For each:
    - Briefly explain WHY it might seem applicable
    - Clearly explain WHY it is NOT the best choice

    Focus especially on:
    - Symptom vs cause confusion (e.g., breathing vs allergic reaction)
    - Similar categories (e.g., trauma vs falls vs assault)
    - Overlapping keywords

    --------------------------------------------------
    OUTPUT FORMAT (STRICT)
    --------------------------------------------------

    Return your answer in the following format:

    [ID]

    Reasoning:
    - Concisely explain why this is the correct classification
    - Reference key parts of the transcript and/or keyword matches

    Possible Confusions (for each):
    - Nature code name
    - Why it could apply:
    - Why it is incorrect:

    (Include 2-3 total confusion comparisons)

    --------------------------------------------------
    FINAL INSTRUCTION
    --------------------------------------------------

    Prioritize the initiating event over symptoms. Be decisive. Do not hedge between multiple final answers.
""")
