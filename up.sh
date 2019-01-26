rsync -avz --exclude "__history" --exclude "*~" --exclude "*.gif" --exclude "*.JPG" --exclude "*.rrd" --exclude "*.png" --exclude "graphs"  -e ssh . pi@envmon1.lan:/home/pi/envmon/
