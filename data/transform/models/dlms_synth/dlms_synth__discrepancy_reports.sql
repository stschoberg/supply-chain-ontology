-- DLMS 842A/W, Standard Supply Discrepancy Report (SDR) Notifications: the depot reports a shipment
-- that arrived short. Procure-to-Pay: Perform Receipt, Acceptance, and Return.

select
    tcn, award_key, piid, clin,
    storage_activity as reporting_activity,
    receipt_date + 1 as report_date,
    'SHORTAGE' as discrepancy,
    quantity_shipped, quantity_received,
    true as synthetic
from {{ ref('int_dlms_synth__shipments') }}
where is_short
