/* Start Somewhere - shared UI behavior: Tools dropdown, scroll reveals, ticker. */
(function () {
  "use strict";

  // ---- Tools dropdown ----
  var tools = document.querySelector(".nav-tools");
  if (tools) {
    var btn = tools.querySelector(".nav-tools-btn");
    var open = function (state) {
      tools.classList.toggle("open", state);
      btn.setAttribute("aria-expanded", state ? "true" : "false");
    };
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      open(!tools.classList.contains("open"));
    });
    document.addEventListener("click", function (e) {
      if (!tools.contains(e.target)) open(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") open(false);
    });
    // Hover-open for mouse users only
    if (window.matchMedia("(hover: hover)").matches) {
      var hoverTimer;
      tools.addEventListener("mouseenter", function () { clearTimeout(hoverTimer); open(true); });
      tools.addEventListener("mouseleave", function () { hoverTimer = setTimeout(function () { open(false); }, 180); });
    }
  }

  // ---- Scroll reveals ----
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add("in"); });
    }
  }

  // Stagger children of any [data-reveal-group]
  document.querySelectorAll("[data-reveal-group]").forEach(function (group) {
    Array.prototype.forEach.call(group.children, function (child, i) {
      child.style.setProperty("--d", (i * 0.09).toFixed(2) + "s");
    });
  });

  // ---- Ticker: duplicate track content once for a seamless loop ----
  document.querySelectorAll(".tick-track").forEach(function (track) {
    track.innerHTML += track.innerHTML;
  });
})();
