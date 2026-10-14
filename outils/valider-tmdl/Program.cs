// Ouvre un modèle TMDL avec la bibliothèque officielle (TOM) et en affiche le résumé : échoue si le TMDL est invalide.
// Usage (Docker) : voir README, section « Vérifier sans Power BI ».
using Microsoft.AnalysisServices.Tabular;
var db = TmdlSerializer.DeserializeDatabaseFromFolder(args[0]);
var m = db.Model;
Console.WriteLine($"Base OK : niveau {db.CompatibilityLevel}, culture {m.Culture}");
foreach (var t in m.Tables)
  Console.WriteLine($"  {t.Name,-12} colonnes={t.Columns.Count(c => c.Type != ColumnType.RowNumber),2} mesures={t.Measures.Count,2} partition={t.Partitions[0].SourceType}");
foreach (var r in m.Relationships.OfType<SingleColumnRelationship>())
  Console.WriteLine($"  relation {r.FromColumn.Table.Name}[{r.FromColumn.Name}] -> {r.ToColumn.Table.Name}[{r.ToColumn.Name}]");
foreach (var e in m.Expressions) Console.WriteLine($"  paramètre {e.Name} = {e.Expression.Split(' ')[0]}");
foreach (var c in m.Tables.SelectMany(t => t.Columns).Where(c => c.SortByColumn != null)) Console.WriteLine($"  tri {c.Table.Name}[{c.Name}] par [{c.SortByColumn.Name}]");
