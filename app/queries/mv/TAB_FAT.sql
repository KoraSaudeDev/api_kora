SELECT 
    cd_tab_fat
	,NULLIF(REGEXP_REPLACE(ds_tab_fat,'[''"!/:@;]', ''),'') as ds_tab_fat
    ,tp_tab_fat
    ,tp_tab_fat_tiss
FROM tab_fat;
