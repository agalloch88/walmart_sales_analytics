{% macro to_date_id(date_col) %}
    to_number(to_char({{ date_col }}, 'YYYYMMDD'))
{% endmacro %}