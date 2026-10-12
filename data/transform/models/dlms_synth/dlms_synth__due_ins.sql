-- DLMS 527D, Pre-positioned Materiel Receipt (PMR) and Due-in Actions: the depot is told what to
-- expect from a purchase, and by when. Plan-to-Stock: Determine Source.

select
    award_key, piid, clin, nsn, psc, unit_of_issue, storage_activity, supplier_cage,
    quantity_ordered as quantity_due,
    performance_end_date as estimated_delivery_date,
    true as synthetic
from {{ ref('int_dlms_synth__purchases') }}
