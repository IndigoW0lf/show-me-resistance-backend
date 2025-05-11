<?php
;// vim: ft=dosini:
;// Just in case the user is not protecting this file properly,
;// create a valid php file that also parses as an INI file
;die();
/* START OF REAL CONFIGURATION */

[database]
dsn = "mysql:host=localhost;port=3306;dbname=legiscan_api"
db_user = legiscan_api
db_pass = "Goddess88!Goddess88!"
massage_dates = 1

[memory_cache]
use_memcached = 0
memcache_host = localhost
memcache_port = 11211

[legiscan]
api_key = "ad252f849960a5479826a7941ae7ebd2"
api_auth_token = 
email = 
api_cache = "./cache/api"
doc_cache = "./cache/doc"
log_dir = "./log"
want_vote_details = 1
want_bill_text = 0
want_amendment = 0
want_supplement = 0
prefer_pdf = 0
;middleware_signal = table
;middleware_signal = directory

[legiscand]
;update_type = state
use_ignore_table = 0
interval = 10800
relevance = 50
states[] = MO
years[] = 2024

; END OF CONFIGURATION -- DO NOT MODIFY BELOW */
?>
