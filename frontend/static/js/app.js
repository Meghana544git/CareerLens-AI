/**
 * CareerLens AI — Main Application JavaScript
 * Handles all UI interactions, API calls, and state management.
 */

"use strict";

// ─── Global State ─────────────────────────────────────────────────────────────
const State = {
  resumeText: null,
  resumeFilename: null,
  currentJD: null,
  lastATSResult: null,
  userName: "You",
  isChatOpen: false,
  isChatLoading: false,
  currentSection: "dashboard",
  theme: "dark",
};

// ─── API Helpers ──────────────────────────────────────────────────────────────
async function apiPost(endpoint, data = {}) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!json.success) throw new Error(json.error || "Request failed");
  return json.data;
}

async function apiGet(endpoint) {
  const res = await fetch(endpoint, { credentials: "include" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error || "Request failed");
  return json.data;
}

// ─── Navigation ───────────────────────────────────────────────────────────────
function navigateTo(section) {
  // Hide all sections
  document.querySelectorAll(".content-section").forEach((s) => s.classList.remove("active"));
  document.querySelectorAll(".nav-pill").forEach((n) => n.classList.remove("active"));

  // Show target section
  const target = document.getElementById(`section-${section}`);
  if (target) {
    target.classList.add("active");
    State.currentSection = section;
  }

  // Activate nav link
  const navLink = document.querySelector(`[data-section="${section}"]`);
  if (navLink) navLink.classList.add("active");

  // Close mobile nav
  const navCollapse = document.getElementById("navbarMain");
  if (navCollapse && navCollapse.classList.contains("show")) {
    new bootstrap.Collapse(navCollapse).hide();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ─── Theme Toggle ─────────────────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem("cl-theme") || "dark";
  applyTheme(saved);
}

function toggleTheme() {
  const next = State.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("cl-theme", next);
}

function applyTheme(theme) {
  State.theme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
  }
}

// ─── Resume Upload ────────────────────────────────────────────────────────────
async function uploadResume(input) {
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  showLoading("Parsing your resume...");
  try {
    const res = await fetch("/api/resume/upload", {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const data = json.data;
    State.resumeText = true; // Signal that resume is uploaded (server keeps the text)
    State.resumeFilename = data.filename;

    // Update UI
    showResumePreview(data);
    hideLoading();
    showToast(`✅ Resume uploaded: ${data.filename}`, "success");
    loadDashboardStats();
  } catch (err) {
    hideLoading();
    showToast(`❌ Upload failed: ${err.message}`, "danger");
  }
  input.value = "";
}

function showResumePreview(data) {
  const zone = document.getElementById("uploadZone");
  const preview = document.getElementById("resumePreview");

  zone.classList.add("d-none");
  preview.classList.remove("d-none");

  document.getElementById("resumePreviewName").textContent = data.filename;
  document.getElementById("resumeFormatBadge").textContent = data.format || "DOC";
  document.getElementById("resumeMeta").textContent =
    `${data.word_count} words · ${data.sections_detected?.length || 0} sections detected` +
    (data.contact?.email ? ` · ${data.contact.email}` : "");

  const skillsEl = document.getElementById("resumeSkillsPreview");
  skillsEl.innerHTML = "";
  (data.skills_detected || []).slice(0, 12).forEach((s) => {
    skillsEl.innerHTML += `<span class="skill-tag">${s}</span>`;
  });

  // Update hero ring to reflect "ready" state
  animateRing("heroRingFill", 0, "heroRingText", "--");
}

// Drag-and-drop on upload zone
function initUploadDragDrop() {
  const zone = document.getElementById("uploadZone");
  if (!zone) return;

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const input = document.getElementById("resumeFileInput");
      // Create a DataTransfer to assign to input
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      input.files = dt.files;
      uploadResume(input);
    }
  });
}

// ─── Dashboard Stats ──────────────────────────────────────────────────────────
async function loadDashboardStats() {
  try {
    const data = await apiGet("/api/session/stats");
    document.getElementById("statAnalyses").textContent = data.total_analyses || 0;
    document.getElementById("statAvgScore").textContent =
      data.avg_ats_score ? `${data.avg_ats_score}` : "--";
    document.getElementById("statSavedJobs").textContent = data.saved_jobs || 0;
    document.getElementById("statChats").textContent = data.chat_messages || 0;

    // Update hero ring if we have an avg score
    if (data.avg_ats_score) {
      animateRing("heroRingFill", data.avg_ats_score, "heroRingText", data.avg_ats_score);
    }

    // Update username
    if (data.user_name && data.user_name !== "User") {
      State.userName = data.user_name;
      document.getElementById("userName").textContent = data.user_name;
    }

    // Restore resume state
    if (data.resume_uploaded) {
      State.resumeText = true;
      State.resumeFilename = data.resume_filename;
    }

    // Recent analyses
    if (data.recent_analyses && data.recent_analyses.length > 0) {
      showRecentAnalyses(data.recent_analyses);
    }
  } catch (err) {
    console.error("Dashboard stats error:", err);
  }
}

