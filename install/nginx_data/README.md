vi /etc/nginx/nginx.conf

http {
        client_max_body_size 10m;
}



service nginx reload


vi /etc/php5/fpm/php.ini

post_max_size = 10M
upload_max_filesize = 10M

service php5-fpm restart 


