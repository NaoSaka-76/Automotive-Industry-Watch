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

  // ---- ① トヨタ自動車 最新トピックス ---------------------------------------

  function buildToyotaPanel(section) {
    var panel = el("section", "panel panel--full");
    panel.id = "section-toyota";
    panel.appendChild(buildPanelHeader("car", "① トヨタ自動車 最新トピックス", (section.newest || []).length));
    panel.appendChild(el("p", "panel__note", "トヨタ自動車に関するニュースをGoogleニュース検索から日英で集約しています。"));

    var listWrap = el("div");
    var sort = "newest";
    function render() { renderInto(listWrap, section[sort]); }

    panel.appendChild(makeTabGroup(["最新順", "話題順"], 0, function (idx) {
      sort = idx === 0 ? "newest" : "popular";
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
    var listWrap = el("div");

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
    var listWrap = el("div");
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

  // ---- rendering entrypoint ------------------------------------------------

  function render(data) {
    board.innerHTML = "";
    board.appendChild(buildToyotaPanel(data.sections.toyota_news));
    board.appendChild(buildIndustryPanel(data.sections.industry_news));
    board.appendChild(buildMotorsportsPanel(data.sections.motorsports));

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
