cd /data/Projects/shop_distance

period_list='["30","60","day"]'

nohup /data/anaconda3/bin/python -m src.ample_temp --period_list ${period_list} --is_circle false --path /data/Projects/shop_distance > /data/Projects/shop_distance/bin/big_period.log 2>&1 &