function showRecentAnalyses(analyses) {
  const card = document.getElementById("recentAnalysesCard");
  const list = document.getElementById("recentAnalysesList");
  card.style.display = "";
  list.innerHTML = analyses
    .map((a) => {
      const color = scoreColor(a.ats_score);
      return `
        <div class="analysis-row">
          <div>
            <div class="analysis-role">${escHtml(a.job_title || "Unknown Role")}</div>
            ${a.company_name ? `<div class="analysis-company">${escHtml(a.company_name)}</div>` : ""}
          </div>
          <span class="analysis-score-pill" style="background:${color}22;color:${color}">
            ${a.ats_score}/100
          </span>
        </div>`;
    })
    .join("");
}

// ─── ATS Analysis ─────────────────────────────────────────────────────────────
async function runATSAnalysis() {
  const jd = document.getElementById("atsJobDescription").value.trim();
  const jobTitle = document.getElementById("atsJobTitle").value.trim();
  const company = document.getElementById("atsCompany").value.trim();

  if (!jd) { showToast("Please paste a job description first", "warning"); return; }
  if (jd.length < 50) { showToast("Job description is too short (min 50 chars)", "warning"); return; }

  if (!State.resumeText) {
    document.getElementById("atsNoResumeWarn").style.display = "";
    showToast("Please upload your resume first", "warning");
    return;
  }

  State.currentJD = jd;
  setLoading("atsBtn", true);
  showLoading("Analyzing your resume with IBM watsonx.ai...");

  try {
    const result = await apiPost("/api/ats/analyze", {
      job_description: jd,
      job_title: jobTitle,
      company_name: company,
    });
    State.lastATSResult = result;
    displayATSResult(result);
    loadDashboardStats();
    showToast(`🎯 Analysis complete! ATS Score: ${result.ats_score}/100`, "success");
  } catch (err) {
    showToast(`Analysis failed: ${err.message}`, "danger");
  } finally {
    setLoading("atsBtn", false);
    hideLoading();
  }
}

function displayATSResult(result) {
  // Show cards
  document.getElementById("atsScoreCard").style.display = "";
  document.getElementById("skillsResultRow").style.display = "";
  document.getElementById("improvementsCard").style.display = "";
  document.getElementById("atsPlaceholder").style.display = "none";

  // Animate score ring
  animateRing("atsRingFill", result.ats_score, "atsScoreNum", result.ats_score);

  // Update hero ring too
  animateRing("heroRingFill", result.ats_score, "heroRingText", result.ats_score);

  // Verdict badge
  const verdictEl = document.getElementById("atsVerdictBadge");
  verdictEl.textContent = result.overall_verdict || result.score_label || "Complete";
  const color = scoreColor(result.ats_score);
  verdictEl.style.background = `${color}18`;
  verdictEl.style.borderColor = `${color}35`;
  verdictEl.style.color = color;

  // Role fit summary
  document.getElementById("atsRoleFit").textContent = result.role_fit_summary || "";

  // Score breakdown bars
  const breakdown = result.score_breakdown || {};
  const breakdownEl = document.getElementById("scoreBreakdown");
  const labels = {
    keyword_match: "Keyword Match",
    skills_coverage: "Skills Coverage",
    experience_relevance: "Experience Relevance",
    education_match: "Education Match",
    resume_quality: "Resume Quality",
  };
  breakdownEl.innerHTML = Object.entries(labels)
    .map(([key, label]) => {
      const val = breakdown[key] || 0;
      const c = scoreColor(val);
      return `
        <div class="score-bar-item">
          <div class="score-bar-label">
            <span class="score-bar-name">${label}</span>
            <span class="score-bar-val" style="color:${c}">${val}%</span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width:0%;background:${c}" data-target="${val}"></div>
          </div>
        </div>`;
    })
    .join("");

  // Animate bars with slight delay
  setTimeout(() => {
    breakdownEl.querySelectorAll(".score-bar-fill").forEach((bar) => {
      bar.style.width = bar.dataset.target + "%";
    });
  }, 150);

  // Matched skills
  const matchedEl = document.getElementById("matchedSkillsList");
  matchedEl.innerHTML = "";
  (result.matched_skills || []).forEach((s) => {
    matchedEl.innerHTML += `<span class="skill-tag matched">${escHtml(s)}</span>`;
  });
  if (!result.matched_skills?.length) {
    matchedEl.innerHTML = '<span class="text-muted small">No exact matches found</span>';
  }

  // Missing keywords
  const missingEl = document.getElementById("missingKeywordsList");
  missingEl.innerHTML = "";
  (result.missing_keywords || []).forEach((s) => {
    missingEl.innerHTML += `<span class="skill-tag missing">${escHtml(s)}</span>`;
  });

  // Improvements
  const impEl = document.getElementById("improvementsList");
  impEl.innerHTML = (result.improvement_actions || [])
    .map((a) => `<div class="improvement-item">${escHtml(a)}</div>`)
    .join("") || '<span class="text-muted small">No specific improvements noted.</span>';

  // Bullet rewrites
  const rewrites = result.resume_bullet_rewrites || [];
  if (rewrites.length > 0) {
    document.getElementById("bulletRewritesCard").style.display = "";
    const rewritesEl = document.getElementById("bulletRewritesList");
    rewritesEl.innerHTML = rewrites
      .map(
        (r) => `
        <div class="bullet-rewrite">
          <div class="bullet-label text-danger">❌ Original</div>
          <div class="bullet-original">${escHtml(r.original || "")}</div>
          <div class="bullet-label text-success mt-2">✅ Improved</div>
          <div class="bullet-improved">${escHtml(r.improved || "")}</div>
        </div>`
      )
      .join("");
  }
}

