-- DLMS 940R, Materiel Release Order (MRO): the depot is told to release stock against a
-- requisition. Order-to-Cash: Fulfill Orders.

select
    document_number, nsn, psc, unit_of_issue, storage_activity,
    customer_activity as ship_to_activity,
    quantity as quantity_to_release,
    release_date,
    true as synthetic
from {{ ref('int_dlms_synth__orders') }}
