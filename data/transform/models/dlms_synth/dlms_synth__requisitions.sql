-- DLMS 511R, Requisition: a customer asks for an item from stock. Order-to-Cash: Accept Orders.

select
    document_number, nsn, psc, unit_of_issue,
    customer_activity as requisitioner,
    quantity as quantity_requisitioned,
    requisition_date, priority,
    true as synthetic
from {{ ref('int_dlms_synth__orders') }}
