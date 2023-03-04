cd /data/Projects/shop_distance

nohup python3 -m src.get_basis_info --path /data/Projects/shop_distance > /data/Projects/shop_distance/aa.log 2>&1 &

nohup python3 -m src.ample_temp.py --period $1 --path /data/Projects/shop_distance > /data/Projects/shop_distance/aa2.log 2>&1 &