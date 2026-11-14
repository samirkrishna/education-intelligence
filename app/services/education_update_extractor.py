
import re

from app.database.models import EducationUpdate


MONTH_DATE = (
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2}"
    r"(?:,\s*20\d{2})?"
)


def clean_content(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def get_applicant_type(text: str):
    text = text.lower()

    if "first-year" in text or "first year" in text:
        return "FIRST_YEAR"

    if "graduate" in text:
        return "GRADUATE"

    if "international" in text:
        return "INTERNATIONAL"

    return None


def get_academic_cycle(text: str):
    match = re.search(
        r"\b(?:Fall|Spring|Summer)\s+(20\d{2})\b",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


def save_candidate(
    db,
    source_id,
    snapshot_id,
    source_url,
    category,
    title,
    evidence,
    deadline=None,
    amount=None,
    importance="MEDIUM",
    applicant_type=None,
    academic_cycle=None
):
    # Find the latest record for this particular information item.
    previous = (
        db.query(EducationUpdate)
        .filter(
            EducationUpdate.source_id == source_id,
            EducationUpdate.category == category,
            EducationUpdate.title == title
        )
        .order_by(EducationUpdate.id.desc())
        .first()
    )

    current_value = deadline or amount

    previous_value = None
    change_type = "EXISTING_INFORMATION"

    if previous:
        old_value = previous.deadline or previous.amount

        # Don't create duplicate records for unchanged information.
        if old_value == current_value:
            return None

        previous_value = old_value
        change_type = "CHANGED_INFORMATION"

    update = EducationUpdate(
        source_id=source_id,
        snapshot_id=snapshot_id,
        category=category,
        update_type=category,
        title=title,
        previous_value=previous_value,
        new_value=current_value,
        importance=importance,
        source_url=source_url,
        evidence_text=evidence,
        status="DETECTED",
        academic_cycle=academic_cycle,
        applicant_type=applicant_type,
        deadline=deadline,
        amount=amount,
        change_type=change_type,
        verification_status="UNVERIFIED"
    )

    db.add(update)
    db.flush()

    return {
        "id": update.id,
        "category": category,
        "title": title,
        "deadline": deadline,
        "amount": amount,
        "applicant_type": applicant_type,
        "academic_cycle": academic_cycle,
        "change_type": change_type
    }


def extract_updates(
    db,
    source_id: int,
    snapshot_id: int,
    source_url: str,
    content: str
):
    content = clean_content(content)

    extracted = []

    # 1. Extract Early Action and Regular Action deadlines.
    deadline_pattern = re.compile(
        rf"(?P<track>Early Action|Regular Action)"
        rf"\s*\((?:EA|RA)\)\s+applications?\s+are\s+due\s+"
        rf"(?P<date>{MONTH_DATE})",
        re.IGNORECASE
    )

    for match in deadline_pattern.finditer(content):
        track = match.group("track").upper()
        date = match.group("date")

        evidence = match.group(0)

        result = save_candidate(
            db=db,
            source_id=source_id,
            snapshot_id=snapshot_id,
            source_url=source_url,
            category="DEADLINE",
            title=f"{track} application deadline",
            evidence=evidence,
            deadline=date,
            importance="HIGH",
            applicant_type="FIRST_YEAR",
            academic_cycle=get_academic_cycle(content)
        )

        if result:
            extracted.append(result)

    # 2. Extract financial aid deadlines for EA and RA.
    financial_aid_pattern = re.compile(
        rf"Financial aid applications?.*?"
        rf"due\s+(?P<ea>{MONTH_DATE})\s+for EA applicants"
        rf"\s+and\s+(?P<ra>{MONTH_DATE})\s+for RA applicants",
        re.IGNORECASE
    )

    for match in financial_aid_pattern.finditer(content):
        for track, date in [
            ("EA", match.group("ea")),
            ("RA", match.group("ra"))
        ]:
            result = save_candidate(
                db=db,
                source_id=source_id,
                snapshot_id=snapshot_id,
                source_url=source_url,
                category="DEADLINE",
                title=f"Financial aid deadline - {track} applicants",
                evidence=match.group(0),
                deadline=date,
                importance="HIGH",
                applicant_type="FIRST_YEAR",
                academic_cycle=get_academic_cycle(content)
            )

            if result:
                extracted.append(result)

    # 3. Extract application fees.
    fee_pattern = re.compile(
        r"application fee of\s+"
        r"(?P<amount>[$€£]\s?[\d,]+(?:\.\d{2})?)",
        re.IGNORECASE
    )

    for match in fee_pattern.finditer(content):
        result = save_candidate(
            db=db,
            source_id=source_id,
            snapshot_id=snapshot_id,
            source_url=source_url,
            category="FEES",
            title="Application fee",
            evidence=match.group(0),
            amount=match.group("amount"),
            importance="MEDIUM",
            applicant_type=get_applicant_type(content),
            academic_cycle=get_academic_cycle(content)
        )

        if result:
            extracted.append(result)

    db.commit()

    return {
        "updates_found": len(extracted),
        "updates": extracted
    }
