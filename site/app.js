(function () {
  "use strict";

  var ICONS = {
    car:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16.5V12l1.8-5A2 2 0 017.7 5.5h8.6a2 2 0 011.9 1.5l1.8 5v4.5"/><path d="M4 16.5h16"/><path d="M4 16.5v2.3a1 1 0 001 1h1.2a1 1 0 001-1v-2.3"/><path d="M16.8 16.5v2.3a1 1 0 001 1H19a1 1 0 001-1v-2.3"/><circle cx="7.5" cy="13.2" r="1.1" fill="currentColor" stroke="none"/><circle cx="16.5" cy="13.2" r="1.1" fill="currentColor" stroke="none"/></svg>',
    globe:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 010 18 15 15 0 010-18z"/></svg>',
    flag:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3v18"/><path d="M5 4h14l-3 3.5 3 3.5H5z"/></svg>',
    clock:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/></svg>',
    shield:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5.5c0 4.6-3 8.3-7 9.5-4-1.2-7-4.9-7-9.5V6z"/><path d="M9 12l2 2 4-4.5"/></svg>',
  };

  var CATEGORY_ORDER = ["new_product", "new_tech", "regulation", "management", "policy", "other"];
  var CATEGORY_LABEL = {
    new_product: "新製品",
    new_tech: "新技術",
    regulation: "規制",
    management: "経営",
    policy: "政策",
    other: "他",
    all: "すべて",
  };
  var REGION_ORDER = ["global", "japan", "us", "europe", "asia", "oceania", "africa", "middle_east", "russia"];
  var MOTORSPORTS_ORDER = [
    "f1", "wec", "wrc", "nascar_indycar", "super_gt_sf", "formula_e",
    "cross_country_rally", "drift", "all_japan_rally",
  ];

  var board = document.getElementById("board");
  var statsEl = document.getElementById("stats");
  var lastUpdatedEl = document.getElementById("last-updated");
  var statusDot = document.getElementById("status-dot");
  var loadingEl = document.getElementById("loading");

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function formatPublished(raw) {
    if (!raw) return "";
    var parsed = new Date(raw);
    if (isNaN(parsed.getTime())) return raw;
    return parsed.toLocaleString("ja-JP", {
      year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  function isWithin24h(item) {
    if (!item.published) return false;
    var parsed = Date.parse(item.published);
    if (isNaN(parsed)) return false;
    return Date.now() - parsed <= 86400000;
  }

  function countRecent(items) {
    return (items || []).filter(isWithin24h).length;
  }

  function buildItem(item) {
    var recent = isWithin24h(item);
    var a = el("a", "item" + (recent ? " item--recent" : ""));
    a.href = item.url || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    if (!item.url) {
      a.removeAttribute("href");
      a.style.cursor = "default";
    }

    var body = el("div", "item__body");
    body.appendChild(el("span", "item__title", item.title || "(タイトル不明)"));
    if (item.title_ja) {
      body.appendChild(el("span", "item__title-ja", item.title_ja));
    }

    var meta = el("div", "item__meta");
    if (recent) meta.appendChild(el("span", "new-badge", "24時間以内"));
    if (item.category && CATEGORY_LABEL[item.category]) {
      meta.appendChild(el("span", "cat-chip cat-chip--" + item.category, CATEGORY_LABEL[item.category]));
    }
    if (item.source) meta.appendChild(el("span", null, item.source));
    var published = formatPublished(item.published);
    if (published) meta.appendChild(el("span", null, published));
    body.appendChild(meta);
    a.appendChild(body);
    return a;
  }

  function buildList(items) {
    var list = el("ul", "panel__list");
    (items || []).forEach(function (item) {
      var li = el("li");
      li.appendChild(buildItem(item));
      list.appendChild(li);
    });
    return list;
  }

  function renderInto(wrap, items) {
    wrap.innerHTML = "";
    if (!items || items.length === 0) {
      wrap.appendChild(el("p", "panel__empty", "現在、該当する情報はありません。"));
    } else {
      wrap.appendChild(buildList(items));
    }
  }

  function buildPanelHeader(icon, label, count) {
    var header = el("div", "panel__header");
    var iconWrap = el("div", "panel__icon");
    iconWrap.innerHTML = ICONS[icon] || "";
    header.appendChild(iconWrap);
    header.appendChild(el("h2", "panel__title", label));
    if (count !== undefined) header.appendChild(el("span", "panel__count", count + " 件"));
    return header;
  }

  function makeTabGroup(labels, activeIdx, onSelect, extraClass) {
    var group = el("div", "tab-group" + (extraClass ? " " + extraClass : ""));
    var buttons = labels.map(function (label, idx) {
      var btn = el("button", "tab-group__btn" + (idx === activeIdx ? " is-active" : ""), label);
      btn.addEventListener("click", function () {
        buttons.forEach(function (b, i) { b.classList.toggle("is-active", i === idx); });
        onSelect(idx);
      });
      group.appendChild(btn);
      return btn;
    });
    return group;
  }

  function filterByCategory(items, category) {
    if (category === "all") return items;
    return (items || []).filter(function (item) { return item.category === category; });
  }

  // ---- 上部ダイジェスト(直近24時間ハイライト) ------------------------------

  function buildDigestPanel(data) {
    var sections = data.sections || {};
    var panel = el("section", "panel panel--full digest-panel");
    var rows = [];

    if (sections.toyota_news) {
      rows.push({ label: "① トヨタ自動車トピックス", count: countRecent(sections.toyota_news.newest), anchor: "section-toyota" });
    }
    if (sections.industry_news && sections.industry_news.regions) {
      var regions = sections.industry_news.regions;
      var industryCount = REGION_ORDER.reduce(function (sum, key) {
        return sum + (regions[key] ? countRecent(regions[key].newest) : 0);
      }, 0);
      rows.push({ label: "② 自動車産業に関するトピックス", count: industryCount, anchor: "section-industry" });
    }
    if (sections.motorsports && sections.motorsports.categories) {
      var cats = sections.motorsports.categories;
      var motorsportsCount = MOTORSPORTS_ORDER.reduce(function (sum, key) {
        return sum + (cats[key] ? countRecent(cats[key].newest) : 0);
      }, 0);
      rows.push({ label: "③ モータースポーツ", count: motorsportsCount, anchor: "section-motorsports" });
    }
    if (sections.regulations && sections.regulations.regions) {
      var regRegions = sections.regulations.regions;
      var regCount = 0;
      REGULATION_REGION_ORDER.forEach(function (rk) {
        var r = regRegions[rk];
        if (!r) return;
        REGULATION_CATEGORY_ORDER.forEach(function (ck) {
          var c = r.categories[ck];
          regCount += countRecent(c.summary.newest) + countRecent(c.authority.newest);
        });
      });
      rows.push({ label: "④ 規制動向", count: regCount, anchor: "section-regulations" });
    }

    var totalCount = rows.reduce(function (sum, r) { return sum + r.count; }, 0);
    panel.appendChild(buildPanelHeader("clock", "直近24時間ダイジェスト", totalCount));
    panel.appendChild(el("p", "panel__note", "各項目で過去24時間以内に更新された件数です。クリックすると該当セクションへ移動します。"));

    var list = el("div", "digest-list");
    rows.forEach(function (r) {
      var row = el("a", "digest-row" + (r.count > 0 ? " digest-row--active" : ""));
      row.href = "#" + r.anchor;
      row.addEventListener("click", function (evt) {
        var target = document.getElementById(r.anchor);
        if (target) {
          evt.preventDefault();
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
      row.appendChild(el("span", "digest-row__label", r.label));
      row.appendChild(el("span", "digest-row__count", String(r.count)));
      list.appendChild(row);
    });
    panel.appendChild(list);
    return panel;
  }

  // ---- ① トヨタ自動車: 株価チャート ------------------------------------------

  var SVG_NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs) {
    var node = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    return node;
  }

  function formatYen0(n) {
    return "¥" + Math.round(n).toLocaleString("ja-JP");
  }

  function jstDate(t) {
    // tはUnix秒(UTC)。日本株なので表示はJST(UTC+9)に固定する。
    return new Date((t + 9 * 3600) * 1000);
  }

  function fmtTime(t) {
    var d = jstDate(t);
    var hh = String(d.getUTCHours()).padStart(2, "0");
    var mm = String(d.getUTCMinutes()).padStart(2, "0");
    return hh + ":" + mm;
  }

  function fmtDateShort(t) {
    var d = jstDate(t);
    return (d.getUTCMonth() + 1) + "/" + d.getUTCDate();
  }

  function fmtDateMonth(t) {
    var d = jstDate(t);
    return d.getUTCFullYear() + "/" + String(d.getUTCMonth() + 1).padStart(2, "0");
  }

  function dayKey(t) {
    var d = jstDate(t);
    return d.getUTCFullYear() + "-" + d.getUTCMonth() + "-" + d.getUTCDate();
  }

  var STOCK_PERIODS = [
    { key: "1d", label: "日", source: "intraday", xFmt: fmtTime, filter: function (pts) {
      if (!pts.length) return [];
      var lastKey = dayKey(pts[pts.length - 1].t);
      return pts.filter(function (p) { return dayKey(p.t) === lastKey; });
    } },
    { key: "1w", label: "週", source: "intraday", xFmt: fmtDateShort, filter: function (pts) { return pts; } },
    { key: "1mo", label: "月", source: "daily", xFmt: fmtDateShort, filter: function (pts) { return sliceLastNDays(pts, 31); } },
    { key: "3mo", label: "3ヶ月", source: "daily", xFmt: fmtDateShort, filter: function (pts) { return sliceLastNDays(pts, 92); } },
    { key: "6mo", label: "6ヶ月", source: "daily", xFmt: fmtDateMonth, filter: function (pts) { return sliceLastNDays(pts, 183); } },
    { key: "1y", label: "1年", source: "daily", xFmt: fmtDateMonth, filter: function (pts) { return pts; } },
  ];

  function sliceLastNDays(pts, days) {
    if (!pts.length) return [];
    var cutoff = pts[pts.length - 1].t - days * 86400;
    return pts.filter(function (p) { return p.t >= cutoff; });
  }

  function niceTicks(min, max, count) {
    var ticks = [];
    for (var i = 0; i < count; i++) ticks.push(min + ((max - min) * i) / (count - 1));
    return ticks;
  }

  function renderStockSVG(points, xFmt) {
    var W = 640, H = 260;
    var marginLeft = 58, marginRight = 12, marginTop = 12, marginBottom = 26;
    var plotW = W - marginLeft - marginRight;
    var plotH = H - marginTop - marginBottom;

    var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, class: "stock-card__chart" });

    if (!points || points.length === 0) {
      var emptyText = svgEl("text", { x: W / 2, y: H / 2, "text-anchor": "middle", "font-size": "13" });
      emptyText.style.fill = "var(--ink-muted)";
      emptyText.textContent = "データがありません";
      svg.appendChild(emptyText);
      return svg;
    }

    var closes = points.map(function (p) { return p.close; });
    var rawMin = Math.min.apply(null, closes);
    var rawMax = Math.max.apply(null, closes);
    var pad = (rawMax - rawMin) * 0.08 || rawMax * 0.02 || 1;
    var min = rawMin - pad;
    var max = rawMax + pad;
    var range = max - min || 1;
    var up = points[points.length - 1].close >= points[0].close;

    function xAt(i) { return marginLeft + (i / Math.max(1, points.length - 1)) * plotW; }
    function yAt(v) { return marginTop + (1 - (v - min) / range) * plotH; }

    // Y軸: 目盛線とラベル
    var yTicks = niceTicks(min, max, 4);
    yTicks.forEach(function (v) {
      var y = yAt(v);
      var gridline = svgEl("line", { x1: marginLeft, x2: W - marginRight, y1: y.toFixed(1), y2: y.toFixed(1) });
      gridline.style.stroke = "var(--line)";
      gridline.setAttribute("stroke-width", "1");
      svg.appendChild(gridline);

      var label = svgEl("text", { x: marginLeft - 8, y: (y + 3.5).toFixed(1), "text-anchor": "end", "font-size": "11" });
      label.style.fill = "var(--ink-muted)";
      label.textContent = "¥" + Math.round(v).toLocaleString("ja-JP");
      svg.appendChild(label);
    });

    // X軸: 5点の目盛ラベル
    var xTickCount = Math.min(5, points.length);
    for (var i = 0; i < xTickCount; i++) {
      var idx = Math.round((i / Math.max(1, xTickCount - 1)) * (points.length - 1));
      var x = xAt(idx);
      // 端のラベルは中央揃えだとviewBox外にはみ出るため、両端だけ内側寄せにする。
      var anchor = i === 0 ? "start" : i === xTickCount - 1 ? "end" : "middle";
      var xLabel = svgEl("text", { x: x.toFixed(1), y: H - 6, "text-anchor": anchor, "font-size": "11" });
      xLabel.style.fill = "var(--ink-muted)";
      xLabel.textContent = xFmt(points[idx].t);
      svg.appendChild(xLabel);
    }

    // 折れ線 + 塗りつぶし
    var linePoints = points.map(function (p, i) { return xAt(i).toFixed(1) + "," + yAt(p.close).toFixed(1); });
    var areaPoints = linePoints.concat([
      xAt(points.length - 1).toFixed(1) + "," + (marginTop + plotH),
      xAt(0).toFixed(1) + "," + (marginTop + plotH),
    ]).join(" ");
    var area = svgEl("polygon", { points: areaPoints });
    area.style.fill = up ? "rgba(255,90,90,0.14)" : "rgba(63,208,208,0.14)";
    svg.appendChild(area);

    var line = svgEl("polyline", {
      points: linePoints.join(" "), fill: "none", "stroke-width": "2",
      "stroke-linejoin": "round", "stroke-linecap": "round",
    });
    line.style.stroke = up ? "var(--critical)" : "var(--cat-new_tech)";
    svg.appendChild(line);

    return svg;
  }

  function buildStockChart(stock) {
    var card = el("div", "stock-card");
    card.appendChild(el("div", "stock-card__title", "トヨタ自動車 株価 (7203.T)"));

    if (!stock || stock.error || (!stock.daily && !stock.intraday)) {
      card.appendChild(el("p", "panel__empty", "株価データを取得できませんでした。"));
      return card;
    }

    var up = (stock.change || 0) >= 0;
    var sign = up ? "+" : "";

    var priceRow = el("div", "stock-card__price-row");
    priceRow.appendChild(el("span", "stock-card__price", formatYen0(stock.price)));
    if (stock.change != null && stock.change_percent != null) {
      priceRow.appendChild(el(
        "span",
        "stock-card__change " + (up ? "stock-card__change--up" : "stock-card__change--down"),
        sign + stock.change.toFixed(1) + " (" + sign + stock.change_percent.toFixed(2) + "%)"
      ));
    }
    card.appendChild(priceRow);

    var periodTabs = el("div", "tab-group");
    var chartWrap = el("div");
    var rangeRow = el("div", "stock-card__range");
    card.appendChild(periodTabs);
    card.appendChild(chartWrap);
    card.appendChild(rangeRow);

    var defaultIdx = 3; // 3ヶ月
    var buttons = STOCK_PERIODS.map(function (period, idx) {
      var btn = el("button", "tab-group__btn" + (idx === defaultIdx ? " is-active" : ""), period.label);
      btn.addEventListener("click", function () {
        buttons.forEach(function (b, i) { b.classList.toggle("is-active", i === idx); });
        renderPeriod(period);
      });
      periodTabs.appendChild(btn);
      return btn;
    });

    function renderPeriod(period) {
      var source = (period.source === "intraday" ? stock.intraday : stock.daily) || [];
      var points = period.filter(source.slice());
      chartWrap.innerHTML = "";
      chartWrap.appendChild(renderStockSVG(points, period.xFmt));

      rangeRow.innerHTML = "";
      if (points.length > 0) {
        var closes = points.map(function (p) { return p.close; });
        var min = Math.min.apply(null, closes);
        var max = Math.max.apply(null, closes);
        rangeRow.appendChild(el("span", null, "安値 " + formatYen0(min)));
        rangeRow.appendChild(el("span", null, "高値 " + formatYen0(max)));
      }
    }

    renderPeriod(STOCK_PERIODS[defaultIdx]);

    card.appendChild(el(
      "p", "panel__note stock-card__note",
      "終値ベース。データ提供: Yahoo Finance(非公式・無認証エンドポイント)。「日」「週」は15分足、" +
      "「月」以降は日足を表示しています。"
    ));

    return card;
  }

  // ---- ① トヨタ自動車: 最新決算ダイジェスト ----------------------------------

  function formatMillionYen(millions) {
    if (millions == null) return "—";
    var trillion = millions / 1000000;
    if (Math.abs(trillion) >= 0.1) return trillion.toFixed(2) + "兆円";
    return Math.round(millions).toLocaleString("ja-JP") + "百万円";
  }

  function buildEarningsCard(earnings) {
    var card = el("div", "earnings-card");
    card.appendChild(el("div", "earnings-card__title", "直近四半期決算(前年同期比)"));

    if (!earnings || earnings.error || !earnings.quarterly) {
      card.appendChild(el("p", "panel__empty", "決算データを取得できませんでした。"));
      return card;
    }

    var q = earnings.quarterly;
    card.appendChild(el(
      "div", "earnings-card__period",
      (q.release_title || q.period_label) + (q.announced ? " ・発表日 " + q.announced : "")
    ));

    var rows = [
      { key: "revenue", label: "営業収益" },
      { key: "operating_income", label: "営業利益" },
      { key: "income_before_tax", label: "税引前利益" },
      { key: "net_income", label: "親会社帰属 四半期利益" },
    ];

    var grid = el("div", "earnings-card__grid");
    rows.forEach(function (r) {
      var value = q[r.key];
      var yoy = q[r.key + "_yoy"];
      var cell = el("div", "earnings-card__cell");
      cell.appendChild(el("div", "earnings-card__cell-label", r.label));
      cell.appendChild(el("div", "earnings-card__cell-value", formatMillionYen(value)));
      if (yoy !== undefined && yoy !== null) {
        var yoyUp = yoy >= 0;
        cell.appendChild(el(
          "div", "earnings-card__yoy " + (yoyUp ? "earnings-card__yoy--up" : "earnings-card__yoy--down"),
          "前年同期比 " + (yoyUp ? "+" : "") + yoy.toFixed(1) + "%"
        ));
      }
      grid.appendChild(cell);
    });
    card.appendChild(grid);

    var extra = el("div", "earnings-card__extra");
    if (q.eps != null) extra.appendChild(el("span", null, "EPS " + q.eps + "円"));
    if (q.operating_margin != null) extra.appendChild(el("span", null, "営業利益率 " + q.operating_margin + "%"));
    if (extra.children.length > 0) card.appendChild(extra);

    var note = el("p", "panel__note earnings-card__note");
    note.appendChild(document.createTextNode(
      "出典: " + (earnings.source_label || "トヨタ自動車 投資家情報") + "(IFRS連結決算短信より)。 "
    ));
    var link = el("a", null, "決算報告ページ ↗");
    link.href = earnings.source_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    note.appendChild(link);
    if (q.pdf_url) {
      note.appendChild(document.createTextNode(" "));
      var pdfLink = el("a", null, "決算要旨PDF ↗");
      pdfLink.href = q.pdf_url;
      pdfLink.target = "_blank";
      pdfLink.rel = "noopener noreferrer";
      note.appendChild(pdfLink);
    }
    card.appendChild(note);

    return card;
  }

  // ---- ① トヨタ自動車: 通期業績比較(実績/期初見通し/最新見通し) --------------

  function pctDelta(latest, base) {
    if (latest == null || base == null || base === 0) return null;
    return ((latest - base) / Math.abs(base)) * 100;
  }

  function buildFullYearComparisonCard(earnings) {
    var card = el("div", "panel panel--full fullyear-card");
    card.appendChild(el("div", "earnings-card__title", "通期業績比較(全年期実績 / 期初見通し / 最新見通し)"));

    var fy = earnings && earnings.full_year;
    if (!earnings || earnings.error || !fy || !fy.prior_actual || !fy.initial_forecast || !fy.latest_forecast) {
      card.appendChild(el("p", "panel__empty", "通期業績データを取得できませんでした。"));
      return card;
    }

    var prior = fy.prior_actual;
    var initial = fy.initial_forecast;
    var latestFc = fy.latest_forecast;

    function extractParenDate(text) {
      var m = /[（(](.*?)[）)]/.exec(text || "");
      return m ? m[1] : "";
    }

    var table = el("table", "fullyear-table");
    var thead = el("thead");
    var headRow = el("tr");
    headRow.appendChild(el("th", "fullyear-table__row-label"));
    [
      { title: "全年期実績", sub: prior.period_label },
      { title: "期初見通し", sub: extractParenDate(fy.prior_release_title) + "時点" },
      { title: "最新見通し", sub: (earnings.quarterly.announced || "") + "時点" },
    ].forEach(function (h) {
      var th = el("th");
      th.appendChild(el("div", "fullyear-table__head-title", h.title));
      if (h.sub) th.appendChild(el("div", "fullyear-table__head-sub", h.sub));
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var metricRows = [
      { key: "revenue", label: "営業収益" },
      { key: "operating_income", label: "営業利益" },
      { key: "income_before_tax", label: "税引前利益" },
      { key: "net_income", label: "親会社帰属利益" },
    ];

    var tbody = el("tbody");
    metricRows.forEach(function (m) {
      var tr = el("tr");
      tr.appendChild(el("th", "fullyear-table__row-label", m.label));

      // 全年期実績(前期比のみ参考表示)
      var priorCell = el("td");
      priorCell.appendChild(el("div", "fullyear-table__value", formatMillionYen(prior[m.key])));
      tbody.appendChild(tr);
      tr.appendChild(priorCell);

      // 期初見通し(全年期実績との比較)
      var initialCell = el("td");
      initialCell.appendChild(el("div", "fullyear-table__value", formatMillionYen(initial[m.key])));
      var initialYoy = initial[m.key + "_yoy"];
      if (initialYoy != null) {
        var initUp = initialYoy >= 0;
        initialCell.appendChild(el(
          "div", "earnings-card__yoy " + (initUp ? "earnings-card__yoy--up" : "earnings-card__yoy--down"),
          "前期比 " + (initUp ? "+" : "") + initialYoy.toFixed(1) + "%"
        ));
      }
      tr.appendChild(initialCell);

      // 最新見通し(全年期実績との比較 + 期初見通しからの修正幅)
      var latestCell = el("td");
      latestCell.appendChild(el("div", "fullyear-table__value", formatMillionYen(latestFc[m.key])));
      var latestYoy = latestFc[m.key + "_yoy"];
      if (latestYoy != null) {
        var lUp = latestYoy >= 0;
        latestCell.appendChild(el(
          "div", "earnings-card__yoy " + (lUp ? "earnings-card__yoy--up" : "earnings-card__yoy--down"),
          "前期比 " + (lUp ? "+" : "") + latestYoy.toFixed(1) + "%"
        ));
      }
      var revision = pctDelta(latestFc[m.key], initial[m.key]);
      if (revision != null) {
        var revUp = revision >= 0;
        latestCell.appendChild(el(
          "div", "fullyear-table__revision " + (revUp ? "earnings-card__yoy--up" : "earnings-card__yoy--down"),
          "期初比 " + (revUp ? "+" : "") + revision.toFixed(1) + "%"
        ));
      }
      tr.appendChild(latestCell);
    });
    table.appendChild(tbody);

    var tableWrap = el("div", "list-scroll fullyear-table-wrap");
    tableWrap.appendChild(table);
    card.appendChild(tableWrap);

    var note = el("p", "panel__note earnings-card__note");
    note.appendChild(document.createTextNode(
      "「期初見通し」は" + (fy.prior_release_title || "前期決算") + "で発表された翌期予想、" +
      "「最新見通し」は直近四半期決算で更新された今期予想です。「前期比」は全年期実績との比較、" +
      "「期初比」は期初見通しからの修正幅です。出典: トヨタ自動車 投資家情報(公式)。 "
    ));
    if (fy.prior_pdf_url) {
      var priorLink = el("a", null, "前期決算要旨PDF ↗");
      priorLink.href = fy.prior_pdf_url;
      priorLink.target = "_blank";
      priorLink.rel = "noopener noreferrer";
      note.appendChild(priorLink);
    }
    card.appendChild(note);

    return card;
  }

  // ---- ① トヨタ自動車 最新トピックス ---------------------------------------

  function buildToyotaPanel(section, stockData, earningsData) {
    var panel = el("section", "panel panel--full");
    panel.id = "section-toyota";
    panel.appendChild(buildPanelHeader("car", "① トヨタ自動車 最新トピックス", (section.newest || []).length));

    var topRow = el("div", "toyota-top-row");
    topRow.appendChild(buildStockChart(stockData));
    topRow.appendChild(buildEarningsCard(earningsData));
    panel.appendChild(topRow);

    panel.appendChild(buildFullYearComparisonCard(earningsData));

    panel.appendChild(el("p", "panel__note", "トヨタ自動車に関するニュースをGoogleニュース検索から日英で集約し、見出しのキーワードから新製品・新技術・規制・経営・政策・他へ自動分類しています(参考値)。"));

    var listWrap = el("div", "list-scroll");
    var activeCategory = "all";
    var activeSort = "newest";

    function render() {
      renderInto(listWrap, filterByCategory(section[activeSort], activeCategory));
    }

    // 実際にトピックス内に存在するカテゴリーのみをタブ化する
    // (押しても該当ゼロ件になるタブを作らないため)。
    var presentCategories = CATEGORY_ORDER.filter(function (c) {
      return (section.newest || []).some(function (item) { return item.category === c; });
    });
    var categoryLabels = ["すべて"].concat(presentCategories.map(function (c) { return CATEGORY_LABEL[c]; }));
    var categoryKeys = ["all"].concat(presentCategories);
    panel.appendChild(makeTabGroup(categoryLabels, 0, function (idx) {
      activeCategory = categoryKeys[idx];
      render();
    }));

    panel.appendChild(makeTabGroup(["最新順", "話題順"], 0, function (idx) {
      activeSort = idx === 0 ? "newest" : "popular";
      render();
    }));
    panel.appendChild(listWrap);
    render();
    return panel;
  }

  // ---- ② 自動車産業に関するトピックス(地域×カテゴリ) ------------------------

  function buildIndustryPanel(section) {
    var regions = section.regions || {};
    var panel = el("section", "panel panel--full");
    panel.id = "section-industry";
    var totalCount = REGION_ORDER.reduce(function (sum, k) {
      return sum + (regions[k] ? regions[k].newest.length : 0);
    }, 0);
    panel.appendChild(buildPanelHeader("globe", "② 自動車産業に関するトピックス", totalCount));
    panel.appendChild(el("p", "panel__note", "地域別に自動車産業ニュースを集約し、見出しのキーワードから新製品・新技術・規制・経営・政策・他へ自動分類しています(参考値)。"));

    var regionLabels = REGION_ORDER.filter(function (k) { return regions[k]; }).map(function (k) {
      return (regions[k].flag || "") + " " + regions[k].label;
    });
    var regionKeys = REGION_ORDER.filter(function (k) { return regions[k]; });

    var categoryWrap = el("div");
    var sortWrap = el("div");
    var listWrap = el("div", "list-scroll");

    var activeRegionIdx = 0;
    var activeCategory = "all";
    var activeSort = "newest";

    var categoryTabs = null;
    var sortTabs = null;

    function renderList() {
      var region = regions[regionKeys[activeRegionIdx]];
      var items = filterByCategory(region[activeSort], activeCategory);
      renderInto(listWrap, items);
    }

    function renderCategoryTabs() {
      categoryWrap.innerHTML = "";
      var labels = ["すべて"].concat(CATEGORY_ORDER.map(function (c) { return CATEGORY_LABEL[c]; }));
      var keys = ["all"].concat(CATEGORY_ORDER);
      var activeIdx = keys.indexOf(activeCategory);
      categoryTabs = makeTabGroup(labels, activeIdx, function (idx) {
        activeCategory = keys[idx];
        renderList();
      });
      categoryWrap.appendChild(categoryTabs);
    }

    function renderSortTabs() {
      sortWrap.innerHTML = "";
      sortTabs = makeTabGroup(["最新順", "話題順"], activeSort === "newest" ? 0 : 1, function (idx) {
        activeSort = idx === 0 ? "newest" : "popular";
        renderList();
      });
      sortWrap.appendChild(sortTabs);
    }

    var regionTabs = makeTabGroup(regionLabels, 0, function (idx) {
      activeRegionIdx = idx;
      activeCategory = "all";
      renderCategoryTabs();
      renderList();
    }, "tab-group--region");

    panel.appendChild(regionTabs);
    panel.appendChild(categoryWrap);
    panel.appendChild(sortWrap);
    panel.appendChild(listWrap);

    renderCategoryTabs();
    renderSortTabs();
    renderList();

    return panel;
  }

  // ---- ③ モータースポーツ(カテゴリ×並び順) ----------------------------------

  function mergeCategories(categories, keys, sortKey) {
    var seen = {};
    var pools = keys.map(function (k) { return (categories[k] && categories[k][sortKey]) || []; });

    if (sortKey === "newest") {
      var flat = [].concat.apply([], pools);
      flat.sort(function (a, b) {
        var ta = a.published ? Date.parse(a.published) : 0;
        var tb = b.published ? Date.parse(b.published) : 0;
        return tb - ta;
      });
      var out1 = [];
      flat.forEach(function (item) {
        var k = item.url || item.title;
        if (k && seen[k]) return;
        if (k) seen[k] = true;
        out1.push(item);
      });
      return out1;
    }

    // 話題順(popular)はカテゴリ間で比較可能なスコアがないため、
    // 各カテゴリの順位を保ったままラウンドロビンで均等に混ぜる。
    var out2 = [];
    var maxLen = pools.reduce(function (m, p) { return Math.max(m, p.length); }, 0);
    for (var i = 0; i < maxLen; i++) {
      pools.forEach(function (p) {
        if (i >= p.length) return;
        var item = p[i];
        var k = item.url || item.title;
        if (k && seen[k]) return;
        if (k) seen[k] = true;
        out2.push(item);
      });
    }
    return out2;
  }

  function buildMotorsportsPanel(section) {
    var categories = section.categories || {};
    var keys = MOTORSPORTS_ORDER.filter(function (k) { return categories[k]; });
    var panel = el("section", "panel panel--full");
    panel.id = "section-motorsports";
    var totalCount = keys.reduce(function (sum, k) { return sum + categories[k].newest.length; }, 0);
    panel.appendChild(buildPanelHeader("flag", "③ モータースポーツ", totalCount));
    panel.appendChild(el("p", "panel__note", "F1・WEC・WRC・NASCAR/IndyCar・Super GT/スーパーフォーミュラ・Formula E・クロスカントリーラリー・ドリフト・全日本ラリー選手権の話題をカテゴリー別に集約しています。"));

    var labels = ["すべて"].concat(keys.map(function (k) { return categories[k].label; }));
    var catKeys = ["all"].concat(keys);

    var sortWrap = el("div");
    var listWrap = el("div", "list-scroll");
    var activeCatIdx = 0;
    var activeSort = "newest";

    function renderList() {
      var items;
      if (catKeys[activeCatIdx] === "all") {
        items = mergeCategories(categories, keys, activeSort);
      } else {
        items = categories[catKeys[activeCatIdx]][activeSort];
      }
      renderInto(listWrap, items);
    }

    var categoryTabs = makeTabGroup(labels, activeCatIdx, function (idx) {
      activeCatIdx = idx;
      renderList();
    });

    function renderSortTabs() {
      sortWrap.innerHTML = "";
      sortWrap.appendChild(makeTabGroup(["最新順", "話題順"], activeSort === "newest" ? 0 : 1, function (idx) {
        activeSort = idx === 0 ? "newest" : "popular";
        renderList();
      }));
    }

    panel.appendChild(categoryTabs);
    panel.appendChild(sortWrap);
    panel.appendChild(listWrap);

    renderSortTabs();
    renderList();

    return panel;
  }

  // ---- ④ 規制動向(地域×カテゴリー、サマリー/当局トピックス) -------------------

  var REGULATION_REGION_ORDER = ["japan", "us", "europe", "china"];
  var REGULATION_CATEGORY_ORDER = ["emissions", "safety", "noise", "cybersecurity"];
  var REGULATION_CATEGORY_LABEL = {
    emissions: "排気規制",
    safety: "安全性能規制",
    noise: "騒音規制",
    cybersecurity: "サイバーセキュリティ規制",
  };

  function mergeRegulationLists(categories, keys, listKey) {
    var seen = {};
    var pools = keys.map(function (k) { return (categories[k][listKey] && categories[k][listKey].newest) || []; });
    var flat = [].concat.apply([], pools);
    flat.sort(function (a, b) {
      var ta = a.published ? Date.parse(a.published) : 0;
      var tb = b.published ? Date.parse(b.published) : 0;
      return tb - ta;
    });
    var out = [];
    flat.forEach(function (item) {
      var k = item.url || item.title;
      if (k && seen[k]) return;
      if (k) seen[k] = true;
      out.push(item);
    });
    return out;
  }

  function buildRegulationSubPanel(title, items) {
    var wrap = el("div", "reg-subpanel");
    wrap.appendChild(el("div", "reg-subpanel__title", title + "(" + (items ? items.length : 0) + ")"));
    var listWrap = el("div", "list-scroll");
    renderInto(listWrap, items);
    wrap.appendChild(listWrap);
    return wrap;
  }

  function buildRegulationsPanel(section) {
    var regions = section.regions || {};
    var regionKeys = REGULATION_REGION_ORDER.filter(function (k) { return regions[k]; });
    var panel = el("section", "panel panel--full");
    panel.id = "section-regulations";

    var totalCount = regionKeys.reduce(function (sum, rk) {
      var cats = regions[rk].categories;
      return sum + REGULATION_CATEGORY_ORDER.reduce(function (s2, ck) {
        return s2 + cats[ck].summary.newest.length + cats[ck].authority.newest.length;
      }, 0);
    }, 0);

    panel.appendChild(buildPanelHeader("shield", "④ 規制動向(排気・安全性能・騒音・サイバーセキュリティ)", totalCount));
    panel.appendChild(el(
      "p", "panel__note",
      "日本・アメリカ・ヨーロッパ・中国における自動車開発に影響する規制動向を、排気規制・安全性能規制・" +
      "騒音規制・サイバーセキュリティ規制の4カテゴリーで集約しています。「最新サマリー」は規制動向に" +
      "関する報道全般、「当局の最新トピックス」は所管当局(国土交通省・NHTSA・欧州委員会/UNECE・MIIT等)の" +
      "名称を含む報道を中心に集約したものです(キーワード検索による自動集計のため参考値)。"
    ));

    var regionLabels = regionKeys.map(function (k) { return (regions[k].flag || "") + " " + regions[k].label; });
    var categoryWrap = el("div");
    var contentWrap = el("div");

    var activeRegionIdx = 0;
    var activeCategory = "all";

    function renderContent() {
      contentWrap.innerHTML = "";
      var cats = regions[regionKeys[activeRegionIdx]].categories;
      var summaryItems, authorityItems;
      if (activeCategory === "all") {
        summaryItems = mergeRegulationLists(cats, REGULATION_CATEGORY_ORDER, "summary");
        authorityItems = mergeRegulationLists(cats, REGULATION_CATEGORY_ORDER, "authority");
      } else {
        summaryItems = cats[activeCategory].summary.newest;
        authorityItems = cats[activeCategory].authority.newest;
      }
      var grid = el("div", "reg-grid");
      grid.appendChild(buildRegulationSubPanel("最新サマリー", summaryItems));
      grid.appendChild(buildRegulationSubPanel("当局の最新トピックス", authorityItems));
      contentWrap.appendChild(grid);
    }

    function renderCategoryTabs() {
      categoryWrap.innerHTML = "";
      var labels = ["すべて"].concat(REGULATION_CATEGORY_ORDER.map(function (k) { return REGULATION_CATEGORY_LABEL[k]; }));
      var keys = ["all"].concat(REGULATION_CATEGORY_ORDER);
      categoryWrap.appendChild(makeTabGroup(labels, keys.indexOf(activeCategory), function (idx) {
        activeCategory = keys[idx];
        renderContent();
      }));
    }

    var regionTabs = makeTabGroup(regionLabels, activeRegionIdx, function (idx) {
      activeRegionIdx = idx;
      activeCategory = "all";
      renderCategoryTabs();
      renderContent();
    }, "tab-group--region");

    panel.appendChild(regionTabs);
    panel.appendChild(categoryWrap);
    panel.appendChild(contentWrap);

    renderCategoryTabs();
    renderContent();

    return panel;
  }

  // ---- rendering entrypoint ------------------------------------------------

  function render(data) {
    board.innerHTML = "";
    board.appendChild(buildToyotaPanel(data.sections.toyota_news, data.sections.toyota_stock, data.sections.toyota_earnings));
    board.appendChild(buildIndustryPanel(data.sections.industry_news));
    board.appendChild(buildMotorsportsPanel(data.sections.motorsports));
    if (data.sections.regulations) {
      board.appendChild(buildRegulationsPanel(data.sections.regulations));
    }

    statsEl.innerHTML = "";
    statsEl.appendChild(buildDigestPanel(data));

    lastUpdatedEl.textContent = "最終更新: " + (data.generated_at_jst || "不明");
  }

  fetch("data/latest.json?_=" + Date.now())
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      render(data);
    })
    .catch(function (err) {
      loadingEl.textContent = "ダッシュボードデータの読み込みに失敗しました(" + err.message + ")。";
      statusDot.style.background = "var(--critical)";
      lastUpdatedEl.textContent = "更新情報を取得できませんでした";
    });
})();
