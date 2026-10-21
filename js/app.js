(() => {
  const money = (n) => {
    if (n == null) return null;
    const fixed = Math.abs(n - Math.round(n)) < 0.005 ? String(Math.round(n)) : n.toFixed(2);
    return fixed.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  const state = {
    products: [],
    categories: [],
    tiers: [],
    q: "",
    cat: "全部",
    tier: "全部",
  };

  const el = {
    grid: document.getElementById("grid"),
    empty: document.getElementById("empty"),
    meta: document.getElementById("meta"),
    q: document.getElementById("q"),
    cats: document.getElementById("cat-chips"),
    tiers: document.getElementById("tier-chips"),
    drawer: document.getElementById("drawer"),
    dMedia: document.getElementById("d-media"),
    dBrand: document.getElementById("d-brand"),
    dTitle: document.getElementById("d-title"),
    dPrice: document.getElementById("d-price"),
    dTier: document.getElementById("d-tier"),
    dModel: document.getElementById("d-model"),
    dSpec: document.getElementById("d-spec"),
    dLink: document.getElementById("d-link"),
  };

  function chip(label, active, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip" + (active ? " active" : "");
    b.textContent = label;
    b.setAttribute("aria-pressed", active ? "true" : "false");
    b.addEventListener("click", onClick);
    return b;
  }

  function renderChips() {
    el.cats.replaceChildren(
      chip("全部", state.cat === "全部", () => { state.cat = "全部"; render(); }),
      ...state.categories.map((c) =>
        chip(c, state.cat === c, () => { state.cat = c; render(); })
      )
    );
    el.tiers.replaceChildren(
      chip("全部预算", state.tier === "全部", () => { state.tier = "全部"; render(); }),
      ...state.tiers.map((t) =>
        chip(t, state.tier === t, () => { state.tier = t; render(); })
      )
    );
  }

  function filtered() {
    const q = state.q.trim().toLowerCase();
    return state.products.filter((p) => {
      if (state.cat !== "全部" && p.category !== state.cat) return false;
      if (state.tier !== "全部" && p.tier !== state.tier) return false;
      if (!q) return true;
      const hay = [p.name, p.title, p.brand, p.model, p.category].join(" ").toLowerCase();
      return hay.includes(q);
    });
  }

  function card(p, index) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "card";
    btn.addEventListener("click", () => openDrawer(p));

    const plinth = document.createElement("div");
    plinth.className = "plinth";
    const no = document.createElement("span");
    no.className = "card-no";
    no.textContent = "No." + String(index + 1).padStart(3, "0");
    plinth.appendChild(no);
    if (p.image) {
      const img = document.createElement("img");
      img.src = p.image;
      img.alt = "";
      img.loading = "lazy";
      img.decoding = "async";
      img.onerror = () => { img.remove(); };
      plinth.appendChild(img);
    } else {
      const empty = document.createElement("span");
      empty.className = "plinth-empty";
      empty.innerHTML = "<b>礼</b><small>图待补</small>";
      plinth.appendChild(empty);
    }

    const brand = document.createElement("p");
    brand.className = "card-brand";
    brand.textContent = p.brand || p.category || "华甄选";

    const title = document.createElement("h3");
    title.className = "card-title";
    title.textContent = p.title || p.name;

    const price = document.createElement("p");
    price.className = "card-price";
    if (p.retail != null) {
      price.innerHTML = "<em>¥</em>" + money(p.retail);
    } else {
      price.innerHTML = '<span class="ask">询价</span>';
    }

    btn.append(plinth, brand, title, price);
    return btn;
  }

  function openDrawer(p) {
    el.dMedia.replaceChildren();
    if (p.image) {
      const img = document.createElement("img");
      img.src = p.image;
      img.alt = p.name;
      el.dMedia.appendChild(img);
    }
    el.dBrand.textContent = p.brand || p.category || "华甄选";
    el.dTitle.textContent = p.title || p.name;
    el.dPrice.innerHTML = p.retail != null ? ("¥ " + money(p.retail)) : "询价";
    el.dTier.textContent = p.tier ? ("预算档 · " + p.tier) : "";
    el.dModel.textContent = p.model ? ("型号 · " + p.model) : "";
    el.dSpec.textContent = p.spec || "";
    if (p.link) {
      el.dLink.hidden = false;
      el.dLink.href = p.link;
    } else {
      el.dLink.hidden = true;
    }
    el.drawer.showModal();
  }

  function render() {
    renderChips();
    const list = filtered();
    el.meta.textContent = `共 ${list.length} / ${state.products.length} 件`;
    el.grid.replaceChildren(...list.map((p, i) => card(p, i)));
    el.empty.hidden = list.length > 0;
  }

  el.q.addEventListener("input", () => {
    state.q = el.q.value;
    render();
  });

  fetch("data/products.json")
    .then((r) => {
      if (!r.ok) throw new Error("products.json " + r.status);
      return r.json();
    })
    .then((data) => {
      state.products = data.products || [];
      state.categories = data.categories || [];
      state.tiers = data.tiers || [];
      render();
    })
    .catch((err) => {
      el.meta.textContent = "加载失败：" + err.message;
    });
})();
