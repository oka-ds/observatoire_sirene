
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select libelle_commune
from "observatoire_sirene"."observatoire_observatoire"."dim_commune"
where libelle_commune is null



  
  
      
    ) dbt_internal_test