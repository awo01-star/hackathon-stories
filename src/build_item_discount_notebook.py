"""Execute a read-only inspection notebook for saved item-discount scenarios."""
from pathlib import Path
import nbformat as n
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
R=Path(__file__).resolve().parents[1]
cells=[n.v4.new_markdown_cell('''# Item-level forecast and discount business value

Existing July 1, 2026 forecasts are historical demonstrations. Unit lifts are hypothetical, not modeled promotion responses. No model is retrained. Full-list-price no-discount GP is a reference, not expected GP under the actual historical discount policy. No profit floor is guaranteed.

See `reports/item_discount_scenarios/REPORT.md` for formulas, caveats and location-model feasibility.'''),n.v4.new_code_cell('''from pathlib import Path
import pandas as pd
import numpy as np
from IPython.display import display, Image
ROOT=Path.cwd()
if not (ROOT/'src').exists(): ROOT=ROOT.parent
OUT=ROOT/'reports/item_discount_scenarios'
history=pd.read_csv(OUT/'historical_product_economics.csv')
forecast=pd.read_csv(OUT/'forecast_reference.csv')
scenarios=pd.read_csv(OUT/'discount_scenarios.csv')
print('135 branch/products; 4860 hypothetical scenarios. Inputs generated without training.')
display(history)
display(forecast[['Branch','Product','forecast_units','price','cost','ForecastNoDiscountGPUSD']])'''),n.v4.new_markdown_cell('''## Examine any branch/product

Change the two selectors and rerun this cell. Historical GP/unit is observed. Forecast quantity is estimated. Discount/lift GP is conditional accounting with all modeled product units discounted, no waste or incremental operating costs. The minimum extra units and break-even discount limits do not predict that demand is attainable.'''),n.v4.new_code_cell('''BRANCH='Garden'
PRODUCT='Chicken Pesto Sandwich'
display(history[(history.Branch==BRANCH)&(history.Product==PRODUCT)])
selected=scenarios[(scenarios.Branch==BRANCH)&(scenarios.Product==PRODUCT)]
display(selected[['DiscountFraction','AssumedUnitLift','ScenarioUnits','ScenarioGPUSD','GPChangeUSD','RequiredUnitLift','RequiredExtraUnits','MinimumWholeUnitsToPreserveGP','MaxDiscountAtAssumedLift','PreservesReferenceGP']].round(4))'''),n.v4.new_markdown_cell('''## Compare branch break-even requirements at 10% off

A positive unit margin is insufficient to preserve total GP. A discount with no additional units lowers this reference. Extra-unit requirements are more demanding where recorded margins are lower; reconcile Garden costing before assuming avoidable cash costs.'''),n.v4.new_code_cell('''example=scenarios[(scenarios.DiscountFraction==.1)&(scenarios.AssumedUnitLift==0)&scenarios.Product.isin(['Iced Latte','Chicken Pesto Sandwich'])]
display(example[['Branch','Product','BaselineForecastUnits','NoDiscountReferenceGPUSD','DiscountedUnitGPUSD','RequiredUnitLift','RequiredExtraUnits']])
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/stories-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
labels=[r.Branch+' / '+r.Product for r in example.itertuples()]
ax.barh(labels,example.RequiredUnitLift*100,color='#667858')
ax.axvline(20,color='#ad593e',linestyle='--',label='20% assumed lift example')
ax.set_xlabel('Extra units required to preserve reference GP (%)')
ax.set_title('10% discount: accounting break-even, not predicted demand response')
ax.legend()
p=ROOT/'figures/item_discount_scenarios';p.mkdir(exist_ok=True)
fig.savefig(p/'required_unit_lift.png',dpi=150);plt.close(fig)
display(Image(filename=str(p/'required_unit_lift.png')))'''),n.v4.new_markdown_cell('''## How location context fits

Bliss Street/AUB and LeMall Dbayeh are separately sourced research cases, not mapped to Garden/Harbour/Uptown. Context rules can suggest audiences to investigate, but a trained location/offer-response model requires verified branch mapping and observed offer exposures/responses. Do not assign these anonymous forecasts to real-world places.

To measure incremental profit, prospectively randomize eligible opportunities, include nonbuyers and all basket purchases, and account for service, campaign, waste, capacity and cannibalization costs. The analysis does not activate an offer or demonstrate causal uplift.'''),n.v4.new_code_cell('''assert len(history)==135 and len(forecast)==135 and len(scenarios)==4860
assert (scenarios[(scenarios.DiscountFraction>0)&(scenarios.AssumedUnitLift==0)].GPChangeUSD<0).all()
p=scenarios[scenarios.DiscountedUnitGPUSD>0]
np.testing.assert_allclose(p.RequiredUnitsToPreserveGP*p.DiscountedUnitGPUSD,p.NoDiscountReferenceGPUSD)
print('PASS accounting identities. No response model, guaranteed gain, active offer or causal inference.')''')]
nb=n.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}});shell=InteractiveShell.instance();i=0
for c in nb.cells:
 if c.cell_type!='code':continue
 i+=1
 with capture_output() as cap:r=shell.run_cell(c.source,store_history=False)
 if r.error_before_exec or r.error_in_exec:raise RuntimeError(r.error_before_exec or r.error_in_exec)
 c.execution_count=i;c.outputs=[]
 if cap.stdout:c.outputs.append(n.v4.new_output('stream',name='stdout',text=cap.stdout))
 if cap.stderr:c.outputs.append(n.v4.new_output('stream',name='stderr',text=cap.stderr))
 for o in cap.outputs:c.outputs.append(n.v4.new_output('display_data',data=o.data,metadata=o.metadata))
n.validate(nb);p=R/'notebooks/09_item_discount_business_value.ipynb';n.write(nb,p);print('Executed',i,'cells:',p)
