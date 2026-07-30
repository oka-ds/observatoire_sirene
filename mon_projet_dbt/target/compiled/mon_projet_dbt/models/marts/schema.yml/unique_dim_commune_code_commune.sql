
    
    

select
    code_commune as unique_field,
    count(*) as n_records

from "observatoire_sirene"."observatoire_observatoire"."dim_commune"
where code_commune is not null
group by code_commune
having count(*) > 1


