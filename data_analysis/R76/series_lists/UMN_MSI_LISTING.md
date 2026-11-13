# The UMN (MSI) deep-storage listing

On 2026-11-13, with Yan Liu's help, a listing was found of the raw SuperCDMS data that the group thought it had lost. It is a listing of `s3://cdms1/k100/midasraw/byseries/` on the University of Minnesota deep storage (MSI cluster); the listing's own file dates are 6 to 11 June 2026. It has 9,213 series folders and 285,463 files (`.mid.gz` MIDAS files, with a few hundred `.json`), about 23.7 TiB, for series from 2016-01-04 to 2024-10-04.

The full listing (about 366,000 lines, about 55 MB) is not in this repository. These two files condense it and compare it with `DataSeriesList.xlsx`:

| File | What it holds |
|---|---|
| `umn_msi_series_listing.csv` | One row per series in the listing: `series`, the `run_sheet`(s) of `DataSeriesList.xlsx` that list it (empty if none), the number of `files`, how many are MIDAS files (`midas_files`), and the total size in MiB. |
| `umn_msi_run_summary.csv` | One row per `RunNN` sheet: series in the sheet, how many are in the listing, the percent, the files and the size (GiB) of those. The last row counts each series once. |

How the comparison was made: every cell of every `RunNN` sheet was read, hidden columns and filtered rows included; a series counts as present when its ID (`07YYMMDD_HHMM`) is a folder in the listing. Only folder names were matched and the file lists read; nobody has checked that the files are complete and readable. The listing shows sizes rounded to whole megabytes (kilobytes for small files), so sizes are approximate; 1 MiB, 1 GiB are 1,024-based. The listing covers only that one path, so a run with no series in it (Runs 55, 58, 59, 60, 65; Runs 61 and 62 almost none) may be held elsewhere.
