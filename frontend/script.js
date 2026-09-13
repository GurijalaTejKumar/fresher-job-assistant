/* =========================================================
   ELEMENTS
========================================================= */

const form =
    document.getElementById("job-search-form");

const resultsContainer =
    document.getElementById("results");

const manualMethod =
    document.getElementById("manual-method");

const resumeMethod =
    document.getElementById("resume-method");

const manualSection =
    document.getElementById("manual-section");

const resumeSection =
    document.getElementById("resume-section");

const resumeInput =
    document.getElementById("resume");

const selectedFile =
    document.getElementById("selected-file");


/* =========================================================
   INPUT METHOD - MANUAL
========================================================= */

manualMethod.addEventListener(
    "click",
    () => {

        manualMethod.classList.add(
            "active"
        );

        resumeMethod.classList.remove(
            "active"
        );

        manualSection.classList.remove(
            "hidden"
        );

        resumeSection.classList.add(
            "hidden"
        );

    }
);


/* =========================================================
   INPUT METHOD - RESUME
========================================================= */

resumeMethod.addEventListener(
    "click",
    () => {

        resumeMethod.classList.add(
            "active"
        );

        manualMethod.classList.remove(
            "active"
        );

        manualSection.classList.add(
            "hidden"
        );

        resumeSection.classList.remove(
            "hidden"
        );

    }
);


/* =========================================================
   RESUME FILE SELECTION
========================================================= */

resumeInput.addEventListener(
    "change",
    () => {

        if (
            resumeInput.files.length === 0
        ) {

            selectedFile.textContent = "";

            return;
        }


        const file =
            resumeInput.files[0];


        selectedFile.textContent =
            `Selected resume: ${file.name}`;

    }
);


/* =========================================================
   MANUAL JOB SEARCH
========================================================= */

form.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        /* -------------------------------------------------
           Loading message
        ------------------------------------------------- */

        resultsContainer.innerHTML = `
            <div class="empty">
                Searching for suitable jobs...
            </div>
        `;


        /* -------------------------------------------------
           Read form values
        ------------------------------------------------- */

        const targetRole =
            document
                .getElementById("target-role")
                .value
                .trim();


        const degree =
            document
                .getElementById("degree")
                .value;


        const branch =
            document
                .getElementById("branch")
                .value;


        const graduationYear =
            document
                .getElementById("graduation-year")
                .value;


        const experience =
            document
                .getElementById("experience")
                .value;


        const skills =
            document
                .getElementById("skills")
                .value
                .trim();


        const location =
            document
                .getElementById("location")
                .value
                .trim();


        /* -------------------------------------------------
           Build API query
        ------------------------------------------------- */

        const params =
            new URLSearchParams();


        if (targetRole) {

            params.append(
                "target_role",
                targetRole
            );

        }


        if (degree) {

            params.append(
                "degree",
                degree
            );

        }


        if (branch) {

            params.append(
                "branch",
                branch
            );

        }


        if (graduationYear) {

            params.append(
                "graduation_year",
                graduationYear
            );

        }


        if (experience) {

            params.append(
                "experience",
                experience
            );

        }


        if (skills) {

            params.append(
                "skills",
                skills
            );

        }


        if (location) {

            params.append(
                "location",
                location
            );

        }


        /* -------------------------------------------------
           Call FastAPI
        ------------------------------------------------- */

        try {

            const response =
                await fetch(
                    `http://127.0.0.1:8000/jobs/search?${params.toString()}`
                );


            if (!response.ok) {

                throw new Error(
                    `Backend returned ${response.status}`
                );

            }


            const data =
                await response.json();


            displayResults(data);


        } catch (error) {

            console.error(error);


            resultsContainer.innerHTML = `
                <div class="error">

                    <strong>
                        Unable to search for jobs.
                    </strong>

                    <p>
                        Make sure the FastAPI backend
                        is running at
                        http://127.0.0.1:8000
                    </p>

                </div>
            `;

        }

    }
);


/* =========================================================
   DISPLAY RESULTS
========================================================= */

