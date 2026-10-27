<!doctype html>
<html lang="zh-CN" data-resolution="landscape-4k">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=3840, height=2160" />
    <title>AI 早报 · HyperFrames</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {
        font-family: "HF Sans";
        src: url("assets/fonts/NotoSansSC-VF.ttf") format("truetype");
        font-weight: 100 900;
        font-display: block;
      }
      @font-face {
        font-family: "HF Serif";
        src: url("assets/fonts/NotoSerifSC-VF.ttf") format("truetype");
        font-weight: 100 900;
        font-display: block;
      }
      :root {
        --ink: #2b2620;
        --muted: #6e6459;
        --orange: #c8552c;
        --orange-deep: #a8461f;
        --cream: #f7f1e4;
        --dock: #ecede1;
        --track: #d9d4c4;
        --line: #e4dacb;
        --dock-ink: #4f463c;
        --dock-soft: #5f564b;
        --font-sans: "HF Sans", sans-serif;
        --font-serif: "HF Serif", serif;
        --font-num: Georgia, "Times New Roman", serif;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        width: 3840px;
        height: 2160px;
        overflow: hidden;
        background: var(--cream);
        font-family: var(--font-sans);
        color: var(--ink);
        -webkit-font-smoothing: antialiased;
      }
      #root {
        position: relative;
        width: 3840px;
        height: 2160px;
        overflow: hidden;
        background: var(--cream);
      }
      #stage-clip {
        position: relative;
        width: 3840px;
        height: 2160px;
        overflow: hidden;
      }
      #stage {
        position: absolute;
        top: 0;
        left: 0;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        transform: scale(2);
        transform-origin: 0 0;
        background: var(--cream);
      }
      .stage-bg {
        position: absolute;
        inset: 0;
        background:
          radial-gradient(1600px 1100px at 82% 4%, rgba(200, 85, 44, 0.10), transparent 64%),
          radial-gradient(1200px 900px at 0% 100%, rgba(62, 107, 90, 0.07), transparent 62%),
          linear-gradient(160deg, #f8f3e8 0%, #f5eddf 58%, #f1e8d8 100%);
      }
      .grain {
        position: absolute;
        inset: 0;
        z-index: 30;
        pointer-events: none;
        opacity: 0.06;
        mix-blend-mode: multiply;
        filter: grayscale(1);
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='.55'/%3E%3C/svg%3E");
      }

      /* ---------- top nav ---------- */
      .nav {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 92px;
        z-index: 40;
        display: flex;
        align-items: stretch;
        padding: 0 24px;
        background: rgba(247, 241, 228, 0.94);
        border-bottom: 1px solid rgba(43, 38, 32, 0.12);
      }
      .nav-items {
        position: relative;
        display: flex;
        flex: 1;
        height: 100%;
        border-left: 1px solid rgba(43, 38, 32, 0.08);
      }
      .nav-pill {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #b4471f;
        transform-origin: 0 0;
        z-index: 0;
      }
      .nav-item {
        position: relative;
        z-index: 1;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        border-right: 1px solid rgba(43, 38, 32, 0.08);
      }
      .nav-label {
        font-size: 21px;
        font-weight: 500;
        letter-spacing: 0.02em;
        color: var(--muted);
        white-space: nowrap;
      }
      .nav-date {
        width: 154px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 9px;
        font-size: 17px;
        letter-spacing: 0.12em;
        color: var(--muted);
        white-space: nowrap;
      }
      .nav-date-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--orange);
        box-shadow: 0 0 0 4px rgba(200, 85, 44, 0.10);
      }

      /* ---------- screens ---------- */
      .screens {
        position: absolute;
        inset: 0;
        z-index: 10;
      }
      .screen {
        position: absolute;
        inset: 0;
        overflow: hidden;
        opacity: 0;
        z-index: 1;
      }
      #screen-cover { opacity: 1; }
      .screen-bg {
        position: absolute;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        background: #f7f1e4;
        box-shadow: -44px 0 80px rgba(43, 38, 32, 0.10);
      }
      .screen-bg::after {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(1100px 760px at 84% 8%, rgba(200, 85, 44, 0.055), transparent 70%);
        pointer-events: none;
      }
      .bg-cover { background: #f7f1e4; }
      .bg-qoder { background: #f8f2e6; }
      .bg-agents { background: #f5efe2; }
      .bg-minimax { background: #f6f0e3; }
      .bg-claude { background: #f4eddf; }
      .bg-outro { background: #f7f1e4; }
      .wipe-edge {
        position: absolute;
        top: 0;
        left: 0;
        width: 8px;
        height: 100%;
        background: var(--orange);
        opacity: 0;
        box-shadow: 0 0 34px rgba(200, 85, 44, 0.35);
      }
      .screen-inner {
        position: absolute;
        inset: 0;
        z-index: 2;
      }

      /* ---------- shared type ---------- */
      .eyebrow {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 21px;
        letter-spacing: 0.08em;
        color: var(--muted);
        white-space: nowrap;
      }
      .eyebrow-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--orange);
        box-shadow: 0 0 0 5px rgba(200, 85, 44, 0.10);
        flex: 0 0 auto;
      }
      .caption {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 150px;
        display: flex;
        justify-content: center;
        z-index: 3;
      }
      .caption-pill {
        max-width: 1480px;
        padding: 24px 44px;
        border-radius: 14px;
        background: rgba(58, 48, 42, 0.93);
        color: #fbf4e6;
        font-size: 34px;
        line-height: 1.28;
        letter-spacing: 0.01em;
        text-align: center;
        box-shadow: 0 18px 44px rgba(58, 48, 42, 0.18);
      }

      /* ---------- cover ---------- */
      .cover-grid {
        position: absolute;
        top: 148px;
        left: 96px;
        right: 96px;
        display: grid;
        grid-template-columns: 1.32fr 0.68fr;
        gap: 84px;
        align-items: start;
        z-index: 2;
      }
      .cover-title {
        margin-top: 28px;
        width: 100%;
        font-family: var(--font-serif);
        font-size: 106px;
        line-height: 1.13;
        letter-spacing: -0.025em;
        color: var(--ink);
      }
      .cover-sub {
        margin-top: 28px;
        font-size: 31px;
        letter-spacing: 0.01em;
        color: #5f564b;
      }
      .cover-rule {
        width: 128px;
        height: 4px;
        border-radius: 2px;
        background: var(--orange);
        margin-top: 34px;
        transform-origin: 0 50%;
      }
      .cover-meta {
        display: flex;
        gap: 24px;
        margin-top: 26px;
        font-size: 17px;
        letter-spacing: 0.08em;
        color: var(--muted);
      }
      .cover-index {
        margin-top: 8px;
        padding: 28px 30px 8px;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255, 253, 248, 0.88), rgba(255, 252, 244, 0.62));
        box-shadow: 0 22px 60px rgba(80, 60, 40, 0.06);
      }
      .index-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--line);
        font-size: 18px;
        letter-spacing: 0.12em;
        color: var(--muted);
      }
      .index-head span:last-child {
        font-family: var(--font-num);
        font-size: 20px;
        letter-spacing: 0.04em;
        color: var(--orange-deep);
      }
      .index-row {
        display: grid;
        grid-template-columns: 34px 96px 1fr;
        gap: 13px;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid rgba(228, 218, 203, 0.72);
      }
      .index-row:last-child { border-bottom: 0; }
      .index-no {
        font-family: var(--font-num);
        font-size: 18px;
        color: #6b6156;
      }
      .index-cat {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border: 1px solid var(--line);
        border-radius: 999px;
        font-size: 14px;
        line-height: 1;
        color: var(--muted);
        white-space: nowrap;
      }
      .index-cat i {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex: 0 0 auto;
      }
      .index-text {
        font-size: 20px;
        line-height: 1.42;
        color: var(--ink);
      }
      .issue-stamp {
        position: absolute;
        top: 118px;
        right: 86px;
        z-index: 0;
        font-family: var(--font-num);
        font-size: 252px;
        line-height: 1;
        letter-spacing: -0.055em;
        color: rgba(43, 38, 32, 0.92);
        pointer-events: none;
      }

      /* ---------- story ---------- */
      .story-top {
        position: absolute;
        top: 136px;
        left: 96px;
        right: 96px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        z-index: 2;
      }
      .issue-no {
        margin-top: -30px;
        font-family: var(--font-num);
        font-size: 118px;
        line-height: 0.9;
        letter-spacing: -0.04em;
        color: rgba(43, 38, 32, 0.92);
      }
      .story-title {
        position: absolute;
        top: 186px;
        left: 96px;
        width: 1560px;
        z-index: 2;
        font-family: var(--font-serif);
        font-size: 80px;
        line-height: 1.13;
        letter-spacing: -0.015em;
        color: var(--ink);
      }
      .story-sub {
        position: absolute;
        top: 316px;
        left: 100px;
        z-index: 2;
        font-size: 29px;
        letter-spacing: 0.01em;
        color: #5f564b;
      }
      .story-rule {
        position: absolute;
        top: 372px;
        left: 100px;
        width: 96px;
        height: 4px;
        border-radius: 2px;
        background: var(--orange);
        transform-origin: 0 50%;
        z-index: 2;
      }
      .cards {
        position: absolute;
        top: 426px;
        left: 96px;
        right: 96px;
        height: 316px;
        display: flex;
        gap: 36px;
        z-index: 2;
      }
      .card {
        flex: 1 1 0;
        min-width: 0;
        padding: 32px 36px;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(255, 253, 248, 0.92), rgba(255, 252, 244, 0.72));
        box-shadow: 0 20px 54px rgba(80, 60, 40, 0.055);
        display: flex;
        flex-direction: column;
      }
      .card-icon {
        width: 56px;
        height: 56px;
        border-radius: 15px;
        background: rgba(200, 85, 44, 0.10);
        color: var(--orange-deep);
        display: grid;
        place-items: center;
        margin-bottom: 20px;
        flex: 0 0 auto;
      }
      .card h3 {
        font-size: 29px;
        font-weight: 700;
        line-height: 1.3;
        letter-spacing: 0.01em;
        color: var(--ink);
        margin-bottom: 13px;
      }
      .card p {
        font-size: 24px;
        line-height: 1.62;
        color: #51483f;
      }
      .story.single .cards { justify-content: flex-start; }
      .story.single .card { flex: 0 0 1020px; }
      .story.has-evidence .cards { right: 760px; }
      .story.has-evidence .card { padding: 28px 30px; }
      .story.has-evidence .card h3 { font-size: 27px; }
      .story.has-evidence .card p { font-size: 22px; }
      .story.has-evidence.single .card { flex: 0 0 100%; }
      .evidence {
        position: absolute;
        top: 426px;
        right: 96px;
        width: 640px;
        height: 340px;
        z-index: 3;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: #fffdf8;
        box-shadow: 0 22px 60px rgba(80, 60, 40, 0.12);
      }
      .evidence-head {
        flex: 0 0 44px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 18px;
        border-bottom: 1px solid var(--line);
        font-size: 14px;
        letter-spacing: 0.08em;
        color: var(--muted);
        background: rgba(255, 253, 248, 0.96);
      }
      .evidence-head b {
        font-weight: 700;
        color: var(--orange-deep);
      }
      .evidence-shot {
        position: relative;
        flex: 1 1 auto;
        min-height: 0;
        overflow: hidden;
        background: #f3eee4;
      }
      .evidence-shot img {
        width: 100%;
        height: 100%;
        display: block;
        object-fit: cover;
        object-position: top center;
      }
      .evidence-foot {
        flex: 0 0 36px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 0 16px;
        border-top: 1px solid var(--line);
        font-size: 12px;
        letter-spacing: 0.04em;
        color: var(--muted);
        background: rgba(255, 253, 248, 0.96);
      }
      .evidence-stamp {
        flex: 0 0 auto;
        padding: 3px 8px;
        border: 1px solid rgba(200, 85, 44, 0.35);
        border-radius: 999px;
        color: var(--orange-deep);
        font-size: 11px;
      }
      .source {
        position: absolute;
        top: 778px;
        left: 100px;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 18px;
        letter-spacing: 0.04em;
        color: var(--muted);
      }
      .source-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--orange);
      }
      .vendor-mark {
        position: absolute;
        top: 296px;
        right: 34px;
        z-index: 1;
        writing-mode: vertical-rl;
        font-family: var(--font-num);
        font-size: 20px;
        letter-spacing: 0.34em;
        color: rgba(43, 38, 32, 0.92);
        text-transform: uppercase;
        white-space: nowrap;
      }

      /* ---------- outro ---------- */
      .outro-center {
        position: absolute;
        inset: 0;
        z-index: 2;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 70px;
        text-align: center;
      }
      .outro-title {
        margin-top: 30px;
        font-family: var(--font-serif);
        font-size: 218px;
        line-height: 1;
        letter-spacing: -0.03em;
        color: var(--ink);
      }
      .outro-sub {
        margin-top: 28px;
        font-size: 28px;
        letter-spacing: 0.05em;
        color: #5f564b;
      }
      .recap-row {
        display: flex;
        gap: 14px;
        margin-top: 46px;
        align-items: center;
      }
      .recap-item {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 8px 14px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: rgba(255, 253, 248, 0.55);
        font-size: 17px;
        color: #5f564b;
      }
      .recap-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
      }

      /* ---------- bottom two-tier timeline ---------- */
      .dock {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 126px;
        z-index: 50;
        background: var(--dock);
        border-top: 1px solid rgba(43, 38, 32, 0.12);
        box-shadow: 0 -14px 40px rgba(80, 60, 40, 0.05);
      }
      .dock-inner {
        display: flex;
        height: 100%;
        padding: 12px 24px 0;
      }
      .dock-gutter {
        position: relative;
        flex: 0 0 88px;
        width: 88px;
        height: 114px;
      }
      .g-label {
        position: absolute;
        left: 0;
        font-size: 13px;
        letter-spacing: 0.18em;
        color: var(--dock-soft);
      }
      .g-label.cat { top: 8px; }
      .g-label.vendor { top: 42px; }
      .g-brand {
        position: absolute;
        left: 0;
        bottom: 10px;
        font-family: var(--font-num);
        font-size: 13px;
        line-height: 1.15;
        letter-spacing: 0.1em;
        color: var(--dock-soft);
      }
      .dock-body {
        position: relative;
        flex: 1;
        height: 114px;
      }
      .cat-row {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 30px;
      }
      .cat-group {
        position: absolute;
        top: 0;
        height: 30px;
        border-right: 1px solid rgba(43, 38, 32, 0.08);
      }
      .cat-line {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        border-radius: 2px;
        background: var(--cat);
        opacity: 0.4;
      }
      .cat-name {
        position: absolute;
        top: 7px;
        left: 10px;
        font-size: 16px;
        letter-spacing: 0.04em;
        color: var(--dock-ink);
        white-space: nowrap;
      }
      .vendor-row {
        position: absolute;
        top: 36px;
        left: 0;
        right: 0;
        height: 34px;
      }
      .active-band {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 34px;
        border: 1px solid rgba(200, 85, 44, 0.20);
        border-radius: 8px;
        background: rgba(255, 253, 248, 0.55);
        transform-origin: 0 0;
        opacity: 0;
        z-index: 0;
      }
      .vendor-seg {
        position: absolute;
        top: 0;
        height: 34px;
        display: flex;
        align-items: center;
        gap: 9px;
        padding-left: 13px;
        border-right: 1px solid rgba(43, 38, 32, 0.07);
        z-index: 1;
      }
      .v-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: var(--vc);
        flex: 0 0 auto;
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.35);
      }
      .vendor-name {
        font-size: 19px;
        letter-spacing: 0.01em;
        color: var(--dock-ink);
        white-space: nowrap;
      }
      .v-idx {
        margin-left: auto;
        margin-right: 12px;
        font-family: var(--font-num);
        font-size: 12px;
        letter-spacing: 0.04em;
        color: var(--dock-soft);
      }
      .vendor-seg.vseg-outro {
        gap: 7px;
        padding-left: 10px;
      }
      .vendor-seg.vseg-outro .v-idx { display: none; }
      .track {
        position: absolute;
        top: 78px;
        left: 0;
        right: 0;
        height: 8px;
      }
      .track-line {
        position: absolute;
        inset: 0;
        background: var(--track);
        border-radius: 4px;
      }
      .seg-fill {
        position: absolute;
        top: 0;
        height: 8px;
        background: var(--orange);
        border-radius: 4px;
        transform-origin: 0 50%;
        opacity: 0;
        z-index: 2;
      }
      .playhead {
        position: absolute;
        top: 72px;
        left: 0;
        width: 2px;
        height: 22px;
        z-index: 6;
        opacity: 0;
      }
      .ph-line {
        position: absolute;
        top: 6px;
        left: 0;
        width: 2px;
        height: 8px;
        background: rgba(200, 85, 44, 0.72);
        border-radius: 2px;
      }
      .ph-dot {
        position: absolute;
        top: 5px;
        left: -4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--orange);
        box-shadow: 0 0 0 4px rgba(200, 85, 44, 0.12);
      }
      .click-ring {
        position: absolute;
        top: 73px;
        left: 0;
        width: 18px;
        height: 18px;
        border: 2px solid var(--orange);
        border-radius: 50%;
        opacity: 0;
        z-index: 7;
        pointer-events: none;
      }
      .dock-foot {
        position: absolute;
        top: 94px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        line-height: 1;
        letter-spacing: 0.1em;
        color: var(--dock-soft);
      }
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{{DURATION}}"
      data-width="3840"
      data-height="2160"
      data-fps="30"
    >
      <div id="stage-clip" class="clip" data-start="0" data-duration="{{DURATION}}" data-track-index="1">
        <div id="stage">
          <div class="stage-bg"></div>
          <div class="grain"></div>
          {{NAV}}
          <main class="screens">
            {{SCREENS}}
          </main>
          {{DOCK}}
        </div>
      </div>
      <audio
        id="mix"
        src="assets/audio/mix.wav"
        data-start="0"
        data-duration="{{DURATION}}"
        data-track-index="20"
        data-volume="1"
      ></audio>
    </div>
    <script>
      window.__TIMELINE__ = {{TIMELINE_JSON}};
      (() => {
        const T = window.__TIMELINE__;
        const $ = (s) => document.querySelector(s);
        const $$ = (s) => Array.from(document.querySelectorAll(s));
        const DOCKW = T.timelineWidth;
        const REVEAL = ".eyebrow, .cover-title, .cover-sub, .cover-rule, .cover-meta, .index-row, .story-title, .story-sub, .story-rule, .card, .evidence, .source, .outro-title, .outro-sub, .recap-row, .caption-pill";

        gsap.set(".screen", { autoAlpha: 0 });
        gsap.set("#screen-cover", { autoAlpha: 1 });
        gsap.set(".screen:not(#screen-cover) .screen-bg", { xPercent: 100 });
        gsap.set(".screen:not(#screen-cover) .wipe-edge", { opacity: 0 });
        gsap.set(REVEAL, { autoAlpha: 0 });
        gsap.set(".issue-no, .issue-stamp, .vendor-mark", { autoAlpha: 0 });
        gsap.set(".seg-fill", { scaleX: 0, opacity: 1 });
        gsap.set("#active-band", {
          x: (T.screens[0].leftPct / 100) * DOCKW,
          scaleX: T.screens[0].widthPct / 100,
          opacity: 1,
        });
        gsap.set("#playhead", { x: 0, opacity: 1 });
        gsap.set("#click-ring", { opacity: 0 });
        gsap.set(".nav-label", { color: T.colors.muted });
        gsap.set("#nav-label-" + T.screens[0].navIndex, { color: T.colors.cream });
        gsap.set("#nav-pill", {
          xPercent: T.nav[T.screens[0].navIndex].leftPct,
          scaleX: T.nav[T.screens[0].navIndex].widthPct / 100,
        });
        gsap.set(".cat-name", { color: T.colors.dockMuted });
        gsap.set(".cat-line", { opacity: 0.4 });
        gsap.set("#cat-name-" + T.screens[0].catGroup, { color: T.colors.ink });
        gsap.set("#cat-line-" + T.screens[0].catGroup, { opacity: 1 });
        gsap.set(".vendor-name", { color: T.colors.dockMuted });
        gsap.set("#vendor-name-" + T.screens[0].id, { color: T.colors.ink });

        const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });

        tl.fromTo("#nav", { y: -18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.5, ease: "power2.out" }, 0);
        tl.fromTo("#dock", { y: 28, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.6 }, 0.04);

        tl.fromTo("#screen-cover .eyebrow", { y: 24, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.55 }, 0.1);
        tl.fromTo("#screen-cover .cover-title", { y: 56, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.85 }, 0.16);
        tl.fromTo("#screen-cover .cover-sub", { y: 22, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.5 }, 0.3);
        tl.fromTo("#screen-cover .cover-rule", { scaleX: 0, autoAlpha: 0 }, { scaleX: 1, autoAlpha: 1, duration: 0.65, ease: "power3.inOut" }, 0.38);
        tl.fromTo("#screen-cover .index-row", { y: 22, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.5, stagger: 0.06 }, 0.4);
        tl.fromTo("#screen-cover .cover-meta", { y: 14, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, 0.52);
        tl.fromTo("#screen-cover .issue-stamp", { autoAlpha: 0 }, { autoAlpha: 0.06, duration: 0.9 }, 0.2);
        tl.fromTo("#screen-cover .caption-pill", { y: 16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, 0.62);

        T.screens.forEach((s) => {
          tl.fromTo(
            "#fill-" + s.id,
            { scaleX: 0 },
            { scaleX: 1, duration: Math.max(0.01, s.segEnd - s.segStart), ease: "none" },
            s.segStart
          );
        });
        tl.fromTo("#playhead", { x: 0 }, { x: DOCKW, duration: T.total, ease: "none" }, 0);

        const enter = (id, at, kind) => {
          const root = "#screen-" + id;
          tl.fromTo(root + " .eyebrow", { y: 20, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, at);
          if (kind === "outro") {
            tl.fromTo(root + " .outro-title", { y: 40, autoAlpha: 0, scale: 0.985 }, { y: 0, autoAlpha: 1, scale: 1, duration: 0.45 }, at + 0.02);
            tl.fromTo(root + " .outro-sub", { y: 20, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, at + 0.12);
            tl.fromTo(root + " .recap-row", { y: 16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, at + 0.2);
            tl.fromTo(root + " .issue-stamp", { autoAlpha: 0 }, { autoAlpha: 0.05, duration: 0.6 }, at + 0.06);
          } else {
            tl.fromTo(root + " .story-title", { y: 36, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.6 }, at + 0.03);
            tl.fromTo(root + " .story-sub", { y: 18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.45 }, at + 0.1);
            tl.fromTo(root + " .story-rule", { scaleX: 0, autoAlpha: 0 }, { scaleX: 1, autoAlpha: 1, duration: 0.55 }, at + 0.12);
            tl.fromTo(root + " .card", { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.5, stagger: 0.07 }, at + 0.16);
            tl.fromTo(root + " .evidence", { y: 22, autoAlpha: 0, scale: 0.985 }, { y: 0, autoAlpha: 1, scale: 1, duration: 0.55 }, at + 0.2);
            tl.fromTo(root + " .source", { y: 10, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.4 }, at + 0.26);
            tl.fromTo(root + " .issue-no", { autoAlpha: 0 }, { autoAlpha: 0.09, duration: 0.5 }, at + 0.04);
            tl.fromTo(root + " .vendor-mark", { autoAlpha: 0 }, { autoAlpha: 0.16, duration: 0.6 }, at + 0.06);
          }
          tl.fromTo(root + " .caption-pill", { y: 14, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.4 }, at + 0.18);
        };

        T.transitions.forEach((tr) => {
          const ts = tr.at;
          const prev = "#screen-" + tr.from;
          const next = "#screen-" + tr.to;
          const nxt = T.screens.find((s) => s.id === tr.to);
          // Keep the outgoing page visible; the incoming sheet wipes over it.
          tl.to(prev + " .screen-inner", { x: -26, duration: 0.55, ease: "power2.inOut" }, ts);
          tl.set(next, { autoAlpha: 1 }, ts);
          tl.to(next + " .screen-bg", { xPercent: 0, duration: 0.55, ease: "power3.inOut" }, ts);
          tl.fromTo(next + " .wipe-edge", { opacity: 0 }, { opacity: 1, duration: 0.06 }, ts);
          tl.to(next + " .wipe-edge", { opacity: 0, duration: 0.2 }, ts + 0.36);
          tl.set(prev, { autoAlpha: 0 }, ts + 0.56);

          tl.to("#active-band", { x: tr.bandX, scaleX: tr.bandScale, duration: 0.45, ease: "power3.inOut" }, ts + 0.02);
          tl.set("#click-ring", {
            x: (T.timelineWidth * ts) / T.total - 9,
            scale: 0.3,
            autoAlpha: 0.9,
          }, ts);
          tl.to("#click-ring", { scale: 2.3, autoAlpha: 0, duration: 0.5, ease: "power2.out" }, ts + 0.02);

          tl.to(".vendor-name", { color: T.colors.dockMuted, duration: 0.2 }, ts + 0.02);
          tl.to("#vendor-name-" + tr.to, { color: T.colors.ink, duration: 0.3 }, ts + 0.05);

          if (tr.catChanged) {
            tl.to(".cat-name", { color: T.colors.dockMuted, duration: 0.2 }, ts + 0.02);
            tl.to(".cat-line", { opacity: 0.4, duration: 0.2 }, ts + 0.02);
            tl.to("#cat-name-" + tr.catGroup, { color: T.colors.ink, duration: 0.3 }, ts + 0.05);
            tl.to("#cat-line-" + tr.catGroup, { opacity: 1, duration: 0.3 }, ts + 0.05);
          }
          if (tr.navChanged) {
            tl.to(".nav-label", { color: T.colors.muted, duration: 0.2 }, ts + 0.02);
            tl.to("#nav-label-" + tr.navIndex, { color: T.colors.cream, duration: 0.3 }, ts + 0.05);
            tl.to("#nav-pill", {
              xPercent: T.nav[tr.navIndex].leftPct,
              scaleX: T.nav[tr.navIndex].widthPct / 100,
              duration: 0.55,
              ease: "power3.inOut",
            }, ts + 0.05);
          }

          enter(tr.to, ts + 0.5, nxt.type);
        });

        window.__TIMELINES__ = window.__TIMELINES__ || {};
        window.__timelines = window.__timelines || {};
        window.__timelines["main"] = tl;
        tl.seek(0);
      })();
    </script>
  </body>
</html>
