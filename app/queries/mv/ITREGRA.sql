SELECT 
    cd_regra
    ,cd_tab_fat
    ,cd_gru_pro
    ,TO_CHAR(vl_percetual_pago) as vl_percetual_pago
    ,tp_hor_esp_sd
    ,cd_horario
    ,tp_valor_base
FROM itregra
