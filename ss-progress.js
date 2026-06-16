/* Start Somewhere - shared gamification (XP, levels, badges, floating widget). Extracted from the inline copy in each page so new pages can reuse it. */
// ========== START SOMEWHERE PROGRESS TRACKER ==========
// Self-contained gamified progress system using localStorage
(function() {
  var LEVELS = [
    { name: "Curious", xp: 0, color: "#918E85" },
    { name: "Explorer", xp: 25, color: "#534AB7" },
    { name: "Builder", xp: 75, color: "#1D9E75" },
    { name: "Momentum", xp: 150, color: "#C4652A" },
    { name: "Unstoppable", xp: 300, color: "#B8336A" }
  ];

  var BADGES = {
    first_step:     { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z'/><path d='M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z'/><path d='M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0'/><path d='M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5'/></svg>", name: "First Step",      desc: "Did something. That's the whole point.", check: function(s) { return s.totalActions >= 1; } },
    sprint_star:    { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/></svg>", name: "Sprint Star",      desc: "Completed 5 skill sprints.", check: function(s) { return s.sprintsCompleted >= 5; } },
    scholar:        { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z'/><path d='M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z'/></svg>", name: "Scholar",          desc: "Clicked through to 10 courses.", check: function(s) { return s.coursesClicked >= 10; } },
    cartographer:   { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polygon points='3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21'/><line x1='9' y1='3' x2='9' y2='18'/><line x1='15' y1='6' x2='15' y2='21'/></svg>", name: "Cartographer",    desc: "Explored the Skill Map.", check: function(s) { return s.visitedPages.indexOf("skill-map") >= 0; } },
    deep_diver:     { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='8'/><line x1='21' y1='21' x2='16.65' y2='16.65'/></svg>", name: "Deep Diver",       desc: "Checked out 3 different careers.", check: function(s) { return s.careersViewed >= 3; } },
    full_send:      { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'/><circle cx='12' cy='12' r='6'/><circle cx='12' cy='12' r='2'/></svg>", name: "Full Send",        desc: "Visited Explore, Build, and Apply.", check: function(s) { var p = s.visitedPages; return p.indexOf("explore") >= 0 && p.indexOf("build") >= 0 && p.indexOf("apply") >= 0; } },
    roulette:       { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' height='18' rx='2'/><circle cx='8' cy='8' r='1' fill='#C4652A'/><circle cx='16' cy='8' r='1' fill='#C4652A'/><circle cx='12' cy='12' r='1' fill='#C4652A'/><circle cx='8' cy='16' r='1' fill='#C4652A'/><circle cx='16' cy='16' r='1' fill='#C4652A'/></svg>", name: "Roulette Roller",  desc: "Spun the roulette 3 times.", check: function(s) { return s.rouletteSpins >= 3; } },
    completionist:  { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7z'/><path d='M5 20h14'/></svg>", name: "Completionist",    desc: "Finished all 18 sprints.", check: function(s) { return s.sprintsCompleted >= 18; } },
    skill_hunter:   { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M3.5 21 14 3'/><path d='M20.5 21 10 3'/><path d='M15.5 21 12 15l-3.5 6'/><path d='M2 21h20'/></svg>", name: "Skill Hunter",     desc: "Explored 10 different skills.", check: function(s) { return s.skillsExplored >= 10; } },
    analyzer:       { icon: "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#C4652A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 18h8'/><path d='M3 22h18'/><path d='M14 22a7 7 0 1 0 0-14h-1'/><path d='M9 14h2'/><path d='M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2z'/><path d='M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3'/></svg>", name: "Analyzer",         desc: "Used the Job Analyzer.", check: function(s) { return s.jobsAnalyzed >= 1; } }
  };

  // ---- State management ----
  function getState() {
    try {
      var raw = localStorage.getItem("ss_progress");
      if (raw) return JSON.parse(raw);
    } catch(e) {}
    return {
      xp: 0,
      totalActions: 0,
      sprintsCompleted: 0,
      coursesClicked: 0,
      careersViewed: 0,
      skillsExplored: 0,
      rouletteSpins: 0,
      jobsAnalyzed: 0,
      visitedPages: [],
      earnedBadges: [],
      completedSprintIds: [],
      viewedCareerNames: [],
      clickedCourseNames: [],
      exploredSkillNames: []
    };
  }

  function saveState(s) {
    try { localStorage.setItem("ss_progress", JSON.stringify(s)); } catch(e) {}
  }

  function getLevel(xp) {
    var level = LEVELS[0];
    for (var i = 0; i < LEVELS.length; i++) {
      if (xp >= LEVELS[i].xp) level = LEVELS[i];
    }
    return level;
  }

  function getNextLevel(xp) {
    for (var i = 0; i < LEVELS.length; i++) {
      if (xp < LEVELS[i].xp) return LEVELS[i];
    }
    return null;
  }

  function checkBadges(state) {
    var newBadges = [];
    var keys = Object.keys(BADGES);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (state.earnedBadges.indexOf(key) < 0 && BADGES[key].check(state)) {
        state.earnedBadges.push(key);
        newBadges.push(key);
      }
    }
    return newBadges;
  }

  // ---- Public API ----
  window.SSProgress = {
    award: function(type, detail) {
      var s = getState();
      var xpGain = 0;

      if (type === "sprint") {
        if (detail && s.completedSprintIds.indexOf(detail) >= 0) return; // already done
        if (detail) s.completedSprintIds.push(detail);
        s.sprintsCompleted++;
        xpGain = 15;
      } else if (type === "course") {
        if (detail && s.clickedCourseNames.indexOf(detail) < 0) {
          s.clickedCourseNames.push(detail);
        }
        s.coursesClicked++;
        xpGain = 5;
      } else if (type === "career") {
        if (detail && s.viewedCareerNames.indexOf(detail) < 0) {
          s.viewedCareerNames.push(detail);
          s.careersViewed++;
          xpGain = 5;
        }
      } else if (type === "skill") {
        if (detail && s.exploredSkillNames.indexOf(detail) < 0) {
          s.exploredSkillNames.push(detail);
          s.skillsExplored++;
          xpGain = 3;
        }
      } else if (type === "roulette") {
        s.rouletteSpins++;
        xpGain = 5;
      } else if (type === "job_analyze") {
        s.jobsAnalyzed++;
        xpGain = 10;
      } else if (type === "ask") {
        s.questionsAsked = (s.questionsAsked || 0) + 1;
        xpGain = 5;
      } else if (type === "page") {
        if (detail && s.visitedPages.indexOf(detail) < 0) {
          s.visitedPages.push(detail);
          xpGain = 1;
        }
      }

      if (xpGain > 0) {
        s.xp += xpGain;
        s.totalActions++;
        var oldLevel = getLevel(s.xp - xpGain);
        var newLevel = getLevel(s.xp);
        var newBadges = checkBadges(s);
        saveState(s);
        updateWidget(s);

        if (newLevel.name !== oldLevel.name) {
          showToast("Level up! You're now " + newLevel.name + "!", newLevel.color);
        } else if (newBadges.length > 0) {
          var b = BADGES[newBadges[0]];
          showToast(b.name + " unlocked!", "#C4652A");
        } else if (xpGain >= 10) {
          showToast("+" + xpGain + " XP", "#1D9E75");
        }
      }
    },

    getState: getState,
    getLevel: function() { return getLevel(getState().xp); },

    reset: function() {
      localStorage.removeItem("ss_progress");
      updateWidget(getState());
    }
  };

  // ---- Toast notification ----
  function showToast(msg, color) {
    var toast = document.createElement("div");
    toast.className = "ss-toast";
    toast.style.cssText = "position:fixed;bottom:80px;right:20px;z-index:10001;background:" + (color || "#C4652A") + ";color:white;padding:10px 18px;border-radius:8px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;opacity:0;transform:translateY(10px);transition:all 0.3s;box-shadow:0 4px 12px rgba(0,0,0,0.15);pointer-events:none;";
    toast.textContent = msg;
    document.body.appendChild(toast);
    requestAnimationFrame(function() {
      toast.style.opacity = "1";
      toast.style.transform = "translateY(0)";
    });
    setTimeout(function() {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(function() { toast.remove(); }, 300);
    }, 2500);
  }

  // ---- Widget ----
  function createWidget() {
    var css = document.createElement("style");
    css.textContent = [
      ".ss-widget{position:fixed;bottom:20px;right:20px;z-index:10000;font-family:'DM Sans',sans-serif;}",
      ".ss-pill{display:flex;align-items:center;gap:8px;background:#FFFFFF;border:1px solid rgba(0,0,0,0.1);border-radius:40px;padding:6px 14px 6px 8px;cursor:pointer;box-shadow:0 2px 12px rgba(0,0,0,0.08);transition:all 0.2s;}",
      ".ss-pill:hover{box-shadow:0 4px 20px rgba(0,0,0,0.12);transform:translateY(-1px);}",
      ".ss-pill-xp{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:white;}",
      ".ss-pill-info{display:flex;flex-direction:column;line-height:1.2;}",
      ".ss-pill-level{font-size:11px;font-weight:600;color:#1A1A18;}",
      ".ss-pill-bar{width:60px;height:4px;background:#F0EDE6;border-radius:2px;overflow:hidden;margin-top:2px;}",
      ".ss-pill-fill{height:100%;border-radius:2px;transition:width 0.5s ease;}",
      ".ss-panel{position:absolute;bottom:50px;right:0;width:300px;background:#FFFFFF;border:1px solid rgba(0,0,0,0.1);border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,0.12);padding:20px;display:none;max-height:70vh;overflow-y:auto;}",
      ".ss-panel.open{display:block;animation:ss-fadeIn 0.2s ease;}",
      "@keyframes ss-fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}",
      ".ss-panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;}",
      ".ss-panel-title{font-family:'DM Serif Display',Georgia,serif;font-size:20px;}",
      ".ss-panel-xp{font-size:13px;color:#6B6860;font-weight:500;}",
      ".ss-progress-bar{width:100%;height:8px;background:#F0EDE6;border-radius:4px;overflow:hidden;margin-bottom:4px;}",
      ".ss-progress-fill{height:100%;border-radius:4px;transition:width 0.5s ease;}",
      ".ss-progress-label{display:flex;justify-content:space-between;font-size:11px;color:#918E85;margin-bottom:20px;}",
      ".ss-stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:20px;}",
      ".ss-stat{background:#FAF9F6;border-radius:8px;padding:10px;text-align:center;}",
      ".ss-stat-num{font-size:20px;font-weight:700;color:#1A1A18;}",
      ".ss-stat-label{font-size:11px;color:#6B6860;margin-top:2px;}",
      ".ss-badges-title{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#918E85;margin-bottom:10px;}",
      ".ss-badge{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.04);}",
      ".ss-badge:last-child{border-bottom:none;}",
      ".ss-badge-icon{font-size:20px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:#FAF9F6;border-radius:8px;flex-shrink:0;}",
      ".ss-badge-locked .ss-badge-icon{filter:grayscale(1);opacity:0.3;}",
      ".ss-badge-info{flex:1;min-width:0;}",
      ".ss-badge-name{font-size:13px;font-weight:600;color:#1A1A18;}",
      ".ss-badge-locked .ss-badge-name{color:#918E85;}",
      ".ss-badge-desc{font-size:11px;color:#918E85;line-height:1.3;}",
      "@media(max-width:480px){.ss-panel{width:280px;right:-5px;}.ss-widget{bottom:12px;right:12px;}}"
    ].join("\n");
    document.head.appendChild(css);

    var widget = document.createElement("div");
    widget.className = "ss-widget";
    widget.id = "ss-widget";
    widget.innerHTML = '<div class="ss-pill" id="ss-pill">' +
      '<div class="ss-pill-xp" id="ss-pill-icon"></div>' +
      '<div class="ss-pill-info">' +
        '<div class="ss-pill-level" id="ss-pill-level"></div>' +
        '<div class="ss-pill-bar"><div class="ss-pill-fill" id="ss-pill-fill"></div></div>' +
      '</div>' +
    '</div>' +
    '<div class="ss-panel" id="ss-panel"></div>';
    document.body.appendChild(widget);

    document.getElementById("ss-pill").addEventListener("click", function(e) {
      e.stopPropagation();
      var panel = document.getElementById("ss-panel");
      panel.classList.toggle("open");
      if (panel.classList.contains("open")) renderPanel(getState());
    });

    document.addEventListener("click", function(e) {
      var panel = document.getElementById("ss-panel");
      if (panel && panel.classList.contains("open") && !e.target.closest(".ss-widget")) {
        panel.classList.remove("open");
      }
    });
  }

  function updateWidget(state) {
    var level = getLevel(state.xp);
    var next = getNextLevel(state.xp);
    var pct = 100;
    if (next) {
      pct = Math.round(((state.xp - level.xp) / (next.xp - level.xp)) * 100);
    }

    var icon = document.getElementById("ss-pill-icon");
    var levelEl = document.getElementById("ss-pill-level");
    var fill = document.getElementById("ss-pill-fill");

    if (icon) {
      icon.style.background = level.color;
      icon.textContent = state.xp;
    }
    if (levelEl) levelEl.textContent = level.name;
    if (fill) {
      fill.style.width = pct + "%";
      fill.style.background = level.color;
    }
  }

  function renderPanel(state) {
    var level = getLevel(state.xp);
    var next = getNextLevel(state.xp);
    var pct = 100;
    var nextLabel = "Max level!";
    if (next) {
      pct = Math.round(((state.xp - level.xp) / (next.xp - level.xp)) * 100);
      nextLabel = next.xp + " XP to " + next.name;
    }

    var badgesHTML = "";
    var badgeKeys = Object.keys(BADGES);
    for (var i = 0; i < badgeKeys.length; i++) {
      var key = badgeKeys[i];
      var b = BADGES[key];
      var earned = state.earnedBadges.indexOf(key) >= 0;
      badgesHTML += '<div class="ss-badge ' + (earned ? "" : "ss-badge-locked") + '">' +
        '<div class="ss-badge-icon">' + b.icon + '</div>' +
        '<div class="ss-badge-info">' +
          '<div class="ss-badge-name">' + b.name + '</div>' +
          '<div class="ss-badge-desc">' + (earned ? b.desc : "???") + '</div>' +
        '</div>' +
      '</div>';
    }

    document.getElementById("ss-panel").innerHTML =
      '<div class="ss-panel-header">' +
        '<div class="ss-panel-title">Your Progress</div>' +
        '<div class="ss-panel-xp">' + state.xp + ' XP</div>' +
      '</div>' +
      '<div class="ss-progress-bar"><div class="ss-progress-fill" style="width:' + pct + '%;background:' + level.color + '"></div></div>' +
      '<div class="ss-progress-label"><span>' + level.name + '</span><span>' + nextLabel + '</span></div>' +
      '<div class="ss-stats">' +
        '<div class="ss-stat"><div class="ss-stat-num">' + state.sprintsCompleted + '</div><div class="ss-stat-label">Sprints</div></div>' +
        '<div class="ss-stat"><div class="ss-stat-num">' + state.coursesClicked + '</div><div class="ss-stat-label">Courses</div></div>' +
        '<div class="ss-stat"><div class="ss-stat-num">' + state.careersViewed + '</div><div class="ss-stat-label">Careers</div></div>' +
        '<div class="ss-stat"><div class="ss-stat-num">' + state.earnedBadges.length + '/' + badgeKeys.length + '</div><div class="ss-stat-label">Badges</div></div>' +
      '</div>' +
      '<div class="ss-badges-title">Badges</div>' +
      badgesHTML;
  }

  // ---- Auto-detect page and track visit ----
  function detectPage() {
    var path = window.location.pathname.split("/").pop().replace(".html", "");
    var pageMap = {
      "start-somewhere": "home",
      "explore": "explore",
      "build": "build",
      "apply": "apply",
      "skill-explorer-production": "skill-explorer",
      "job-analyzer": "job-analyzer",
      "ask": "ask",
      "skill-roulette": "skill-roulette",
      "skill-sprints": "skill-sprints",
      "skill-map": "skill-map",
      "career": "career"
    };
    return pageMap[path] || path;
  }

  // ---- Init ----
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  function init() {
    createWidget();
    var state = getState();

    // Track page visit
    var page = detectPage();
    if (page) {
      SSProgress.award("page", page);
    }

    // Auto-track career page views
    if (page === "career") {
      var params = new URLSearchParams(window.location.search);
      var job = params.get("job");
      if (job) SSProgress.award("career", job);
    }

    updateWidget(getState());
  }
})();
