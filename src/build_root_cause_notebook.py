"""Build and execute the root-cause notebook in-process (no network/kernel server)."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
R=Path(__file__).resolve().parents[1];cells=[]
def md(s):cells.append(nbf.v4.new_markdown_cell(s))
def code(s):cells.append(nbf.v4.new_code_cell(s))
md('# Why does Stories earn different dollars?\n\nRoot-cause investigation extending the supplied `01_eda.ipynb`. Separate observed accounting mechanisms, tested competing explanations, unresolved behavioral causes and conditional financial scenarios. Original CSV rows and the supplied notebook remain unchanged.')
code("from pathlib import Path\nimport json, os, sys, subprocess\nimport pandas as pd\nfrom IPython.display import display, Image, Markdown\nROOT = Path.cwd()\nif not (ROOT / 'reports').exists(): ROOT = ROOT.parent\nDATA = Path(os.environ.get('STORIES_DATA', '/Users/aya/Downloads/stories_transactions.csv'))\nsubprocess.run([sys.executable, str(ROOT/'src/root_cause.py'), '--data', str(DATA)], check=True, stdout=subprocess.DEVNULL)\nO = ROOT/'reports/root_cause'\nf = json.loads((O/'findings.json').read_text())\nprint('Input SHA-256:', f['sourceSHA256'])\nprint('Basis:', f['basis'])")
md('## 1. Audit the assumptions before explaining a pattern\n\nThe provided notebook is a useful starting point, but exact duplicates are not proven errors; missing IDs are not proven nonmembers; first-observed is not first-ever. Similar Tuesday composition does not identify the same customers or their motivation.')
code("display(pd.Series(f['notebookReview'], name='Review'))\ndisplay(pd.Series(f['duplicateSensitivity'], name='Sensitivity'))")
md('## 2. Why Harbour records more GP/day\n\nWe decompose the exact identity `transactions/day × units/transaction × Σ share × [price × (1−discount) − cost]`. Average over all 720 permutations of the six accounting factors to allocate interactions. These are accounting contributions, not causal effects or savings.')
code("display(pd.Series(f['branchDecomposition']['dailyGP'], name='Recorded GP/day'))\ndisplay(pd.read_csv(O/'branch_profit_shapley.csv'))\ndisplay(Image(filename=str(ROOT/'figures/root_cause/branch_profit_decomposition.png')))")
md('## 3. Does product mix explain Garden?\n\nCompare the same products, rather than pooled average costs. A near-constant multiplier is compatible with standard-cost allocation or a branch-wide cost difference. Invoices, recipes and accounting definitions distinguish those mechanisms.')
code("ratios = pd.read_csv(O/'matched_product_ratios.csv', index_col=0)\ndisplay(ratios.describe())\ndisplay(ratios.head(10))")
md('## 4. Turn an unresolved cost cause into a bounded dollar decision\n\nThe fixed-Garden-volume scenario is different from the Shapley interaction allocation. Do not add them. Cost recovery fractions are hypothetical. The price alignment break-even assumes uniform unit loss and fixed mix; it is not a price-elasticity estimate.')
code("display(pd.Series(f['gardenDecision'], name='Fixed-volume sensitivity'))")
md('## 5. Tuesday: more transactions or larger baskets?\n\nNormalize by actual calendar-day exposure. Compare within complete weeks to limit long-run growth confounding. Similar category distributions are not proof of identical individuals or equivalent behavior.')
code("display(pd.DataFrame(f['tuesdayBasketComparisons']).T)\nprint(f['weeklyTuesday'])\ndisplay(pd.read_csv(O/'tuesday_category_mix.csv', index_col=0))\ndisplay(Image(filename=str(ROOT/'figures/root_cause/tuesday_within_week.png')))")
md('## 6. Could this be a single branch, hour, or recorded campaign?\n\nTest heterogeneity and exclude all dates with a recorded 15% discount anywhere in the network. This is a robustness check, not randomized treatment-effect estimation; unrecorded promotions remain possible.')
code("w = pd.read_csv(O/'tuesday_by_branch_week.csv')\ndisplay(w.groupby('branch').agg(ratio_min=('ratio','min'),ratio_median=('ratio','median'),ratio_max=('ratio','max'),weeks_tuesday_wins=('tuesdayWins','sum')))\ndisplay(pd.read_csv(O/'tuesday_hour_ratios.csv'))\ndisplay(pd.Series(f['tuesdayExcluding15PercentDates'], name='Excluding campaign dates'))")
md('## 7. Investigate the payday hypothesis without inventing local facts\n\nExploratory log-count regression controls branch×week, weekday and illustrative days 1–3, 14–16 and 25–end. These are **not actual salary dates**. Week-clustered intervals allow common variation within each week. A weekly payday always on Tuesday cannot be separated from weekday in this file. Multiple exploratory tests and only six months limit inference.')
code("display(pd.Series(f['tuesdayControlled'], name='Controlled weekday association'))\ndisplay(pd.DataFrame(f['tuesdayControlled']['calendarProxyRatios']).T)")
md('## 8. Growth: traffic, baskets, pricing or changing observed cohorts?\n\nMonth-length-normalized revenue/day is decomposed by transactions/day, units/basket and realized revenue/unit. Transaction growth is not proof of acquisition or footfall. Cohorts are first-observed, censored by the data window; January activity is guaranteed for the January-observed cohort.')
code("display(pd.Series(f['growthAccounting']))\ndisplay(pd.DataFrame(f['identifiedGrowth']).T)\ndisplay(pd.read_csv(O/'observed_first_cohort_growth.csv').tail(12))")
if (R/'reports/activity/step5_tuesday_distribution.json').exists():
 md('## Step 5 — Daily transaction distributions\n\nOther weekdays means Monday, Wednesday, Thursday and Friday only. Weekends are visible in the plot but excluded from the comparison values. No ML is trained here. Higher pooled mean and median are descriptive; the complete-week results above address persistence separately.')
 code("step5 = json.loads((ROOT/'reports/activity/step5_tuesday_distribution.json').read_text())\nfor label, key in [('Tuesday mean','tuesdayMean'),('Other weekdays mean','otherWeekdaysMean'),('Tuesday median','tuesdayMedian'),('Other weekdays median','otherWeekdaysMedian')]: print(label + ':', step5[key])\ndisplay(pd.DataFrame(step5['byBranch']).T)\ndisplay(Image(filename=str(ROOT/'figures/activity/tuesday_weekday_boxplot.png')))")
md('## 9. Competing hypotheses, required evidence, and financial decisions\n\nThe detailed report ranks cost reconciliation, Tuesday calendar/provenance investigation and growth-mechanism validation ahead of additional product features. No new promotion or loyalty claim is needed to establish an accounting finding.')
code("display(Markdown((O/'REPORT.md').read_text()))")
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
shell=InteractiveShell.instance();count=0
for cell in nb.cells:
 if cell.cell_type!='code':continue
 count+=1
 with capture_output() as cap:res=shell.run_cell(cell.source,store_history=False)
 if res.error_before_exec or res.error_in_exec:raise RuntimeError(f'Notebook cell {count} failed: {res.error_before_exec or res.error_in_exec}')
 cell.execution_count=count;cell.outputs=[]
 if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
 if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
 for o in cap.outputs:cell.outputs.append(nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata))
nbf.validate(nb);path=R/'notebooks/02_root_cause_investigation.ipynb';nbf.write(nb,path);print(f'Executed {count} cells and wrote {path}')