// ─── Cover Letter ─────────────────────────────────────────────────────────────
async function generateCoverLetter(jdOverride = null) {
  const jd = jdOverride || document.getElementById("coverJobDescription").value.trim();
  const name = document.getElementById("coverUserName").value.trim() || State.userName;

  if (!jd) { showToast("Please provide a job description", "warning"); return; }

  setLoading("coverBtn", true);
  showLoading("Crafting your cover letter...");

  try {
    const result = await apiPost("/api/cover-letter/generate", {
      job_description: jd,
      user_name: name,
    });

    const el = document.getElementById("coverLetterResult");
    const placeholder = document.getElementById("coverPlaceholder");
    const actions = document.getElementById("coverActions");

    el.classList.remove("d-none");
    el.textContent = result.cover_letter;
    placeholder.style.display = "none";
    actions.style.display = "flex";
    document.getElementById("coverCopyBtn").style.display = "";

    showToast("✅ Cover letter generated!", "success");
  } catch (err) {
    showToast(`Failed: ${err.message}`, "danger");
  } finally {
    setLoading("coverBtn", false);
    hideLoading();
  }
}

function generateCoverFromAnalyzer() {
  const jd = document.getElementById("atsJobDescription").value.trim();
  if (!jd) { showToast("Enter a job description first", "warning"); return; }
  navigateTo("cover");
  document.getElementById("coverJobDescription").value = jd;
  document.getElementById("coverUserName").value = State.userName !== "You" ? State.userName : "";
}

function copyCoverLetter() {
  const text = document.getElementById("coverLetterResult").textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToast("📋 Cover letter copied to clipboard!", "success");
  });
}

