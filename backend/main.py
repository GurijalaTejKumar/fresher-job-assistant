from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
import sqlite3

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Fresher Job Assistant API",
    description="Backend for the Fresher Job Assistant MVP",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================
#
# Our frontend is currently running through Live Server:
#
# http://127.0.0.1:5500
#
# Our FastAPI backend:
#
# http://127.0.0.1:8000
#
# CORS allows the frontend to communicate with the backend.
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database" / "jobs.db"


def get_connection():
    """
    Open a connection to the SQLite database.

    sqlite3.Row lets us access database columns by name.
    """

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# SKILL NORMALIZATION
# =========================================================

SKILL_ALIASES = {
    "js": "javascript",
    "javascript programming": "javascript",

    "node": "node.js",
    "nodejs": "node.js",

    "reactjs": "react",
    "react.js": "react",

    "vuejs": "vue",
    "vue.js": "vue",

    "angularjs": "angular",
    "angular.js": "angular",

    "rest api": "rest apis",
    "rest api's": "rest apis",

    "api test": "api testing",
    "api tests": "api testing",
    "api testing tools": "api testing",

    "html css": "html/css",
    "html css3": "html/css",

    "ci cd": "ci/cd",
    "cicd": "ci/cd",

    "powerbi": "power bi",
    "power bi desktop": "power bi",

    "ms excel": "excel",
    "microsoft excel": "excel",

    "postgres": "postgresql",
    "postgre sql": "postgresql",

    "mongo": "mongodb",

    "ml": "machine learning",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize one skill.
    """

    skill = skill.strip().lower()

    skill = " ".join(
        skill.split()
    )

    skill = skill.strip(
        ".,;:()[]{}"
    )

    return SKILL_ALIASES.get(
        skill,
        skill
    )


def split_skills(
    skills: str | None
) -> list[str]:
    """
    Convert comma-separated skills into
    normalized unique skills.
    """

    if not skills:
        return []

    result = []

    for skill in skills.split(","):

        if skill.strip():

            result.append(
                normalize_skill(skill)
            )

    return list(
        dict.fromkeys(result)
    )


# =========================================================
# SKILL MATCHING
# =========================================================

def calculate_skill_match(
    candidate_skills: str | None,
    job_skills: str | None
):
    """
    Compare candidate skills with job skills.

    Example:

    Candidate:
        Python, SQL

    Job:
        Python, SQL, Docker

    Result:
        Match = 67%
        Matched = Python, SQL
        Missing = Docker
    """

    candidate_list = split_skills(
        candidate_skills
    )

    job_list = split_skills(
        job_skills
    )

    if not job_list:

        return {
            "match_percentage": 0,
            "matched_skills": [],
            "missing_skills": []
        }

    matched_skills = []
    missing_skills = []

    for job_skill in job_list:

        best_ratio = 0.0

        for candidate_skill in candidate_list:

            # Exact match
            if candidate_skill == job_skill:

                best_ratio = 1.0
                break

            # Phrase relationship
            if (
                candidate_skill in job_skill
                or job_skill in candidate_skill
            ):

                ratio = 0.90

            else:

                ratio = SequenceMatcher(
                    None,
                    candidate_skill,
                    job_skill
                ).ratio()

            best_ratio = max(
                best_ratio,
                ratio
            )

        if best_ratio >= 0.80:

            matched_skills.append(
                job_skill
            )

        else:

            missing_skills.append(
                job_skill
            )

    match_percentage = round(
        len(matched_skills)
        / len(job_list)
        * 100
    )

    return {
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }


# =========================================================
# CAREER ROLE FAMILIES
# =========================================================

ROLE_FAMILIES = {

    "software engineer": {
        "software engineer",
        "associate software engineer",
        "software developer",
        "junior software developer",
        "software trainee",
        "software programmer",
        "developer",
        "backend developer",
        "backend software developer",
        "frontend developer",
        "frontend software developer",
        "full stack developer",
        "fullstack developer",
        "application developer",
        "application software developer",
        "web developer",
        "programmer",
        "programmer analyst",
        "graduate software engineer",
    },

    "data analyst": {
        "data analyst",
        "junior data analyst",
        "data analytics",
        "business analyst",
        "business intelligence analyst",
        "bi analyst",
        "reporting analyst",
        "data reporting analyst",
    },

    "qa engineer": {
        "qa engineer",
        "qa tester",
        "quality analyst",
        "test engineer",
        "testing engineer",
        "automation test engineer",
        "software tester",
        "quality assurance engineer",
        "qa automation engineer",
    },

    "devops engineer": {
        "devops engineer",
        "devops",
        "cloud engineer",
        "site reliability engineer",
        "sre",
        "infrastructure engineer",
        "cloud infrastructure engineer",
    },

    "data scientist": {
        "data scientist",
        "junior data scientist",
        "machine learning engineer",
        "ml engineer",
        "ai engineer",
        "machine learning scientist",
    },

    "product manager": {
        "product manager",
        "product owner",
        "associate product manager",
        "product management",
    },

    "project manager": {
        "project manager",
        "project management",
        "associate project manager",
        "junior project manager",
    },

    "network engineer": {
        "network engineer",
        "network administrator",
        "network support engineer",
        "network support",
        "networking engineer",
    },

    "cyber security": {
        "cyber security",
        "cybersecurity",
        "security analyst",
        "security engineer",
        "information security analyst",
        "information security engineer",
        "cyber security analyst",
    },

    "database administrator": {
        "database administrator",
        "database admin",
        "database engineer",
        "dba",
    },

    "ui ux designer": {
        "ui designer",
        "ux designer",
        "ui ux designer",
        "product designer",
        "user experience designer",
        "user interface designer",
    },

    "financial analyst": {
        "financial analyst",
        "finance analyst",
        "junior financial analyst",
    },

    "marketing": {
        "marketing",
        "marketing analyst",
        "digital marketing",
        "marketing executive",
    },

    "human resources": {
        "hr",
        "hr executive",
        "human resources",
        "hr manager",
        "human resources manager",
    },
}


# =========================================================
# RELATED ROLE SUGGESTIONS
# =========================================================

RELATED_ROLES = {

    "software engineer": [
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Software Developer",
        "Application Developer",
    ],

    "data analyst": [
        "Business Analyst",
        "Business Intelligence Analyst",
        "Reporting Analyst",
    ],

    "qa engineer": [
        "QA Tester",
        "Automation Test Engineer",
        "Test Engineer",
        "Software Tester",
    ],

    "devops engineer": [
        "Cloud Engineer",
        "Infrastructure Engineer",
        "Site Reliability Engineer",
    ],

    "data scientist": [
        "Machine Learning Engineer",
        "AI Engineer",
        "Data Analyst",
    ],

    "product manager": [
        "Associate Product Manager",
        "Business Analyst",
        "Project Manager",
    ],

    "project manager": [
        "Associate Project Manager",
        "Product Manager",
        "Business Analyst",
    ],

    "network engineer": [
        "Network Administrator",
        "Network Support Engineer",
    ],

    "cyber security": [
        "Security Analyst",
        "Security Engineer",
        "Information Security Analyst",
    ],

    "database administrator": [
        "Database Engineer",
        "Database Administrator",
    ],
}


def normalize_role(role: str) -> str:
    """
    Normalize a role string.
    """

    role = role.strip().lower()

    role = " ".join(
        role.split()
    )

    return role


def correct_role_spelling(
    role: str
) -> str:
    """
    Correct obvious spelling mistakes by comparing
    the user's role only against known career vocabulary.

    Example:

        qa enginner
        ↓
        qa engineer
    """

    normalized_role = normalize_role(
        role
    )

    # Already a known family
    if normalized_role in ROLE_FAMILIES:
        return normalized_role

    # Already a known alias
    for family_terms in ROLE_FAMILIES.values():

        if normalized_role in family_terms:
            return normalized_role

    # Build known role vocabulary
    all_known_roles = []

    for family_terms in ROLE_FAMILIES.values():
        all_known_roles.extend(
            family_terms
        )

    best_match = normalized_role
    best_ratio = 0.0

    # Compare with known roles
    for known_role in all_known_roles:

        ratio = SequenceMatcher(
            None,
            normalized_role,
            known_role
        ).ratio()

        if ratio > best_ratio:

            best_ratio = ratio
            best_match = known_role

    # Only accept high-confidence corrections
    if best_ratio >= 0.85:
        return best_match

    return normalized_role


def get_role_family(
    candidate_role: str
) -> set[str]:
    """
    Return the career family belonging to the
    corrected candidate role.
    """

    corrected_role = correct_role_spelling(
        candidate_role
    )

    # Direct family name
    if corrected_role in ROLE_FAMILIES:
        return ROLE_FAMILIES[
            corrected_role
        ]

    # Alias inside a family
    for family_name, family_terms in ROLE_FAMILIES.items():

        if corrected_role in family_terms:
            return ROLE_FAMILIES[
                family_name
            ]

    # Unknown role
    return {
        corrected_role
    }


def calculate_role_match(
    candidate_role: str | None,
    job_title: str | None,
    job_description: str | None
):
    """
    Calculate career relevance.

    100 = matching career title
     60 = role appears meaningfully in description
      0 = no meaningful career relationship

    We do NOT use generic fuzzy title matching because:

        Software Engineer
        QA Engineer

    share the word "Engineer" but are different careers.
    """

    if not candidate_role:

        return {
            "match_percentage": 0,
            "match_type": "not_provided",
            "matched_terms": []
        }

    corrected_role = correct_role_spelling(
        candidate_role
    )

    job_title_normalized = normalize_role(
        job_title or ""
    )

    job_description_normalized = normalize_role(
        job_description or ""
    )

    role_terms = get_role_family(
        corrected_role
    )

    # -----------------------------------------------------
    # Strong title match
    # -----------------------------------------------------

    for term in role_terms:

        if job_title_normalized == term:

            return {
                "match_percentage": 100,
                "match_type": "exact_title_match",
                "matched_terms": [term]
            }

    # -----------------------------------------------------
    # Related title match
    # -----------------------------------------------------

    for term in role_terms:

        if term in job_title_normalized:

            return {
                "match_percentage": 100,
                "match_type": "related_title_match",
                "matched_terms": [term]
            }

    # -----------------------------------------------------
    # Description match
    # -----------------------------------------------------

    description_matches = []

    for term in role_terms:

        if term in job_description_normalized:

            description_matches.append(
                term
            )

    if description_matches:

        return {
            "match_percentage": 60,
            "match_type": "description_match",
            "matched_terms": list(
                dict.fromkeys(
                    description_matches
                )
            )
        }

    # -----------------------------------------------------
    # No meaningful match
    # -----------------------------------------------------

    return {
        "match_percentage": 0,
        "match_type": "no_match",
        "matched_terms": []
    }


# =========================================================
# EXPERIENCE
# =========================================================

def is_fresher_job(
    experience_requirement: str | None
) -> bool:
    """
    Determine whether the job accepts a fresher.
    """

    if not experience_requirement:
        return False

    value = (
        experience_requirement
        .strip()
        .lower()
    )

    return value in {
        "fresher",
        "0-1 years",
        "0-2 years"
    }


# =========================================================
# ELIGIBILITY
# =========================================================

def check_eligibility(
    degree: str | None,
    branch: str | None,
    graduation_year: int | None,
    experience: str | None,
    job: dict
):
    """
    Check whether the candidate meets the
    basic job requirements.
    """

    eligible = True

    reasons = []
    problems = []

    # -----------------------------------------------------
    # Degree
    # -----------------------------------------------------

    if degree:

        candidate_degree = (
            degree
            .strip()
            .lower()
        )

        job_degree = (
            job.get("degree") or ""
        ).strip().lower()

        if candidate_degree == job_degree:

            reasons.append(
                "Degree matches"
            )

        elif job_degree == "any graduate":

            reasons.append(
                "Job accepts any graduate"
            )

        else:

            eligible = False

            problems.append(
                f"Degree required: "
                f"{job['degree']}"
            )

    # -----------------------------------------------------
    # Branch
    # -----------------------------------------------------

    if branch:

        candidate_branch = (
            branch
            .strip()
            .lower()
        )

        job_branch = (
            job.get("branch") or ""
        ).strip().lower()

        if candidate_branch == job_branch:

            reasons.append(
                "Branch matches"
            )

        elif job_branch == "general":

            reasons.append(
                "Job accepts a general branch"
            )

        else:

            eligible = False

            problems.append(
                f"Branch required: "
                f"{job['branch']}"
            )

    # -----------------------------------------------------
    # Graduation year
    # -----------------------------------------------------

    if graduation_year:

        if (
            graduation_year
            == job["graduation_year"]
        ):

            reasons.append(
                "Graduation year matches"
            )

        else:

            eligible = False

            problems.append(
                f"Graduation year required: "
                f"{job['graduation_year']}"
            )

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    if experience:

        candidate_experience = (
            experience
            .strip()
            .lower()
        )

        if candidate_experience == "fresher":

            if is_fresher_job(
                job["experience_requirement"]
            ):

                reasons.append(
                    "Suitable for a fresher"
                )

            else:

                eligible = False

                problems.append(
                    "Job requires prior "
                    "experience: "
                    f"{job['experience_requirement']}"
                )

    return {
        "eligible": eligible,
        "reasons": reasons,
        "problems": problems
    }


# =========================================================
# OVERALL MATCH SCORE
# =========================================================

def calculate_overall_match(
    candidate_role: str | None,
    candidate_degree: str | None,
    candidate_branch: str | None,
    candidate_graduation_year: int | None,
    candidate_location: str | None,
    candidate_experience: str | None,
    candidate_skills: str | None,
    job: dict
):
    """
    Overall weighting:

        Career role       30%
        Skills            30%
        Degree            15%
        Branch            10%
        Graduation year    5%
        Experience         5%
        Location           5%

    Total = 100%
    """

    score = 0.0

    # -----------------------------------------------------
    # Career role - 30%
    # -----------------------------------------------------

    role_match = calculate_role_match(
        candidate_role,
        job["job_title"],
        job["job_description"]
    )

    score += (
        role_match["match_percentage"]
        / 100
    ) * 30

    # -----------------------------------------------------
    # Degree - 15%
    # -----------------------------------------------------

    if candidate_degree:

        candidate_degree_normalized = (
            candidate_degree
            .strip()
            .lower()
        )

        job_degree_normalized = (
            job["degree"]
            .strip()
            .lower()
        )

        if (
            candidate_degree_normalized
            == job_degree_normalized
            or job_degree_normalized
            == "any graduate"
        ):

            score += 15

    # -----------------------------------------------------
    # Branch - 10%
    # -----------------------------------------------------

    if candidate_branch:

        candidate_branch_normalized = (
            candidate_branch
            .strip()
            .lower()
        )

        job_branch_normalized = (
            job["branch"]
            .strip()
            .lower()
        )

        if (
            candidate_branch_normalized
            == job_branch_normalized
            or job_branch_normalized
            == "general"
        ):

            score += 10

    # -----------------------------------------------------
    # Graduation year - 5%
    # -----------------------------------------------------

    if candidate_graduation_year:

        if (
            candidate_graduation_year
            == job["graduation_year"]
        ):

            score += 5

    # -----------------------------------------------------
    # Experience - 5%
    # -----------------------------------------------------

    if candidate_experience:

        if (
            candidate_experience
            .strip()
            .lower()
            == "fresher"
            and is_fresher_job(
                job["experience_requirement"]
            )
        ):

            score += 5

    # -----------------------------------------------------
    # Skills - 30%
    # -----------------------------------------------------

    skill_result = calculate_skill_match(
        candidate_skills,
        job["skills"]
    )

    score += (
        skill_result["match_percentage"]
        / 100
    ) * 30

    # -----------------------------------------------------
    # Location - 5%
    # -----------------------------------------------------

    if candidate_location:

        candidate_location_normalized = (
            candidate_location
            .strip()
            .lower()
        )

        job_location_normalized = (
            job["location"]
            .strip()
            .lower()
        )

        if (
            candidate_location_normalized
            in job_location_normalized
            or job_location_normalized
            in candidate_location_normalized
        ):

            score += 5

    overall_percentage = round(
        score
    )

    # -----------------------------------------------------
    # Match level
    # -----------------------------------------------------

    if overall_percentage >= 80:

        match_level = "Excellent"

    elif overall_percentage >= 65:

        match_level = "Good"

    elif overall_percentage >= 50:

        match_level = "Partial"

    else:

        match_level = "Low"

    return {
        "overall_match_percentage":
            overall_percentage,

        "match_level":
            match_level
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message":
            "B.Tech Fresher Job Assistant is running!"
    }


# =========================================================
# ALL JOBS
# =========================================================

@app.get("/jobs")
def get_jobs():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM jobs
            LIMIT 20
        """)

        jobs = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return jobs

    finally:

        connection.close()