function displayResults(data) {

    /* -----------------------------------------------------
       No jobs
    ----------------------------------------------------- */

    if (
        !data.jobs ||
        data.jobs.length === 0
    ) {

        const message =
            data.message ||
            "No suitable jobs found.";


        let suggestions = "";


        if (
            data.suggested_roles &&
            data.suggested_roles.length > 0
        ) {

            suggestions = `
                <div class="job-section">

                    <h4>
                        You could also try
                    </h4>

                    <p>
                        ${escapeHTML(
                            data.suggested_roles.join(
                                ", "
                            )
                        )}
                    </p>

                </div>
            `;

        }


        resultsContainer.innerHTML = `
            <div class="empty">

                <h3>
                    No suitable jobs found
                </h3>

                <p>
                    ${escapeHTML(message)}
                </p>

                ${suggestions}

            </div>
        `;


        return;
    }


    /* -----------------------------------------------------
       Results heading
    ----------------------------------------------------- */

    resultsContainer.innerHTML = `
        <h2 class="results-title">
            ${data.count} suitable job(s) found
        </h2>
    `;


    /* -----------------------------------------------------
       Create each job card
    ----------------------------------------------------- */

    for (
        const job of data.jobs
    ) {

        const eligibility =
            job.eligibility || {};


        const skillMatch =
            job.skill_match || {};


        const roleMatch =
            job.role_match || {};


        const overallMatch =
            job.overall_match || {};


        const matchedSkills =
            skillMatch.matched_skills || [];


        const missingSkills =
            skillMatch.missing_skills || [];


        const reasons =
            eligibility.reasons || [];


        const problems =
            eligibility.problems || [];


        /* -------------------------------------------------
           Convert arrays to HTML
        ------------------------------------------------- */

        const matchedSkillsHTML =
            matchedSkills.length > 0
                ? escapeHTML(
                    matchedSkills.join(" • ")
                )
                : "None";


        const missingSkillsHTML =
            missingSkills.length > 0
                ? escapeHTML(
                    missingSkills.join(" • ")
                )
                : "None";


        const reasonsHTML =
            reasons.length > 0
                ? reasons
                    .map(
                        reason =>
                            `<li>✓ ${escapeHTML(
                                reason
                            )}</li>`
                    )
                    .join("")
                : "<li>No additional information</li>";


        const problemsHTML =
            problems.length > 0
                ? problems
                    .map(
                        problem =>
                            `<li>⚠ ${escapeHTML(
                                problem
                            )}</li>`
                    )
                    .join("")
                : "";


        /* -------------------------------------------------
           Create card
        ------------------------------------------------- */

        const card =
            document.createElement("div");


        card.className =
            "job-card";


        card.innerHTML = `

            <h3>
                ${escapeHTML(
                    job.job_title
                )}
            </h3>


            <p class="company">
                ${escapeHTML(
                    job.company
                )}
            </p>


            <p class="meta">

                📍 ${escapeHTML(
                    job.location
                )}

                &nbsp; | &nbsp;

                🎓 ${escapeHTML(
                    job.degree
                )}

                &nbsp; | &nbsp;

                💼 ${escapeHTML(
                    job.experience_requirement
                )}

            </p>


            <div class="match-grid">


                <div class="match-box">

                    Overall Match

                    <strong>
                        ${
                            overallMatch
                                .overall_match_percentage
                            ?? 0
                        }%
                    </strong>

                </div>


                <div class="match-box">

                    Career Fit

                    <strong>
                        ${
                            roleMatch
                                .match_percentage
                            ?? 0
                        }%
                    </strong>

                </div>


                <div class="match-box">

                    Skill Match

                    <strong>
                        ${
                            skillMatch
                                .match_percentage
                            ?? 0
                        }%
                    </strong>

                </div>


            </div>


            <span class="badge">

                ${escapeHTML(
                    overallMatch.match_level ||
                    "Unknown"
                )}

            </span>


            <p class="eligibility">

                ${
                    eligibility.eligible
                        ? "✅ Eligible"
                        : "❌ Not eligible"
                }

            </p>


            <div class="job-section">

                <h4>
                    Matched Skills
                </h4>

                <p class="skills-list">
                    ${matchedSkillsHTML}
                </p>

            </div>


            <div class="job-section">

                <h4>
                    Missing Skills
                </h4>

                <p class="skills-list">
                    ${missingSkillsHTML}
                </p>

            </div>


            <div class="job-section">

                <h4>
                    Why this job matches
                </h4>

                <ul>
                    ${reasonsHTML}
                </ul>

            </div>


            ${
                problemsHTML
                    ? `
                        <div class="job-section">

                            <h4>
                                Eligibility issues
                            </h4>

                            <ul>
                                ${problemsHTML}
                            </ul>

                        </div>
                    `
                    : ""
            }


            <div class="job-section">

                <h4>
                    Job Description
                </h4>

                <p>
                    ${escapeHTML(
                        job.job_description || ""
                    )}
                </p>

            </div>

        `;


        resultsContainer.appendChild(
            card
        );

    }

}


/* =========================================================
   HTML SAFETY
========================================================= */

function escapeHTML(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value ?? "";


    return div.innerHTML;
}