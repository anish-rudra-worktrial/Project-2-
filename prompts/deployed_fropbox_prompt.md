# SouthPark Centre underwriting handoff

You are a second-year acquisitions associate at Harborview Capital Partners, working on Fund III.
Sarah Chen has handed you SouthPark Centre, a 280,000 SF value-add office opportunity in Charlotte,
and wants it ready before the next IC packet lock with a live model, source-backed recommendation,
and LOI. She also wants a quick screen on Ballantyne Office Centre so the pipeline tracker does not
sit stale.

## Deal Room Conventions

Work from Outlook and Fropbox/Docket. Open the SouthPark underwriting emails in the inbox, leave the
thread read, and treat it as part of the deal record. The Fropbox deal room root is
`/SouthPark Centre Underwriting`; use those files as the diligence room and leave the source folders
intact.

The starting files are:

- SouthPark model template:
  `/SouthPark Centre Underwriting/Internal/SouthPark_Centre_Model_Template.xlsx`
- Pipeline tracker:
  `/SouthPark Centre Underwriting/Internal/Pipeline_Tracker_Q2_2026.xlsx`

You can work locally in bash with Python spreadsheet libraries such as `openpyxl` or `xlsxwriter`.
Use these names for the final deal-room package so Sarah and IC can find the files:

- `southpark_centre_underwriting.xlsx`
- `ballantyne_wacc_screen.xlsx`
- `Pipeline_Tracker_Q2_2026.xlsx`

Upload the final files to `/SouthPark Centre Underwriting/Outputs`. Create the `Outputs` folder
first if it is missing, and verify the files are present before you finish.

Docket upload note: use `namespace_id="1"` for the final upload.

## Handoff Notes

Sarah's main worry is that the broker NOI bridge is not audit-ready yet. She does not need a memo on
every source file, but the model needs to stand up if IC asks where occupancy, NOI, rollover, capex,
and debt sizing came from.

Use the diligence room to clean up the open questions around income, occupancy, rollover, market
support, renovation scope, reserves, and financing. If the broker materials conflict with better
source evidence, make the model reflect the source-backed view and leave a clear trail in the
workbook or notes showing what you changed and why.

The workbook should also show your work well enough that Sarah or IC can audit the major judgments
without reconstructing your whole process. Add a `Source Notes`, `Diligence Log`, or similar review
tab if the template does not already have a good place for this. Use it to briefly document the key
sources reviewed, source conflicts resolved, assumption changes made, and model checks performed.
This does not need to be a polished memo; it should be a practical audit trail for another reviewer.

After the initial case, Sarah's final revisions are a $50,000,000 purchase price, $40/SF spec-suite
TI, and spec-suite buildout starts pushed two months later. The final SouthPark model and LOI should
reflect those revised terms, and your notes or email reply should make the return impact clear.

## Underwriting Work

For SouthPark, the core work product is an IC-ready live workbook built from the template. Preserve
the template structure, including tabs, row labels, and monthly `Month #` headers, so the formulas
and review checks stay usable. Keep the diligence notes inside the workbook rather than in a
local-only scratch file.

The SouthPark workbook should be the file Sarah can take to IC: corrected rent roll and NOI bridge,
live cash flow, market support, leasing and capex assumptions, debt case, waterfall, sensitivities,
recommendation, and LOI.

For financing, do not use Atlantic Life as the active lender if the current materials show it is
stale or has no capacity. Compare the viable term sheets, size the loan from the model, and select
the lender with the best defensible execution. Capture the rationale in the model and in the reply to
Rachel.

For Ballantyne, do a concise screen rather than a full underwrite. Use the IM and rent roll to show
the WACC/return math, basic rollover and concentration risk, fund hurdle comparison, and verdict.
Update the tracker to `Screened - Pass` if the screen shows Harborview should pass on the deal.

## Before You Close The File

Set the tracker to the final state implied by the work: SouthPark Centre should be `LOI Sent`, and
Ballantyne Office Centre should be `Screened - Pass`.

Reply to the open deal emails with model-backed answers: Sarah's NOI reconciliation, the Ballantyne
screen verdict, Rachel's lender-selection question, and Sarah's final revision/return update. Keep
the replies concise and tied to the workbooks and the diligence trail you left there.

When you are done, the email thread, tracker, and workbooks should tell the same story.