# =========================================================
# JOB SEARCH
# =========================================================

@app.get("/jobs/search")
def search_jobs(
    degree: str | None = None,
    branch: str | None = None,
    graduation_year: int | None = None,
    location: str | None = None,
    experience: str | None = None,
    skills: str | None = None,
    target_role: str | None = None
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # -------------------------------------------------
        # Base query
        # -------------------------------------------------

        query = """
            SELECT *
            FROM jobs
            WHERE 1 = 1
        """

        parameters = []

        # -------------------------------------------------
        # Degree
        # -------------------------------------------------

        if degree:

            query += """
                AND (
                    degree = ?
                    OR degree = 'Any Graduate'
                )
            """

            parameters.append(
                degree
            )

        # -------------------------------------------------
        # Branch
        # -------------------------------------------------

        if branch:

            query += """
                AND (
                    branch = ?
                    OR branch = 'General'
                )
            """

            parameters.append(
                branch
            )

        # -------------------------------------------------
        # Graduation year
        # -------------------------------------------------

        if graduation_year:

            query += """
                AND graduation_year = ?
            """

            parameters.append(
                graduation_year
            )

        # -------------------------------------------------
        # Location
        # -------------------------------------------------

        if location:

            query += """
                AND location LIKE ?
            """

            parameters.append(
                f"%{location}%"
            )

        # -------------------------------------------------
        # Experience
        # -------------------------------------------------

        if experience:

            if (
                experience
                .strip()
                .lower()
                == "fresher"
            ):

                query += """
                    AND experience_requirement
                    IN (?, ?, ?)
                """

                parameters.extend([
                    "Fresher",
                    "0-1 Years",
                    "0-2 Years"
                ])

        # -------------------------------------------------
        # Get all matching database rows
        #
        # We intentionally do NOT use LIMIT here.
        # Otherwise relevant jobs could be hidden before
        # role matching and ranking happens.
        # -------------------------------------------------

        cursor.execute(
            query,
            parameters
        )

        jobs = [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()

    # =====================================================
    # MATCH JOBS
    # =====================================================

    final_jobs = []

    for job in jobs:

        # -------------------------------------------------
        # Eligibility
        # -------------------------------------------------

        eligibility = check_eligibility(
            degree=degree,
            branch=branch,
            graduation_year=graduation_year,
            experience=experience,
            job=job
        )

        # -------------------------------------------------
        # Skill matching
        # -------------------------------------------------

        skill_match = calculate_skill_match(
            candidate_skills=skills,
            job_skills=job["skills"]
        )

        # -------------------------------------------------
        # Career matching
        # -------------------------------------------------

        role_match = calculate_role_match(
            candidate_role=target_role,
            job_title=job["job_title"],
            job_description=job["job_description"]
        )

        # -------------------------------------------------
        # Overall matching
        # -------------------------------------------------

        overall_match = calculate_overall_match(
            candidate_role=target_role,
            candidate_degree=degree,
            candidate_branch=branch,
            candidate_graduation_year=graduation_year,
            candidate_location=location,
            candidate_experience=experience,
            candidate_skills=skills,
            job=job
        )

        # -------------------------------------------------
        # Add calculated information to job
        # -------------------------------------------------

        job["eligibility"] = eligibility

        job["skill_match"] = skill_match

        job["role_match"] = role_match

        job["overall_match"] = overall_match

        final_jobs.append(
            job
        )

    # =====================================================
    # REMOVE BASICALLY INELIGIBLE JOBS
    # =====================================================

    final_jobs = [
        job
        for job in final_jobs
        if job["eligibility"]["eligible"]
    ]

    # =====================================================
    # TARGET ROLE FILTER
    #
    # When the user has explicitly requested a career,
    # remove jobs that have no meaningful career match.
    # =====================================================

    if target_role:

        final_jobs = [
            job
            for job in final_jobs
            if (
                job["role_match"]
                ["match_percentage"]
                >= 60
            )
        ]

    # =====================================================
    # RANK RESULTS
    # =====================================================

    final_jobs.sort(
        key=lambda job: (
            job["role_match"]
            ["match_percentage"],

            job["overall_match"]
            ["overall_match_percentage"],

            job["skill_match"]
            ["match_percentage"]
        ),
        reverse=True
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    response = {
        "count": len(final_jobs),
        "jobs": final_jobs
    }

    # -----------------------------------------------------
    # Helpful response when nothing matches
    # -----------------------------------------------------

    if (
        not final_jobs
        and target_role
    ):

        corrected_role = correct_role_spelling(
            target_role
        )

        response["message"] = (
            f"No suitable {corrected_role} jobs "
            "were found for the current profile."
        )

        response["suggested_roles"] = (
            get_related_roles(
                corrected_role
            )
        )

    return response


# =========================================================
# RESUME UPLOAD
# =========================================================

@app.post("/resume/upload")
async def upload_resume(
    resume: UploadFile = File(...)
):
    """
    Upload a PDF resume and extract readable text.

    This endpoint currently performs:

        PDF upload
            ↓
        PDF text extraction

    Resume field extraction and job matching will be
    connected after this step is verified.
    """

    # -----------------------------------------------------
    # Validate file
    # -----------------------------------------------------

    if not resume.filename:

        return {
            "success": False,
            "message": "No file was selected."
        }

    # -----------------------------------------------------
    # Validate PDF
    # -----------------------------------------------------

    filename = resume.filename.lower()

    if not filename.endswith(".pdf"):

        return {
            "success": False,
            "message": (
                "Please upload a PDF resume."
            )
        }

    # -----------------------------------------------------
    # Read uploaded file
    # -----------------------------------------------------

    file_bytes = await resume.read()

    if not file_bytes:

        return {
            "success": False,
            "message": "The uploaded file is empty."
        }

    # -----------------------------------------------------
    # Extract PDF text
    # -----------------------------------------------------

    try:

        pdf = PdfReader(
            BytesIO(file_bytes)
        )

        pages_text = []

        for page in pdf.pages:

            text = page.extract_text()

            if text:

                pages_text.append(
                    text
                )

        resume_text = "\n".join(
            pages_text
        ).strip()

    except Exception:

        return {
            "success": False,
            "message": (
                "Unable to read this PDF resume."
            )
        }

    # -----------------------------------------------------
    # Check extracted text
    # -----------------------------------------------------

    if not resume_text:

        return {
            "success": False,
            "message": (
                "The PDF was uploaded, but no readable "
                "text was found."
            ),
            "possible_reason": (
                "The PDF may be image/scanned based."
            )
        }

    # -----------------------------------------------------
    # Return extracted text
    # -----------------------------------------------------

    return {
        "success": True,
        "filename": resume.filename,
        "message": (
            "Resume uploaded and text extracted successfully."
        ),
        "text": resume_text
    }