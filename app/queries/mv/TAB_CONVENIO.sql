SELECT 
    tc.CD_CON_PLA
    ,tc.CD_CONVENIO
    ,tc.CD_PRO_FAT
    ,TO_CHAR(tc.DT_VIGENCIA, 'YYYY-MM-DD hh24:mi:ss') as DT_VIGENCIA
    ,TO_CHAR(tc.VL_TAB_CONVENIO) as vl_tab_convenio
    ,tc.SN_USAR_INDICE
    ,tc.SN_ATIVO
    ,tc.SN_HORARIO_ESPECIAL
    ,tc.SN_FILME
    ,tc.CD_REGRA
    ,tc.CD_MULTI_EMPRESA
    ,tc.CD_TAB_CONVENIO
    ,tc.CD_PRESTADOR
    ,tc.CD_SETOR
FROM tab_convenio tc 