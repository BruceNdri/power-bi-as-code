/* Page « ventes » : KPI et visuels, partagés par les maquettes v1 et v2. */
(window.PAGES_RAPPORT = window.PAGES_RAPPORT || {}).ventes = {
  cle: 'ventes',
  titre: 'Ventes',
  rendu(ctx, ui) {
    const { M, sel, prec, base, n1, evol, grouper, COULEURS, MOIS } = ctx;
    const { tuile, carte, fmt, badgeEvol, echap } = ui;
    const G = window.Graph;
    const ev = (a, b) => (n1 ? evol(a, b) : null);
    const evolCellule = v => badgeEvol(v, { suffixe: '' });
    const pastille = (couleur, txt) => `<i class="pastille" style="background:${couleur}"></i>${echap(txt)}`;
    const ca = M.ca(sel);

    // ---------- KPI ----------
    tuile({ lib: "Chiffre d'affaires", val: fmt.eurC(ca), delta: badgeEvol(ev(ca, M.ca(prec))) });
    tuile({ lib: 'Quantité vendue', val: fmt.nb(M.qte(sel)), delta: badgeEvol(ev(M.qte(sel), M.qte(prec))) });
    tuile({ lib: 'Nombre de ventes', val: fmt.nb(M.nb(sel)), delta: badgeEvol(ev(M.nb(sel), M.nb(prec))) });
    tuile({ lib: 'Prix moyen de vente', val: fmt.eur(M.prixMoyen(sel)), delta: badgeEvol(ev(M.prixMoyen(sel), M.prixMoyen(prec))) });
    tuile({ lib: 'Montant des remises', val: fmt.eurC(M.remises(sel)), sous: `taux de remise : ${fmt.pct(M.tauxRemise(sel))}` });
    tuile({ lib: 'Produits vendus', val: fmt.nb(M.produits(sel)), sous: `sur ${ctx.produits.length} au catalogue` });

    // ---------- CA par mois + moyenne mobile 3 mois (même unité, un seul axe) ----------
    const caBase = ctx.parMois(base);
    const labels = ctx.cles.map(ctx.libMois);
    const caMois = ctx.cles.map(ctx.parMois(sel));
    const mm3 = ctx.cles.map(k => (caBase(k) + caBase(k - 1) + caBase(k - 2)) / 3);
    G.temporel(carte({ titre: "Chiffre d'affaires par mois", sous: 'Avec la moyenne mobile sur 3 mois', span: 8,
      tableau: () => ({ colonnes: [{ titre: 'Mois', cle: 'm' }, { titre: 'CA', cle: 'v', f: fmt.eur, d: true },
                                   { titre: 'Moyenne mobile 3 mois', cle: 'mm', f: fmt.eur, d: true }],
                        lignes: labels.map((m, i) => ({ m, v: caMois[i], mm: mm3[i] })) }) }),
      { labels, format: fmt.eur0, formatAxe: fmt.eurAxe,
        barres: { nom: "Chiffre d'affaires", couleur: 'var(--primaire)', valeurs: caMois },
        lignes: [{ nom: 'Moyenne mobile 3 mois', couleur: 'var(--s2)', valeurs: mm3 }] });

    // ---------- Cumul annuel N vs N-1 ----------
    const annee = Math.floor(ctx.kMax / 12), moisFin = ctx.kMax % 12;
    const cumul = a => { let s = 0; return MOIS.slice(0, moisFin + 1).map((_, m) => (s += caBase(a * 12 + m))); };
    const cumN = cumul(annee);
    const cumN1 = annee * 12 - 12 >= ctx.kMin ? cumul(annee - 1) : null;
    G.temporel(carte({ titre: `CA cumulé ${annee}`, sous: cumN1 ? `Comparé à ${annee - 1}` : 'Pas de données N-1', span: 4,
      tableau: () => ({ colonnes: [{ titre: 'Mois', cle: 'm' }, { titre: String(annee), cle: 'n', f: fmt.eur, d: true },
                                   { titre: String(annee - 1), cle: 'n1', f: fmt.eur, d: true }],
                        lignes: cumN.map((v, i) => ({ m: MOIS[i], n: v, n1: cumN1 ? cumN1[i] : null })) }) }),
      { labels: MOIS.slice(0, moisFin + 1), format: fmt.eur0, formatAxe: fmt.eurAxe,
        lignes: [{ nom: String(annee), couleur: 'var(--primaire)', valeurs: cumN },
                 ...(cumN1 ? [{ nom: String(annee - 1), couleur: 'var(--n1)', valeurs: cumN1 }] : [])] });

    // ---------- Évolution vs N-1 par catégorie ----------
    const cN = grouper(sel, v => v.p.categorie), cN1 = grouper(prec, v => v.p.categorie);
    const cats = Object.keys(COULEURS.categorie).filter(c => cN.has(c));
    const corpsEvol = carte({ titre: 'Évolution du CA vs N-1 par catégorie', sous: 'Écart en euros et en pourcentage',
      tableau: n1 ? () => ({ colonnes: [{ titre: 'Catégorie', cle: 'c' }, { titre: 'CA', cle: 'v', f: fmt.eur, d: true },
                                        { titre: 'CA N-1', cle: 'v1', f: fmt.eur, d: true }, { titre: 'Écart', cle: 'd', f: fmt.evolEur, d: true },
                                        { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) }],
                             lignes: cats.map(c => { const v = M.ca(cN.get(c)), v1 = cN1.has(c) ? M.ca(cN1.get(c)) : 0;
                                                     return { c, v, v1, d: v - v1, e: evol(v, v1) }; }) }) : null });
    if (n1) {
      G.barresH(corpsEvol, {
        items: cats.map(c => {
          const v = M.ca(cN.get(c)), v1 = cN1.has(c) ? M.ca(cN1.get(c)) : 0, e = evol(v, v1);
          return { label: c, valeurs: [v - v1], etiquette: `${fmt.evolEur(v - v1)} (${fmt.evol(e)})`,
                   details: [{ nom: 'CA', valeur: fmt.eur0(v) }, { nom: 'CA N-1', valeur: fmt.eur0(v1) }, { nom: 'Évolution', valeur: fmt.evol(e) }] };
        }).sort((a, b) => b.valeurs[0] - a.valeurs[0]),
        series: [{ nom: 'Écart vs N-1', couleur: 'var(--primaire)', couleurSigne: true }], format: fmt.evolEur });
    } else {
      corpsEvol.append(ui.el('div', { class: 'vide' }, 'Pas de données N-1 pour cette période (les données commencent en 2024).'));
    }

    // ---------- Variation du CA : effets volume, prix et mix ----------
    // Volume : quantités N - N-1 au prix moyen N-1. Prix : écart de prix de chaque produit sur les quantités N.
    // Mix : déplacement des ventes vers des produits plus ou moins chers. Les trois effets somment à l'écart de CA.
    const parProduitQ = l => { const m = new Map(); for (const v of l) { const x = m.get(v.idp) || { q: 0, ca: 0 }; x.q += v.q; x.ca += v.m; m.set(v.idp, x); } return m; };
    const pqN = parProduitQ(sel), pqN1 = parProduitQ(prec);
    const qN = M.qte(sel), qN1 = M.qte(prec), caN1v = M.ca(prec), pm1 = qN1 ? caN1v / qN1 : 0;
    let caPrixN1 = 0;   // CA de la période valorisé aux prix N-1 (prix de la période pour un produit absent en N-1)
    for (const [id, x] of pqN) { const y = pqN1.get(id); caPrixN1 += x.q * (y && y.q ? y.ca / y.q : x.ca / x.q); }
    const effets = { volume: (qN - qN1) * pm1, mix: caPrixN1 - qN * pm1, prix: ca - caPrixN1 };
    const etapesPvm = [{ label: 'CA N-1', valeur: caN1v, total: true },
      { label: 'Effet volume', valeur: effets.volume, details: [{ nom: 'Quantité', valeur: `${fmt.nb(qN)} vs ${fmt.nb(qN1)}` }] },
      { label: 'Effet prix', valeur: effets.prix, details: [{ nom: 'Prix et remises, produit par produit', valeur: '' }] },
      { label: 'Effet mix', valeur: effets.mix, details: [{ nom: 'Poids des produits chers ou bon marché', valeur: '' }] },
      { label: 'CA période', valeur: ca, total: true }];
    const cascadePvm = carte({ titre: 'Variation du CA : volume, prix, mix', sous: 'Ce qui explique l’écart avec N-1', span: 6,
      tableau: n1 ? () => ({ colonnes: [{ titre: 'Étape', cle: 'label' }, { titre: 'Montant', cle: 'valeur', f: fmt.eur, d: true }],
                             lignes: etapesPvm }) : null });
    if (n1) G.cascade(cascadePvm, { etapes: etapesPvm, format: fmt.eur, formatCourt: fmt.eurC, formatAxe: fmt.eurAxe });
    else cascadePvm.append(ui.el('div', { class: 'vide' }, 'Pas de données N-1 pour cette période (les données commencent en 2024).'));

    // ---------- Répartition du CA : catégorie × segment ----------
    const segsCle = Object.keys(COULEURS.segment);
    const catSeg = Object.keys(COULEURS.categorie).filter(c => cN.has(c)).map(c => {
      const g = grouper(cN.get(c), v => v.c.segment);
      return { label: c, ca: M.ca(cN.get(c)), valeurs: segsCle.map(s => (g.has(s) ? M.ca(g.get(s)) : 0)) };
    }).sort((a, b) => b.ca - a.ca);
    G.empile100(carte({ titre: 'Répartition du CA par catégorie et segment', sous: 'Qui achète quoi : part de chaque segment client', span: 6,
      tableau: () => ({ colonnes: [{ titre: 'Catégorie', cle: 'label' }, { titre: 'CA', cle: 'ca', f: fmt.eur, d: true },
                                   ...segsCle.map((s, j) => ({ titre: s, cle: 'p' + j, f: fmt.pct, d: true }))],
                        lignes: catSeg.map(r => ({ label: r.label, ca: r.ca, ...Object.fromEntries(r.valeurs.map((v, j) => ['p' + j, v / r.ca])) })) }) }),
      { items: catSeg, series: segsCle.map(s => ({ nom: s, couleur: COULEURS.segment[s] })), format: fmt.eur0, pct: fmt.pct });

    // ---------- CA mensuel par catégorie ----------
    const caCatMois = Object.fromEntries(cats.map(c => [c, ctx.cles.map(ctx.parMois(cN.get(c)))]));
    G.temporel(carte({ titre: 'CA mensuel par catégorie',
      tableau: () => ({ colonnes: [{ titre: 'Mois', cle: 'm' }, ...cats.map(c => ({ titre: c, cle: c, f: fmt.eur0, d: true }))],
                        lignes: labels.map((m, i) => ({ m, ...Object.fromEntries(cats.map(c => [c, caCatMois[c][i]])) })) }) }),
      { labels, format: fmt.eur0, formatAxe: fmt.eurAxe,
        lignes: cats.map(c => ({ nom: c, couleur: COULEURS.categorie[c], valeurs: caCatMois[c] })) });

    // ---------- Évolution vs mois précédent, 12 derniers mois ----------
    const derniers = Array.from({ length: 12 }, (_, i) => ctx.kMax - 11 + i);
    const mom = derniers.map(k => (k - 1 >= ctx.kMin && caBase(k - 1) ? evol(caBase(k), caBase(k - 1)) : null));
    G.temporel(carte({ titre: 'Évolution vs mois précédent', sous: '12 derniers mois jusqu’à la fin de la période', span: 12,
      tableau: () => ({ colonnes: [{ titre: 'Mois', cle: 'm' }, { titre: 'CA', cle: 'v', f: fmt.eur, d: true },
                                   { titre: 'vs mois précédent', cle: 'e', d: true, html: l => evolCellule(l.e) }],
                        lignes: derniers.map((k, i) => ({ m: ctx.libMois(k), v: caBase(k), e: mom[i] })) }) }),
      { labels: derniers.map(ctx.libMois), format: fmt.evol, formatAxe: v => fmt.nb(v * 100) + ' %', hauteur: 200,
        barres: { nom: 'Évolution vs mois précédent', couleurSigne: true, valeurs: mom } });

    // ---------- Matrice catégorie > produit × mois ----------
    const gProd = grouper(sel, v => v.idp);
    const lignesMatrice = [];
    for (const c of [...cats].sort((a, b) => M.ca(cN.get(b)) - M.ca(cN.get(a)))) {
      lignesMatrice.push({ label: c, niveau: 0, valeurs: caCatMois[c] });
      const prods = [...gProd].filter(([, l]) => l[0].p.categorie === c).sort((a, b) => M.ca(b[1]) - M.ca(a[1]));
      for (const [idp, l] of prods) {
        lignesMatrice.push({ label: ctx.produitParId.get(idp).nom, niveau: 1, valeurs: ctx.cles.map(ctx.parMois(l)) });
      }
    }
    G.matrice(carte({ titre: 'CA par produit et par mois', sous: 'Catégories puis produits · montants en k€', span: 12 }),
      { titreLignes: 'Catégorie / produit', colonnes: labels, lignes: lignesMatrice,
        format: v => (v ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(v / 1000) : '—'),
        formatInfobulle: fmt.eur0 });

    // ---------- Détail des produits ----------
    const pN1 = grouper(prec, v => v.idp);
    const produits = [...gProd].map(([idp, l]) => {
      const p = ctx.produitParId.get(idp), v = M.ca(l), v1 = n1 ? (pN1.has(idp) ? M.ca(pN1.get(idp)) : 0) : null;
      return { nom: p.nom, cat: p.categorie, q: M.qte(l), ca: v, caN1: v1, d: n1 ? v - v1 : null, e: n1 ? evol(v, v1) : null,
               part: v / ca, prix: M.prixMoyen(l), remise: M.tauxRemise(l) };
    }).sort((a, b) => b.ca - a.ca).map((x, i) => ({ ...x, rang: i + 1 }));
    G.tableau(carte({ titre: 'Détail des produits', sous: 'Cliquer un en-tête pour trier', span: 12 }), {
      tri: { cle: 'ca', desc: true },
      colonnes: [
        { titre: '#', cle: 'rang', d: true }, { titre: 'Produit', cle: 'nom' },
        { titre: 'Catégorie', cle: 'cat', html: l => pastille(COULEURS.categorie[l.cat], l.cat) },
        { titre: 'Quantité', cle: 'q', f: fmt.nb, d: true }, { titre: 'CA', cle: 'ca', f: fmt.eur, d: true },
        { titre: 'CA N-1', cle: 'caN1', f: fmt.eur, d: true }, { titre: 'Écart', cle: 'd', f: fmt.evolEur, d: true },
        { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) },
        { titre: 'Part du CA', cle: 'part', f: fmt.pct, d: true }, { titre: 'Prix moyen', cle: 'prix', f: fmt.eur, d: true },
        { titre: 'Taux de remise', cle: 'remise', f: fmt.pct, d: true }],
      lignes: produits });
  },
};
