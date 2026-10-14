/* Maquettes ProjetTest — graphiques SVG sans dépendance.
   Règles : traits fins, barres ≤ 24 px à bout arrondi, lignes 2 px, grille en filet,
   légende dès 2 séries, infobulle au survol, vue tableau sur chaque carte. */
(function () {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  function s(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v != null) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  }
  const echap = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---------- Infobulle ----------
  function montrer(e, titre, lignes) {
    const b = document.getElementById('infobulle');
    b.innerHTML = `<div class="t">${echap(titre)}</div>` + lignes.map(l =>
      `<div class="l"><span>${l.couleur ? `<i class="cle${l.trait ? ' ligne' : ''}" style="background:${l.couleur}"></i>` : ''}${echap(l.nom)}</span><b>${echap(l.valeur)}</b></div>`).join('');
    b.hidden = false;
    const r = b.getBoundingClientRect();
    let x = e.clientX + 14, y = e.clientY + 14;
    if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 14;
    if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - 14;
    b.style.left = Math.max(8, x) + 'px';
    b.style.top = Math.max(8, y) + 'px';
  }
  function cacher() { document.getElementById('infobulle').hidden = true; }

  // ---------- Échelles ----------
  function pasRond(brut) {
    const p = Math.pow(10, Math.floor(Math.log10(brut)));
    const r = brut / p;
    return (r <= 1 ? 1 : r <= 2 ? 2 : r <= 2.5 ? 2.5 : r <= 5 ? 5 : 10) * p;
  }
  function graduations(min, max, n = 4) {
    if (min === max) { max = min + 1; }
    const pas = pasRond((max - min) / n);
    const debut = Math.floor(min / pas) * pas, fin = Math.ceil(max / pas) * pas;
    const t = [];
    for (let v = debut; v <= fin + pas / 2; v += pas) t.push(Math.round(v * 1e6) / 1e6);
    return t;
  }
  const largeurTexte = (t, px = 6.6) => String(t).length * px;

  function legende(conteneur, series) {
    if (series.length < 2) return;
    const l = document.createElement('div');
    l.className = 'legende';
    l.innerHTML = series.map(x => `<span><i class="cle${x.trait ? ' ligne' : ''}" style="background:${x.couleur}"></i>${echap(x.nom)}</span>`).join('');
    conteneur.appendChild(l);
  }

  // Barre à bout arrondi côté valeur, carrée côté ligne de base.
  function barreV(x, w, y0, y1) {
    const h = Math.abs(y1 - y0), r = Math.min(4, h, w / 2), d = y1 <= y0 ? 1 : -1;
    return `M${x},${y0}V${y1 + d * r}Q${x},${y1} ${x + r},${y1}H${x + w - r}Q${x + w},${y1} ${x + w},${y1 + d * r}V${y0}Z`;
  }
  function barreH(y, h, x0, x1) {
    const w = Math.abs(x1 - x0), r = Math.min(4, w, h / 2), d = x1 >= x0 ? 1 : -1;
    return `M${x0},${y}H${x1 - d * r}Q${x1},${y} ${x1},${y + r}V${y + h - r}Q${x1},${y + h} ${x1 - d * r},${y + h}H${x0}Z`;
  }
  const couleurSigne = v => (v >= 0 ? 'var(--bon)' : 'var(--mauvais)');

  // ---------- Série temporelle : colonnes et/ou lignes sur UN seul axe ----------
  function temporel(el, o) {
    const series = [...(o.barres ? [{ ...o.barres, type: 'barre' }] : []),
                    ...(o.lignes || []).map(l => ({ ...l, type: 'ligne', trait: true }))];
    legende(el, series.filter(x => !x.sansLegende));
    const W = Math.max(280, el.clientWidth), H = o.hauteur || 250, n = o.labels.length;
    const valeurs = series.flatMap(x => x.valeurs).filter(v => v != null);
    const t = graduations(Math.min(0, ...valeurs), Math.max(0, ...valeurs));
    const lo = t[0], hi = t[t.length - 1];
    const ml = Math.max(...t.map(v => largeurTexte(o.formatAxe(v)))) + 12, mr = 14, mt = 8, mb = 26;
    const iw = W - ml - mr, ih = H - mt - mb, bw = iw / n;
    const x = i => ml + bw * (i + 0.5), y = v => mt + ih * (1 - (v - lo) / (hi - lo));
    const svg = s('svg', { class: 'graph', viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': o.titre || '' }, el);

    for (const v of t) {
      s('line', { class: v === 0 ? 'axe-l' : 'grille-l', x1: ml, x2: W - mr, y1: y(v), y2: y(v) }, svg);
      s('text', { x: ml - 8, y: y(v) + 4, 'text-anchor': 'end' }, svg).textContent = o.formatAxe(v);
    }
    const pas = Math.ceil(n / Math.max(1, Math.floor(iw / 54)));
    o.labels.forEach((l, i) => {
      if (i % pas === 0) s('text', { x: x(i), y: H - 8, 'text-anchor': 'middle' }, svg).textContent = l;
    });

    const bandes = s('g', {}, svg);
    const curseur = s('line', { class: 'curseur', y1: mt, y2: mt + ih, visibility: 'hidden' }, svg);
    for (const se of series.filter(x => x.type === 'barre')) {
      const w = Math.min(24, bw * 0.62);
      se.valeurs.forEach((v, i) => {
        if (v == null || v === 0) return;
        s('path', { d: barreV(x(i) - w / 2, w, y(0), y(v)), style: `fill:${se.couleurSigne ? couleurSigne(v) : se.couleur}` }, svg);
      });
    }
    for (const se of series.filter(x => x.type === 'ligne')) {
      let d = '', dernier = null;
      se.valeurs.forEach((v, i) => {
        if (v == null) { dernier = null; return; }
        d += (dernier == null ? 'M' : 'L') + x(i) + ',' + y(v);
        dernier = i;
      });
      s('path', { d, fill: 'none', style: `stroke:${se.couleur}`, 'stroke-width': se.epaisseur || 2,
                  'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
      const fin = se.valeurs.map((v, i) => (v == null ? -1 : i)).filter(i => i >= 0).pop();
      if (fin != null && fin >= 0) {
        s('circle', { cx: x(fin), cy: y(se.valeurs[fin]), r: 4, style: `fill:${se.couleur};stroke:var(--surface)`, 'stroke-width': 2 }, svg);
      }
    }
    o.labels.forEach((l, i) => {
      const r = s('rect', { class: 'bande', x: ml + bw * i, y: mt, width: bw, height: ih }, bandes);
      const survol = e => {
        curseur.setAttribute('x1', x(i)); curseur.setAttribute('x2', x(i)); curseur.setAttribute('visibility', 'visible');
        montrer(e, o.titresInfobulle ? o.titresInfobulle[i] : l, series.map(se => ({
          nom: se.nom, couleur: se.couleurSigne ? couleurSigne(se.valeurs[i] || 0) : se.couleur, trait: se.trait,
          valeur: se.valeurs[i] == null ? '—' : (se.format || o.format)(se.valeurs[i]) })));
      };
      r.addEventListener('mousemove', survol);
      r.addEventListener('mouseleave', () => { cacher(); curseur.setAttribute('visibility', 'hidden'); });
    });
  }

  // ---------- Barres horizontales (1 ou 2 séries, valeurs signées possibles) ----------
  function barresH(el, o) {
    const series = o.series;
    legende(el, series);
    const W = Math.max(280, el.clientWidth);
    const nbS = series.length, hb = nbS > 1 ? 11 : 14, hl = nbS > 1 ? 2 * hb + 2 + 12 : hb + 12;
    const H = o.items.length * hl + 6;
    const valeurs = o.items.flatMap(it => it.valeurs).filter(v => v != null);
    const lo = Math.min(0, ...valeurs), hi = Math.max(0, ...valeurs);
    const etiq = o.etiquette || o.format;
    const ml = Math.min(W * 0.4, Math.max(...o.items.map(it => largeurTexte(it.label))) + 14);
    const reserve = Math.max(...o.items.map(it => largeurTexte(it.etiquette ?? etiq(it.valeurs[0] ?? 0)))) + 10;
    const gauche = ml + (lo < 0 ? reserve : 0), droite = W - (hi > 0 ? reserve : 6);
    const x = v => gauche + (droite - gauche) * ((v - lo) / ((hi - lo) || 1));
    const svg = s('svg', { class: 'graph', viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': o.titre || '' }, el);
    s('line', { class: 'axe-l', x1: x(0), x2: x(0), y1: 0, y2: H - 4 }, svg);

    o.items.forEach((it, i) => {
      const y0 = i * hl + 6;
      const fond = s('rect', { class: 'bande', x: 0, y: y0 - 6, width: W, height: hl }, svg);
      let lib = String(it.label);
      const maxCar = Math.floor((ml - 8) / 6.6);
      if (lib.length > maxCar) lib = lib.slice(0, maxCar - 1) + '…';
      const tl = s('text', { x: ml - 10, y: y0 + (nbS > 1 ? hb + 5 : hb - 3), 'text-anchor': 'end' }, svg);
      tl.textContent = lib;
      tl.style.fill = 'var(--encre-2)';
      series.forEach((se, j) => {
        const v = it.valeurs[j];
        if (v == null) return;
        const yb = y0 + j * (hb + 2);
        if (v !== 0) s('path', { d: barreH(yb, hb, x(0), x(v)), style: `fill:${se.couleurSigne ? couleurSigne(v) : se.couleur}` }, svg);
        if (j === 0) {
          const tv = s('text', { class: 'val', x: v >= 0 ? x(v) + 6 : x(v) - 6, y: yb + hb - 3, 'text-anchor': v >= 0 ? 'start' : 'end' }, svg);
          tv.textContent = it.etiquette ?? etiq(v);
        }
      });
      const survol = e => montrer(e, it.label, [
        ...series.map((se, j) => ({ nom: se.nom, couleur: se.couleurSigne ? couleurSigne(it.valeurs[j] || 0) : se.couleur,
                                    valeur: it.valeurs[j] == null ? '—' : o.format(it.valeurs[j]) })),
        ...(it.details || [])]);
      fond.addEventListener('mousemove', survol);
      fond.addEventListener('mouseleave', cacher);
    });
  }

  // ---------- Anneau (≤ 6 parts) ----------
  function anneau(el, o) {
    const total = o.items.reduce((a, it) => a + it.valeur, 0);
    const conteneur = document.createElement('div');
    conteneur.style.cssText = 'display:flex;flex-wrap:wrap;align-items:center;gap:16px 24px';
    el.appendChild(conteneur);
    const T = 190, R = T / 2, r = R * 0.62, c = T / 2;
    const svg = s('svg', { class: 'graph', viewBox: `0 0 ${T} ${T}`, width: T, height: T, role: 'img', 'aria-label': o.titre || '' }, conteneur);
    svg.style.width = T + 'px'; svg.style.flex = 'none';
    let a0 = -Math.PI / 2;
    for (const it of o.items) {
      const a1 = a0 + (it.valeur / total) * Math.PI * 2;
      const p = (a, rr) => `${c + rr * Math.cos(a)},${c + rr * Math.sin(a)}`;
      const grand = a1 - a0 > Math.PI ? 1 : 0;
      const arc = s('path', {
        d: `M${p(a0, R)}A${R},${R} 0 ${grand} 1 ${p(a1, R)}L${p(a1, r)}A${r},${r} 0 ${grand} 0 ${p(a0, r)}Z`,
        style: `fill:${it.couleur};stroke:var(--surface)`, 'stroke-width': 2 }, svg);
      arc.addEventListener('mousemove', e => montrer(e, it.label, [
        { nom: 'Valeur', valeur: o.format(it.valeur) }, { nom: 'Part', valeur: o.pct(it.valeur / total) }]));
      arc.addEventListener('mouseleave', cacher);
      a0 = a1;
    }
    const t1 = s('text', { x: c, y: c - 2, 'text-anchor': 'middle' }, svg);
    t1.textContent = o.formatTotal(total); t1.style.cssText = 'font-size:17px;font-weight:650;fill:var(--encre)';
    const t2 = s('text', { x: c, y: c + 16, 'text-anchor': 'middle' }, svg);
    t2.textContent = o.libTotal || 'Total';
    const l = document.createElement('div');
    l.style.cssText = 'display:grid;gap:8px;flex:1;min-width:170px';
    l.innerHTML = o.items.map(it => `<div style="display:flex;align-items:center;gap:8px">
      <i class="cle" style="background:${it.couleur}"></i><span style="color:var(--encre-2)">${echap(it.label)}</span>
      <span style="margin-left:auto;font-weight:600">${echap(o.pct(it.valeur / total))}</span>
      <span style="color:var(--encre-3);min-width:76px;text-align:right">${echap(o.formatTotal(it.valeur))}</span></div>`).join('');
    conteneur.appendChild(l);
  }

  // ---------- Nuage de points (≤ 3 couleurs) ----------
  function nuage(el, o) {
    legende(el, o.legende);
    const W = Math.max(280, el.clientWidth), H = o.hauteur || 280;
    const tx = graduations(0, Math.max(...o.points.map(p => p.x)));
    const ty = graduations(0, Math.max(...o.points.map(p => p.y)));
    const ml = Math.max(...ty.map(v => largeurTexte(o.fy(v)))) + 14, mr = 16, mt = 10, mb = 40;
    const iw = W - ml - mr, ih = H - mt - mb;
    const x = v => ml + iw * (v / tx[tx.length - 1]), y = v => mt + ih * (1 - v / ty[ty.length - 1]);
    const tMax = Math.max(...o.points.map(p => p.t));
    const rayon = p => 4 + 9 * Math.sqrt(p.t / tMax);
    const svg = s('svg', { class: 'graph', viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': o.titre || '' }, el);
    for (const v of ty) {
      s('line', { class: v === 0 ? 'axe-l' : 'grille-l', x1: ml, x2: W - mr, y1: y(v), y2: y(v) }, svg);
      s('text', { x: ml - 8, y: y(v) + 4, 'text-anchor': 'end' }, svg).textContent = o.fy(v);
    }
    for (const v of tx) s('text', { x: x(v), y: mt + ih + 16, 'text-anchor': 'middle' }, svg).textContent = o.fx(v);
    s('text', { x: ml + iw / 2, y: H - 4, 'text-anchor': 'middle' }, svg).textContent = o.titreX;
    const ty0 = s('text', { x: ml, y: mt - 0, 'text-anchor': 'start' }, svg);
    ty0.textContent = ''; // le titre de l'axe Y est porté par le sous-titre de la carte
    const pts = [...o.points].sort((a, b) => b.t - a.t);
    const cercles = pts.map(p => s('circle', { cx: x(p.x), cy: y(p.y), r: rayon(p),
      style: `fill:${p.couleur};fill-opacity:.78;stroke:var(--surface)`, 'stroke-width': 2 }, svg));
    const zone = s('rect', { x: ml, y: mt, width: iw, height: ih, fill: 'transparent' }, svg);
    let actif = null;
    zone.addEventListener('mousemove', e => {
      const b = svg.getBoundingClientRect(), k = W / b.width;
      const mx = (e.clientX - b.left) * k, my = (e.clientY - b.top) * k;
      let meilleur = null, dmin = 24 * k;
      pts.forEach((p, i) => {
        const d = Math.hypot(x(p.x) - mx, y(p.y) - my) - rayon(p);
        if (d < dmin) { dmin = d; meilleur = i; }
      });
      if (actif != null) cercles[actif].style.fillOpacity = '.78';
      actif = meilleur;
      if (meilleur == null) { cacher(); return; }
      cercles[meilleur].style.fillOpacity = '1';
      montrer(e, pts[meilleur].label, pts[meilleur].lignes);
    });
    zone.addEventListener('mouseleave', () => { cacher(); if (actif != null) cercles[actif].style.fillOpacity = '.78'; });
  }

  // ---------- Tableau triable ----------
  function tableau(el, o) {
    let tri = { ...(o.tri || {}) };
    const boite = document.createElement('div');
    boite.className = 'tab-conteneur';
    if (o.hauteurMax) boite.style.maxHeight = o.hauteurMax + 'px';
    el.appendChild(boite);
    const dessiner = () => {
      const lignes = [...o.lignes];
      if (tri.cle) {
        lignes.sort((a, b) => {
          const va = a[tri.cle], vb = b[tri.cle];
          if (va == null) return 1; if (vb == null) return -1;
          const r = typeof va === 'string' ? va.localeCompare(vb, 'fr') : va - vb;
          return tri.desc ? -r : r;
        });
      }
      const th = o.colonnes.map(c => `<th class="${c.d ? 'd' : ''}" data-cle="${c.cle}" scope="col"
        ${tri.cle === c.cle ? `aria-sort="${tri.desc ? 'descending' : 'ascending'}"` : ''}>${echap(c.titre)}</th>`).join('');
      const tr = lignes.slice(0, o.limite || lignes.length).map(l => `<tr class="${l._classe || ''}">` + o.colonnes.map(c => {
        const v = l[c.cle];
        const contenu = c.html ? c.html(l) : echap(c.f ? c.f(v) : v ?? '—');
        const cls = [c.d ? 'd' : '', c.cls ? c.cls(v, l) : ''].join(' ');
        return `<td class="${cls}">${contenu}</td>`;
      }).join('') + '</tr>').join('');
      boite.innerHTML = `<table class="tab"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
      if (o.triable !== false) {
        boite.querySelectorAll('th').forEach(h => h.addEventListener('click', () => {
          const cle = h.dataset.cle;
          tri = { cle, desc: tri.cle === cle ? !tri.desc : true };
          dessiner();
        }));
      }
    };
    dessiner();
  }

  // ---------- Matrice en carte de chaleur (une teinte, clair → foncé) ----------
  function matrice(el, o) {
    const max = Math.max(...o.lignes.filter(l => l.niveau === 1).flatMap(l => l.valeurs));
    const boite = document.createElement('div');
    boite.className = 'tab-conteneur';
    boite.style.maxHeight = 'none';
    el.appendChild(boite);
    const th = `<th scope="col">${echap(o.titreLignes)}</th>` + o.colonnes.map(c => `<th class="d" scope="col">${echap(c)}</th>`).join('') +
      `<th class="d" scope="col">Total</th>`;
    const tr = o.lignes.map(l => {
      const cellules = l.valeurs.map((v, i) => {
        if (l.niveau === 0) return `<td class="d">${echap(o.format(v))}</td>`;
        const p = max ? Math.round((v / max) * 85) : 0;
        const encre = p > 50 ? '#fff' : 'var(--encre)';
        return `<td class="chaleur" title="${echap(l.label + ' · ' + o.colonnes[i] + ' : ' + o.formatInfobulle(v))}"
          style="background:color-mix(in srgb, var(--s1) ${p}%, var(--surface));color:${encre}">${echap(o.format(v))}</td>`;
      }).join('');
      const total = l.valeurs.reduce((a, b) => a + b, 0);
      return `<tr class="niv${l.niveau}"><td>${l.niveau ? '&nbsp;&nbsp;&nbsp;' : ''}${echap(l.label)}</td>${cellules}<td class="d"><b>${echap(o.format(total))}</b></td></tr>`;
    }).join('');
    boite.innerHTML = `<table class="tab"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
    const note = document.createElement('div');
    note.className = 'legende';
    note.style.marginTop = '8px';
    note.innerHTML = `<span>Échelle : <i class="cle" style="background:color-mix(in srgb, var(--s1) 8%, var(--surface));border:1px solid var(--bord)"></i> faible
      <i class="cle" style="background:color-mix(in srgb, var(--s1) 85%, var(--surface))"></i> élevé (par produit et par mois)</span>`;
    el.appendChild(note);
  }

  window.Graph = { temporel, barresH, anneau, nuage, tableau, matrice };
})();
