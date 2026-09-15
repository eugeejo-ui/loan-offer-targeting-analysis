/* 화면 동작: 사이드바 자동 전환, 앵커 스크롤, 계산기 재계산. 데이터는 data.js가 넣어 준 window.DASHBOARD. */
(function () {
  "use strict";

  var data = window.DASHBOARD;
  if (!data) { return; }

  /* 링크 미리보기 캡처용 (analysis/23_capture_screens.py). 첫 화면에 지표 카드가 들어오도록 용어 카드를 접는다. */
  if (/[?&]preview\b/.test(window.location.search)) { document.body.classList.add("preview-mode"); }

  var fmt = {
    int: function (v) { return Math.round(v).toLocaleString("ko-KR"); },
    pct: function (v, digits) { return (v * 100).toFixed(digits === undefined ? 1 : digits) + "%"; },
    eur: function (v) { return Math.round(v).toLocaleString("ko-KR"); },
    million: function (v) { return (v / 1e6).toFixed(1); },
    hours: function (v) { return v.toFixed(2); }
  };

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined) { node.textContent = text; }
    return node;
  }

  function card(label, value, sub) {
    var box = el("div", "card metric");
    box.appendChild(el("div", "label", label));
    var v = el("div", "value");
    v.innerHTML = value;
    box.appendChild(v);
    if (sub) { box.appendChild(el("div", "sub", sub)); }
    return box;
  }

  function table(node, headers, rows) {
    node.innerHTML = "";
    var thead = el("thead"), tr = el("tr");
    headers.forEach(function (h) { tr.appendChild(el("th", null, h)); });
    thead.appendChild(tr);
    var tbody = el("tbody");
    rows.forEach(function (row) {
      var line = el("tr");
      row.forEach(function (cell) {
        var td = el("td", cell && cell.cls ? cell.cls : null,
                    cell && cell.html !== undefined ? undefined : (cell && cell.text !== undefined ? cell.text : cell));
        if (cell && cell.html !== undefined) { td.innerHTML = cell.html; }
        line.appendChild(td);
      });
      tbody.appendChild(line);
    });
    node.appendChild(thead);
    node.appendChild(tbody);
  }

  function bar(container, name, valueText, ratio, tone) {
    var row = el("div");
    var head = el("div", "bar-row");
    head.appendChild(el("div", "name", name));
    head.appendChild(el("div", "value", valueText));
    row.appendChild(head);
    var track = el("div", "bar-track");
    var fill = el("div", "bar-fill" + (tone ? " " + tone : ""));
    fill.style.width = Math.max(0, Math.min(1, ratio)) * 100 + "%";
    track.appendChild(fill);
    row.appendChild(track);
    container.appendChild(row);
  }

  /* ---------- 고정 구역 ---------- */

  document.getElementById("build-meta").textContent =
    data.built_on + " 기준 · 세그먼트 " + data.segment_count + "개 · 신청 " + fmt.int(data.cases_in_segments) + "건";

  var pop = data.population || {};
  var cards = document.getElementById("overview-cards");
  cards.appendChild(card("분석 모집단", fmt.int(pop.cases) + "<small>건</small>", "접수 2016-01~11, 결과 확정"));
  cards.appendChild(card("성사율", fmt.pct(pop.success_rate), "성사 " + fmt.int(pop.success_cases) + "건"));
  cards.appendChild(card("총 공수", fmt.int(pop.effort_hours) + "<small>시간</small>",
                         "직원이 실제로 작업한 시간의 합 (대기 시간 제외)"));
  cards.appendChild(card("세그먼트", data.segment_count + "<small>개</small>", "접수 시점 변수 3축 교차"));

  document.getElementById("overview-verdict").innerHTML =
    "성사율 순위와 효율 순위의 상관은 <b>" + data.alignment.rho.toFixed(3) + "</b>이며, 90% 구간 " +
    data.alignment.ci_lo.toFixed(3) + "~" + data.alignment.ci_hi.toFixed(3) +
    "는 모두 판정 경계 0.7 미만입니다. 성사율이 높은 신청과 이익이 되는 신청은 일치하지 않습니다.";

  var chips = document.getElementById("core-chips");
  [["ρ(성사율, η)", data.alignment.rho.toFixed(3)],
   ["90% 구간", data.alignment.ci_lo.toFixed(3) + "~" + data.alignment.ci_hi.toFixed(3)],
   ["판정 경계", "0.7"],
   ["세그먼트", data.segment_count + "개"]].forEach(function (pair) {
    var chip = el("div", "chip");
    chip.innerHTML = pair[0] + " <b>" + pair[1] + "</b>";
    chips.appendChild(chip);
  });

  var mismatch = (data.mismatch || []).slice().sort(function (a, b) { return b.rank_gap - a.rank_gap; });
  var mismatchBox = document.getElementById("core-mismatch");
  var maxEta = Math.max.apply(null, data.segments.map(function (s) { return s.eta; }));
  mismatch.slice(0, 3).concat(mismatch.slice(-3)).forEach(function (row) {
    bar(mismatchBox, row.label, "성사율 " + row.rank_p + "위 · 효율 " + row.rank_eta + "위",
        row.eta / maxEta, row.rank_gap > 0 ? "cool" : "warm");
  });

  table(document.getElementById("allocation-table"),
    ["공수 예산", "성사율 순서", "효율 순서", "차이"],
    data.allocation.map(function (row) {
      return [row.budget + "%", fmt.million(row.by_rate) + "백만", fmt.million(row.by_eta) + "백만",
              { text: "+" + fmt.pct(row.gain), cls: "pos" }];
    }));

  var groupBox = document.getElementById("multioffer-bars");
  (data.groups || []).forEach(function (row) {
    bar(groupBox, row.name, fmt.pct(row.p) + " · 공수 " + fmt.hours(row.e_mean) + "시간", row.p, "cool");
  });

  var failureBox = document.getElementById("failure-bars");
  (data.failures || []).forEach(function (row) {
    bar(failureBox, row.name, fmt.pct(row.share) + " (발송 후 " + fmt.pct(row.after) + ")", row.share / 0.2, "warm");
  });

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  table(document.getElementById("checks-table"), ["판정 항목", "값"],
    (data.checks || []).map(function (row) {
      var head = escapeHtml(row.check);
      var body = row.verdict ? '<span class="cell-note">' + escapeHtml(row.verdict) + "</span>" : "";
      return [{ html: head + body }, row.value];
    }));

  table(document.getElementById("experiments-table"),
    ["실험", "효과", "군당 표본", "필요 기간"],
    (data.experiments || []).map(function (row) {
      return [row.name + " (" + row.source + ")",
              (row.delta > 0 ? "+" : "") + (row.delta * 100).toFixed(1) + "%p",
              fmt.int(row.per_arm),
              { text: row.months.toFixed(1) + "개월", cls: row.feasible ? "pos" : "neg" }];
    }));

  document.getElementById("page-note").innerHTML =
    "세그먼트 이름은 금액 등급 · 접수 경로 · 대출 용도 순으로 표기합니다. 금액 등급은 소액 6,500유로 이하, " +
    "중소액 10,000유로 이하, 중액 15,500유로 이하, 고액 25,000유로 이하, 초고액 25,000유로 초과입니다. " +
    "표식은 신규 신청에만 기록되는 시스템 값 A_Submitted이며, 업무상 의미는 확인되지 않았습니다. " +
    "공수는 직원이 실제로 작업한 시간이며 대기 시간은 제외합니다.<br><br>" +
    "본 화면의 수치는 outputs/의 산출물에서 그대로 인용했습니다. 배분 비교는 관측된 세그먼트 평균으로 산출한 " +
    "가상 배분이며, 개입 효과가 아님을 명시합니다. 참조 인건비 " + data.reference_cost + "유로/시간 — 출처: " +
    data.reference_cost_source;

  /* ---------- 계산 (analysis/calculator.py와 같은 정의) ---------- */

  function priceSegments(cost, margin) {
    return data.segments.map(function (s) {
      var evPerCase = (margin * s.eta_I - cost) * s.e_mean;
      return { seg: s, required: cost / s.eta_I, ev: evPerCase, evTotal: evPerCase * s.n, negative: evPerCase < 0 };
    });
  }

  function summarise(priced) {
    var negatives = priced.filter(function (r) { return r.negative; });
    var sum = function (rows, pick) { return rows.reduce(function (acc, r) { return acc + pick(r); }, 0); };
    var cases = sum(priced, function (r) { return r.seg.n; });
    var effort = sum(priced, function (r) { return r.seg.n * r.seg.e_mean; });
    var required = priced.map(function (r) { return r.required; });
    return {
      negatives: negatives,
      negativeCaseShare: sum(negatives, function (r) { return r.seg.n; }) / cases,
      negativeEffortShare: sum(negatives, function (r) { return r.seg.n * r.seg.e_mean; }) / effort,
      firstPositive: Math.min.apply(null, required),
      allPositive: Math.max.apply(null, required)
    };
  }

  function curve(order) {
    var sorted = data.segments.slice().sort(function (a, b) { return b[order] - a[order]; });
    var effort = 0, volume = 0, points = [{ share: 0, volume: 0 }];
    var totalEffort = sorted.reduce(function (sum, s) { return sum + s.n * s.e_mean; }, 0);
    sorted.forEach(function (s) {
      effort += s.n * s.e_mean;
      volume += s.n * s.p * s.r_mean;
      points.push({ share: effort / totalEffort, volume: volume });
    });
    return points;
  }

  function volumeAt(points, share) {
    for (var i = 1; i < points.length; i++) {
      if (points[i].share >= share) {
        var a = points[i - 1], b = points[i];
        return a.volume + (share - a.share) / (b.share - a.share) * (b.volume - a.volume);
      }
    }
    return points[points.length - 1].volume;
  }

  var curves = { eta: curve("eta"), p: curve("p") };

  /* ---------- 계산기 화면 ---------- */

  var costInput = document.getElementById("cost");
  var marginInput = document.getElementById("margin");
  var budgetInput = document.getElementById("budget");
  costInput.value = data.reference_cost;
  document.getElementById("cost-hint").textContent = "참조값 " + data.reference_cost + " — 출처: " + data.reference_cost_source;

  function render() {
    var cost = parseFloat(costInput.value);
    var margin = parseFloat(marginInput.value) / 100;
    var budget = parseFloat(budgetInput.value) / 100;

    document.getElementById("cost-value").textContent = cost.toFixed(1) + " 유로";
    document.getElementById("margin-value").textContent = (margin * 100).toFixed(1) + "%";
    document.getElementById("budget-value").textContent = (budget * 100).toFixed(0) + "%";

    var priced = priceSegments(cost, margin);
    var totals = summarise(priced);

    var box = document.getElementById("calc-cards");
    box.innerHTML = "";
    box.appendChild(card("적자 세그먼트", totals.negatives.length + "<small> / " + priced.length + "</small>"));
    box.appendChild(card("적자 신청 비중", fmt.pct(totals.negativeCaseShare)));
    box.appendChild(card("적자 공수 비중", fmt.pct(totals.negativeEffortShare)));

    var byEta = volumeAt(curves.eta, budget), byRate = volumeAt(curves.p, budget);
    document.getElementById("breakeven").innerHTML =
      "순마진 비중이 <b>" + fmt.pct(totals.firstPositive, 2) + "</b>를 초과하면 첫 세그먼트가, <b>" +
      fmt.pct(totals.allPositive, 2) + "</b>를 초과하면 " + priced.length + "개 전부가 흑자로 전환됩니다. 두 값의 배율 " +
      (totals.allPositive / totals.firstPositive).toFixed(1) + "배는 시간당 비용과 무관하게 유지됩니다." +
      "<br><br>공수 " + (budget * 100).toFixed(0) + "%에서 효율 순서는 <b>" + fmt.million(byEta) +
      "백만 유로</b>, 성사율 순서는 " + fmt.million(byRate) + "백만 유로로 " +
      fmt.pct(byEta / byRate - 1) + "의 차이가 발생합니다.";

    table(document.getElementById("calc-table"),
      ["세그먼트", "신청 수", "성사율", "효율 η", "필요 순마진", "신청당 기대값", "합계"],
      priced.map(function (r) {
        return [r.seg.label, fmt.int(r.seg.n), fmt.pct(r.seg.p), fmt.eur(r.seg.eta),
                fmt.pct(r.required, 2),
                { text: fmt.eur(r.ev) + " 유로", cls: r.negative ? "neg" : "pos" },
                fmt.eur(r.evTotal)];
      }));
  }

  [costInput, marginInput, budgetInput].forEach(function (input) {
    input.addEventListener("input", render);
  });
  render();

  /* ---------- 파이썬 계산과의 교차 확인 ---------- */

  (function verify() {
    var check = data.reference_check;
    if (!check) { return; }
    var totals = summarise(priceSegments(check.cost, check.margin_share));
    var close = function (a, b, tol) { return Math.abs(a - b) <= (tol || 1e-6) * Math.max(1, Math.abs(b)); };
    var problems = [];
    if (totals.negatives.length !== check.negative_segments) { problems.push("적자 세그먼트 수"); }
    if (!close(totals.negativeCaseShare, check.negative_case_share)) { problems.push("적자 신청 비중"); }
    if (!close(totals.negativeEffortShare, check.negative_effort_share)) { problems.push("적자 공수 비중"); }
    if (!close(totals.firstPositive, check.first_positive)) { problems.push("첫 흑자 비중"); }
    if (!close(totals.allPositive, check.all_positive)) { problems.push("전체 흑자 비중"); }
    if (!close(volumeAt(curves.eta, check.budget), check.volume_by_eta)) { problems.push("효율 순서 배분"); }
    if (!close(volumeAt(curves.p, check.budget), check.volume_by_success_rate)) { problems.push("성사율 순서 배분"); }
    if (problems.length) {
      console.warn("화면 계산이 analysis/calculator.py의 기준값과 다르다: " + problems.join(", "));
    } else {
      console.info("계산 교차 확인 통과 — 시간당 " + check.cost + "유로, 순마진 " +
                   (check.margin_share * 100).toFixed(1) + "%에서 파이썬 기준값과 일치");
    }
  })();

  /* ---------- 스크롤 ---------- */

  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-item"));
  var sections = links.map(function (link) { return document.getElementById(link.dataset.target); });

  function activate(id) {
    links.forEach(function (link) { link.classList.toggle("active", link.dataset.target === id); });
  }

  links.forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      var target = document.getElementById(link.dataset.target);
      activate(link.dataset.target);
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", "#" + link.dataset.target);
    });
  });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) { activate(entry.target.id); }
    });
  }, { rootMargin: "-15% 0px -70% 0px", threshold: 0 });

  sections.forEach(function (section) { if (section) { observer.observe(section); } });
  activate(sections[0].id);

  /* README 화면 캡처용 (analysis/23_capture_screens.py). headless 캡처는 스크롤한 화면을 다시 그리지 않으므로,
     스크롤 대신 다른 구역을 숨겨 대상 구역을 첫 화면에 둔다. */
  var shot = /[?&]shot=([\w-]+)/.exec(window.location.search);
  if (shot && document.getElementById(shot[1])) {
    document.querySelector(".topbar").style.display = "none";
    document.getElementById("page-note").style.display = "none";
    sections.forEach(function (section) {
      if (section && section.id !== shot[1]) { section.style.display = "none"; }
    });
    activate(shot[1]);
  }
})();
