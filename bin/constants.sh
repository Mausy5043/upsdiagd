app_name="upsdiagd"

# determine controller's identity
host_name=$(hostname)


# construct database paths
database_filename="upsdata.sqlite3"
database_path="/srv/databases"
db_full_path="${database_path}/${database_filename}"
