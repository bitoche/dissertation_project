
-- deleting data with same calc_id
DELETE FROM &db_schema_rep.&data_mart_name 
WHERE calc_id = &calc_id;

with

prep__group_attrs as (
    #select_group_attrs_script
)

, prep__temp_res_table as (
    select 
        *
    from &db_schema_sandbox.&temp_table_name
)

#prep_refs_including_scripts

, prep__res_mart as (
    select
        #cols_to_be_in_mart
    from prep__group_attrs
    left join prep__temp_res_table trt
        #temp_res_table_to_mart_left_join_conditions_script
    #refs_to_mart_cols_left_join_scripts
    where prep__temp_res_table.&temp_res_table_amount_type_cd_column_name in (
        #report_amount_type_cd_list
    ) or prep__temp_res_table.&temp_res_table_amount_type_cd_column_name is null
)

insert into &db_schema_rep.&data_mart_name
    select 
        * 
    from prep__res_mart
;

drop &db_schema_sandbox.&temp_table_name
