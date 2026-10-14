/* Page « clients » : KPI et visuels, partagés par les maquettes v1 et v2. */
(window.PAGES_RAPPORT = window.PAGES_RAPPORT || {}).clients = {
  cle: 'clients',
  titre: 'Clients',
  rendu(ctx, ui) {
    const { M, sel, prec, n1, evol, grouper, COULEURS } = ctx;
    const { tuile, carte, fmt, badgeEvol, echap } = ui;
    const G = window.Graph;
    const ev = (a, b) => (n1 ? evol(a, b) : null);
    const evolCellule = v => badgeEvol(v, { suffixe: '' });
    const pastille = (couleur, txt) => `<i class="pastille" style="background:${couleur}"></i>${echap(txt)}`;

    // ---------- Agrégats par client ----------
    const gN = grouper(sel, v => v.idc), gN1 = grouper(prec, v => v.idc);
    const parClient = [...gN].map(([id, l]) => {
      const c = ctx.clientParId.get(id), ca = M.ca(l), caN1 = gN1.has(id) ? M.ca(gN1.get(id)) : null;
      const dernier = Math.max(...l.map(v => v.t));
      return { id, nom: c.nom, segment: c.segment, ville: c.ville, region: c.region, ca, caN1,
               e: n1 ? evol(ca, caN1 || 0) : null, nb: l.length, panier: ca / l.length,
               dernier, recence: Math.round((ctx.fin - dernier) / 864e5) };
    }).sort((a, b) => b.ca - a.ca).map((x, i) => ({ ...x, rang: i + 1 }));
    const caTotal = M.ca(sel);

    // ---------- KPI ----------
    const actifs = M.clients(sel), actifsN1 = M.clients(prec);
    tuile({ lib: 'Clients actifs', val: fmt.nb(actifs), delta: badgeEvol(ev(actifs, actifsN1)) });
    tuile({ lib: 'Taux de clients actifs', val: fmt.pct(actifs / ctx.portefeuille), sous: `sur ${fmt.nb(ctx.portefeuille)} clients au portefeuille` });
    tuile({ lib: 'Nouveaux clients', val: fmt.nb(ctx.nouveaux(sel)), sous: 'premier achat sur la période' });
    tuile({ lib: 'Taux de rétention', val: fmt.pct(ctx.retention), sous: n1 ? 'clients N-1 revenus acheter' : 'pas de données N-1' });
    tuile({ lib: 'Clients perdus', val: fmt.nb(ctx.perdus), sous: n1 ? 'actifs en N-1, sans achat depuis' : 'pas de données N-1' });
    tuile({ lib: 'CA moyen par client', val: fmt.eur0(M.caParClient(sel)), delta: badgeEvol(ev(M.caParClient(sel), M.caParClient(prec))) });
    tuile({ lib: "Fréquence d'achat", val: fmt.nb1(M.frequence(sel)), sous: 'achats par client actif' });
    const top10 = parClient.slice(0, 10).reduce((a, x) => a + x.ca, 0);
    tuile({ lib: 'Part du CA des 10 premiers', val: fmt.pct(top10 / caTotal), sous: 'concentration du chiffre d’affaires' });

    // ---------- Variation du CA expliquée par les mouvements de clients ----------
    const caParId = l => { const m = new Map(); for (const v of l) m.set(v.idc, (m.get(v.idc) || 0) + v.m); return m; };
    const aN = caParId(sel), aN1 = caParId(prec);
    const mvt = { perdus: [0, 0], fideles: [0, 0], revenus: [0, 0], nouveaux: [0, 0] };   // [montant, nombre de clients]
    for (const [id, v1] of aN1) {
      if (!aN.has(id)) { mvt.perdus[0] -= v1; mvt.perdus[1]++; } else { mvt.fideles[0] += aN.get(id) - v1; mvt.fideles[1]++; }
    }
    for (const [id, v] of aN) {
      if (aN1.has(id)) continue;
      const k = ctx.premierAchat.get(id) >= ctx.debut ? 'nouveaux' : 'revenus';
      mvt[k][0] += v; mvt[k][1]++;
    }
    const nbCli = n => ({ nom: 'Clients concernés', valeur: fmt.nb(n) });
    const etapesCli = [{ label: 'CA N-1', valeur: M.ca(prec), total: true },
      { label: 'Clients perdus', valeur: mvt.perdus[0], details: [nbCli(mvt.perdus[1]), { nom: 'Leur CA N-1, non renouvelé', valeur: '' }] },
      { label: 'Clients fidèles', valeur: mvt.fideles[0], details: [nbCli(mvt.fideles[1]), { nom: 'Variation de leur CA', valeur: '' }] },
      { label: 'Clients revenus', valeur: mvt.revenus[0], details: [nbCli(mvt.revenus[1]), { nom: 'Absents en N-1, déjà clients avant', valeur: '' }] },
      { label: 'Nouveaux clients', valeur: mvt.nouveaux[0], details: [nbCli(mvt.nouveaux[1]), { nom: 'Premier achat sur la période', valeur: '' }] },
      { label: 'CA période', valeur: caTotal, total: true }];
    const cascadeCli = carte({ titre: 'Variation du CA par type de client', sous: 'Du CA N-1 au CA de la période', span: 6,
      tableau: n1 ? () => ({ colonnes: [{ titre: 'Étape', cle: 'label' }, { titre: 'Montant', cle: 'valeur', f: fmt.eur, d: true }],
                             lignes: etapesCli }) : null });
    if (n1) G.cascade(cascadeCli, { etapes: etapesCli, format: fmt.eur, formatCourt: fmt.eurC, formatAxe: fmt.eurAxe });
    else cascadeCli.append(ui.el('div', { class: 'vide' }, 'Pas de données N-1 pour cette période (les données commencent en 2024).'));

    // ---------- Concentration du CA ----------
    G.concentration(carte({ titre: 'Concentration du CA', sous: 'Part cumulée du CA selon la part des clients, du plus gros au plus petit', span: 6,
      tableau: () => { let c = 0; return { colonnes: [{ titre: 'Rang', cle: 'rang' }, { titre: 'Client', cle: 'nom' },
                                                     { titre: 'CA', cle: 'ca', f: fmt.eur, d: true }, { titre: 'Part cumulée', cle: 'cumul', f: fmt.pct, d: true }],
                                       lignes: parClient.map(x => ({ ...x, cumul: (c += x.ca) / caTotal })) }; } }),
      { valeurs: parClient.map(x => x.ca), pct: fmt.pct, nomCourbe: 'Part cumulée du CA', titreX: 'Part des clients actifs' });

    // ---------- Répartition du CA : région × segment ----------
    const segsCle = Object.keys(COULEURS.segment);
    const regSeg = [...grouper(sel, v => v.c.region)].map(([r, l]) => {
      const g = grouper(l, v => v.c.segment);
      return { label: r, ca: M.ca(l), valeurs: segsCle.map(s => (g.has(s) ? M.ca(g.get(s)) : 0)) };
    }).sort((a, b) => b.ca - a.ca);
    G.empile100(carte({ titre: 'Répartition du CA par région et segment', sous: 'Part de chaque segment dans le CA de la région', span: 12,
      tableau: () => ({ colonnes: [{ titre: 'Région', cle: 'label' }, { titre: 'CA', cle: 'ca', f: fmt.eur, d: true },
                                   ...segsCle.map((s, j) => ({ titre: s, cle: 'p' + j, f: fmt.pct, d: true }))],
                        lignes: regSeg.map(r => ({ label: r.label, ca: r.ca, ...Object.fromEntries(r.valeurs.map((v, j) => ['p' + j, v / r.ca])) })) }) }),
      { items: regSeg, series: segsCle.map(s => ({ nom: s, couleur: COULEURS.segment[s] })), format: fmt.eur0, pct: fmt.pct });

    // ---------- Clients actifs et nouveaux par mois ----------
    const premierMois = new Map([...ctx.premierAchat].map(([id, t]) => {
      const d = new Date(t); return [id, d.getUTCFullYear() * 12 + d.getUTCMonth()];
    }));
    const gMois = grouper(sel, v => v.k);
    const labels = ctx.cles.map(ctx.libMois);
    const actifsMois = ctx.cles.map(k => (gMois.has(k) ? M.clients(gMois.get(k)) : 0));
    const nouveauxMois = ctx.cles.map(k => (gMois.has(k) ? [...new Set(gMois.get(k).map(v => v.idc))].filter(id => premierMois.get(id) === k).length : 0));
    G.temporel(carte({ titre: 'Clients actifs et nouveaux clients par mois', sous: 'Nombre de clients distincts',
      tableau: () => ({ colonnes: [{ titre: 'Mois', cle: 'm' }, { titre: 'Clients actifs', cle: 'a', f: fmt.nb, d: true },
                                   { titre: 'Nouveaux clients', cle: 'n', f: fmt.nb, d: true }],
                        lignes: labels.map((m, i) => ({ m, a: actifsMois[i], n: nouveauxMois[i] })) }) }),
      { labels, format: fmt.nb, formatAxe: fmt.nb,
        lignes: [{ nom: 'Clients actifs', couleur: 'var(--primaire)', valeurs: actifsMois },
                 { nom: 'Nouveaux clients', couleur: 'var(--s2)', valeurs: nouveauxMois }] });

    // ---------- CA par segment, N vs N-1 ----------
    const sN = grouper(sel, v => v.c.segment), sN1 = grouper(prec, v => v.c.segment);
    const segs = Object.keys(COULEURS.segment).filter(s => sN.has(s));
    const itemsSeg = segs.map(s => {
      const v = M.ca(sN.get(s)), v1 = n1 ? (sN1.has(s) ? M.ca(sN1.get(s)) : 0) : null;
      return { label: s, valeurs: n1 ? [v, v1] : [v], e: ev(v, v1),
               details: [{ nom: 'Évolution', valeur: fmt.evol(ev(v, v1)) }] };
    });
    G.barresH(carte({ titre: 'CA par segment client', sous: n1 ? 'Période comparée à N-1' : 'Pas de données N-1 pour cette période',
      tableau: () => ({ colonnes: [{ titre: 'Segment', cle: 'label' }, { titre: 'CA', cle: 'v', f: fmt.eur, d: true },
                                   { titre: 'CA N-1', cle: 'v1', f: fmt.eur, d: true }, { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) }],
                        lignes: itemsSeg.map(it => ({ label: it.label, v: it.valeurs[0], v1: it.valeurs[1], e: it.e })) }) }),
      { items: itemsSeg, format: fmt.eur, etiquette: fmt.eurC,
        series: n1 ? [{ nom: 'Période', couleur: 'var(--primaire)' }, { nom: 'Même période N-1', couleur: 'var(--n1)' }]
                   : [{ nom: 'Période', couleur: 'var(--primaire)' }] });

    // ---------- Par région : deux mesures, deux graphiques (jamais deux axes) ----------
    const gReg = grouper(sel, v => v.c.region);
    const regions = [...gReg].map(([r, l]) => ({ r, actifs: M.clients(l), moyen: M.caParClient(l), ca: M.ca(l) }));
    const tableRegions = () => ({ colonnes: [{ titre: 'Région', cle: 'r' }, { titre: 'Clients actifs', cle: 'actifs', f: fmt.nb, d: true },
                                             { titre: 'CA moyen par client', cle: 'moyen', f: fmt.eur, d: true }, { titre: 'CA', cle: 'ca', f: fmt.eur, d: true }],
                                  lignes: regions, tri: { cle: 'actifs', desc: true } });
    G.barresH(carte({ titre: 'Clients actifs par région', tableau: tableRegions }),
      { items: [...regions].sort((a, b) => b.actifs - a.actifs).map(x => ({ label: x.r, valeurs: [x.actifs] })),
        series: [{ nom: 'Clients actifs', couleur: 'var(--primaire)' }], format: fmt.nb });
    G.barresH(carte({ titre: 'CA moyen par client et par région', tableau: tableRegions }),
      { items: [...regions].sort((a, b) => b.moyen - a.moyen).map(x => ({ label: x.r, valeurs: [x.moyen] })),
        series: [{ nom: 'CA moyen par client', couleur: 'var(--primaire)' }], format: fmt.eur, etiquette: fmt.eurC });

    // ---------- Nuage : fréquence × panier moyen ----------
    G.nuage(carte({ titre: 'Profil des clients', sous: "Panier moyen (axe vertical) selon le nombre d'achats · taille = CA",
      tableau: () => ({ colonnes: [{ titre: 'Client', cle: 'nom' }, { titre: 'Segment', cle: 'segment' },
                                   { titre: 'Achats', cle: 'nb', f: fmt.nb, d: true }, { titre: 'Panier moyen', cle: 'panier', f: fmt.eur, d: true },
                                   { titre: 'CA', cle: 'ca', f: fmt.eur, d: true }],
                        lignes: parClient, tri: { cle: 'ca', desc: true } }) }),
      { legende: segs.map(s => ({ nom: s, couleur: COULEURS.segment[s] })),
        titreX: "Nombre d'achats sur la période", fx: fmt.nb, fy: fmt.eurAxe,
        points: parClient.map(c => ({ x: c.nb, y: c.panier, t: c.ca, couleur: COULEURS.segment[c.segment], label: c.nom,
          lignes: [{ nom: 'Segment', valeur: c.segment }, { nom: 'Achats', valeur: fmt.nb(c.nb) },
                   { nom: 'Panier moyen', valeur: fmt.eur0(c.panier) }, { nom: 'CA', valeur: fmt.eur0(c.ca) }] })) });

    // ---------- Top 10 clients ----------
    G.barresH(carte({ titre: 'Top 10 clients', sous: "Classés par chiffre d'affaires",
      tableau: () => ({ colonnes: [{ titre: '#', cle: 'rang' }, { titre: 'Client', cle: 'nom' }, { titre: 'CA', cle: 'ca', f: fmt.eur, d: true },
                                   { titre: 'Part', cle: 'part', f: fmt.pct, d: true }],
                        lignes: parClient.slice(0, 10).map(c => ({ ...c, part: c.ca / caTotal })) }) }),
      { items: parClient.slice(0, 10).map(c => ({ label: c.nom, valeurs: [c.ca],
          details: [{ nom: 'Segment', valeur: c.segment }, { nom: 'Ville', valeur: c.ville }, { nom: 'Part du CA', valeur: fmt.pct(c.ca / caTotal) }] })),
        series: [{ nom: "Chiffre d'affaires", couleur: 'var(--primaire)' }], format: fmt.eur, etiquette: fmt.eurC });

    // ---------- Détail des clients ----------
    G.tableau(carte({ titre: 'Détail des clients', sous: 'Clients actifs sur la période · cliquer un en-tête pour trier · récence > 90 jours en rouge', span: 12 }), {
      tri: { cle: 'ca', desc: true }, hauteurMax: 460,
      colonnes: [
        { titre: '#', cle: 'rang', d: true }, { titre: 'Client', cle: 'nom' },
        { titre: 'Segment', cle: 'segment', html: l => pastille(COULEURS.segment[l.segment], l.segment) },
        { titre: 'Ville', cle: 'ville' }, { titre: 'Région', cle: 'region' },
        { titre: 'CA', cle: 'ca', f: fmt.eur, d: true }, { titre: 'CA N-1', cle: 'caN1', f: fmt.eur, d: true },
        { titre: 'Évolution', cle: 'e', d: true, html: l => evolCellule(l.e) },
        { titre: 'Ventes', cle: 'nb', f: fmt.nb, d: true }, { titre: 'Panier moyen', cle: 'panier', f: fmt.eur, d: true },
        { titre: 'Dernier achat', cle: 'dernier', f: fmt.date, d: true },
        { titre: 'Récence (j)', cle: 'recence', d: true, cls: v => (v > 90 ? 'attention' : ''),
          html: l => (l.recence > 90 ? '⚠ ' : '') + fmt.nb(l.recence) }],
      lignes: parClient });
  },
};