function downloadCoverLetter() {
  const text = document.getElementById("coverLetterResult").textContent;
  if (!text) return;
  const blob = new Blob([text], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "cover_letter_careerlens.txt";
  a.click();
}

// ─── Interview Questions ──────────────────────────────────────────────────────
async function generateInterviewQuestions() {
  const jd = document.getElementById("interviewJD").value.trim();
  if (!jd) { showToast("Please provide a job description", "warning"); return; }

  setLoading("interviewBtn", true);
  showLoading("Predicting interview questions with Granite AI...");

  try {
    const result = await apiPost("/api/interview/questions", { job_description: jd });
    displayInterviewQuestions(result);
    showToast("✅ Interview questions ready!", "success");
  } catch (err) {
    showToast(`Failed: ${err.message}`, "danger");
  } finally {
    setLoading("interviewBtn", false);
    hideLoading();
  }
}

function displayInterviewQuestions(data) {
  document.getElementById("interviewPlaceholder").style.display = "none";
  document.getElementById("interviewResults").style.display = "";

  // Behavioral
  const behavEl = document.getElementById("tab-behavioral");
  behavEl.innerHTML = (data.behavioral_questions || [])
    .map((q) => `
      <div class="interview-q-card">
        <div class="interview-q-text">${escHtml(q.question)}</div>
        ${q.why_asked ? `<div class="interview-why"><i class="bi bi-info-circle"></i> ${escHtml(q.why_asked)}</div>` : ""}
        ${q.sample_answer_framework ? `<div class="interview-answer"><strong>Answer Framework:</strong> ${escHtml(q.sample_answer_framework)}</div>` : ""}
        ${q.tip ? `<div class="interview-tip"><i class="bi bi-lightbulb-fill"></i> Tip: ${escHtml(q.tip)}</div>` : ""}
      </div>`
    ).join("") || '<p class="text-muted small">No behavioral questions generated.</p>';

  // Technical
  const techEl = document.getElementById("tab-technical");
  techEl.innerHTML = (data.technical_questions || [])
    .map((q) => `
      <div class="interview-q-card">
        <div class="d-flex align-items-start justify-content-between mb-2">
          <div class="interview-q-text mb-0">${escHtml(q.question)}</div>
          ${q.difficulty ? `<span class="difficulty-badge diff-${q.difficulty} ms-2 flex-shrink-0">${q.difficulty}</span>` : ""}
        </div>
        ${
          (q.expected_answer_points || []).length
            ? `<ul class="interview-answer mb-0 ps-3">${q.expected_answer_points.map((p) => `<li>${escHtml(p)}</li>`).join("")}</ul>`
            : ""
        }
      </div>`
    ).join("") || '<p class="text-muted small">No technical questions generated.</p>';

  // Situational
  const sitEl = document.getElementById("tab-situational");
  sitEl.innerHTML = (data.situational_questions || [])
    .map((q) => `
      <div class="interview-q-card">
        <div class="interview-q-text">${escHtml(q.question)}</div>
        ${q.ideal_approach ? `<div class="interview-answer"><strong>Ideal Approach:</strong> ${escHtml(q.ideal_approach)}</div>` : ""}
      </div>`
    ).join("") || '<p class="text-muted small">No situational questions generated.</p>';

  // Checklist
  const checkEl = document.getElementById("tab-checklist");
  let checkHtml = "";

  if (data.questions_to_ask_interviewer?.length) {
    checkHtml += `<h6 class="text-muted small mb-2 mt-0">Questions to ask the interviewer:</h6>`;
    checkHtml += data.questions_to_ask_interviewer
      .map((q) => `<div class="interview-q-card mb-2"><i class="bi bi-question-circle text-accent me-2"></i>${escHtml(q)}</div>`)
      .join("");
  }

  if (data.preparation_checklist?.length) {
    checkHtml += `<h6 class="text-muted small mb-2 mt-3">Preparation checklist:</h6>`;
    checkHtml += data.preparation_checklist
      .map((item) => `
        <label class="checklist-item">
          <input type="checkbox" onchange="this.parentElement.style.opacity=this.checked?'0.5':'1'"/>
          ${escHtml(item)}
        </label>`)
      .join("");
  }
  checkEl.innerHTML = checkHtml || '<p class="text-muted small">No checklist generated.</p>';

  // Init interview tabs
  initInterviewTabs();
}

function initInterviewTabs() {
  document.querySelectorAll(".cl-tab").forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      const targetTabId = tab.dataset.tab;

      document.querySelectorAll(".cl-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      document.querySelectorAll(".interview-tab-pane").forEach((p) => (p.style.display = "none"));
      const target = document.getElementById(`tab-${targetTabId}`);
      if (target) target.style.display = "";
    });
  });
}

// ─── Skill Gap Analysis ───────────────────────────────────────────────────────
async function runSkillGapAnalysis() {
  const jd = document.getElementById("skillsJD").value.trim();
  if (!jd) { showToast("Please provide a job description", "warning"); return; }
  if (!State.resumeText) { showToast("Upload your resume first", "warning"); return; }

  setLoading("skillsBtn", true);
  showLoading("Identifying skill gaps with Granite AI...");

  try {
    const result = await apiPost("/api/skills/gap", { job_description: jd });
    displaySkillGaps(result);
    showToast("✅ Skill gap analysis complete!", "success");
  } catch (err) {
    showToast(`Failed: ${err.message}`, "danger");
  } finally {
    setLoading("skillsBtn", false);
    hideLoading();
  }
}

