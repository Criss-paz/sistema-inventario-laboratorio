/*
 * app.js — comportamiento de la interfaz (estilo SIGAL). Sin librerías.
 * Todo es mejora progresiva: si este archivo no carga, cada pantalla sigue
 * funcionando con enlaces y formularios normales.
 *   - Tema claro/oscuro (se recuerda en este navegador).
 *   - Menú de usuario y menú lateral en celular.
 *   - Avisos flotantes: los de éxito se retiran solos; los de error se quedan.
 *   - Búsqueda rápida (Ctrl K): pantallas del menú y productos.
 *   - Ficha emergente de los puntos del calendario de vencimientos.
 */
(function () {
  "use strict";
  var raiz = document.documentElement;

  // ---------- Tema ----------
  var temaBtn = document.getElementById("theme-btn");
  function temaActual() {
    return raiz.dataset.theme || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  function pintarTemaBtn() {
    if (!temaBtn) return;
    var oscuro = temaActual() === "dark";
    temaBtn.querySelector(".tema-claro").hidden = oscuro;
    temaBtn.querySelector(".tema-oscuro").hidden = !oscuro;
  }
  if (temaBtn) {
    pintarTemaBtn();
    temaBtn.addEventListener("click", function () {
      var nuevo = temaActual() === "dark" ? "light" : "dark";
      raiz.dataset.theme = nuevo;
      try { localStorage.setItem("inventario-tema", nuevo); } catch (e) {}
      pintarTemaBtn();
    });
  }

  // ---------- Menú de usuario ----------
  var userBtn = document.getElementById("user-menu-btn");
  var userMenu = document.getElementById("user-dropdown");
  function cerrarUserMenu() { if (userMenu) { userMenu.hidden = true; userBtn.setAttribute("aria-expanded", "false"); } }
  if (userBtn && userMenu) {
    userBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var abrir = userMenu.hidden;
      userMenu.hidden = !abrir;
      userBtn.setAttribute("aria-expanded", String(abrir));
    });
    document.addEventListener("click", function (e) { if (!userMenu.contains(e.target)) cerrarUserMenu(); });
  }

  // ---------- Menú lateral en celular ----------
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("side-scrim");
  var menuBtn = document.getElementById("menu-btn");
  function menuLateral(abrir) {
    if (!sidebar) return;
    sidebar.classList.toggle("on", abrir);
    scrim.classList.toggle("on", abrir);
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { menuLateral(true); });
  if (scrim) scrim.addEventListener("click", function () { menuLateral(false); });

  // ---------- Avisos flotantes ----------
  function retirar(el) { el.classList.add("saliendo"); setTimeout(function () { el.remove(); }, 220); }
  document.querySelectorAll("#flash-stack .flash").forEach(function (el, n) {
    el.querySelector(".flash-cerrar").addEventListener("click", function () { retirar(el); });
    if (el.classList.contains("flash-success") || el.classList.contains("flash-info")) {
      setTimeout(function () { retirar(el); }, 5000 + n * 400);
    }
  });

  // ---------- Búsqueda rápida (Ctrl K) ----------
  var palette = document.getElementById("palette");
  var trigger = document.getElementById("search-trigger");
  if (palette && trigger) {
    var input = document.getElementById("palette-q");
    var lista = document.getElementById("palette-list");
    var urlBuscar = trigger.dataset.buscar;
    var pantallas = Array.prototype.map.call(document.querySelectorAll("#menu-principal a"), function (a) {
      return { titulo: a.dataset.pantalla, url: a.getAttribute("href"), ico: a.querySelector("svg").outerHTML };
    });
    var opciones = [], sel = 0, pedido = 0, temporizador = null;
    var icoProducto = (document.querySelector('#menu-principal a[data-icono="productos"] svg') || { outerHTML: "" }).outerHTML;

    var norm = function (t) { return (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
    var esc = function (t) { return String(t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };

    function pintar(productos, cargando) {
      var q = norm(input.value.trim());
      var vistas = pantallas.filter(function (p) { return !q || norm(p.titulo).indexOf(q) >= 0; });
      opciones = [];
      var html = "";
      if (vistas.length) {
        html += '<li class="grp">Pantallas</li>';
        vistas.forEach(function (p) {
          opciones.push(p.url);
          html += '<li><a class="opt" role="option" href="' + esc(p.url) + '"><span class="ico">' + p.ico + "</span><span><b>" + esc(p.titulo) + "</b><span>Pantalla</span></span><em></em></a></li>";
        });
      }
      if (productos && productos.length) {
        html += '<li class="grp">Productos</li>';
        productos.forEach(function (p) {
          opciones.push(p.url);
          html += '<li><a class="opt" role="option" href="' + esc(p.url) + '"><span class="ico">' + icoProducto + '</span><span><b>' + esc(p.nombre) + "</b><span>" + esc(p.codigo) + "</span></span><em>" + esc(p.existencia) + "</em></a></li>";
        });
      }
      if (!opciones.length) html = '<li class="none">' + (cargando ? "Buscando…" : "Sin resultados para esa búsqueda.") + "</li>";
      lista.innerHTML = html;
      sel = Math.min(sel, Math.max(opciones.length - 1, 0));
      marcar();
    }
    function marcar() {
      lista.querySelectorAll(".opt").forEach(function (o, n) {
        o.setAttribute("aria-selected", String(n === sel));
        if (n === sel) o.scrollIntoView({ block: "nearest" });
      });
    }
    function buscarProductos() {
      var q = input.value.trim();
      if (q.length < 2) { pintar([]); return; }
      var este = ++pedido;
      pintar([], true);
      fetch(urlBuscar + "?q=" + encodeURIComponent(q), { headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (datos) { if (este === pedido) pintar(datos); })
        .catch(function () { if (este === pedido) pintar([]); });
    }
    function abrir() { palette.hidden = false; input.value = ""; sel = 0; pintar([]); input.focus(); }
    function cerrar() { palette.hidden = true; trigger.focus(); }

    trigger.addEventListener("click", abrir);
    palette.addEventListener("click", function (e) { if (e.target === palette) cerrar(); });
    input.addEventListener("input", function () { sel = 0; clearTimeout(temporizador); temporizador = setTimeout(buscarProductos, 180); pintar([]); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, opciones.length - 1); marcar(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); marcar(); }
      else if (e.key === "Enter" && opciones[sel]) { e.preventDefault(); window.location.href = opciones[sel]; }
      else if (e.key === "Escape") { cerrar(); }
    });
    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette.hidden ? abrir() : cerrar(); }
      else if (e.key === "Escape") { cerrarUserMenu(); menuLateral(false); }
    });
  }

  // ---------- Ficha emergente del calendario ----------
  var tip = document.getElementById("tip");
  if (tip) {
    var mostrar = function (el) {
      tip.innerHTML = "<b></b><span></span>";
      tip.querySelector("b").textContent = el.dataset.tipTitulo;
      tip.querySelector("span").textContent = el.dataset.tipTexto;
      var r = el.getBoundingClientRect();
      tip.classList.add("on");
      var x = Math.min(Math.max(8, r.left + r.width / 2 - tip.offsetWidth / 2), window.innerWidth - tip.offsetWidth - 8);
      var y = r.top - tip.offsetHeight - 10;
      tip.style.left = x + "px";
      tip.style.top = (y < 8 ? r.bottom + 10 : y) + "px";
    };
    var ocultar = function () { tip.classList.remove("on"); };
    document.addEventListener("pointerover", function (e) { var d = e.target.closest("[data-tip-titulo]"); d ? mostrar(d) : ocultar(); });
    document.addEventListener("focusin", function (e) { var d = e.target.closest("[data-tip-titulo]"); d ? mostrar(d) : ocultar(); });
    document.addEventListener("scroll", ocultar, true);
  }
})();
