rsync -avz --exclude "__history" --exclude "*~" --exclude "*.gif" --exclude "*.JPG" -e ssh . pi@envmon1.lan:/home/pi/envmon/
