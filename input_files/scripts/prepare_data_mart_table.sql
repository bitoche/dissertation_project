create table if not exists &db_schema_rep.&data_mart_name (
    #cols_to_be_in_mart_with_types_script
);

delete from &db_schema_rep.&data_mart_name
where calc_id = &calc_id
;
