-- DLMS 527R, Physical Receipt and Materiel Receipt Acknowledgement (MRA): the depot takes a shipment
-- into stock. Plan-to-Stock: Receive, Accept and Warehouse Inventory.

select
    tcn, award_key, piid, clin, nsn, psc, unit_of_issue, storage_activity, quantity_received,
    receipt_date,
    -- A: serviceable, issuable without qualification.
    'A' as supply_condition_code,
    true as synthetic
from {{ ref('int_dlms_synth__shipments') }}
