-- DLMS 867I, Issue: the depot issues the stock. Order-to-Cash: Fulfill Orders.

select
    document_number, nsn, psc, unit_of_issue, storage_activity,
    quantity as quantity_issued,
    issue_date,
    'A' as supply_condition_code,
    true as synthetic
from {{ ref('int_dlms_synth__orders') }}
