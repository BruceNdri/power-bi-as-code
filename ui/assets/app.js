/* Maquettes ProjetTest — données, filtres et calcul des KPI (miroir des mesures DAX). */
(function () {
  'use strict';

  const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  const PAGES = [
    { cle: 'overview', titre: 'Overview', fichier: 'overview.html', icone: '◧' },
    { cle: 'clients', titre: 'Clients', fichier: 'clients.html', icone: '◉' },
    { cle: 'ventes', titre: 'Ventes', fichier: 'ventes.html', icone: '▤' },
  ];
  // La couleur suit l'entité, jamais son rang : un filtre ne repeint pas les survivants.
  const COULEURS = {
    categorie: { 'Informatique': 'var(--s1)', 'Mobilier': 'var(--s2)', 'Fournitures': 'var(--s3)', 'Téléphonie': 'var(--s4)' },
    segment: { 'Grand compte': 'var(--s1)', 'PME': 'var(--s2)', 'Particulier': 'var(--s3)' },
  };

  // ---------- Données ----------
  const D = window.DONNEES;
  const produits = D.produits.map(([id, nom, categorie, prix]) => ({ id, nom, categorie, prix }));
  const clients = D.clients.map(([id, nom, ville, region, segment]) => ({ id, nom, ville, region, segment }));
  const produitParId = new Map(produits.map(p => [p.id, p]));
  const clientParId = new Map(clients.map(c => [c.id, c]));
  const ventes = D.ventes.map(([id, date, idc, idp, q, pu, m]) => {
    const a = +date.slice(0, 4), mo = +date.slice(5, 7), p = produitParId.get(idp);
    return { id, date, t: Date.parse(date), a, mo, k: a * 12 + mo - 1, idc, idp, q, pu, m,
             catalogue: q * p.prix, p, c: clientParId.get(idc) };
  });
  const ANNEES = [...new Set(ventes.map(v => v.a))].sort();
  const K_MIN = Math.min(...ventes.map(v => v.k));
  const uniques = l => [...new Set(l)].sort((x, y) => String(x).localeCompare(String(y), 'fr'));

  // ---------- Filtres ----------
  const DIMS = [
    { cle: 'categorie', lib: 'Catégorie', val: v => v.p.categorie,
      options: () => uniques(produits.map(p => p.categorie)).map(x => ({ v: x, l: x })) },
    { cle: 'produit', lib: 'Produit', val: v => v.idp,
      options: f => produits.filter(p => !f.categorie.length || f.categorie.includes(p.categorie))
        .sort((x, y) => x.nom.localeCompare(y.nom, 'fr')).map(p => ({ v: p.id, l: p.nom, d: p.categorie })) },
    { cle: 'segment', lib: 'Segment', val: v => v.c.segment, client: c => c.segment,
      options: () => uniques(clients.map(c => c.segment)).map(x => ({ v: x, l: x })) },
    { cle: 'region', lib: 'Région', val: v => v.c.region, client: c => c.region,
      options: () => uniques(clients.map(c => c.region)).map(x => ({ v: x, l: x })) },
    { cle: 'ville', lib: 'Ville', val: v => v.c.ville, client: c => c.ville,
      options: f => uniques(clients.filter(c => !f.region.length || f.region.includes(c.region)).map(c => c.ville))
        .map(x => ({ v: x, l: x })) },
    { cle: 'client', lib: 'Client', val: v => v.idc, client: c => c.id,
      options: f => clients.filter(c => (!f.segment.length || f.segment.includes(c.segment)) &&
                                         (!f.region.length || f.region.includes(c.region)) &&
                                         (!f.ville.length || f.ville.includes(c.ville)))
        .sort((x, y) => x.nom.localeCompare(y.nom, 'fr')).map(c => ({ v: c.id, l: c.nom, d: c.ville })) },
  ];
  const FILTRE_MOIS = { cle: 'mois', lib: 'Mois', options: () => MOIS.map((l, i) => ({ v: i + 1, l })) };

  const defaut = () => ({ annees: [ANNEES[ANNEES.length - 1]], mois: [],
                          ...Object.fromEntries(DIMS.map(d => [d.cle, []])) });
  const STOCKAGE = 'projettest.filtres';
  let etat = defaut();
  try {
    const lu = JSON.parse(localStorage.getItem(STOCKAGE) || 'null');
    if (lu) etat = Object.assign(defaut(), lu);
  } catch (e) { /* stockage indisponible : filtres par défaut */ }
  const sauver = () => { try { localStorage.setItem(STOCKAGE, JSON.stringify(etat)); } catch (e) { /* ignoré */ } };

  // ---------- Calculs ----------
  const somme = (l, f) => l.reduce((s, x) => s + f(x), 0);
  const div = (a, b) => (b ? a / b : null);
  const evol = (a, b) => (b ? (a - b) / b : null);
  const ensemble = (l, f) => new Set(l.map(f));

  const M = {
    ca: l => somme(l, v => v.m),
    qte: l => somme(l, v => v.q),
    nb: l => l.length,
    panier: l => div(M.ca(l), l.length),
    prixMoyen: l => div(M.ca(l), M.qte(l)),
    produits: l => ensemble(l, v => v.idp).size,
    catalogue: l => somme(l, v => v.catalogue),
    remises: l => M.catalogue(l) - M.ca(l),
    tauxRemise: l => div(M.remises(l), M.catalogue(l)),
    clients: l => ensemble(l, v => v.idc).size,
    caParClient: l => div(M.ca(l), M.clients(l)),
    frequence: l => div(l.length, M.clients(l)),
  };

  function grouper(l, cle) {
    const g = new Map();
    for (const v of l) { const k = cle(v); if (!g.has(k)) g.set(k, []); g.get(k).push(v); }
    return g;
  }

  function contexte() {
    const f = etat;
    const okDim = v => DIMS.every(d => !f[d.cle].length || f[d.cle].includes(d.val(v)));
    const base = ventes.filter(okDim);                       // toutes périodes, autres filtres appliqués
    const annees = f.annees.length ? [...f.annees].sort() : ANNEES;
    const mois = f.mois.length ? [...f.mois].sort((a, b) => a - b) : MOIS.map((_, i) => i + 1);
    const cles = annees.flatMap(a => mois.map(m => a * 12 + m - 1)).sort((a, b) => a - b);
    const cN = new Set(cles), cN1 = new Set(cles.map(k => k - 12));
    const sel = base.filter(v => cN.has(v.k));
    const prec = base.filter(v => cN1.has(v.k));
    const kMax = cles[cles.length - 1], kDebutAnnee = Math.floor(kMax / 12) * 12;
    const ytd = base.filter(v => v.k >= kDebutAnnee && v.k <= kMax);
    const ytdN1 = base.filter(v => v.k >= kDebutAnnee - 12 && v.k <= kMax - 12);
    const n1 = cles.some(k => k - 12 >= K_MIN);              // des données N-1 existent pour la période
    const debut = Date.UTC(Math.floor(cles[0] / 12), cles[0] % 12, 1);
    const fin = Date.UTC(Math.floor(kMax / 12), kMax % 12 + 1, 0);

    const ctx = { f, base, sel, prec, cles, kMax, kMin: K_MIN, ytd, ytdN1, n1, debut, fin, M, evol, div, grouper,
                  MOIS, COULEURS, produits, clients, produitParId, clientParId };

    ctx.parMois = (l, mesure = M.ca) => {
      const g = grouper(l, v => v.k);
      return k => (g.has(k) ? mesure(g.get(k)) : 0);
    };
    ctx.libMois = k => MOIS[k % 12] + ' ' + String(Math.floor(k / 12)).slice(2);

    // Clients au portefeuille : filtres « client » uniquement (segment, région, ville, client).
    ctx.portefeuille = clients.filter(c => DIMS.every(d => !d.client || !f[d.cle].length || f[d.cle].includes(d.client(c)))).length;

    // Nouveaux clients : premier achat (toutes périodes) dans la période.
    const premier = new Map();
    for (const v of base) if (!premier.has(v.idc) || v.t < premier.get(v.idc)) premier.set(v.idc, v.t);
    ctx.premierAchat = premier;
    ctx.nouveaux = l => [...ensemble(l, v => v.idc)].filter(id => premier.get(id) >= debut).length;

    const actifsN = ensemble(sel, v => v.idc), actifsN1 = ensemble(prec, v => v.idc);
    ctx.retention = n1 && actifsN1.size ? [...actifsN1].filter(id => actifsN.has(id)).length / actifsN1.size : null;
    ctx.perdus = n1 ? [...actifsN1].filter(id => !actifsN.has(id)).length : null;
    return ctx;
  }

  // ---------- Formats ----------
  const nf = (min, max) => new Intl.NumberFormat('fr-FR', { minimumFractionDigits: min, maximumFractionDigits: max });
  const F0 = nf(0, 0), F1 = nf(1, 1), F2 = nf(2, 2);
  const fmt = {
    eur: v => (v == null ? '—' : F2.format(v) + ' €'),
    eur0: v => (v == null ? '—' : F0.format(v) + ' €'),
    eurC: v => {
      if (v == null) return '—';
      const a = Math.abs(v);
      if (a >= 1e6) return F2.format(v / 1e6) + ' M€';
      if (a >= 1e3) return F1.format(v / 1e3) + ' k€';
      return F0.format(v) + ' €';
    },
    eurAxe: v => {
      const a = Math.abs(v);
      if (a >= 1e6) return nf(0, 1).format(v / 1e6) + ' M';
      if (a >= 1e3) return nf(0, 1).format(v / 1e3) + ' k';
      return F0.format(v);
    },
    nb: v => (v == null ? '—' : F0.format(v)),
    nb1: v => (v == null ? '—' : F1.format(v)),
    pct: v => (v == null ? '—' : F1.format(v * 100) + ' %'),
    evol: v => (v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + F1.format(Math.abs(v) * 100) + ' %'),
    evolEur: v => (v == null ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + F0.format(Math.abs(v)) + ' €'),
    date: t => (t == null ? '—' : new Date(t).toLocaleDateString('fr-FR', { timeZone: 'UTC' })),
  };

  // ---------- Petits utilitaires DOM ----------
  function el(tag, attrs, ...enfants) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') n.className = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else if (k === 'html') n.innerHTML = v;
      else n.setAttribute(k, v === true ? '' : v);
    }
    for (const e of enfants.flat()) if (e != null) n.append(e.nodeType ? e : document.createTextNode(e));
    return n;
  }
  const echap = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // Évolution : flèche + signe + couleur (jamais la couleur seule).
  function badgeEvol(v, { inverse = false, suffixe = 'vs N-1' } = {}) {
    if (v == null) return `<span>— ${suffixe}</span>`;
    const bon = inverse ? v < 0 : v > 0;
    const cls = v === 0 ? '' : bon ? 'haut' : 'bas';
    const fl = v > 0 ? '▲' : v < 0 ? '▼' : '■';
    return `<span class="${cls}">${fl} ${fmt.evol(v)}</span> ${suffixe}`;
  }

  // ---------- Coquille de page ----------
  let page, zoneKpis, zoneGrille, zonePeriode, barre;

  function libPeriode() {
    const a = etat.annees.length ? [...etat.annees].sort().join(', ') : 'Toutes les années';
    const m = etat.mois.length ? [...etat.mois].sort((x, y) => x - y).map(i => MOIS[i - 1]).join(', ') : 'tous les mois';
    const autres = DIMS.filter(d => etat[d.cle].length).map(d => d.lib.toLowerCase());
    return `${a} · ${m}` + (autres.length ? ` · filtré par ${autres.join(', ')}` : '');
  }

  function construireFiltres() {
    barre = el('div', { class: 'filtres', role: 'search', 'aria-label': 'Filtres du rapport' });
    const annees = el('div', { class: 'groupe-annees', role: 'group', 'aria-label': 'Année' });
    const btnToutes = el('button', { type: 'button', onclick: () => { etat.annees = []; maj(); } }, 'Toutes');
    annees.append(btnToutes);
    for (const a of ANNEES) {
      // Clic : cette année seule. Ctrl/Cmd + clic : ajoute ou retire l'année (comme un segment Power BI).
      annees.append(el('button', { type: 'button', 'data-annee': a, title: 'Ctrl + clic pour sélectionner plusieurs années', onclick: e => {
        if (e.ctrlKey || e.metaKey) etat.annees = etat.annees.includes(a) ? etat.annees.filter(x => x !== a) : [...etat.annees, a];
        else etat.annees = [a];
        maj();
      } }, String(a)));
    }
    barre.append(annees);
    for (const d of [FILTRE_MOIS, ...DIMS]) barre.append(menuFiltre(d));
    barre.append(el('button', { type: 'button', class: 'reinit', onclick: () => { etat = defaut(); maj(); } }, '↺ Réinitialiser'));
    return barre;
  }

  function majFiltres() {
    barre.querySelector('.groupe-annees button:first-child').setAttribute('aria-pressed', String(!etat.annees.length));
    barre.querySelectorAll('[data-annee]').forEach(b => b.setAttribute('aria-pressed', String(etat.annees.includes(+b.dataset.annee))));
    barre.querySelectorAll('.filtre').forEach(f => f.majLibelle());
  }

  let panneauOuvert = null;
  function fermerPanneau() { if (panneauOuvert) { panneauOuvert.remove(); panneauOuvert = null; } }
  document.addEventListener('click', e => { if (panneauOuvert && !e.target.closest('.filtre')) fermerPanneau(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') fermerPanneau(); });

  function menuFiltre(d) {
    const bouton = el('button', { type: 'button', 'aria-haspopup': 'true' });
    const conteneur = el('div', { class: 'filtre' }, bouton);
    conteneur.majLibelle = () => {
      const s = etat[d.cle];
      let txt = 'Tous';
      if (s.length === 1) { const o = d.options(etat).find(x => x.v === s[0]); txt = o ? o.l : '1 sélection'; }
      else if (s.length > 1) txt = `${s.length} sélections`;
      bouton.innerHTML = `<span class="lib">${d.lib} :</span> ${echap(txt)}`;
      conteneur.classList.toggle('actif', s.length > 0);
    };
    bouton.addEventListener('click', () => {
      const dejaOuvert = panneauOuvert && panneauOuvert.parentNode === conteneur;
      fermerPanneau();
      if (dejaOuvert) return;
      const options = d.options(etat);
      const recherche = el('input', { type: 'search', placeholder: 'Rechercher…', 'aria-label': `Rechercher (${d.lib})` });
      const liste = el('div', { class: 'options' });
      const dessiner = () => {
        const q = recherche.value.trim().toLowerCase();
        liste.replaceChildren(...options.filter(o => !q || o.l.toLowerCase().includes(q)).map(o => {
          const cb = el('input', { type: 'checkbox' });
          cb.checked = etat[d.cle].includes(o.v);
          cb.addEventListener('change', () => {
            etat[d.cle] = cb.checked ? [...etat[d.cle], o.v] : etat[d.cle].filter(x => x !== o.v);
            nettoyer(); maj();
          });
          return el('label', {}, cb, o.l, o.d ? el('small', {}, o.d) : null);
        }));
      };
      recherche.addEventListener('input', dessiner);
      dessiner();
      panneauOuvert = el('div', { class: 'panneau', role: 'dialog', 'aria-label': d.lib },
        options.length > 8 ? recherche : null, liste,
        el('div', { class: 'actions' },
          el('button', { type: 'button', class: 'lien', onclick: () => { etat[d.cle] = []; nettoyer(); maj(); dessiner(); } }, 'Effacer'),
          el('button', { type: 'button', class: 'lien', onclick: fermerPanneau }, 'Fermer')));
      conteneur.append(panneauOuvert);
      if (options.length > 8) recherche.focus();
    });
    return conteneur;
  }

  // Retire les sélections devenues impossibles (ex. un produit hors de la catégorie choisie).
  function nettoyer() {
    for (const d of DIMS) {
      if (!etat[d.cle].length) continue;
      const possibles = new Set(d.options(etat).map(o => o.v));
      etat[d.cle] = etat[d.cle].filter(v => possibles.has(v));
    }
  }

  // ---------- Briques de page ----------
  function tuile({ lib, val, delta, sous }) {
    zoneKpis.append(el('div', { class: 'tuile' },
      el('div', { class: 'lib' }, lib),
      el('div', { class: 'val', title: val }, val),
      el('div', { class: 'delta', html: delta || (sous ? echap(sous) : '&nbsp;') })));
  }

  function carte({ titre, sous, span = 6, tableau }) {
    const corps = el('div', { class: 'corps' });
    const vue = el('div', { class: 'vue-tableau', hidden: true });
    const entete = el('header', {}, el('div', {}, el('h2', {}, titre), sous ? el('p', {}, sous) : null));
    if (tableau) {
      const b = el('button', { type: 'button', class: 'bascule', 'aria-pressed': 'false' }, 'Voir le tableau');
      b.addEventListener('click', () => {
        const t = vue.hidden;
        vue.hidden = !t; corps.hidden = t;
        b.textContent = t ? 'Voir le graphique' : 'Voir le tableau';
        b.setAttribute('aria-pressed', String(t));
        if (t && !vue.firstChild) window.Graph.tableau(vue, tableau());
      });
      entete.append(b);
    }
    zoneGrille.append(el('section', { class: `carte s${span}` }, entete, corps, vue));
    return corps;
  }

  // ---------- Rendu ----------
  function maj() {
    sauver();
    majFiltres();
    zonePeriode.textContent = libPeriode();
    zoneKpis.replaceChildren();
    zoneGrille.replaceChildren();
    const ctx = contexte();
    if (!ctx.sel.length) {
      zoneGrille.append(el('div', { class: 'carte s12 vide' }, 'Aucune vente pour cette sélection.'));
      return;
    }
    page.rendu(ctx, { tuile, carte, fmt, badgeEvol, el, echap });
    // Toutes les tuiles sur une ligne quand la largeur le permet (≥ 140 px chacune).
    const n = zoneKpis.children.length;
    zoneKpis.style.gridTemplateColumns = zoneKpis.clientWidth >= n * 140 ? `repeat(${n}, minmax(0, 1fr))` : '';
  }

  function demarrer(def) {
    page = def;
    document.title = `${def.titre} · ProjetTest`;
    const nav = el('nav', { class: 'nav', 'aria-label': 'Pages du rapport' },
      el('div', { class: 'marque' }, 'ProjetTest', el('small', {}, 'Maquette du rapport Power BI')),
      PAGES.map(p => el('a', { href: p.fichier, 'aria-current': p.cle === def.cle ? 'page' : null },
        el('span', { 'aria-hidden': 'true' }, p.icone), p.titre)),
      el('div', { class: 'pied' }, 'Données d’exemple · 2024–2025'));
    zonePeriode = el('p', { class: 'periode' });
    zoneKpis = el('section', { class: 'kpis', 'aria-label': 'Indicateurs clés' });
    zoneGrille = el('section', { class: 'grille' });
    const main = el('main', {},
      el('div', { class: 'entete' }, el('div', {}, el('h1', {}, def.titre), zonePeriode)),
      construireFiltres(), zoneKpis, zoneGrille);
    document.body.append(el('div', { class: 'app' }, nav, main), el('div', { id: 'infobulle', hidden: true }));
    maj();
    let minuteur;
    let largeur = window.innerWidth;
    window.addEventListener('resize', () => {
      if (window.innerWidth === largeur) return;
      largeur = window.innerWidth;
      clearTimeout(minuteur); minuteur = setTimeout(maj, 150);
    });
  }

  window.App = { demarrer, fmt };
})();
