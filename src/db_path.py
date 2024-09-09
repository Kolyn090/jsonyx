import secret_path

# data and system might not be storing under the same directory
# data path can be just the relative directory to the data
# system path must be stored within the DBMS (usr/db/system)

# data_path = f'../usr/example-db/data'
# system_path = f'../usr/example-db/system'
data_path = secret_path.data_path
system_path = secret_path.system_path
