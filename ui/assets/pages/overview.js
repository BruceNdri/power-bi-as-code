/* Page « overview » : KPI et visuels, partagés par les maquettes v1 et v2. */
(window.PAGES_RAPPORT = window.PAGES_RAPPORT || {}).overview = {
  cle: 'overview',
  titre: 'Overview',
  rendu(ctx, ui) {
    const { M, sel, prec, n1, evol, grouper, COULEURS } = ctx;
    const { tuile, carte, fmt, badgeEvol } = ui;
    const G = window.Graph;
    const ev = (a, b) => (n1 ? evol(a, b) : null);
    const evolCellule = v => badgeEvol(v, { suffixe: '' });

    // ---------- KPI ----------
    const ca = M.ca(sel), caN1 = M.ca(prec);
    tuile({ lib: "Chiffre d'affaires", val: fmt.eurC(ca), delta: badgeEvol(ev(ca, caN1)) });
    tuile({ lib: 'CA cumul annuel', val: fmt.eurC(M.ca(ctx.ytd)), delta: badgeEvol(ev(M.ca(ctx.ytd), M.ca(ctx.ytdN1))) });
    tuile({ lib: 'Nombre de ventes', val: fmt.nb(M.nb(sel)), delta: badgeEvol(ev(M.nb(sel), M.nb(prec))) });
    tuile({ lib: 'Panier moyen', val: fmt.eur0(M.panier(sel)), delta: badgeEvol(ev(M.panier(sel), M.panier(prec))) });
    tuile({ lib: 'Clients actifs', val: fmt.nb(M.clients(sel)), delta: badgeEvol(ev(M.clients(sel), M.clients(prec))) });
    const nouveaux = ctx.nouveaux(sel);
    tuile({ lib: 'Nouveaux clients', val: fmt.nb(nouveaux), sous: `${fmt.pct(nouveaux / M.clients(sel))} des clients actifs` });
    tuile({ lib: 'Taux de remise', val: fmt.pct(M.tauxRemise(sel)), sous: `${fmt.eurC(M.remises(sel))} de remises accordées` });

    // ---------- CA par mois, N vs N-1 ----------
    const caMois = ctx.parMois(sel), caMoisN1 = ctx.parMois(prec);
    const labels = ctx.cles.map(ctx.libMois);
    const valN = ctx.cles.map(caMois);
    const valN1 = ctx.cles.map(k => (k - 12 >= ctx.kMin ? caMoisN1(k - 12) : null));
    G.temporel(carte({
      titre: "Chiffre d'affaires par mois", sous: 'Période sélectionnée comparée à la même période un an plus tôt', span: 8,
      tableau: () => ({ colonnes: [
          { titre: 'Mois', cle: 'mois' }, { titre: 'CA', cle: 'n', f: fmt.eur, d: true },
          { titre: 'CA N-1', cle: 'n1', f: fmt.eur, d: true },
          { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) }],
        lignes: labels.map((m, i) => ({ mois: m, n: valN[i], n1: valN1[i], e: valN1[i] ? evol(valN[i], valN1[i]) : null })) }),
    }), { labels, format: fmt.eur0, formatAxe: fmt.eurAxe,
          lignes: [{ nom: 'Période', couleur: 'var(--primaire)', valeurs: valN },
                   { nom: 'Même période N-1', couleur: 'var(--n1)', valeurs: valN1 }] });

    // ---------- CA par segment ----------
    const parSegment = grouper(sel, v => v.c.segment);
    const segments = Object.keys(COULEURS.segment).filter(x => parSegment.has(x))
      .map(x => ({ label: x, valeur: M.ca(parSegment.get(x)), couleur: COULEURS.segment[x] }));
    G.anneau(carte({ titre: 'CA par segment client', span: 4,
      tableau: () => ({ colonnes: [{ titre: 'Segment', cle: 'label' }, { titre: 'CA', cle: 'valeur', f: fmt.eur, d: true },
                                   { titre: 'Part', cle: 'part', f: fmt.pct, d: true }],
                        lignes: segments.map(x => ({ ...x, part: x.valeur / ca })) }) }),
      { items: segments, format: fmt.eur, formatTotal: fmt.eurC, pct: fmt.pct, libTotal: 'CA total' });

    // ---------- Pont du CA N-1 au CA de la période : contribution de chaque catégorie ----------
    const cascadeCat = carte({ titre: 'Du CA N-1 au CA de la période', sous: 'Contribution de chaque catégorie à la variation', span: 6,
      tableau: n1 ? () => ({ colonnes: [{ titre: 'Étape', cle: 'label' }, { titre: 'Montant', cle: 'valeur', f: fmt.eur, d: true }],
                             lignes: etapesCat }) : null });
    const gcN = grouper(sel, v => v.p.categorie), gcN1 = grouper(prec, v => v.p.categorie);
    const etapesCat = [{ label: 'CA N-1', valeur: caN1, total: true },
      ...[...new Set([...gcN.keys(), ...gcN1.keys()])].map(c => {
        const v = gcN.has(c) ? M.ca(gcN.get(c)) : 0, v1 = gcN1.has(c) ? M.ca(gcN1.get(c)) : 0;
        return { label: c, valeur: v - v1, details: [{ nom: 'CA', valeur: fmt.eur0(v) }, { nom: 'CA N-1', valeur: fmt.eur0(v1) }] };
      }).sort((a, b) => b.valeur - a.valeur),
      { label: 'CA période', valeur: ca, total: true }];
    if (n1) G.cascade(cascadeCat, { etapes: etapesCat, format: fmt.eur, formatCourt: fmt.eurC, formatAxe: fmt.eurAxe });
    else cascadeCat.append(ui.el('div', { class: 'vide' }, 'Pas de données N-1 pour cette période (les données commencent en 2024).'));

    // ---------- Répartition du CA : catégorie > produit ----------
    const groupesCat = Object.keys(COULEURS.categorie).filter(c => gcN.has(c)).map(c => {
      const parProduit = grouper(gcN.get(c), v => v.p.nom);
      return { label: c, couleur: COULEURS.categorie[c], valeur: M.ca(gcN.get(c)),
               enfants: [...parProduit].map(([nom, l]) => ({ label: nom, valeur: M.ca(l) })).sort((a, b) => b.valeur - a.valeur) };
    });
    G.treemap(carte({ titre: 'Répartition du CA', sous: 'Par catégorie puis par produit · surface proportionnelle au CA', span: 6,
      tableau: () => ({ colonnes: [{ titre: 'Catégorie', cle: 'c' }, { titre: 'Produit', cle: 'p' }, { titre: 'CA', cle: 'v', f: fmt.eur, d: true },
                                   { titre: 'Part du CA', cle: 'part', f: fmt.pct, d: true }],
                        lignes: groupesCat.flatMap(g => g.enfants.map(e => ({ c: g.label, p: e.label, v: e.valeur, part: e.valeur / ca }))) }) }),
      { groupes: groupesCat, format: fmt.eur, pct: fmt.pct });

    // ---------- CA par catégorie et par région ----------
    const barresParDim = (cle, titre, sous) => {
      const gN = grouper(sel, cle), gN1 = grouper(prec, cle);
      const items = [...gN].map(([k, l]) => {
        const v = M.ca(l), v1 = gN1.has(k) ? M.ca(gN1.get(k)) : 0;
        return { label: k, valeurs: [v], etiquette: `${fmt.eurC(v)} · ${fmt.pct(v / ca)}`, n1: v1, e: ev(v, v1),
                 details: [{ nom: 'Part du CA', valeur: fmt.pct(v / ca) }, { nom: 'Évolution vs N-1', valeur: fmt.evol(ev(v, v1)) }] };
      }).sort((a, b) => b.valeurs[0] - a.valeurs[0]);
      G.barresH(carte({ titre, sous, span: 6,
        tableau: () => ({ colonnes: [{ titre: titre.replace('CA par ', '').replace(/^./, c => c.toUpperCase()), cle: 'label' },
                                     { titre: 'CA', cle: 'ca', f: fmt.eur, d: true }, { titre: 'Part', cle: 'part', f: fmt.pct, d: true },
                                     { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) }],
                          lignes: items.map(it => ({ label: it.label, ca: it.valeurs[0], part: it.valeurs[0] / ca, e: it.e })) }) }),
        { items, series: [{ nom: "Chiffre d'affaires", couleur: 'var(--primaire)' }], format: fmt.eur });
    };
    barresParDim(v => v.p.categorie, 'CA par catégorie', 'Montant et part du chiffre d’affaires');
    barresParDim(v => v.c.region, 'CA par région', 'Montant et part du chiffre d’affaires');

    // ---------- Tops ----------
    const top = (cle, decrire) => {
      const gN = grouper(sel, cle), gN1 = grouper(prec, cle);
      return [...gN].map(([k, l]) => {
        const v = M.ca(l);
        return { ...decrire(l[0]), ca: v, e: ev(v, gN1.has(k) ? M.ca(gN1.get(k)) : 0) };
      }).sort((a, b) => b.ca - a.ca).slice(0, 5).map((x, i) => ({ ...x, rang: i + 1 }));
    };
    const pastille = (couleur, txt) => `<i class="pastille" style="background:${couleur}"></i>${ui.echap(txt)}`;
    G.tableau(carte({ titre: 'Top 5 produits', sous: "Classés par chiffre d'affaires" }), {
      triable: false,
      colonnes: [{ titre: '#', cle: 'rang' }, { titre: 'Produit', cle: 'nom' },
                 { titre: 'Catégorie', cle: 'cat', html: l => pastille(COULEURS.categorie[l.cat], l.cat) },
                 { titre: 'CA', cle: 'ca', f: fmt.eur0, d: true }, { titre: 'vs N-1', cle: 'e', d: true, html: l => evolCellule(l.e) }],
      lignes: top(v => v.idp, v => ({ nom: v.p.nom, cat: v.p.categorie })) });
    G.tableau(carte({ titre: 'Top 5 clients', sous: "Classés par chiffre d'affaires" }), {
      triable: false,
      colonnes: [{ titre: '#', cle: 'rang' }, { titre: 'Client', cle: 'nom' },
                 { titre: 'Segment', cle: 'seg', html: l => pastille(COULEURS.segment[l.seg], l.seg) },
                 { titre: 'CA', cle: 'ca', f: fmt.eur0, d: true }, { titre: 'vs N-1', cle: 'e', d: true, html: l => evolCellule(l.e) }],
      lignes: top(v => v.idc, v => ({ nom: v.c.nom, seg: v.c.segment })) });
  },
};
