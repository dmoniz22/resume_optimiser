import asyncio
import json
import re
from app.config import settings
from app.services.llm_client import get_llm_client

REWRITE_PROMPT = """You are an expert resume optimizer. Rewrite each resume bullet to better match the target job description.

ABSOLUTE RULES (these are not suggestions):
1. NEVER invent experience the candidate doesn't have
2. NEVER add technologies, tools, or skills not in the original bullet
3. PRESERVE all numbers, percentages, dollar amounts, dates
4. DO NOT change factual claims — only improve wording and emphasis
5. Use strong action verbs (led, designed, optimized, reduced)
6. Incorporate relevant JD keywords naturally — no keyword stuffing
7. Keep each bullet to 1-2 lines
8. Format for ATS: no columns, no graphics references, no special chars

Output ONLY valid JSON array, no other text:
[
  {{
    "section": "Work Experience",
    "bullet_index": 0,
    "original": "...",
    "optimized": "...",
    "keywords_added": ["..."],
    "change_rationale": "Why this change improves ATS match"
  }}
]

If a bullet cannot be improved without fabrication, return optimized = original with rationale "No safe improvement possible."

Job Description Keywords: {keywords}

Resume Bullets:
{bullets}"""

SUMMARY_PROMPT = """Rewrite this professional summary/profile to better match the target job description.
Do NOT invent experience or skills. Output ONLY the rewritten summary text, no JSON, no explanation.

Target Job Keywords: {keywords}

Original Summary:
{summary}

Rewritten Summary:"""

SKILLS_PROMPT = """Reorder and group these skills to prioritize those mentioned in the job description.
Put JD-matching skills first, then related skills, then remaining skills.
Output ONLY a comma-separated list, no JSON, no explanation.

Job Keywords: {keywords}

Skills: {skills}

Reordered Skills:"""


def extract_all_skills_and_tools(text: str) -> set[str]:
    text_lower = text.lower()
    found = set()

    skill_patterns = [
        r'\bpython\b', r'\bjavascript\b', r'\btypescript\b', r'\bjava\b',
        r'\bgo\b', r'\bgolang\b', r'\bruby\b', r'\bphp\b', r'\brust\b',
        r'\bc\+\+\b', r'\bc#\b', r'\bscala\b', r'\bkotlin\b', r'\bswift\b',
        r'\breact\b', r'\bangular\b', r'\bvue\b', r'\bnode\.?js\b',
        r'\bnext\.?js\b', r'\bdjango\b', r'\bflask\b', r'\bfastapi\b',
        r'\bspring\b', r'\b\.net\b', r'\blaravel\b', r'\brails\b',
        r'\bpostgres\b', r'\bmysql\b', r'\bmongodb\b', r'\bredis\b',
        r'\belasticsearch\b', r'\bcassandra\b', r'\bdynamodb\b',
        r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bgoogle cloud\b',
        r'\bdocker\b', r'\bkubernetes\b', r'\bk8s\b', r'\bterraform\b',
        r'\bansible\b', r'\bjenkins\b', r'\bgithub actions\b', r'\bgitlab ci\b',
        r'\bcircleci\b', r'\bgit\b', r'\blinux\b', r'\bunix\b',
        r'\bgraphql\b', r'\brest\b', r'\bgrpc\b', r'\bapache kafka\b',
        r'\brabbitmq\b', r'\bsqs\b', r'\bsns\b', r'\bcelery\b',
        r'\bpandas\b', r'\bnumpy\b', r'\bpytorch\b', r'\btensorflow\b',
        r'\bscikit-learn\b', r'\bspark\b', r'\bhadoop\b', r'\bairflow\b',
        r'\bdbt\b', r'\bsnowflake\b', r'\bbigquery\b', r'\bredshift\b',
        r'\btableau\b', r'\bpower bi\b', r'\blooker\b',
        r'\bprometheus\b', r'\bgrafana\b', r'\bdatadog\b', r'\bsentry\b',
        r'\bnginx\b', r'\bhaproxy\b', r'\bcdns?\b', r'\bvarnish\b',
        r'\bfigma\b', r'\bsketch\b', r'\bhtml\b', r'\bcss\b',
        r'\bsass\b', r'\bless\b', r'\btailwind\b', r'\bbootstrap\b',
        r'\bselenium\b', r'\bcypress\b', r'\bjest\b', r'\bpytest\b',
        r'\bwebpack\b', r'\bvite\b', r'\brollup\b', r'\bbabel\b',
        r'\bunix\b', r'\bshell\b', r'\bbash\b', r'\bunix/linux\b',
        r'\bsql\b', r'\bnosql\b',
        r'\bci/cd\b', r'\bmicroservices\b', r'\bapi\b',
        r'\bsolidity\b', r'\bweb3\b',
        r'\bgdpr\b', r'\bhipaa\b', r'\bsoc\s*2\b', r'\bpci\b',
        r'\bagile\b', r'\bscrum\b', r'\bkanban\b', r'\bjira\b',
    ]

    for pattern in skill_patterns:
        if re.search(pattern, text_lower):
            found.add(pattern.replace(r'\b', '').replace(r'\.?', '.').replace(r'\s*', ' '))

    return found


