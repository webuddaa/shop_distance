cd /data/Projects/shop_distance

period_list='["15","15","30","60"]'

nohup /data/anaconda3/bin/python -m src.ample_temp --period_list ${period_list} --path /data/Projects/shop_distance > /data/Projects/shop_distance/bin/aa2.log 2>&1 &