function displaySkillGaps(data) {
  document.getElementById("skillsPlaceholder").style.display = "none";
  document.getElementById("skillsResults").style.display = "";

  // Quick wins
  const quickEl = document.getElementById("quickWinsList");
  quickEl.innerHTML = (data.quick_wins || [])
    .map((w) => `<div class="quick-win-item">${escHtml(w)}</div>`)
    .join("") || '<p class="text-muted small">No quick wins identified.</p>';

  // Critical gaps
  const critEl = document.getElementById("criticalGapsList");
  critEl.innerHTML = (data.critical_gaps || [])
    .map((g) => `
      <div class="gap-card">
        <div class="gap-header">
          <span class="gap-name">${escHtml(g.skill)}</span>
          <div class="d-flex gap-2 align-items-center">
            ${g.learning_time ? `<span class="gap-time">~${escHtml(g.learning_time)}</span>` : ""}
            <span class="importance-badge imp-${g.importance || 'medium'}">${g.importance || 'medium'}</span>
          </div>
        </div>
        ${g.reason ? `<div class="gap-reason">${escHtml(g.reason)}</div>` : ""}
        <div class="gap-resources">
          ${(g.free_resources || []).map((r) => `
            <a href="${escHtml(r.url || '#')}" target="_blank" class="resource-link">
              <i class="bi bi-box-arrow-up-right"></i>${escHtml(r.name)}
            </a>`).join("")}
        </div>
      </div>`
    ).join("") || '<p class="text-muted small">No critical gaps identified — great match!</p>';

  // Learning roadmap
  const roadEl = document.getElementById("learningRoadmapList");
  roadEl.innerHTML = (data.learning_roadmap || [])
    .map((w) => `
      <div class="roadmap-week">
        <div class="week-num">W${w.week}</div>
        <div class="week-content">
          <div class="week-focus">${escHtml(w.focus)}</div>
          ${(w.resources || []).length ? `<div class="text-muted small">${w.resources.map(escHtml).join(" · ")}</div>` : ""}
          ${w.milestone ? `<div class="week-milestone"><i class="bi bi-flag-fill"></i> ${escHtml(w.milestone)}</div>` : ""}
        </div>
      </div>`
    ).join("") || '<p class="text-muted small">No roadmap generated.</p>';

  // Career advice
  const advEl = document.getElementById("careerAdviceText");
  advEl.innerHTML = data.career_advice
    ? `<p class="mb-0" style="font-size:14px;color:var(--text-secondary);line-height:1.8">${escHtml(data.career_advice)}</p>`
    : '<p class="text-muted small">No additional advice.</p>';
}

// ─── Career Roadmap ───────────────────────────────────────────────────────────
async function generateRoadmap() {
  const targetRole = document.getElementById("roadmapTargetRole").value.trim();
  if (!targetRole) { showToast("Please enter your target role", "warning"); return; }

  setLoading("roadmapBtn", true);
  showLoading("Building your career roadmap...");

  try {
    const result = await apiPost("/api/roadmap/generate", { target_role: targetRole });
    displayRoadmap(result, targetRole);
    showToast("✅ Your career roadmap is ready!", "success");
  } catch (err) {
    showToast(`Failed: ${err.message}`, "danger");
  } finally {
    setLoading("roadmapBtn", false);
    hideLoading();
  }
}

