SELECT 
    vp.cd_tab_fat
   ,vp.cd_pro_fat
   ,TO_CHAR(vp.dt_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_vigencia
   ,to_char(vp.vl_honorario) as vl_honorario
   ,to_char(vp.vl_operacional) as vl_operacional
   ,to_char(vp.vl_total) as vl_total
   ,vp.cd_import
   ,to_char(vp.vl_sh) as vl_sh
   ,to_char(vp.vl_sd) as vl_sd
   ,vp.qt_pontos
   ,vp.qt_pontos_anest
   ,vp.sn_ativo
FROM val_pro vp;