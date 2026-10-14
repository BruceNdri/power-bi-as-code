-- Schéma de la base d'exemple (exécuté au premier démarrage du conteneur).

CREATE TABLE produits (
    id_produit    integer PRIMARY KEY,
    nom_produit   text          NOT NULL,
    categorie     text          NOT NULL,
    prix_unitaire numeric(10,2) NOT NULL
);

CREATE TABLE clients (
    id_client  integer PRIMARY KEY,
    nom_client text NOT NULL,
    ville      text NOT NULL,
    region     text NOT NULL,
    segment    text NOT NULL
);

CREATE TABLE ventes (
    id_vente      integer PRIMARY KEY,
    date_vente    date          NOT NULL,
    id_client     integer       NOT NULL REFERENCES clients (id_client),
    id_produit    integer       NOT NULL REFERENCES produits (id_produit),
    quantite      integer       NOT NULL,
    prix_unitaire numeric(10,2) NOT NULL,
    montant       numeric(12,2) NOT NULL
);

CREATE INDEX ix_ventes_date ON ventes (date_vente);
