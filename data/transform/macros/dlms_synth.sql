{#-
  Building blocks for the dlms_synth models. Nothing in them is random: every invented value is
  taken from a hash of the award's key and a label saying what the value is for, so the same awards
  always give the same rows.
-#}

{# A number in [0, 1) that depends only on `key` and `purpose`. #}
{% macro draw(key, purpose) -%}
    (('0x' || substr(sha256({{ key }} || '/{{ purpose }}'), 1, 16))::ubigint / 18446744073709551616.0)
{%- endmacro %}

{# A code shaped like a DoD Activity Address Code. Real ones aren't used: these start with Z. #}
{% macro activity_code(name) -%}
    ('Z' || upper(substr(sha256({{ name }}), 1, 5)))
{%- endmacro %}

{#
  Shaped like a MILSTRIP document number: activity code, year digit and day of year, and a serial
  counting the documents that share those, in the order of `order_by`. The single year digit is the
  real format's, so the serial has to count across decades to keep the number unique.
#}
{% macro document_number(activity, day, order_by) -%}
    {%- set prefix = activity ~ " || (year(" ~ day ~ ") % 10)::varchar || strftime(" ~ day ~ ", '%j')" -%}
    ({{ prefix }} || lpad((row_number() over (partition by {{ prefix }} order by {{ order_by }}))::varchar, 4, '0'))
{%- endmacro %}