function displayRoadmap(data, targetRole) {
  document.getElementById("roadmapPlaceholder").style.display = "none";
  document.getElementById("roadmapResults").style.display = "";

  // Overview
  const overviewEl = document.getElementById("roadmapOverview");
  overviewEl.innerHTML = `
    <div class="overview-item">
      <div class="overview-val">${escHtml(data.current_level || "—")}</div>
      <div class="overview-label">Current Level</div>
    </div>
    <div class="overview-item">
      <div class="overview-val">${escHtml(data.target_level || targetRole)}</div>
      <div class="overview-label">Target Level</div>
    </div>
    <div class="overview-item">
      <div class="overview-val">${escHtml(data.estimated_timeline || "—")}</div>
      <div class="overview-label">Est. Timeline</div>
    </div>
    ${data.salary_range?.entry ? `
    <div class="overview-item">
      <div class="overview-val" style="font-size:.95rem">${escHtml(data.salary_range.entry)}</div>
      <div class="overview-label">Entry Salary</div>
    </div>` : ""}`;

  // Phases
  const phasesEl = document.getElementById("roadmapPhases");
  phasesEl.innerHTML = (data.roadmap_phases || []).map((phase) => `
    <div class="phase-card">
      <div class="phase-header">
        <div class="phase-title">${escHtml(phase.phase)}</div>
        ${phase.duration ? `<span class="phase-duration">${escHtml(phase.duration)}</span>` : ""}
      </div>
      ${
        phase.goals?.length
          ? `<div class="mb-2"><strong class="small text-muted">Goals:</strong>
              <ul class="mb-0 mt-1 ps-4">${phase.goals.map((g) => `<li class="small text-secondary">${escHtml(g)}</li>`).join("")}</ul>
             </div>`
          : ""
      }
      ${
        phase.skills_to_build?.length
          ? `<div class="mb-2 d-flex flex-wrap gap-1">
              ${phase.skills_to_build.map((s) => `<span class="skill-tag">${escHtml(s)}</span>`).join("")}
             </div>`
          : ""
      }
      ${
        phase.certifications?.length
          ? `<div class="small text-muted mb-2"><i class="bi bi-award"></i> ${phase.certifications.map(escHtml).join(", ")}</div>`
          : ""
      }
      ${
        phase.projects_to_build?.length
          ? `<div class="small text-secondary mb-1"><i class="bi bi-code-square text-accent"></i> Build: ${phase.projects_to_build.map(escHtml).join(" | ")}</div>`
          : ""
      }
      ${phase.milestone ? `<div class="phase-milestone"><i class="bi bi-check2-circle me-1"></i>${escHtml(phase.milestone)}</div>` : ""}
    </div>`
  ).join("");

  // Internship opps
  const intOpps = data.internship_opportunities || [];
  if (intOpps.length) {
    document.getElementById("internshipOppsCard").style.display = "";
    document.getElementById("internshipOppsList").innerHTML = intOpps.map((o) => `
      <div class="gap-card">
        <div class="gap-name mb-1">${escHtml(o.type)}</div>
        ${o.companies_to_target?.length ? `<div class="small text-muted mb-1">Companies: ${o.companies_to_target.map(escHtml).join(", ")}</div>` : ""}
        ${o.how_to_apply ? `<div class="small text-secondary">${escHtml(o.how_to_apply)}</div>` : ""}
      </div>`
    ).join("");
  }

  // Motivational note
  if (data.motivational_note) {
    document.getElementById("motivNoteCard").style.display = "";
    document.getElementById("motivNote").textContent = data.motivational_note;
  }

  // Networking
  if (data.networking_strategy?.length) {
    const phasesEl2 = document.getElementById("roadmapPhases");
    phasesEl2.innerHTML += `
      <div class="cl-card mt-3">
        <div class="cl-card-header"><i class="bi bi-people-fill"></i> Networking Strategy</div>
        <div class="cl-card-body">
          ${data.networking_strategy.map((s) => `<div class="improvement-item">${escHtml(s)}</div>`).join("")}
        </div>
      </div>`;
  }
}

// ─── Internship Fit ───────────────────────────────────────────────────────────
async function runInternshipFit() {
  const jd = document.getElementById("internshipJD").value.trim();
  if (!jd) { showToast("Please provide an internship description", "warning"); return; }

  setLoading("internshipBtn", true);
  showLoading("Analyzing your internship fit...");

  try {
    const result = await apiPost("/api/internship/fit", { internship_description: jd });
    displayInternshipFit(result);
    showToast(`🎯 Internship fit: ${result.internship_fit_score}/100`, "success");
  } catch (err) {
    showToast(`Failed: ${err.message}`, "danger");
  } finally {
    setLoading("internshipBtn", false);
    hideLoading();
  }
}

function displayInternshipFit(data) {
  document.getElementById("internshipPlaceholder").style.display = "none";
  document.getElementById("internshipResults").style.display = "";

  const score = data.internship_fit_score || 0;
  const scoreEl = document.getElementById("internshipScoreNum");
  animateCounter(scoreEl, 0, score, 1200);

  const recEl = document.getElementById("internshipRecommendation");
  recEl.textContent = data.recommendation || "";
  const color = scoreColor(score);
  recEl.style.background = `${color}15`;
  recEl.style.borderColor = `${color}30`;
  recEl.style.color = color;

  // Indicators
  const indEl = document.getElementById("internIndicators");
  indEl.innerHTML = `
    <div class="intern-indicator ${data.has_projects ? "ind-yes" : "ind-no"}">
      <i class="bi bi-${data.has_projects ? "check-circle-fill" : "x-circle"}"></i> Projects
    </div>
    <div class="intern-indicator ${data.has_prior_internship ? "ind-yes" : "ind-no"}">
      <i class="bi bi-${data.has_prior_internship ? "check-circle-fill" : "x-circle"}"></i> Prior Internship
    </div>
    <div class="intern-indicator ${data.has_certifications ? "ind-yes" : "ind-no"}">
      <i class="bi bi-${data.has_certifications ? "check-circle-fill" : "x-circle"}"></i> Certifications
    </div>
    <div class="intern-indicator ${data.should_apply ? "ind-yes" : "ind-no"}">
      <i class="bi bi-${data.should_apply ? "check-circle-fill" : "x-circle"}"></i>
      ${data.should_apply ? "Apply Now" : "Strengthen First"}
    </div>`;

  // Matched skills
  const matchEl = document.getElementById("internMatchedSkills");
  matchEl.innerHTML = "";
  (data.matched_skills || []).forEach((s) => {
    matchEl.innerHTML += `<span class="skill-tag matched">${escHtml(s)}</span>`;
  });
  if (!data.matched_skills?.length) matchEl.innerHTML = '<span class="text-muted small">Upload resume to see matched skills</span>';

  // Missing skills
  const missEl = document.getElementById("internMissingSkills");
  missEl.innerHTML = "";
  (data.missing_skills || []).forEach((s) => {
    missEl.innerHTML += `<span class="skill-tag missing">${escHtml(s)}</span>`;
  });

  // Platforms
  const platEl = document.getElementById("internPlatforms");
  platEl.innerHTML = `<div class="platform-grid">
    ${(data.platforms || []).map((p) => `
      <a href="${escHtml(p.url)}" target="_blank" class="platform-link">
        <i class="bi bi-arrow-up-right-circle"></i>${escHtml(p.name)}
      </a>`).join("")}
  </div>`;
}