def validate_rewrite(original_bullets: list[dict], optimized_bullets: list[dict], original_resume_full: str) -> list[dict]:
    original_entities = extract_all_skills_and_tools(original_resume_full)
    issues = []

    for opt in optimized_bullets:
        new_entities = extract_all_skills_and_tools(opt["optimized"]) - original_entities
        if new_entities:
            issues.append({
                "bullet_index": opt["bullet_index"],
                "fabricated_skills": list(new_entities),
                "action": "revert_to_original",
            })
            opt["optimized"] = opt["original"]
            opt["change_rationale"] = f"REVERTED: fabricated skills detected ({', '.join(new_entities)})"

    return issues


def format_bullets_for_prompt(bullets: list[dict]) -> str:
    lines = []
    for b in bullets:
        lines.append(f'[Section: {b["section"]}, Index: {b["bullet_index"]}] {b["text"]}')
    return "\n".join(lines)


async def rewrite_bullets(bullets: list[dict], keywords: str, original_full_text: str) -> tuple[list[dict], list[dict]]:
    client = get_llm_client()
    bullets_text = format_bullets_for_prompt(bullets)

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=settings.AI_MODEL_REWRITE,
        messages=[
            {"role": "system", "content": "You are an expert resume optimizer. Follow all rules strictly. Output ONLY valid JSON."},
            {"role": "user", "content": REWRITE_PROMPT.format(keywords=keywords, bullets=bullets_text)},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]

    optimized = json.loads(content)
    fabrication_flags = validate_rewrite(bullets, optimized, original_full_text)
    return optimized, fabrication_flags


def _safe_str_from_kw(kw) -> str:
    if isinstance(kw, dict):
        return kw.get("name", kw.get("skill", kw.get("text", str(kw))))
    return str(kw)


def identify_gaps(resume_structured: dict, jd_keywords: dict) -> list[str]:
    resume_text = json.dumps(resume_structured).lower() if resume_structured else ""
    gaps = []

    for key in ("hard_skills", "must_have", "ats_keywords"):
        for kw in jd_keywords.get(key, []):
            kw_str = _safe_str_from_kw(kw)
            if kw_str.lower() not in resume_text:
                gaps.append(kw_str)

    return gaps


def extract_bullets_from_resume(structured_data: dict) -> list[dict]:
    bullets = []
    for section in structured_data.get("sections", []):
        for i, bullet in enumerate(section.get("bullets", [])):
            if isinstance(bullet, dict) and bullet.get("is_role_title"):
                continue
            bullets.append({
                "section": section["title"],
                "bullet_index": i,
                "text": bullet.get("text", bullet) if isinstance(bullet, dict) else bullet,
            })
    return bullets


async def optimize_summary(summary_text: str, jd_keywords_str: str) -> str:
    if not summary_text.strip():
        return summary_text
    client = get_llm_client()
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=settings.AI_MODEL_REWRITE,
        messages=[
            {"role": "system", "content": "You are a professional resume writer. Never fabricate experience."},
            {"role": "user", "content": SUMMARY_PROMPT.format(summary=summary_text[:2000], keywords=jd_keywords_str)},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


async def reorder_skills(skills_list: list[str], jd_keywords_str: str) -> list[str]:
    if not skills_list or len(skills_list) < 2:
        return skills_list
    client = get_llm_client()
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=settings.AI_MODEL_EXTRACT,
        messages=[
            {"role": "system", "content": "Reorder skills to prioritize job description matches. Output comma-separated only."},
            {"role": "user", "content": SKILLS_PROMPT.format(skills=", ".join(skills_list), keywords=jd_keywords_str)},
        ],
        temperature=0.1,
        max_tokens=512,
    )
    result = response.choices[0].message.content.strip()
    return [s.strip() for s in result.split(",") if s.strip()]