// ─── Save Job ─────────────────────────────────────────────────────────────────
async function saveCurrentJob() {
  const jd = document.getElementById("atsJobDescription").value.trim();
  const title = document.getElementById("atsJobTitle").value.trim() || "Unknown Role";
  const company = document.getElementById("atsCompany").value.trim();

  if (!jd) { showToast("Enter a job description first", "warning"); return; }

  try {
    await apiPost("/api/jobs/save", {
      job_title: title,
      company_name: company,
      job_description: jd,
      ats_score: State.lastATSResult?.ats_score,
    });
    showToast("✅ Job saved!", "success");
    loadDashboardStats();
  } catch (err) {
    showToast(`Failed to save: ${err.message}`, "danger");
  }
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
function toggleChat() {
  const panel = document.getElementById("chatPanel");
  const overlay = document.getElementById("chatOverlay");
  State.isChatOpen = !State.isChatOpen;
  panel.classList.toggle("open", State.isChatOpen);
  overlay.classList.toggle("visible", State.isChatOpen);
  if (State.isChatOpen) {
    setTimeout(() => document.getElementById("chatInput")?.focus(), 350);
  }
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg || State.isChatLoading) return;

  input.value = "";
  autoResizeInput(input);
  appendChatMessage("user", msg);
  showTypingIndicator();
  State.isChatLoading = true;
  document.getElementById("chatSendBtn").disabled = true;

  try {
    const result = await apiPost("/api/chat", { message: msg });
    hideTypingIndicator();
    appendChatMessage("assistant", result.response);
    loadDashboardStats();
  } catch (err) {
    hideTypingIndicator();
    appendChatMessage("assistant", `Sorry, I encountered an error: ${err.message}. Please try again.`);
  } finally {
    State.isChatLoading = false;
    document.getElementById("chatSendBtn").disabled = false;
  }
}

function sendQuick(msg) {
  const input = document.getElementById("chatInput");
  input.value = msg;
  sendChat();
}

function appendChatMessage(role, content) {
  const container = document.getElementById("chatMessages");
  const iconMap = { user: "bi-person", assistant: "bi-robot" };
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.innerHTML = `
    <div class="msg-avatar"><i class="bi ${iconMap[role]}"></i></div>
    <div class="msg-bubble">${markdownToHtml(content)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = "chat-msg assistant typing";
  div.id = "typingIndicator";
  div.innerHTML = `
    <div class="msg-avatar"><i class="bi bi-robot"></i></div>
    <div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function clearChat() {
  try {
    await apiPost("/api/chat/clear");
    const container = document.getElementById("chatMessages");
    container.innerHTML = `
      <div class="chat-msg assistant">
        <div class="msg-avatar"><i class="bi bi-robot"></i></div>
        <div class="msg-bubble">
          <p>Chat cleared! I'm ready to help with your career questions.</p>
          <div class="quick-chips">
            <span class="chip" onclick="sendQuick('How do I optimize my resume for ATS?')">ATS tips</span>
            <span class="chip" onclick="sendQuick('How should I prepare for a technical interview?')">Interview prep</span>
          </div>
        </div>
      </div>`;
    showToast("Chat cleared", "success");
  } catch (err) {
    showToast("Could not clear chat", "danger");
  }
}

async function loadChatHistory() {
  try {
    const messages = await apiGet("/api/chat/history");
    if (!messages.length) return;
    const container = document.getElementById("chatMessages");
    // Clear welcome message
    container.innerHTML = "";
    messages.forEach((m) => appendChatMessage(m.role, m.content));
  } catch (err) {
    console.debug("No chat history");
  }
}

// ─── User Name ────────────────────────────────────────────────────────────────
async function setUserName() {
  const name = prompt("What should I call you?", State.userName === "You" ? "" : State.userName);
  if (!name || !name.trim()) return;
  try {
    await apiPost("/api/session/name", { name: name.trim() });
    State.userName = name.trim();
    document.getElementById("userName").textContent = name.trim();
    showToast(`👋 Nice to meet you, ${name.trim()}!`, "success");
  } catch (err) {
    showToast("Could not update name", "danger");
  }
}

// ─── Animations & Utilities ───────────────────────────────────────────────────
function animateRing(fillId, score, textId, textValue) {
  const fill = document.getElementById(fillId);
  const textEl = document.getElementById(textId);
  if (!fill) return;

  const circumference = 2 * Math.PI * 50; // r=50
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const dash = pct * circumference;
  const color = scoreColor(score);

  fill.style.stroke = color;
  fill.style.strokeDasharray = `${dash} ${circumference}`;
  if (textEl) {
    textEl.textContent = textValue;
    if (textId === "heroRingText" || textId === "atsScoreNum") {
      animateCounter(textEl, 0, parseInt(textValue) || 0, 1200);
    }
  }
}

function animateCounter(el, from, to, duration) {
  const start = performance.now();
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(from + (to - from) * eased);
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function scoreColor(score) {
  if (score >= 85) return "#22c55e";
  if (score >= 70) return "#3b82d4";
  if (score >= 50) return "#eab308";
  if (score >= 30) return "#f97316";
  return "#ef4444";
}

function setLoading(btnId, isLoading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = isLoading;
  if (isLoading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" style="width:14px;height:14px"></span>Analyzing...`;
  } else {
    if (btn.dataset.originalHtml) btn.innerHTML = btn.dataset.originalHtml;
  }
}

function showLoading(text = "Analyzing with IBM watsonx.ai...") {
  document.getElementById("loadingText").textContent = text;
  document.getElementById("loadingOverlay").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loadingOverlay").style.display = "none";
}

function showToast(message, type = "success") {
  const colors = { success: "#22c55e", danger: "#ef4444", warning: "#eab308", info: "#3b82d4" };
  const toast = document.getElementById("toastMsg");
  const body = document.getElementById("toastBody");
  body.textContent = message;
  toast.style.borderLeft = `4px solid ${colors[type] || colors.info}`;
  const bsToast = new bootstrap.Toast(toast, { delay: 3500 });
  bsToast.show();
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function markdownToHtml(text) {
  if (!text) return "";
  return escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^• (.+)$/gm, "<li>$1</li>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/s, "<ul class='mb-1 ps-3'>$1</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[uo]l|<li|<p)(.+)/gm, "$1")
    .replace(/\n/g, "<br>");
}

function autoResizeInput(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// JD character counter
function initJDCharCounter() {
  const jdInput = document.getElementById("atsJobDescription");
  const counter = document.getElementById("jdCharCount");
  if (!jdInput || !counter) return;
  jdInput.addEventListener("input", () => {
    counter.textContent = `${jdInput.value.length} characters`;
  });
}

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────
function initKeyboardShortcuts() {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
      autoResizeInput(chatInput);
    });
    chatInput.addEventListener("input", () => autoResizeInput(chatInput));
  }
}

// ─── SVG Gradient Definition ──────────────────────────────────────────────────
function injectSvgGradient() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "0");
  svg.setAttribute("height", "0");
  svg.style.position = "absolute";
  svg.innerHTML = `
    <defs>
      <linearGradient id="gradientStroke" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#3b82d4"/>
        <stop offset="100%" stop-color="#7c5cd8"/>
      </linearGradient>
    </defs>`;
  document.body.prepend(svg);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Theme
  initTheme();
  document.getElementById("themeToggle")?.addEventListener("click", toggleTheme);

  // Navigation
  document.querySelectorAll(".nav-pill[data-section]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      navigateTo(link.dataset.section);
    });
  });

  // Upload drag-drop
  initUploadDragDrop();

  // JD character counter
  initJDCharCounter();

  // Keyboard shortcuts
  initKeyboardShortcuts();

  // SVG gradient
  injectSvgGradient();

  // Load session state
  loadDashboardStats();
  loadChatHistory();

  // Apply blur-out effect on main content when chat is open on mobile
  const mainContent = document.querySelector(".main-content");
  const observer = new MutationObserver(() => {
    const isOpen = document.getElementById("chatPanel").classList.contains("open");
    if (mainContent) mainContent.style.filter = isOpen && window.innerWidth < 769 ? "blur(2px)" : "";
  });
  observer.observe(document.getElementById("chatPanel"), { attributes: true, attributeFilter: ["class"] });
});
